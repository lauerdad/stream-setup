import requests
import json
import time
from datetime import datetime
import ccxt  # Binance API library

# Binance API keys (get from Binance account, free tier)
BINANCE_API_KEY = 'your_binance_api_key'
BINANCE_SECRET = 'your_binance_secret_key'
# Etherscan API key (free tier, signup at etherscan.io)
ETHERSCAN_API_KEY = 'your_etherscan_api_key'
# BSCScan API key (free tier, signup at bscscan.com)
BSCSCAN_API_KEY = 'your_bscscan_api_key'

# Initialize Binance exchange
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET,
    'enableRateLimit': True,
})

# Track whale transactions for ETH, SOL, AIOZ
def get_whale_transactions(currency, chain='eth'):
    api_key = ETHERSCAN_API_KEY if chain == 'eth' else BSCSCAN_API_KEY
    base_url = 'https://api.etherscan.io/api' if chain == 'eth' else 'https://api.bscscan.com/api'
    params = {
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': {'eth': '0x0000000000000000000000000000000000000000', 'sol': '0x123...', 'aioz': '0x123...'}[currency],  # Replace with actual token addresses
        'sort': 'desc',
        'apikey': api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        return data['result'][:10]  # Last 10 transactions
    except Exception as e:
        print(f"Error fetching whale data: {e}")
        return []

# Auto-buy logic with 10% stop loss
def place_buy_order(symbol, amount_usd):
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        quantity = amount_usd / price
        order = exchange.create_market_buy_order(symbol, quantity)
        stop_price = price * 0.9  # 10% stop loss
        print(f"Bought {quantity} {symbol} at {price}, stop loss at {stop_price}")
        with open('trades.log', 'a') as f:
            f.write(f"{datetime.now()}: Bought {quantity} {symbol} at {price}\n")
        return order
    except Exception as e:
        print(f"Error placing order: {e}")
        return None

def main():
    print("Auto-Trading Bot Started - Buying Altseason Winners...")
    portfolio = {'ETH/USDT': 200, 'SOL/USDT': 100, 'AIOZ/USDT': 100}  # 00 start
    last_tx = {}
    while True:
        for currency, chain in [('eth', 'eth'), ('sol', 'bsc'), ('aioz', 'bsc')]:
            symbol = f"{currency.upper()}/USDT"
            transactions = get_whale_transactions(currency, chain)
            for tx in transactions:
                if float(tx['value']) / 1e18 > 100000:  # 00K+ buy
                    tx_hash = tx['hash']
                    if tx_hash not in last_tx.get(currency, []):
                        print(f"Whale buy detected: {tx['value']} {currency}")
                        place_buy_order(symbol, portfolio[symbol] * 0.3)  # Reinvest 30% of allocation
                        last_tx.setdefault(currency, []).append(tx_hash)
                        if len(last_tx[currency]) > 10:
                            last_tx[currency].pop(0)
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
