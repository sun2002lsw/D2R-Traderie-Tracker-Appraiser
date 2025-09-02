import json
import math
import os
from typing import Dict, List, Optional, Tuple


class AnchorLayeredTrimmedSolver:
    """
    앵커(Perfect Amethyst=1) 단일 오퍼로 씨딩 → 알려진 RHS만으로 LHS 단가 후보 산출 →
    (리테일 우선) 집계로 값 결정.
    solve_with_trimming()은 1차 추정치로 각 아이템의 trade 단가 분포를 계산해
    하위/상위 alpha 비율(기본 10%)을 제외하고 다시 평가한다.
    """

    def __init__(
        self,
        anchor_item: str = "Perfect Amethyst",
        max_iters: int = 50,
        retail_cnt_max: int = 5,  # 리테일로 간주할 최대 묶음
        agg_quantile: float = 0.5,  # 0.5 = 중앙값
        trim_alpha: float = 0.10,  # 하위/상위 절단 비율(각각 alpha)
        trim_min_trades: int = 10,  # 트리밍을 적용하기 위한 최소 trade 개수
    ):
        self.anchor_item = anchor_item
        self.max_iters = max_iters
        self.retail_cnt_max = retail_cnt_max
        self.agg_quantile = agg_quantile
        self.trim_alpha = trim_alpha
        self.trim_min_trades = trim_min_trades

    # ----------------- 유틸 -----------------

    def _round_rule(self, x: float):
        return round(x, 1) if x < 10 else int(round(x))

    def _quantile(self, arr: List[float], q: float) -> float:
        """0~1 사이 q분위 (선형보간 대신 가장 가까운 인덱스)."""
        if not arr:
            return float("nan")
        arr_sorted = sorted(arr)
        idx = int(round(q * (len(arr_sorted) - 1)))
        return arr_sorted[idx]

    def _seed_from_anchor(self, trades_by_item: Dict) -> Tuple[Dict[str, float], set]:
        values: Dict[str, float] = {self.anchor_item: 1.0}
        known = {self.anchor_item}

        for cntA, offers in trades_by_item.get(self.anchor_item, []):
            if cntA <= 0:
                continue
            for offer in offers:
                if len(offer) != 1:
                    continue
                m, name = offer[0]
                if m <= 0:
                    continue
                val = cntA / m  # v(anchor)=1
                if (name not in values) or (val < values[name]):
                    values[name] = val
                    known.add(name)
        return values, known

    def _offer_cost_if_known(
        self, offer: List[List], values: Dict[str, float], known: set
    ) -> Optional[float]:
        s = 0.0
        for m, name in offer:
            if name not in known:
                return None
            v = values.get(name)
            if v is None or not math.isfinite(v) or v <= 0:
                return None
            s += m * v
        return s

    def _aggregate_units(self, units: List[Tuple[int, float]]) -> Optional[float]:
        """
        units: [(cntA, unit_cost), ...]
        리테일(cntA ≤ retail_cnt_max) 표본이 있으면 그것만, 없으면 전체에서
        agg_quantile(기본 중앙값)을 반환.
        """
        if not units:
            return None
        retail = [u for c, u in units if c <= self.retail_cnt_max]
        pool = retail if retail else [u for _, u in units]
        if not pool:
            return None
        pool.sort()
        q = min(max(self.agg_quantile, 0.0), 1.0)
        idx = int(round(q * (len(pool) - 1)))
        return pool[idx]

    # ----------------- 핵심 로직 -----------------

    def appraise(self, trades_by_item: Dict) -> Dict[str, float]:
        """
        (트리밍 없이) 한 번의 레이어드 전파로 값 계산.
        """
        values, known = self._seed_from_anchor(trades_by_item)

        changed = True
        iters = 0
        while changed and iters < self.max_iters:
            changed = False
            iters += 1

            for item, trade_list in trades_by_item.items():
                if item in known:
                    continue
                units: List[Tuple[int, float]] = []
                for cntA, offers in trade_list:
                    if cntA <= 0:
                        continue
                    best_for_trade = math.inf
                    feasible = False
                    for offer in offers:
                        cost = self._offer_cost_if_known(offer, values, known)
                        if cost is None:
                            continue
                        feasible = True
                        best_for_trade = min(best_for_trade, cost / cntA)
                    if feasible and math.isfinite(best_for_trade):
                        units.append((cntA, best_for_trade))

                agg = self._aggregate_units(units)
                if agg is not None:
                    prev = values.get(item)
                    if (prev is None) or (agg < prev - 1e-12):
                        values[item] = agg
                        known.add(item)
                        changed = True

        # 누락 금지 & 포맷팅
        for k in trades_by_item.keys():
            v = values.get(k)
            if v is None or not math.isfinite(v) or v <= 0:
                values[k] = 0.0
        items_sorted = sorted(values.items(), key=lambda kv: -kv[1])
        out = {k: (0 if v <= 0 else self._round_rule(v)) for k, v in items_sorted}
        out[self.anchor_item] = 1
        return out

    # -------- 트리밍(중앙 80%)을 위한 2패스 --------

    def _collect_unit_costs_per_item(
        self, trades_by_item: Dict, values: Dict[str, float]
    ) -> Dict[str, List[Tuple[int, float, int]]]:
        """
        현재 values로 각 아이템의 tradeInfo별 '최저 offer 단가'를 계산.
        반환: item -> [(cntA, unit_cost, trade_index), ...]
        """
        known = {k for k, v in values.items() if v and math.isfinite(v) and v > 0}
        per_item_units: Dict[str, List[Tuple[int, float, int]]] = {}
        for item, trade_list in trades_by_item.items():
            acc = []
            for idx, (cntA, offers) in enumerate(trade_list):
                if cntA <= 0:
                    continue
                best = math.inf
                feasible = False
                for offer in offers:
                    c = self._offer_cost_if_known(offer, values, known)
                    if c is None:
                        continue
                    feasible = True
                    best = min(best, c / cntA)
                if feasible and math.isfinite(best):
                    acc.append((cntA, best, idx))
            per_item_units[item] = acc
        return per_item_units

    def _trim_trades_by_units(
        self,
        trades_by_item: Dict,
        units_per_item: Dict[str, List[Tuple[int, float, int]]],
    ) -> Dict:
        """
        각 아이템별로 (cntA, unit, idx) 리스트에서 하/상위 trim_alpha 비율 제거 후,
        남은 tradeInfo만 유지한 새로운 trades_by_item을 반환.
        """
        trimmed = {}
        for item, trade_list in trades_by_item.items():
            units = units_per_item.get(item, [])
            # 트리밍 적용 조건
            if len(units) >= self.trim_min_trades and 0 < self.trim_alpha < 0.5:
                unit_vals = [u for _, u, _ in units]
                lo = self._quantile(unit_vals, self.trim_alpha)
                hi = self._quantile(unit_vals, 1.0 - self.trim_alpha)
                keep_indices = {idx for _, u, idx in units if lo <= u <= hi}
                trimmed[item] = [
                    ti for i, ti in enumerate(trade_list) if i in keep_indices
                ]
            else:
                # 표본이 작으면 트리밍 없음
                trimmed[item] = list(trade_list)
        return trimmed

    def solve_with_trimming(
        self, trades_by_item: Dict, passes: int = 2
    ) -> Dict[str, float]:
        """
        1) 트리밍 없이 1차 추정(appraise)
        2) 그 값으로 각 아이템 trade의 단가 분포를 산출 → 중앙 80%만 남김
        3) 필터된 데이터로 재평가(appraise)
        passes>2면 (트리밍→재평가)을 반복 수행.
        """
        # 1차
        values1 = self.appraise(trades_by_item)

        # 반복
        filtered = dict(trades_by_item)
        values = values1
        for _ in range(max(1, passes - 1)):
            units = self._collect_unit_costs_per_item(filtered, values)
            filtered = self._trim_trades_by_units(filtered, units)
            values = self.appraise(filtered)

        return values


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file_path = os.path.join(current_dir, "sample_input.json")
    with open(sample_file_path, "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    appraiser = AnchorLayeredTrimmedSolver()
    result = appraiser.appraise(sample_data)
    print(result)
