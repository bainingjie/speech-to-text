from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os,copy,eel,datetime
from .tts import get_audio_file_from_text
from .prompt import *
from langchain.memory import ChatMessageHistory

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()
class CustomChatbot:
    def __init__(self,tts_queue):
        
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.chat = self.create_chat_anthropic()
        self.tts_queue = tts_queue
        self.temp = ""
        self.chain_with_message_history = None

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                   electricity,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | self.chat
        demo_ephemeral_chat_history_for_chain = ChatMessageHistory()

        self.chain_with_message_history = RunnableWithMessageHistory(
            chain,
            lambda session_id: demo_ephemeral_chat_history_for_chain,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def create_chat_anthropic(self):
        return ChatAnthropic(
            temperature=0,
            api_key=self.claude_api_key,
            # claude-3-haiku-20240307
            # claude-3-sonnet-20240229
            model_name="claude-3-haiku-20240307",
            streaming=True
        )



    async def run(self,text):
        async for chunk in self.chain_with_message_history.astream(        
            {"input": text},{"configurable": {"session_id": "unused"}}):
            self.temp += chunk.content
            for split_word in ["。", "?", "!"]:
                if split_word in self.temp:                    
                    eel.on_recive_message(f"{self.temp} LLM responded. Timestamp: {datetime.datetime.now().isoformat()}")
                    temp2 = copy.deepcopy(self.temp)
                    self.temp = ""
                    
                    wav_data = get_audio_file_from_text(temp2,1.1)
                    eel.on_recive_message(f"got audio synthesized. Timestamp: {datetime.datetime.now().isoformat()}")

                    self.tts_queue.put(wav_data)
                

# if __name__ == "__main__":
#     chatbot = CustomChatbot()
#     chatbot.run("hi")


