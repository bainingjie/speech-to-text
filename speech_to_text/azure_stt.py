import asyncio
import websockets
import threading
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
from .llm import CustomChatbot


tts_queue=None
chatbot = None
def init_tts_queue(x):
    global tts_queue,chatbot
    if tts_queue == None:
        tts_queue=x
        chatbot = CustomChatbot(tts_queue)

load_dotenv()

speech_key = os.getenv('AZURE_SUBSCRIPTION_KEY')
service_region = os.getenv('AZURE_REGION')

# Create a speech configuration
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "ja-JP"

# Setup the audio stream
audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000,
                                                    bits_per_sample=8,
                                                    channels=1,
                                                    wave_stream_format=speechsdk.AudioStreamWaveFormat.MULAW)
stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
audio_config = speechsdk.audio.AudioConfig(stream=stream)

# Instantiate the speech recognizer with push stream input
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

recognition_done = threading.Event()

# Connect callbacks to the events fired by the speech recognizer
def session_stopped_cb(evt):
    print('SESSION STOPPED: {}'.format(evt))
    recognition_done.set()

def recognized_cb(evt):
    global chatbot
    print('RECOGNIZED: {}'.format(evt))
    print(evt.result.text)
    asyncio.run(chatbot.run(evt.result.text))
    

speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
speech_recognizer.recognized.connect(recognized_cb)
speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
speech_recognizer.session_stopped.connect(session_stopped_cb)
speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))

# Start continuous speech recognition
speech_recognizer.start_continuous_recognition()



async def transcribe_audio(audio_data):
    
    # Push the received audio data to the stream
    stream.write(audio_data)

# stream.close()
# # Wait until all input processed
# recognition_done.wait()
# # Stop recognition and clean up
# speech_recognizer.stop_continuous_recognition()

# async def main():
#     async with websockets.serve(transcribe_audio, "localhost", 8000):
#         await asyncio.Future()  # Run forever

# asyncio.run(main())