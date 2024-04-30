from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
import os,copy,eel
from .tts import get_audio_file_from_text

class CustomChatbot:
    def __init__(self,tts_queue):
        load_dotenv()
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.chat = self.create_chat_anthropic()
        self.tts_queue = tts_queue
        self.temp = ""

    def create_chat_anthropic(self):
        return ChatAnthropic(
            temperature=0,
            api_key=self.claude_api_key,
            model_name="claude-3-sonnet-20240229",
            streaming=True,

        )


    async def run(self,text):


        # response = self.conversation.invoke(text)

        eel.on_recive_message("start run")
        # chunks = []

        async for chunk in self.chat.astream(text):
            self.temp += chunk.content
            for split_word in ["。", "?", "!"]:
                if split_word in self.temp:
                    eel.on_recive_message(self.temp)
                    temp2 = copy.deepcopy(self.temp)
                    self.temp = ""
                    wav_data = get_audio_file_from_text(temp2)
                    self.tts_queue.put(wav_data)
                    
        # eel.on_recive_message(response)
        # eel.on_recive_message("getting audio from voicevox")
        # wav_data = get_audio_file_from_text(response)
        # eel.on_recive_message("recieved audio from voicevox")
        # self.tts_queue.put(wav_data)


class MyCustomCallbackHandler(BaseCallbackHandler):
    def __init__(self, tts_queue):
        self.temp = ""
        self.tts_queue = tts_queue
    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        '''新しいtokenが来たらprintする'''
        self.temp = self.temp + token

        # for split_word in ["。", "?", "!"]:
        #     if split_word in self.temp:
        #         eel.on_recive_message(self.temp)
        #         eel.on_recive_message("getting audio from voicevox")
        #         temp2 = copy.deepcopy(self.temp)
        #         self.temp = ""
        #         wav_data = get_audio_file_from_text(temp2)
        #         eel.on_recive_message("recieved audio from voicevox")
        #         self.tts_queue.put(wav_data)
                

# if __name__ == "__main__":
#     chatbot = CustomChatbot()
#     chatbot.run("hi")


