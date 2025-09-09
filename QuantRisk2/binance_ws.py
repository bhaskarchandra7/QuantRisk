import websocket
import json
import requests
import threading

# List of coins to track
coins = ['btcusdt', 'ethusdt', 'solusdt', 'adausdt']
timef = '1s'

def send_to_django(coin, data):
    url = "http://127.0.0.1:8000/test-binance/"
    payload = {
        "symbol": coin.upper(),  
        "close": data['c'],
        "high": data['h'],
        "low": data['l'],
        "volume": data['v'],
        "changePercent": data['P']
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f" Sent {coin.upper()} data to Django:", response.json())
    except Exception as e:
        print(f" Error sending {coin} data to Django:", e)

def on_message(ws, message, coin):
    json_message = json.loads(message)
    candle = json_message['k']
    if candle['x']:  # If candle is closed
        change_percent = ((float(candle['c']) - float(candle['o'])) / float(candle['o'])) * 100

        # Print live changePercent
        print(f"[{coin.upper()}] Live Change Percent: {change_percent:.2f}%")

        send_to_django(coin, {
            'c': candle['c'],
            'h': candle['h'],
            'l': candle['l'],
            'v': candle['v'],
            'P': change_percent
        })

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, coin):
    print(f"WebSocket closed for {coin}")

def on_open(ws):
    print("WebSocket connection opened")

def start_websocket(coin):
    socket = f'wss://stream.binance.com:9443/ws/{coin}@kline_{timef}'
    ws = websocket.WebSocketApp(
        socket,
        on_message=lambda ws, msg: on_message(ws, msg, coin),
        on_error=on_error,
        on_close=lambda ws: on_close(ws, coin),
        on_open=on_open
    )
    ws.run_forever()

# Start WebSocket connections for all coins
threads = []
for coin in coins:
    t = threading.Thread(target=start_websocket, args=(coin,))
    t.start()
    threads.append(t)

# Keep the main thread alive
for t in threads:
    t.join()
