from datetime import datetime, timedelta
from typing import Optional
import plotly.graph_objs as go
import streamlit as st
import vectorbt as bt
import pandas as pd
import numpy as np
import pytz as py

from strats import STRATEGIES, get_strategy_signals  # Import strategies
from tickers import TICKERS  # Import tickers
from trading import TRADING_STYLES, DEFAULT_VALUES  # Import trading styles and default values

# === Helper Functions ===

def convert_to_timezone_aware(date_obj):
    """Convert date to datetime with UTC timezone."""
    return datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=py.UTC)

def fetch_historical_data(ticker: str, interval: str, start_date: datetime, end_date: datetime) -> Optional[pd.Series]:
    """Fetch and validate historical price data based on the selected interval."""
    try:
        data = bt.YFData.download(
            ticker, interval=interval, 
            start=convert_to_timezone_aware(start_date), 
            end=convert_to_timezone_aware(end_date)
        ).get('Close')
        
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
    st.subheader("Style Selection")
    
    # Define interval limits for historical data
    days_back = {"1m": 7, "5m": 60, "1h": 60, "1d": 3650}
    
    trading_style = st.selectbox("Trading Style", list(TRADING_STYLES.keys()), index=0)
    interval = TRADING_STYLES[trading_style]
    
    st.subheader("Asset Selection")
    
    current_date = datetime.now(py.UTC)
    min_start_date = current_date - timedelta(days=days_back[interval])
    
    start_date = st.date_input("Start Date", value=min_start_date.date(), min_value=min_start_date.date(), max_value=current_date.date())
    end_date = st.date_input("End Date", value=current_date.date(), min_value=start_date, max_value=current_date.date())
    ticker = st.selectbox("Ticker", options=TICKERS, index=0)
    historical_clicked = st.button("Get Historical")
    
    st.subheader("Strategy Controls")
    
    equity = st.number_input("Initial Equity ($)", value=DEFAULT_VALUES[trading_style]["equity"], min_value=1000)
    size = st.number_input("Position Size (%)", value=DEFAULT_VALUES[trading_style]["size"], min_value=1, max_value=100)
    selected_label = st.selectbox("Strategy", list(STRATEGIES.keys()), index=0)
    
    # === Dynamic Strategy Input Fields ===
    strategy_params = {}
    if selected_label in ["SMA", "EMA"]:
        strategy_params["fast_window"] = st.number_input("Fast Window", value=DEFAULT_VALUES[trading_style]["fast_sma"], min_value=1, step=1)
        strategy_params["slow_window"] = st.number_input("Slow Window", value=DEFAULT_VALUES[trading_style]["slow_sma"], min_value=1, step=1)
    elif selected_label == "RSI":
        strategy_params["rsi_window"] = st.number_input("RSI Period", value=DEFAULT_VALUES[trading_style]["rsi_window"], min_value=1, step=1)
        strategy_params["overbought"] = st.number_input("Overbought Level", value=DEFAULT_VALUES[trading_style]["overbought"], min_value=1, max_value=100, step=1)
        strategy_params["oversold"] = st.number_input("Oversold Level", value=DEFAULT_VALUES[trading_style]["oversold"], min_value=1, max_value=100, step=1)
    elif selected_label == "Bollinger Bands":
        strategy_params["bb_window"] = st.number_input("Bollinger Bands Period", value=DEFAULT_VALUES[trading_style]["bb_window"], min_value=5, step=1)
    
    direction = st.selectbox("Direction", ["longonly", "shortonly"], index=0)
    backtest_clicked = st.button("Run Backtest")

# === Fetch and Display Historical Data ===
if historical_clicked:
    data = fetch_historical_data(ticker, interval, start_date, end_date)
    if data is not None:
        fig = go.Figure([go.Scatter(x=data.index, y=data, mode='lines', name=ticker)])
        fig.update_layout(title=f"{ticker} {trading_style} Price Data", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

# === Run Backtest and Display Results ===
if backtest_clicked:
    data = fetch_historical_data(ticker, interval, start_date, end_date)
    if data is not None:
        short_mode = direction == "shortonly"
        entries, exits = get_strategy_signals(data, selected_label, short_mode=short_mode, **strategy_params)
        
        portfolio = bt.Portfolio.from_signals(
            data, entries, exits,
            direction=direction, size=float(size) / 100.0, size_type='percent',
            fees=0.000, init_cash=equity, freq='1m', min_size=1, size_granularity=1
        )
        
        # === Plot Equity Curve ===
        equity_fig = go.Figure([go.Scatter(x=portfolio.value().index, y=portfolio.value(), mode='lines', name='Equity')])
        equity_fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Equity')
        st.plotly_chart(equity_fig, use_container_width=True)
        
        # === Plot Drawdown Curve ===
        drawdown_fig = go.Figure([go.Scatter(x=portfolio.drawdown().index, y=portfolio.drawdown() * 100, mode='lines', name='Drawdown', fill='tozeroy', line=dict(color='red'))])
        drawdown_fig.update_layout(title='Drawdown Curve', xaxis_title='Date', yaxis_title='% Drawdown')
        st.plotly_chart(drawdown_fig, use_container_width=True)
        
        # === Plot Portfolio ===
        st.markdown("**Portfolio Plot**")
        st.plotly_chart(portfolio.plot(), use_container_width=True)
