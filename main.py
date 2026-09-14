# main.py
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn

from config import TRADING_SYMBOLS
from data_engine import DataEngine
from ai_brain import AIBrain
from execution import ExecutionModule
from auditor import AuditorAgent

app = FastAPI(title="AI Quant Edge Hedge Fund Hub")

# Fixes the Linux folder path structure automatically by using absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_path)

# Core module initialization configurations
data_engine = DataEngine()
ai_brain = AIBrain()
execution = ExecutionModule()
auditor = AuditorAgent()

SYSTEM_STATE = {"status": "OFFLINE", "active_logs": [], "confidence": 0, "pnl": 0.0}


async def autonomous_execution_loop():
    while True:
        if SYSTEM_STATE["status"] == "ONLINE":
            SYSTEM_STATE["active_logs"].append("Initiating multi-asset quantitative scan cycle...")
            # Safely fetch portfolio updates from the account database via data_engine
            # If the MT5 bridge isn't running yet, this safely defaults to 0.0
            try:
                account_pnl = 0.0
                if hasattr(data_engine, 'mt5') and hasattr(data_engine.mt5, 'account_info'):
                    account = data_engine.mt5.account_info()
                    if account:
                        account_pnl = round(account.profit, 2)
                SYSTEM_STATE["pnl"] = account_pnl
            except Exception:
                SYSTEM_STATE["pnl"] = 0.0

            for symbol in TRADING_SYMBOLS:
                context = data_engine.get_market_context(symbol)
                if not context:
                    continue
                decision = ai_brain.formulate_trade_decision(context)
                SYSTEM_STATE["confidence"] = decision.get("confidence_score", 0)
                log_msg = f"Asset {symbol} -> Decision: {decision['action']} | Rationale: {decision['technical_rationale']}"
                SYSTEM_STATE["active_logs"].append(log_msg)
                
                if decision["action"] in ["BUY", "SELL"]:
                    execution.route_order(symbol, decision["action"], decision, risk_percentage=1.0)
            
            # Prune logging window array metrics to optimize overall memory performance
            if len(SYSTEM_STATE["active_logs"]) > 40:
                SYSTEM_STATE["active_logs"] = SYSTEM_STATE["active_logs"][-40:]

        await asyncio.sleep(30)  # Scan cycle execution timing interval (seconds)


@app.get("/")
def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"state": SYSTEM_STATE}
    )


@app.post("/api/toggle")
def toggle_system():
    if SYSTEM_STATE["status"] == "ONLINE":
        SYSTEM_STATE["status"] = "OFFLINE"
    else:
        SYSTEM_STATE["status"] = "ONLINE"
    return {"status": SYSTEM_STATE["status"]}


@app.post("/api/audit")
def run_manual_audit():
    result = auditor.synchronize_and_audit()
    return {"message": result}


@app.get("/api/state")
def get_state():
    try:
        account_pnl = 0.0
        if hasattr(data_engine, 'mt5') and hasattr(data_engine.mt5, 'account_info'):
            account = data_engine.mt5.account_info()
            if account:
                account_pnl = round(account.profit, 2)
        SYSTEM_STATE["pnl"] = account_pnl
    except Exception:
        pass
    return SYSTEM_STATE


@app.on_event("startup")
async def app_startup():
    asyncio.create_task(autonomous_execution_loop())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)