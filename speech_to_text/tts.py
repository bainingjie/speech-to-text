import requests
import json
import time
from pydub import AudioSegment
from pydub.playback import play
import os,io,eel

def get_audio_query(text, speaker=1, max_retries=5, retry_interval=0.1):
    query_payload = {"text": text, "speaker": speaker}
    retries = 0
    while retries < max_retries:
        try:
            url = "http://localhost:50021/audio_query"
            r = requests.post(url, params=query_payload, timeout=(1.0, 5.0))
            if r.status_code == 200:
                eel.on_recive_message("tts request1 done with " + str(retries))
                return r.json()
        except requests.exceptions.RequestException:
            print('Request failed, retrying...')
            retries += 1
            time.sleep(retry_interval)
    raise Exception("Failed to get audio query after {} retries".format(max_retries))

def run_synthesis(query_data, speaker=0, max_retries=5, retry_interval=0.1):
    synth_payload = {"speaker": speaker}
    query_data["speedScale"] = 1
    retries = 0
    while retries < max_retries:
        try:
            url = "http://localhost:50021/synthesis"
            r = requests.post(url, params=synth_payload, data=json.dumps(query_data), timeout=(1.0, 5.0))
            if r.status_code == 200:
                eel.on_recive_message("tts request2 done")
                return r.content
        except requests.exceptions.RequestException:
            print('Request failed, retrying...')
            retries += 1
            time.sleep(retry_interval)
    raise Exception("Failed to run synthesis after {} retries".format(max_retries))


def get_audio_file_from_text(text):
    eel.on_recive_message("tts request1 start")
    query_data = get_audio_query(text)
    
    return run_synthesis(query_data)

def tts_worker(tts_queue):
    while True:
        wav_data = tts_queue.get()
        if wav_data is None:
            break
        eel.on_recive_message("tts_worker start to play")
        audio_segment = AudioSegment.from_file(io.BytesIO(wav_data), format="wav")
        play(audio_segment)