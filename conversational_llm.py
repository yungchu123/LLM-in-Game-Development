from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain_openai import ChatOpenAI

class ConversationalLLM:
    def __init__(self):
        self.chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        self.messages = [
            SystemMessage(content="You name is Misty. You are a cheerful young lady.")
        ]
        
    def get_response(self, prompt):
        self.messages.append(HumanMessage(content=prompt))
        response = self.chat.invoke(self.messages)
        self.messages.append(AIMessage(content=response.content))
        return response.content