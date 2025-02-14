TRADING_STYLES = {
    "Intra (1m) (7 days max)": "1m",
    "Swing (5m) (60 days max)": "5m",
    "Position (1h) (60 days max)": "1h",
    "Investing (1d) (10 year max)": "1d"
}

DEFAULT_VALUES = {
    "Intra (1m) (7 days max)": {
        "equity": 100000, "size": 100, "fast_sma": 5, "slow_sma": 20,
        "fast_ema": 9, "slow_ema": 21, "rsi_window": 5, "overbought": 80, "oversold": 20, "bb_window": 10
    },
    "Swing (5m) (60 days max)": {
        "equity": 100000, "size": 100, "fast_sma": 10, "slow_sma": 50,
        "fast_ema": 12, "slow_ema": 26, "rsi_window": 14, "overbought": 70, "oversold": 30, "bb_window": 20
    },
    "Position (1h) (60 days max)": {
        "equity": 100000, "size": 100, "fast_sma": 20, "slow_sma": 100,
        "fast_ema": 20, "slow_ema": 50, "rsi_window": 21, "overbought": 65, "oversold": 35, "bb_window": 30
    },
    "Investing (1d) (10 year max)": {
        "equity": 100000, "size": 100, "fast_sma": 50, "slow_sma": 200,
        "fast_ema": 50, "slow_ema": 200, "rsi_window": 30, "overbought": 60, "oversold": 40, "bb_window": 50
    }
}

