import asyncio
import websockets
import base64
import io
import sounddevice as sd
import numpy as np
from queue import Queue
import datetime
import time

send_time = None
sent_time = None

async def play_audio(receive_queue, samplerate):
    global sent_time
    while True:
        audio_data = await receive_queue.get()
        print(f"GOT Size of audio data: {len(audio_data)} bytes . Timestamp: {datetime.datetime.now().isoformat()}")
        decoded_data = base64.b64decode(audio_data)
        audio_array = np.frombuffer(decoded_data, dtype=np.int16)
        audio_float32 = audio_array.astype(np.float32) / 32768.0
        print(f"start to play . Timestamp: {datetime.datetime.now().isoformat()}")
        # sent_time=time.time()
        # latency_ms=(sent_time-send_time)*1000
        # print(f"total latency:{latency_ms:.2f} ms")

        sd.play(audio_float32, samplerate=samplerate)
        sd.wait()
        print(f"play ended . Timestamp: {datetime.datetime.now().isoformat()}")


async def receive_audio_data(websocket, receive_queue, samplerate):
    while True:
        try:
            received_data = await websocket.recv()
            if not received_data:
                break
            print("Received audio data.")
            await receive_queue.put(received_data)
        except websockets.ConnectionClosed:
            break

async def send_and_receive_audio():
    # Set up the audio stream from the default microphone
    samplerate = 16000
    blocksize = 512
    channels = 1

    # Create separate queues for sending and receiving audio data
    send_queue = asyncio.Queue()
    receive_queue = asyncio.Queue()

    loop = asyncio.get_running_loop()

    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        
        # Convert the audio data to base64
        # memo: デフォルトはfloat 32
        # 愚直に考えると、indata*128なんだけど、声が小さい時は認識されないため、amplifyして*1024になってる。
        
        # TODO: float32→int16→mu-lawでint8に変換する
        audio_data_int8 = np.clip(indata*1024,-128,127).astype(np.int8)
        # print(max(audio_data_int8),min(audio_data_int8))
        base64_data = base64.b64encode(audio_data_int8.tobytes()).decode('utf-8')
        
        # Put the audio data in the send queue
        loop.call_soon_threadsafe(send_queue.put_nowait, base64_data)

    # Open the audio stream
    stream = sd.InputStream(callback=audio_callback, channels=channels, samplerate=samplerate, blocksize=blocksize)

    try:
        async with websockets.connect('wss://a8a0-221-242-19-3.ngrok-free.app') as websocket:
            with stream:
                # Inform the user that the microphone stream has started and is now sending audio data to the WebSocket server.
                print("Microphone stream started. Sending audio data to the WebSocket server.")

                # Initiate asynchronous tasks for sending and receiving audio data
                send_task = asyncio.create_task(send_audio_data(websocket, send_queue))
                receive_task = asyncio.create_task(receive_audio_data(websocket, receive_queue, samplerate))
                play_task = asyncio.create_task(play_audio(receive_queue, samplerate))

                # Wait for the tasks to complete
                await asyncio.gather(send_task, receive_task, play_task)

    except KeyboardInterrupt:
        print("Program stopped by user.")
        stream.stop()
        await websocket.close()

count_message=0
async def send_audio_data(websocket, send_queue):
    global count_message,send_time
    while True:
        # Get audio data from the send queue
        audio_data = await send_queue.get()
        
        send_time=time.time()
        # Send the audio data to the WebSocket server
        await websocket.send(audio_data)



asyncio.run(send_and_receive_audio())