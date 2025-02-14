import vectorbt as bt
import pandas as pd

# === Dictionary of Available Strategies ===
STRATEGIES = {
    "SMA (Intraday)": "sma_strategy",
    "EMA (Intraday)": "ema_strategy",
    "RSI (Intraday)": "rsi_strategy",
    "Bollinger Bands (Intraday)": "bollinger_bands_strategy",
}

def get_strategy_signals(data: pd.Series, strategy_name: str, short_mode=False, **kwargs):
    """Selects and runs the appropriate strategy function with parameters."""
    strategy_functions = {
        "SMA (Intraday)": sma_strategy,
        "EMA (Intraday)": ema_strategy,
        "RSI (Intraday)": rsi_strategy,
        "Bollinger Bands (Intraday)": bollinger_bands_strategy,
    }
    strategy_func = strategy_functions.get(strategy_name)

    if strategy_func is None:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    return strategy_func(data, short_mode=short_mode, **kwargs)

# === Moving Average Strategies ===
def sma_strategy(data: pd.Series, fast_window: int = 5, slow_window: int = 20, short_mode=False):
    """Simple Moving Average (SMA) Crossover Strategy."""
    fast = bt.MA.run(data, window=fast_window)
    slow = bt.MA.run(data, window=slow_window)

    if short_mode:
        entries = fast.ma_crossed_below(slow)  # Short when fast SMA crosses below slow SMA
        exits = fast.ma_crossed_above(slow)  # Exit when fast SMA crosses above slow SMA
    else:
        entries = fast.ma_crossed_above(slow)  # Long when fast SMA crosses above slow SMA
        exits = fast.ma_crossed_below(slow)  # Exit when fast SMA crosses below slow SMA

    return entries, exits

def ema_strategy(data: pd.Series, fast_window: int = 9, slow_window: int = 21, short_mode=False):
    """Exponential Moving Average (EMA) Crossover Strategy."""
    fast = bt.MA.run(data, window=fast_window, ewm=True)
    slow = bt.MA.run(data, window=slow_window, ewm=True)

    if short_mode:
        entries = fast.ma_crossed_below(slow)  # Short when fast EMA crosses below slow EMA
        exits = fast.ma_crossed_above(slow)  # Exit when fast EMA crosses above slow EMA
    else:
        entries = fast.ma_crossed_above(slow)  # Long when fast EMA crosses above slow EMA
        exits = fast.ma_crossed_below(slow)  # Exit when fast EMA crosses below slow EMA

    return entries, exits

# === Momentum Strategy ===
def rsi_strategy(data: pd.Series, rsi_window: int = 5, overbought: int = 80, oversold: int = 20, short_mode=False):
    """Relative Strength Index (RSI) Strategy for Overbought/Oversold Conditions."""
    rsi = bt.RSI.run(data, window=rsi_window)

    if short_mode:
        entries = rsi.rsi_crossed_above(overbought)  # Short when RSI enters overbought zone
        exits = rsi.rsi_crossed_below(oversold)  # Exit when RSI enters oversold zone
    else:
        entries = rsi.rsi_crossed_above(oversold)  # Long when RSI enters oversold zone
        exits = rsi.rsi_crossed_below(overbought)  # Exit when RSI enters overbought zone

    return entries, exits

# === Volatility Strategy ===
def bollinger_bands_strategy(data: pd.Series, bb_window: int = 10, short_mode=False):
    """Bollinger Bands Strategy for Volatility Breakouts."""
    bb = bt.BBANDS.run(data, window=bb_window)

    if short_mode:
        entries = data > bb.upper  # Short when price breaks above upper band
        exits = data < bb.middle  # Exit when price drops below middle band
    else:
        entries = data < bb.lower  # Long when price breaks below lower band
        exits = data > bb.middle  # Exit when price rises above middle band

    return entries, exits
