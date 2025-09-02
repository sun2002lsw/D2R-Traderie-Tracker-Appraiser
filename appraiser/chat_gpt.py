import os

from openai import OpenAI


class ChatGPT:
    def __init__(self):
        # 환경변수 OPENAI_API_KEY가 자동 적용됨
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

        self._client = OpenAI(api_key=api_key)

    def _get_initial_system_prompt(self) -> dict:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "chat_gpt_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()

        return {"role": "system", "content": prompt}

    def _send_message(self, system_message: dict, user_message: dict) -> str:
        messages = [system_message, user_message]
        response = self._client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            response_format={"type": "json_object"},
            # gpt-4.1, gpt-4o 전용
            # temperature=0,
        )

        return response.choices[0].message.content

    def echo(self, user_input: str) -> str:
        system_message = {"role": "system", "content": "내 말을 그대로 따라해"}
        user_message = {"role": "user", "content": user_input}

        return self._send_message(system_message, user_message)

    def request_appraise(self, user_input: str) -> str:
        system_message = self._get_initial_system_prompt()
        user_message = {"role": "user", "content": user_input}

        return self._send_message(system_message, user_message)
