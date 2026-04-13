from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def send_all(self, message: dict):
        for ws in self.connections:
            await ws.send_json(message)

    def is_empty(self) -> bool:
        return len(self.connections) == 0        

ws_manager = WSManager()            