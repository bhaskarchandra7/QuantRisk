# binance_ws.py

import websocket
import json

cc='btcusdt'
timef='1m'

socket=f'wss://stream.binance.com:9443/ws/{cc}@kline_{timef}'

# def on_message(ws,message):
#     print(message)

closes,highs,lows=[],[],[]

# makinge candel's    
def on_message(ws,message):
    json_message=json.loads(message)
    candle=json_message['k']
    candle_close=candle['x']
    close=candle['c']
    high=candle['h']
    low=candle['l']
    vol=candle['v']
    
    # print(candle_close)
    # print(close)
    # print(high)
    # print(low)
    # print(vol)
    
    if candle_close:
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        
        print(closes)
        print(highs)
        print(lows)
# def on_error(ws,error):
#     print(error)
    
def on_close(ws):
    print("closed")

ws = websocket.WebSocketApp(socket,on_message=on_message,on_close=on_close)

print('WebSocket client starting...')
ws.run_forever()

