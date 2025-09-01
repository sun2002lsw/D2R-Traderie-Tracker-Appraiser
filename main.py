import json
import time
from datetime import datetime, timedelta

import db
from appraiser.chat_gpt import ChatGPT
from helper import log_print

log_print("===== 객체 생성 시작 =====")
firestore = db.FirestoreDB()
dynamodb = db.DynamoDB()
chat_gpt = ChatGPT()
log_print("===== 객체 생성 완료 =====")
time.sleep(1)

log_print("===== 아이템 거래 내역 추출 시작 =====")
item_trades = firestore.get_trades()
for item_name, trades in item_trades.items():
    log_print(f"{item_name}: {trades}")
log_print(f"===== {len(item_trades)}개의 아이템 추출 완료 =====")
time.sleep(1)

log_print("===== 오래된 거래 내역 삭제 시작 =====")
query_item_trades = dict()
for item_name, trades in item_trades.items():
    update_time = datetime.strptime(trades["update_time"], db.TIME_FORMAT)
    if datetime.now() - update_time > timedelta(hours=3):
        log_print(f"{item_name}: {trades["update_time"]}")
    else:
        query_item_trades[item_name] = trades["trade_list"]
log_print("===== 오래된 거래 내역 삭제 완료 =====")
time.sleep(1)

if len(query_item_trades) == 0:
    log_print("===== 분석할 아이템이 하나도 없음 =====")
    exit()

log_print(f"===== {len(query_item_trades)}개의 아이템에 대해 분석 시작 =====")
trades_json = json.dumps(query_item_trades, ensure_ascii=False, indent=2)
item_values = json.loads(chat_gpt.ask(trades_json))
for item_name, item_value in item_values.items():
    log_print(f"{item_name}: {item_value}")
log_print("===== 분석 완료 =====")
time.sleep(1)

log_print("===== 분석 결과 저장 시작 =====")
dynamodb.put_values(item_values, query_item_trades)
log_print("===== 분석 결과 저장 완료 =====")
