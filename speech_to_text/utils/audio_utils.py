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


# create an audio stream
def create_audio_stream(selected_device, callback):
    RATE = 16000
    CHUNK = 512
    CHANNELS = 1
    DTYPE = "float32"

    stream = sd.InputStream(
        device=selected_device,
        channels=CHANNELS,
        samplerate=RATE,
        callback=callback,
        dtype=DTYPE,
        blocksize=CHUNK,
    )

    return stream


def base64_to_audio(base64_string):
    try:
        # Base64文字列のパディングを修正
        padding = len(base64_string) % 4
        if padding != 0:
            base64_string += "=" * (4 - padding)

        audio_data = base64.b64decode(base64_string)
        audio_float32 = np.frombuffer(audio_data, dtype=np.float32)
        return audio_float32
    except (base64.binascii.Error, ValueError) as e:
        print(f"Error decoding base64 string: {e}")
        return np.array([])