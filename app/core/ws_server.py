import asyncio
import json
import websockets

connected_browser = None

async def handler(websocket):
    global connected_browser
    connected_browser = websocket
    print("[WS] Браузер подключился!")
    try:
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        print("[WS] Браузер отключился.")
    finally:
        connected_browser = None

async def send_command(action: str, query: str = ""):
    """Вызывайте эту функцию из вашего голосового ассистента"""
    if connected_browser:
        payload = json.dumps({"action": action, "query": query})
        await connected_browser.send(payload)
        print(f"[WS] Отправлена команда: {action}")
    else:
        print("[WS] Ошибка: браузер не подключен.")

async def main():
    # Запускаем сервер на порту 8765
    async with websockets.serve(handler, "localhost", 8765):
        print("[WS] Сервер запущен на ws://localhost:8765. Жду браузер...")
        
        # --- ТЕСТОВЫЙ БЛОК (удалите при интеграции в ассистента) ---
        while not connected_browser:
            await asyncio.sleep(1)
            
        await asyncio.sleep(2)
        await send_command("search", "lofi hip hop")
        await asyncio.sleep(5)
        await send_command("pause")
        # ---------------------------------------------------------
        
        await asyncio.Future()  # Держим сервер запущенным бесконечно

if __name__ == "__main__":
    asyncio.run(main())