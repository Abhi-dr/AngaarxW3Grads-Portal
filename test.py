import websockets
import asyncio

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/enrollment_requests/"
    async with websockets.connect(uri) as websocket:
        await websocket.send('{"action": "new_enrollment"}')
        response = await websocket.recv()
        print("Response from server:", response)

asyncio.run(test_websocket())
