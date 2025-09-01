import boto3
import json
from datetime import datetime

from .common import TIME_FORMAT


class DynamoDB:
    """DynamoDB 클라이언트 클래스"""

    def __init__(self):
        # 환경변수로 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY가 자동 적용됨
        db = boto3.resource("dynamodb", region_name="ap-northeast-2")
        db.describe_table("d2r-traderie-values")  # 연결 확인

        self._table = db.Table("d2r-traderie-values")

    def put_values(self, item_values: dict, item_trades: dict) -> None:
        if set(item_values.keys()) != set(item_trades.keys()):
            raise ValueError("item_trades와 item_values의 아이템이 다릅니다.")

        item_values_with_trades = {}
        for item_name, item_value in item_values.items():
            item_values_with_trades[item_name] = {}
            item_values_with_trades[item_name]["value"] = item_value
            item_values_with_trades[item_name]["trades"] = item_trades[item_name]

        values_json = json.dumps(item_values_with_trades, ensure_ascii=False)
        item_data = {
            "update_time": datetime.now().strftime(TIME_FORMAT),
            "item_values": values_json,
        }

        self._table.put_item(Item=item_data)
