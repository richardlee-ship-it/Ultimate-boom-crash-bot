def build_candles(prices, interval=60):
    df = pd.DataFrame(prices, columns=["price"])
    df["time"] = pd.to_datetime(df.index, unit="s")
    df = df.set_index("time")

    ohlc = df["price"].resample(f"{interval}s").ohlc()
    return ohlc.dropna()
