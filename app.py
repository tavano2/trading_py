import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import threading
import time
from datetime import datetime
from waitress import serve  # waitress 임포트
import signal

# logs 폴더 생성 (없는 경우)
if not os.path.exists("logs"):
    os.makedirs("logs")

# 로깅 설정
log_file = "logs/app.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 로그 파일 경로 출력
print("Log file path:", os.path.abspath(log_file))

app = Flask(__name__)
CORS(app)

# 주식 심볼 리스트
symbols = ['NVDA', 'AAPL']
stock_data = {}  # 주식 데이터 저장

# 스레드 간 동기화를 위한 Lock
data_lock = threading.Lock()

def fetch_stock_prices():
    while True:
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                stock_info = stock.history(period="1d", interval="1m")  # 1분 간격 데이터
                if not stock_info.empty:
                    latest_data = stock_info.iloc[-1]  # 가장 최근 데이터
                    current_minute = datetime.now().replace(second=0, microsecond=0)  # 분 단위 시간
                    stock_data[symbol] = {
                        "open": latest_data['Open'],  # 시가
                        "high": latest_data['High'],  # 고가
                        "low": latest_data['Low'],  # 저가
                        "close": latest_data['Close'],  # 종가
                        "timestamp": int(current_minute.timestamp() * 1000),  # 분 단위 timestamp (밀리초)
                    }
                else:
                    print(f"No data found for {symbol}")
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
        time.sleep(1)  # 1초마다 데이터 갱신

@app.route("/stocks", methods=["GET"])
def get_stocks():
    return jsonify(stock_data)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """서버를 종료하는 엔드포인트"""
    logger.debug("Shutting down server...")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'

def run_server():
    """waitress로 Flask 애플리케이션 실행"""
    logger.debug("Starting Waitress server...")
    serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # 백그라운드에서 주식 가격을 가져오는 스레드 시작 (데몬 모드 해제)
    logger.debug("Starting background thread to fetch stock prices...")
    threading.Thread(target=fetch_stock_prices, daemon=False).start()

    # waitress를 별도의 스레드에서 실행
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # 메인 스레드에서 대기
    server_thread.join()