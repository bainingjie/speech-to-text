import os
import io
import eel
import asyncio
import base64
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer, SpeechSynthesisOutputFormat, ResultReason
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio as sa
def get_audio_file_from_text(text, rate=1.0):
    eel.on_recive_message("tts request1 start")
    audio_data = get_azure_tts_audio(text, rate)
    return audio_data

def get_azure_tts_audio(text, rate=1.0):
    speech_config = SpeechConfig(subscription=os.getenv("AZURE_SUBSCRIPTION_KEY"), region=os.getenv("AZURE_REGION"))
    speech_config.speech_synthesis_voice_name = "ja-JP-NanamiNeural"
    speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    
    ssml_template = """
    <speak version='1.0' xmlns="https://www.w3.org/2001/10/synthesis" xml:lang='ja-JP'>
        <voice name="ja-JP-NanamiNeural">
            <prosody  rate='{}'>
                {}
            </prosody>
        </voice>
    </speak>
    """
    
    ssml = ssml_template.format(rate, text)
    
    result = synthesizer.speak_ssml_async(ssml).get()
    
    if result.reason == ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        # Trim the audio to remove the click noise at the end
        audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
        trimmed_audio_segment = audio_segment[:-200]  # Trim the last 100 milliseconds
        trimmed_audio_data = trimmed_audio_segment.raw_data
        return trimmed_audio_data
    elif result.reason == ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        print("Error details: {}".format(cancellation_details.error_details))
    else:
        raise Exception(f"Speech synthesis failed: {result.reason}")

def tts_worker(tts_queue, websocket_server):
    while True:
        wav_data = tts_queue.get()
        if wav_data is None:
            break

        # # Create a PlayObject from the WAV data
        # print("running")
        # play_obj = sa.play_buffer(wav_data, 1, 2, 16000)

        # # Wait for the audio to finish playing
        # play_obj.wait_done()

        # # Get the next item from the queue
        # wav_data = tts_queue.get()
   

        # Convert the audio data to base64
        base64_data = base64.b64encode(wav_data).decode('utf-8')
        
        # Send the encoded audio data via WebSocket server
        if websocket_server._on_tts_audio_handler is not None:
            eel.on_recive_message("tts_worker sending audio to websocket client")
            asyncio.run_coroutine_threadsafe(websocket_server._on_tts_audio_handler(base64_data), websocket_server.loop)
            