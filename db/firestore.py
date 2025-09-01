from google.cloud import firestore
from datetime import datetime, timedelta

from .common import TIME_FORMAT


class FirestoreDB:
    def __init__(self):
        # 환경변수 GOOGLE_APPLICATION_CREDENTIALS가 자동 적용됨
        client = firestore.Client(database="d2r-traderie")
        self._collection = client.collection("recent-trades")

    def get_trades(self) -> dict:
        item_trades = {}
        for doc in self._collection.stream():
            item_trades[doc.id] = doc.to_dict()

        return item_trades
