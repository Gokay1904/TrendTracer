import asyncio
import websockets
import json

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# 20 major stocks (Binance symbols, e.g., BTCUSDT, ETHUSDT, etc.)
STOCKS = [
    "btcusdt", "ethusdt", "bnbusdt", "adausdt", "solusdt", "xrpusdt", "dogeusdt", "maticusdt", "ltcusdt", "trxusdt",
    "dotusdt", "shibusdt", "avaxusdt", "uniusdt", "linkusdt", "atomusdt", "etcusdt", "filusdt", "aptusdt", "nearusdt"
]

async def track_stocks():
    # Prepare stream names for all stocks
    streams = "/".join([f"{symbol}@ticker" for symbol in STOCKS])
    url = f"wss://stream.binance.com:9443/stream?streams={streams}"
    print(f"Connecting to: {url}")
    previous_prices = {}
    async with websockets.connect(url) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if "data" in data:
                symbol = data["data"]["s"].lower()
                price = float(data["data"]["c"])
                prev_price = previous_prices.get(symbol)
                if prev_price is not None:
                    if price > prev_price:
                        print(f"{symbol.upper()}: RISE")
                    elif price < prev_price:
                        print(f"{symbol.upper()}: FALL")
                    else:
                        print(f"{symbol.upper()}: NO CHANGE")
                previous_prices[symbol] = price

if __name__ == "__main__":
    asyncio.run(track_stocks())
