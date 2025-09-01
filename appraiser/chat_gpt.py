import os

from openai import OpenAI


class ChatGPT:
    def __init__(self):
        # 환경변수 OPENAI_API_KEY가 자동 적용됨
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

        self._client = OpenAI(api_key=api_key)

    def _get_initial_system_prompt(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompt.txt")
        prompt = open(prompt_path, "r").read()
        print(prompt)

        message = dict()
        message["role"] = "system"
        message["content"] = prompt

        return message

    def _send_message(self, system_message: dict, user_message: dict) -> str:
        messages = []
        messages.append(system_message)
        messages.append(user_message)

        response = self._client.chat.completions.create(
            model="gpt-4o-mini", messages=messages
        )

        return response.choices[0].message.content

    def echo(self, user_input: str) -> str:
        system_message = {"role": "system", "content": "내 말을 그대로 따라해"}
        user_message = {"role": "user", "content": user_input}

        return self._send_message(system_message, user_message)

    def request_appraise(self, user_input: str) -> str:
        system_prompt = self._get_initial_system_prompt()
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": user_input}

        return self._send_message(system_message, user_message)
