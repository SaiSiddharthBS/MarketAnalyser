"""
WebSocket Server for Pushing Alerts to Mac
"""
import asyncio
import websockets
import json
import logging
from config import WS_HOST, WS_PORT

logger = logging.getLogger("Sentinel_WS")
logger.setLevel(logging.INFO)

connected_clients = set()
server_loop = None

async def handler(websocket, path=None): # Note: websockets 10+ handles path differently but we keep signature generic
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")
    try:
        async for message in websocket:
            # We just expect to push, but handle incoming if needed
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def broadcast_alert(alert_data: dict):
    if not connected_clients:
        return
    
    msg = json.dumps(alert_data)
    # create tasks to send to all clients
    tasks = [asyncio.create_task(client.send(msg)) for client in connected_clients]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"Broadcasted alert to {len(connected_clients)} clients.")

def broadcast_alert_threadsafe(alert_data: dict):
    if server_loop and server_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_alert(alert_data), server_loop)

async def start_server():
    server = await websockets.serve(handler, WS_HOST, WS_PORT)
    logger.info(f"WebSocket Server running on ws://{WS_HOST}:{WS_PORT}")
    await server.wait_closed()

def run_ws_server_in_thread():
    global server_loop
    server_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(server_loop)
    try:
        server_loop.run_until_complete(start_server())
        server_loop.run_forever()
    except OSError as e:
        if e.errno == 10048:
            logger.warning(f"Port {WS_PORT} is already in use (likely by a previous instance). The system will route through the existing open port.")
        else:
            logger.warning(f"WebSocket Server encountered an OS error: {e}")
    except Exception as e:
        logger.warning(f"WebSocket Server stopped: {e}")
