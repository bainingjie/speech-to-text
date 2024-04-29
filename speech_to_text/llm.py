from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from dotenv import load_dotenv
import os

class CustomChatbot:
    def __init__(self):
        load_dotenv()
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.conversational_memory_length = 5
        self.memory = ConversationBufferWindowMemory(k=self.conversational_memory_length)
        self.chat = self.create_chat_anthropic()
        self.prompt = self.create_custom_prompt()
        self.conversation = self.create_conversation_chain()

    def create_chat_anthropic(self):
        return ChatAnthropic(
            temperature=0,
            api_key=self.claude_api_key,
            model_name="claude-3-sonnet-20240229",
            streaming=True,
            callback_manager=AsyncCallbackManager([MyCustomCallbackHandler()])
        )

    def create_custom_prompt(self):
        template = '''
        貴方は愉快な会話できる友達です。毎度の回答はなるべく45文字以内に抑えてください。返答は、質問と同じ言語を使ってください。
        Current conversation: {history}
        Human: {input}
        AI Assistant:"""
        '''
        return PromptTemplate(input_variables=["history", "input"], template=template)

    def create_conversation_chain(self):
        return ConversationChain(
            llm=self.chat,
            prompt=self.prompt,
            memory=self.memory
        )

    def run(self,text):
        response = self.conversation.invoke(text)
        return response

class MyCustomCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.temp = ""

    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        '''新しいtokenが来たらprintする'''
        self.temp = self.temp + token
        for split_word in ["、", "。", "?", "!"]:
            if split_word in self.temp:
                print(self.temp)
                self.temp = ""

# if __name__ == "__main__":
#     chatbot = CustomChatbot()
#     chatbot.run("hi")