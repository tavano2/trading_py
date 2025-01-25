import yfinance as yf
import time

symbols = ['NVDA', 'AAPL']
# 실시간 주가 데이터를 저장할 딕셔너리
stock_data = {symbol: None for symbol in symbols}

if __name__ == '__main__':
    while True:
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            stock_info = stock.history(period="1d", interval="1m")
            if not stock_info.empty:
                latest_price = stock_info['Close'].iloc[-1]
                stock_data[symbol] = latest_price
        print(stock_data)
        time.sleep(1)  # 1초마다 데이터 갱신