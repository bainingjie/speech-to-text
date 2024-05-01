import asyncio
import websockets
import base64
import wave
import io
import sounddevice as sd
import numpy as np

async def send_and_receive_audio():
    audio_file = "audio.wav"  # 送信する音声ファイルのパスを指定
    
    with wave.open(audio_file, 'rb') as wav_file:
        audio_data = wav_file.readframes(wav_file.getnframes())
    
    async with websockets.connect('ws://127.0.0.1:8765') as websocket:
        # 音声データをBase64でエンコード
        base64_data = base64.b64encode(audio_data).decode('utf-8')
        
        # エンコードされた音声データをWebSocketサーバーに送信
        await websocket.send(base64_data)
        
        print("Audio data sent to WebSocket server.")
        
        # WebSocketサーバーからの音声データを受信して順次再生
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
                sd.play(audio_float32, samplerate=8000)
                sd.wait()
                
                print("Received audio data played.")
            except websockets.ConnectionClosed:
                break

asyncio.run(send_and_receive_audio())