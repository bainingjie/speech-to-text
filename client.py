import asyncio
import websockets
import base64
import io
import sounddevice as sd
import numpy as np
from queue import Queue

async def play_audio(receive_queue, samplerate):
    while True:
        audio_data = await receive_queue.get()
        print(f"Size of audio data: {len(audio_data)} bytes")
        decoded_data = base64.b64decode(audio_data)
        audio_array = np.frombuffer(decoded_data, dtype=np.int16)
        audio_float32 = audio_array.astype(np.float32) / 32768.0
        sd.play(audio_float32, samplerate=samplerate)
        sd.wait()

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
        base64_data = base64.b64encode(indata.tobytes()).decode('utf-8')
        
        # Put the audio data in the send queue
        loop.call_soon_threadsafe(send_queue.put_nowait, base64_data)

    # Open the audio stream
    stream = sd.InputStream(callback=audio_callback, channels=channels, samplerate=samplerate, blocksize=blocksize)

    try:
        async with websockets.connect('ws://127.0.0.1:8765') as websocket:
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

async def send_audio_data(websocket, send_queue):
    while True:
        # Get audio data from the send queue
        audio_data = await send_queue.get()
        
        # Send the audio data to the WebSocket server
        await websocket.send(audio_data)

asyncio.run(send_and_receive_audio())