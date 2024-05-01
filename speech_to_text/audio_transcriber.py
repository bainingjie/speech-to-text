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

    async def transcribe_audio(self, audio_data: np.ndarray):
        print(f"Audio data shape: {audio_data.shape}")  # 追加: 音声データの形状を出力
        print(f"Audio data dtype: {audio_data.dtype}")  # 追加: 音声データの型を出力
        eel.on_recive_message("Received audio data from WebSocket")  # 追加

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
            eel.on_recive_message("partiral function start run")
            segments, _ = await self.event_loop.run_in_executor(executor, func)
            eel.on_recive_message("partial function done")

            for segment in segments:
                print(f"Transcribed text: {segment.text}")
                eel.on_recive_message(f"Transcribed text: {segment.text}") 
                eel.display_transcription(segment.text)
                await self.chatbot.run(segment.text)


    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        is_speech = self.vad.is_speech(audio_data)
        if is_speech:
            self.silence_counter = 0
            self.audio_data_list.append(audio_data.flatten())
        else:
            self.silence_counter += 1
            if self.app_options.include_non_speech:
                self.audio_data_list.append(audio_data.flatten())

        if not is_speech and self.silence_counter > self.app_options.silence_limit:
            self.silence_counter = 0

            if self.app_options.create_audio_file:
                self.all_audio_data_list.extend(self.audio_data_list)

            if len(self.audio_data_list) > self.app_options.noise_threshold:
                concatenate_audio_data = np.concatenate(self.audio_data_list)
                self.audio_data_list.clear()
                self.audio_queue.put(concatenate_audio_data)
            else:
                # noise clear
                self.audio_data_list.clear()

    def batch_transcribe_audio(self, audio_data: np.ndarray):
        segment_list = []
        segments, _ = self.whisper_model.transcribe(
            audio=audio_data, **self.transcribe_settings
        )

        for segment in segments:
            word_list = []
            if self.transcribe_settings["word_timestamps"] == True:
                for word in segment.words:
                    word_list.append(
                        {
                            "start": word.start,
                            "end": word.end,
                            "text": word.word,
                        }
                    )
            segment_list.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": word_list,
                }
            )

        eel.transcription_clear()

        if self.openai_api is not None:
            self.text_proofreading(segment_list)
        else:
            eel.on_recive_segments(segment_list)

    def text_proofreading(self, segment_list: list):
        # Use [#] as a separator
        combined_text = "[#]" + "[#]".join(segment["text"] for segment in segment_list)
        result = self.openai_api.text_proofreading(combined_text)
        split_text = result.split("[#]")

        del split_text[0]

        eel.display_transcription("Before text proofreading.")
        eel.on_recive_segments(segment_list)

        if len(split_text) == len(segment_list):
            for i, segment in enumerate(segment_list):
                segment["text"] = split_text[i]
                segment["words"] = []
            eel.on_recive_message("proofread success.")
            eel.display_transcription("After text proofreading.")
            eel.on_recive_segments(segment_list)
        else:
            eel.on_recive_message("proofread failure.")
            eel.on_recive_message(result)

    async def start_transcription(self):
        try:
            self.transcribing = True
            self._running.set()
            eel.on_recive_message("Transcription started.")
            while self._running.is_set():
                await asyncio.sleep(1)
        except Exception as e:
            eel.on_recive_message(str(e))

    async def stop_transcription(self):
        try:
            self.transcribing = False
            if self._transcribe_task is not None:
                self.event_loop.call_soon_threadsafe(self._transcribe_task.cancel)
                self._transcribe_task = None

            # ... (streamに関連する処理を削除)

            eel.on_recive_message("Transcription stopped.")
        except Exception as e:
            eel.on_recive_message(str(e))