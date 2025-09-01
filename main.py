from appraiser.chat_gpt import ChatGPT
from db import DynamoDB, FirestoreDB
from helper import log_print

log_print("===== 객체 생성 시작 =====")
firestore = FirestoreDB()
dynamodb = DynamoDB()
chat_gpt = ChatGPT()
log_print("===== 객체 생성 완료 =====")

log_print("===== 아이템 거래 내역 추출 시작 =====")
item_trades = firestore.get_trades()
for item_name, trades in item_trades.items():
    log_print(f"{item_name}: {trades}")
log_print("===== 아이템 거래 내역 추출 완료 =====")
