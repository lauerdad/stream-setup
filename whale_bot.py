import requests
import time
from datetime import datetime
import json

# Replace with your API keys
BITSGAP_API_KEY = 'your_bitsgap_api_key'
BITSGAP_SECRET = 'your_bitsgap_secret'
WHALE_ALERT_API = 'https://api.whale-alert.io/v1/transactions?api_key=your_free_key&min_value=1000000&currency=eth,sol,aioz'

class WhaleBot:
    def __init__(self):
        self.portfolio = 400.0  # Starting 00
        self.trades_log = 'trades.log'
        self.whale_threshold = 1000000  # M+ buys
        self.stop_loss_pct = 0.10  # 10%

    def get_whale_buys(self):
        try:
            response = requests.get(WHALE_ALERT_API)
            data = response.json()
            buys = [tx for tx in data['transactions'] if float(tx['amount']) > self.whale_threshold]
            return buys
        except Exception as e:
            print(f"Error fetching whale data: {e}")
            return []

    def place_buy_order(self, symbol, amount_usd):
        try:
            # Bitsgap API call (simplified, check Bitsgap docs for exact endpoint)
            url = 'https://api.bitsgap.com/v1/trade'
            headers = {'Authorization': f'Bearer {BITSGAP_API_KEY}'}
            payload = {
                'market': symbol,  # e.g., ETH/USDT
                'amount': amount_usd,
                'side': 'buy',
                'stop_loss': 0.9  # 10% stop loss
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                price = response.json()['price']
                quantity = amount_usd / price
                print(f"Bought {quantity} {symbol} at {price}, stop loss at {price * 0.9}")
                with open(self.trades_log, 'a') as f:
                    f.write(f"{datetime.now()}: Bought {quantity} {symbol} at {price}\n")
                return True
            else:
                print(f"Order failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error placing order: {e}")
            return False

    def main(self):
        print("Auto-Trading Bot Started - Buying Altseason Winners...")
        allocations = {'ETH/USDT': 160, 'SOL/USDT': 120, 'AIOZ/USDT': 120}  # 00 split
        last_tx = {}
        while True:
            for symbol, amount in allocations.items():
                currency = symbol.split('/')[0].lower()
                buys = self.get_whale_buys()
                for tx in buys:
                    if tx['symbol'].lower() == currency and tx['hash'] not in last_tx.get(currency, []):
                        print(f"Whale buy detected: {tx['amount']} {currency}")
                        self.place_buy_order(symbol, amount * 0.3)  # 30% of allocation
                        last_tx.setdefault(currency, []).append(tx['hash'])
                        if len(last_tx[currency]) > 10:
                            last_tx[currency].pop(0)
            time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    bot = WhaleBot()
    bot.main()
