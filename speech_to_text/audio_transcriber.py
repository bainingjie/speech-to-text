import asyncio
import functools
import eel
import queue
import numpy as np

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor

from .vad import Vad
from .websoket_server import WebSocketServer
from .openai_api import OpenAIAPI
from .llm import CustomChatbot

import uuid
from datetime import datetime
from .utils.file_utils import write_audio

class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 8
    noise_threshold: int = 5
    non_speech_threshold: float = 0.1
    include_non_speech: bool = False
    create_audio_file: bool = False
    use_websocket_server: bool = False
    use_openai_api: bool = False


class AudioTranscriber:
    def __init__(
        self,
        event_loop: asyncio.AbstractEventLoop,
        whisper_model: WhisperModel,
        transcribe_settings: dict,
        app_options: AppOptions,
        websocket_server: WebSocketServer,
        openai_api: OpenAIAPI,
        tts_queue: queue.Queue
    ):
        self.event_loop = event_loop
        self.whisper_model: WhisperModel = whisper_model
        self.transcribe_settings = transcribe_settings
        self.app_options = app_options
        self.websocket_server = websocket_server
        self.openai_api = openai_api
        self.vad = Vad(app_options.non_speech_threshold)
        self.silence_counter: int = 0
        self.audio_data_list = []
        self.all_audio_data_list = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None
        self.chatbot = CustomChatbot(tts_queue)
        self.processing_task = None

    async def transcribe_audio(self, audio_data: np.ndarray):
        # print(f"Audio data shape: {audio_data.shape}")  # 追加: 音声データの形状を出力
        # print(f"Audio data dtype: {audio_data.dtype}")  # 追加: 音声データの型を出力
        # eel.on_recive_message("Received audio data from WebSocket")  # 追加

        # Ignore parameters that affect performance
        transcribe_settings = self.transcribe_settings.copy()
        transcribe_settings["without_timestamps"] = True
        transcribe_settings["word_timestamps"] = False

        with ThreadPoolExecutor() as executor:
            # Create a partial function for the model's transcribe method
            func = functools.partial(
                self.whisper_model.transcribe,
                audio=audio_data,
                **transcribe_settings,
            )

            # Run the transcribe method in a thread
            # eel.on_recive_message("partiral function start run")
            segments, _ = await self.event_loop.run_in_executor(executor, func)
            # eel.on_recive_message("partial function done")

            for segment in segments:
                print(f"Transcribed text: {segment.text}")
                eel.on_recive_message(f"Transcribed text: {segment.text}") 
                eel.display_transcription(segment.text)
                eel.on_recive_message(f"transcribed. Timestamp: {datetime.now().isoformat()}")
                await self.chatbot.run(segment.text)
                


    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        # # Generate a unique filename using timestamp or UUID
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # # uuid_str = str(uuid.uuid4())
        # filename = f"audio_{timestamp}.wav"
        # # Save the audio_data to a file
        # write_audio(r'C:\Users\ningj\Documents\GitHub\speech-to-text\temp_audio_files', filename, audio_data)

        is_speech = self.vad.is_speech(audio_data)
        if is_speech:
            # eel.on_recive_message("is_speech before append")
            self.silence_counter = 0
            self.audio_data_list.append(audio_data)
            # eel.on_recive_message("is_speech after append")
        else:
            self.silence_counter += 1
            # if self.silence_counter == 1:
            #     eel.on_recive_message("silence counter is 1")


        if not is_speech and self.silence_counter > self.app_options.silence_limit:
            self.silence_counter = 0

            if len(self.audio_data_list) > self.app_options.noise_threshold:
                eel.on_recive_message(f"audio queue before put . Timestamp: {datetime.now().isoformat()}")
                concatenate_audio_data = np.concatenate(self.audio_data_list)
                # eel.on_recive_message("audio queue put end")
                self.audio_data_list.clear()
                self.audio_queue.put(concatenate_audio_data.flatten())
                eel.on_recive_message(f"audio queue put . Timestamp: {datetime.now().isoformat()}")
            else:
                # noise clear
                self.audio_data_list.clear()

    async def start_transcription(self):
        try:
            self.transcribing = True
            self._running.set()
            # eel.on_recive_message("Transcription started.")
            self.processing_task = asyncio.create_task(self.process_audio_queue())
            while self._running.is_set():
                await asyncio.sleep(1)
        except Exception as e:
            eel.on_recive_message(str(e))

    async def process_audio_queue(self):
        while self._running.is_set():
            # eel.on_recive_message("process_audio_queue running.")
            try:
                audio_data = self.audio_queue.get(block=False)
                # eel.on_recive_message("got from audio queue")
                await self.transcribe_audio(audio_data)
            except queue.Empty:
                await asyncio.sleep(0.1)

    async def stop_transcription(self):
        try:
            self.transcribing = False
            self._running.clear()
            if self.processing_task is not None:
                self.processing_task.cancel()
                self.processing_task = None
            eel.on_recive_message("Transcription stopped.")
        except Exception as e:
            eel.on_recive_message(str(e))