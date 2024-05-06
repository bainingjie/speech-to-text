import sounddevice as sd
import io
import soundfile as sf
import numpy as np
import librosa,base64


# get a list of valid input devices
def get_valid_input_devices():
    valid_devices = []
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    for device in devices:
        if device["max_input_channels"] > 0:
            device["host_api_name"] = hostapis[device["hostapi"]]["name"]
            valid_devices.append(device)
    return valid_devices



def base64_to_audio(base64_string):
    try:
        # Base64文字列のパディングを修正
        padding = len(base64_string) % 4
        if padding != 0:
            base64_string += "=" * (4 - padding)

        audio_data = base64.b64decode(base64_string)
        # audio_data = np.frombuffer(audio_data, dtype=np.int8)
        # audio_data = audio_data.astype(np.float32) / 128.0


        # audio_data = np.frombuffer(audio_data, dtype=np.float32)

        return audio_data
    except (base64.binascii.Error, ValueError) as e:
        print(f"Error decoding base64 string: {e}")
        return np.array([])