from datetime import datetime, timedelta
from typing import Optional
import plotly.graph_objs as go
import streamlit as st
import vectorbt as bt
import pandas as pd
import numpy as np
import pytz as py
from strats import STRATEGIES, get_strategy_signals  # Import strategies
from tickers import TICKERS # Import tickers

# === Helper Functions ===

def convert_to_timezone_aware(date_obj):
    """Convert date to datetime with UTC timezone."""
    return datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=py.UTC)

def fetch_historical_data(ticker: str, end_date: datetime) -> Optional[pd.Series]:
    """Fetch and validate historical price data."""
    try:
        data = bt.YFData.download(ticker, interval="1m", end=end_date).get('Close')
        if data is None or data.empty:
            st.error(f"No data available for {ticker}")
            return None
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

# === Streamlit UI ===
st.set_page_config(page_title='Backtesting', layout='wide')

# === Sidebar Inputs ===
with st.sidebar:
    st.subheader("Asset Selection")
    st.write("7-Day Historical Data")
    ticker = st.selectbox("Ticker", options=TICKERS, index=0)
    end_date = st.date_input('End Date', value=datetime.now(), min_value=datetime.now() - timedelta(days=20), 
                             max_value=datetime.now())

    historical_clicked = st.button("Get Historical")

    st.subheader("Strategy Controls")

    equity = st.number_input("Initial Equity ($)", value=100000, min_value=1000)
    size = st.number_input("Position Size (%)", value=100, min_value=1, max_value=100)
    selected_label = st.selectbox("Strategy", list(STRATEGIES.keys()), index=0)

    # === Dynamic Strategy Input Fields ===
    strategy_params = {}
    if selected_label == "SMA (Intraday)":
        strategy_params["fast_window"] = st.number_input("Fast SMA Period", value=5, min_value=1, step=1)
        strategy_params["slow_window"] = st.number_input("Slow SMA Period", value=20, min_value=1, step=1)

    elif selected_label == "EMA (Intraday)":
        strategy_params["fast_window"] = st.number_input("Fast EMA Period", value=9, min_value=1, step=1)
        strategy_params["slow_window"] = st.number_input("Slow EMA Period", value=21, min_value=1, step=1)

    elif selected_label == "RSI (Intraday)":
        strategy_params["rsi_window"] = st.number_input("RSI Period", value=5, min_value=1, step=1)
        strategy_params["overbought"] = st.number_input("Overbought Level", value=80, min_value=1, max_value=100, step=1)
        strategy_params["oversold"] = st.number_input("Oversold Level", value=20, min_value=1, max_value=100, step=1)

    elif selected_label == "Bollinger Bands (Intraday)":
        strategy_params["bb_window"] = st.number_input("Bollinger Bands Period", value=10, min_value=5, step=1)

    direction = st.selectbox("Direction", ["longonly", "shortonly"], index=0)
    backtest_clicked = st.button("Run Backtest")

# === Fetch and Display Historical Data ===
if historical_clicked:
    end_date_tz = convert_to_timezone_aware(end_date)
    data = fetch_historical_data(ticker, end_date_tz)

    if data is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data, mode='lines', name=ticker))
        fig.update_layout(title=f"{ticker} 1-Minute Price Data", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

# === Run Backtest and Display Results ===
if backtest_clicked:
    end_date_tz = convert_to_timezone_aware(end_date)
    data = fetch_historical_data(ticker, end_date_tz)

    if data is not None:
        short_mode = direction == "shortonly" 
        entries, exits = get_strategy_signals(data, selected_label, short_mode=short_mode, **strategy_params)

        # Convert size
        size_value = float(size) / 100.0

        portfolio = bt.Portfolio.from_signals(
            data, entries, exits,
            direction=direction,
            size=size_value,
            size_type='percent',
            fees=0.000,
            init_cash=equity,
            freq='1m',
            min_size=1,
            size_granularity=1
        )

        # === Plot Equity Curve ===
        equity_data = portfolio.value()
        equity_trace = go.Scatter(x=equity_data.index, y=equity_data, mode='lines', name='Equity')
        equity_fig = go.Figure(data=[equity_trace])
        equity_fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Equity')
        st.plotly_chart(equity_fig, use_container_width=True)

        # === Plot Drawdown Curve ===
        drawdown_data = portfolio.drawdown() * 100
        drawdown_trace = go.Scatter(
            x=drawdown_data.index, y=drawdown_data, mode='lines', name='Drawdown', fill='tozeroy', line=dict(color='red')
        )
        drawdown_fig = go.Figure(data=[drawdown_trace])
        drawdown_fig.update_layout(title='Drawdown Curve', xaxis_title='Date', yaxis_title='% Drawdown')
        st.plotly_chart(drawdown_fig, use_container_width=True)

        # === Plot Portfolio ===
        st.markdown("**Portfolio Plot**")
        st.plotly_chart(portfolio.plot(), use_container_width=True)
