import os
from openai import OpenAI


class ChatGPT:
    def __init__(self):
        # 환경변수 OPENAI_API_KEY가 자동 적용됨
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

        message = self._get_initial_system_messages()

        self._client = OpenAI(api_key=api_key)
        self._messages = [message]

    def _get_initial_system_messages(self):
        message = dict()
        message["role"] = "system"
        message["content"] = ""

    def ask(self, user_input: str) -> str:
        # 유저 메시지 추가
        self._messages.append({"role": "user", "content": user_input})

        # API 호출
        response = self._client.chat.completions.create(
            model="gpt-5", messages=self._messages
        )

        # 모델 응답 꺼내기
        assistant_reply = response.choices[0].message.content

        # assistant 메시지를 대화 이력에 추가
        self._messages.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply
