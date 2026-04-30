def record_trade(group_number: int, trade: dict):
    tab = _get_tab(TAB_TRADES)
    qty = float(trade.get("quantity", 0))
    price = float(trade.get("price", 0))
    amount = qty * price
    tab.append_row([
        group_number,
        datetime.now().isoformat(),
        trade.get("action", ""),
        trade.get("ticker", ""),
        qty,
        price,
        amount,
    ], value_input_option="USER_ENTERED")
    _invalidate_cache()
