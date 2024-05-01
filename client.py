import asyncio
import websockets
import base64
import io
import sounddevice as sd
import numpy as np
from queue import Queue

async def send_and_receive_audio():
    # Set up the audio stream from the default microphone
    samplerate = 16000
    blocksize = 512
    channels = 1

    # Create a queue to pass audio data from the callback to the asyncio loop
    audio_queue = Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        
        # Convert the audio data to base64 and put it in the queue
        base64_data = base64.b64encode(indata.tobytes()).decode('utf-8')
        audio_queue.put(base64_data)

    # Open the audio stream
    stream = sd.InputStream(callback=audio_callback, channels=channels, samplerate=samplerate, blocksize=blocksize)

    try:
        async with websockets.connect('ws://127.0.0.1:8765') as websocket:
            with stream:
                # Inform the user that the microphone stream has started and is now sending audio data to the WebSocket server.
                print("Microphone stream started. Sending audio data to the WebSocket server.")

                # Initiate an asynchronous task that continuously sends audio data from the queue to the WebSocket server.
                # This task runs concurrently with the main event loop, allowing for non-blocking operation.
                asyncio.create_task(send_audio_data(websocket, audio_queue))

                # WebSocket server からの音声データを受信して順次再生
                while True:
                    try:
                        # 音声データを受信
                        received_data = await websocket.recv()
                        if not received_data:
                            break
                        
                        # 受信した音声データをデコード
                        decoded_data = base64.b64decode(received_data)
                        
                        # 受信した音声データをNumPy配列に変換
                        audio_array = np.frombuffer(decoded_data, dtype=np.int16)
                        audio_float32 = audio_array.astype(np.float32) / 32768.0
                        
                        # 音声データを再生
                        sd.play(audio_float32, samplerate=samplerate)
                        sd.wait()
                        
                        print("Received audio data played.")
                    except websockets.ConnectionClosed:
                        break
    except KeyboardInterrupt:
        print("Program stopped by user.")

async def send_audio_data(websocket, audio_queue):
    while True:
        # Get audio data from the queue
        audio_data = audio_queue.get()
        
        # Send the audio data to the WebSocket server
        await websocket.send(audio_data)

asyncio.run(send_and_receive_audio())