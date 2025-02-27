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

    st.subheader("Asset Selection")
    ticker = st.text_input("Ticker", "BTC-USD")
    #ticker = st.selectbox("Ticker", options=TICKERS, index=0)

    st.subheader("Style Selection")
    
    # Define interval limits for historical data
    days_back = {"1m": 7, "5m": 59, "1h": 60, "1d": 3650}
    
    trading_style = st.selectbox("Trading Style", list(TRADING_STYLES.keys()), index=0)
    interval = TRADING_STYLES[trading_style]
    
    current_date = datetime.now(py.UTC)
    min_start_date = current_date - timedelta(days=days_back[interval])
    start_date = st.date_input("Start Date", value=min_start_date.date(), min_value=min_start_date.date(), max_value=current_date.date())
    end_date = st.date_input("End Date", value=current_date.date(), min_value=start_date, max_value=current_date.date())
    
    historical_clicked = st.button("Get Historical")
    
    st.subheader("Strategy Controls")
    
    equity = st.number_input("Initial Equity ($)", value=DEFAULT_VALUES[trading_style]["equity"], min_value=1000)
    size = st.number_input("Position Size (%)", value=DEFAULT_VALUES[trading_style]["size"], min_value=1, max_value=100)
    fees = fees = st.number_input("Fees (as %)", value=0.12, format="%.4f")
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
        # Convert start_date and end_date to mm/dd/yyyy format
        formatted_start_date = start_date.strftime("%m/%d/%Y")
        formatted_end_date = end_date.strftime("%m/%d/%Y")

        # Use the interval directly in the title instead of trading style
        fig = go.Figure([go.Scatter(x=data.index, y=data, mode='lines', name=ticker)])
        fig.update_layout(
            title=f"{ticker} Price Data ({interval}) ({formatted_start_date} to {formatted_end_date})",
            xaxis_title="Time",
            yaxis_title="Price"
        )
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
            fees=fees/100, init_cash=equity, freq=interval, min_size=1, size_granularity=1
        )

        tab1, tab2, tab3 = st.tabs(["Graphs", "Statistics", "Trades"])

        with tab1:
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
        
        with tab2:
            # Display results
            #st.markdown("**Statistics:**")
            stats_df = pd.DataFrame(portfolio.stats(), columns=['Value'])
            stats_df.index.name = 'Metric'  # Set the index name to 'Metric' to serve as the header
            st.dataframe(stats_df, height=1018)  # Adjust the height as needed to remove the scrollbar
        
        with tab3:
            #st.markdown("**Trades:**")
            trades_df = portfolio.trades.records_readable
            trades_df = trades_df.round(2)  # Rounding the values for better readability
            trades_df.index.name = 'Trade No'  # Set the index name to 'Trade Name' to serve as the header
            trades_df.drop(trades_df.columns[[0,1]], axis=1, inplace=True)
            st.dataframe(trades_df, width=920, height=1018)  # Set index to False and use full width