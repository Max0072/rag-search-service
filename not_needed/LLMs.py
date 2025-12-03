from abc import ABC, abstractmethod

from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
import os
from dotenv import load_dotenv




class BaseLLMClass(ABC):
    @abstractmethod
    def ask(self, prompt: str) -> str:
        pass


class LLMopenAI(BaseLLMClass):
    def __init__(self):
        load_dotenv()

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


    def ask(self, prompt: str) -> str:
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": "You are a helpful assistant that answers in Russian."
        }
        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt
        }

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_message, user_message],
        )
        return resp.choices[0].message.content








if __name__ == "__main__":
    load_dotenv()

    model = LLMopenAI()
    answer = model.ask("Расскажи, что такое градиентный бустинг")
    print(answer)