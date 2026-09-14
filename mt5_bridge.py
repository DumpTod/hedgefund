import time
import json
import MetaTrader5 as mt5
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Initialize the internal MetaTrader 5 application engine
if not mt5.initialize():
    print("Bridge connection error: Internal MT5 initialization failed.")
    quit()

class MT5BridgeServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # Bypasses standard terminal log spamming for high performance

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # Endpoint 1: Streams active multi-timeframe bar arrays directly to your bot
        if path == "/rates":
            symbol = query.get("symbol", ["EURUSD"])[0]
            tf_str = query.get("timeframe", ["H1"])[0]
            count = int(query.get("count", [300])[0])

            tf = mt5.TIMEFRAME_H1 if tf_str == "H1" else mt5.TIMEFRAME_D1
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

            if rates is None or len(rates) == 0:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"[]")
                return

            # Package structured financial indices into pure JSON text chunks
            data_list = []
            for r in rates:
                data_list.append({
                    "time": int(r[0]), "open": float(r[1]), "high": float(r[2]),
                    "low": float(r[3]), "close": float(r[4]), "tick_volume": int(r[5])
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data_list).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/order":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            symbol = payload["symbol"]
            action = payload["action"]
            risk = payload["risk_percentage"]

            # Query instant execution parameters from live order ticket matrices
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.send_response(200)
                self.wfile.write(json.dumps({"status": "TICK_ERROR"}).encode("utf-8"))
                return

            price = tick.ask if action == "BUY" else tick.bid
            order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

            # Submit formal trade executions straight to the server ledger
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01, # Default testing safety fractional sizing limit
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 202603,
                "comment": "AI Quant Linux Bridge Order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "retcode": int(result.retcode if result else -1)}).encode("utf-8"))
            return

def run_server():
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, MT5BridgeServer)
    print("MetaTrader 5 Native Linux Web Bridge is actively running online on port 8080...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()

