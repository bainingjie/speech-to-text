import asyncio
import websockets
import webbrowser
import os
from typing import Optional

python_root_dir = os.path.dirname(os.path.abspath(__file__))
app_root_dir = os.path.dirname(python_root_dir)


class WebSocketServer:
    def __init__(self, loop):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.loop = loop
        self.server = None
        self._on_message_handler = None
        self._on_tts_audio_handler = None

    async def start_server(self):
        print(f"Starting WebSocket server on ws://localhost:{3000}")
        self.server = await websockets.serve(self.handler, "localhost", 3000)

    async def handler(self, ws: websockets.WebSocketServerProtocol, path):
        self.websocket = ws
        try:
            async for message in ws:
                if self._on_message_handler is not None:
                    await self._on_message_handler(message)
        finally:
            if self.websocket is ws:
                self.websocket = None

    async def stop_server(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

    async def send_message(self, message: str):
        if self.websocket is not None:
            await self.websocket.send(message)

    def send_message_threadsafe(self, message: str):
        if self.websocket is not None:
            asyncio.run_coroutine_threadsafe(self.send_message(message), self.loop)

    async def send_binary(self, data):
        if self.websocket is not None:
            await self.websocket.send(data)

    def on_message(self, handler):
        self._on_message_handler = handler
        return handler

    def on_tts_audio(self, handler):
        async def wrapper(data):
            await handler(data)
        self._on_tts_audio_handler = wrapper
        return wrapper