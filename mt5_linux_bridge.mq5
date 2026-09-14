// mt5_linux_bridge.mq5
#property copyright "AI Quant Edge Bridge"
#property version "1.05"
#property strict

int OnInit() {
    Print("AI Hedge Fund Native MQL5 Linux File Bridge actively initialized.");
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { }

void OnTick() {
    // Dynamically checks for instructions every time a new tick hits the chart
    string file_name = "ai_hedge_fund_signal.txt";
    if(FileIsExist(file_name)) {
        int file_handle = FileOpen(file_name, FILE_READ|FILE_TXT);
        if(file_handle != INVALID_HANDLE) {
            string signal_data = FileReadString(file_handle);
            FileClose(file_handle);
            FileDelete(file_name); // Immediately wipes file to reset execution queue
            Print("AI Bridge Instruction Detected: ", signal_data);
            ExecuteBridgeOrder(signal_data);
        }
    }
}

void ExecuteBridgeOrder(string command) {
    MqlTradeRequest request;
    MqlTradeResult result;
    ZeroMemory(request);
    ZeroMemory(result);
    request.action = TRADE_ACTION_DEAL;

    // Parse execution direction commands
    if(command == "BUY_BTCUSD") {
        request.symbol = "BTCUSD";
        request.type = ORDER_TYPE_BUY;
    } else if(command == "SELL_BTCUSD") {
        request.symbol = "BTCUSD";
        request.type = ORDER_TYPE_SELL;
    } else {
        return;
    }

    request.volume = 0.01;
    request.price = SymbolInfoDouble(request.symbol, SYMBOL_ASK);
    request.deviation = 20;
    request.magic = 202603;
    request.comment = "AI Quant Linux Order";
    request.type_time = ORDER_TIME_GTC;
    request.type_filling = ORDER_FILLING_IOC;

    if(!OrderSend(request, result)) {
        Print("Order Execution Exception Variance: ", GetLastError());
    } else {
        Print("Success! Order ticket submitted successfully to ledger: ", result.deal);
    }
}