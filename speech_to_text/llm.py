from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
import os,copy,eel,datetime
from .tts import get_audio_file_from_text
from .prompt import system_prompt

load_dotenv()


class CustomChatbot:
    def __init__(self,tts_queue):
        
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.chat = self.create_chat_anthropic()
        self.tts_queue = tts_queue
        self.temp = ""

    def create_chat_anthropic(self):
        return ChatAnthropic(
            temperature=0,
            api_key=self.claude_api_key,
            # claude-3-haiku-20240307
            # claude-3-sonnet-20240229
            model_name="claude-3-sonnet-20240229",
            streaming=True,
            model_kwargs=dict(system=system_prompt)
        )


    async def run(self,text):
        async for chunk in self.chat.astream(text):
            self.temp += chunk.content
            for split_word in ["。", "?", "!"]:
                if split_word in self.temp:
                    print("llm responded")
                    eel.on_recive_message(f"{self.temp} LLM responded. Timestamp: {datetime.datetime.now().isoformat()}")
                    temp2 = copy.deepcopy(self.temp)
                    self.temp = ""
                    wav_data = get_audio_file_from_text(temp2,1.1)
                    eel.on_recive_message(f"got audio synthesized. Timestamp: {datetime.datetime.now().isoformat()}")
                    self.tts_queue.put(wav_data)
                

# if __name__ == "__main__":
#     chatbot = CustomChatbot()
#     chatbot.run("hi")


