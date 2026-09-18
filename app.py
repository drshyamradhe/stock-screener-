import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="Stock Screening", layout="wide")

# App Header
st.title("Stock Screening")
st.markdown("---")

# ---------------------------------------------------------
# 1. USER INPUT CONTROLS
# ---------------------------------------------------------
st.subheader("Screening Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    timeframe = st.selectbox(
        "Select Timeframe",
        options=["1 hr", "1 day", "1 wk"],
        index=0
    )

with col2:
    ema1_val = st.selectbox(
        "Select EMA 1",
        options=[5, 10, 20],
        index=1  # Default: 10
    )

with col3:
    ema2_val = st.selectbox(
        "Select EMA 2",
        options=[20, 50, 200],
        index=0  # Default: 20
    )

st.markdown("---")

# Map timeframe selection to yfinance interval and period settings
tf_mapping = {
    "1 hr": {"interval": "1h", "period": "60d"},
    "1 day": {"interval": "1d", "period": "1y"},
    "1 wk": {"interval": "1wk", "period": "2y"}
}

# Standard Nifty F&O stock tickers
STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LTIM.NS", "LT.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "NTPC.NS",
    "POWERGRID.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS"
]

# ---------------------------------------------------------
# 2. SCREENING LOGIC
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def screen_stocks(stock_list, tf, e1, e2):
    interval = tf_mapping[tf]["interval"]
    period = tf_mapping[tf]["period"]
    
    buy_signals = []
    sell_signals = []
    
    for ticker in stock_list:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            # Ensure sufficient candles exist for indicator calculations
            if len(df) < max(e1, e2) + 2:
                continue
            
            # Calculate Exponential Moving Averages (EMA)
            df[f'EMA_{e1}'] = ta.trend.ema_indicator(df['Close'], window=e1)
            df[f'EMA_{e2}'] = ta.trend.ema_indicator(df['Close'], window=e2)
            
            curr_price = df['Close'].iloc[-1]
            ema1_curr = df[f'EMA_{e1}'].iloc[-1]
            ema2_curr = df[f'EMA_{e2}'].iloc[-1]
            
            ema1_prev = df[f'EMA_{e1}'].iloc[-2]
            ema2_prev = df[f'EMA_{e2}'].iloc[-2]
            
            symbol_clean = ticker.replace(".NS", "")
            
            # Check Crossovers
            bullish_cross = (ema1_prev <= ema2_prev) and (ema1_curr > ema2_curr)
            bearish_cross = (ema1_prev >= ema2_prev) and (ema1_curr < ema2_curr)
            
            if bullish_cross:
                buy_signals.append({
                    "Symbol": symbol_clean,
                    "Price": round(curr_price, 2),
                    f"EMA {e1}": round(ema1_curr, 2),
                    f"EMA {e2}": round(ema2_curr, 2),
                    "Signal": "BUY"
                })
                
            if bearish_cross:
                sell_signals.append({
                    "Symbol": symbol_clean,
                    "Price": round(curr_price, 2),
                    f"EMA {e1}": round(ema1_curr, 2),
                    f"EMA {e2}": round(ema2_curr, 2),
                    "Signal": "SELL"
                })
        except Exception:
            continue
            
    return pd.DataFrame(buy_signals), pd.DataFrame(sell_signals)

# Run Screening Action
if st.button("Run Stock Screener", use_container_width=True):
    with st.spinner(f"Scanning stocks on {timeframe} timeframe for EMA {ema1_val} & EMA {ema2_val} crossovers..."):
        buy_df, sell_df = screen_stocks(STOCKS, timeframe, ema1_val, ema2_val)
        
        col_buy, col_sell = st.columns(2)
        
        with col_buy:
            st.markdown("### 🟢 Buy Signals (EMA 1 Crossed Above EMA 2)")
            if not buy_df.empty:
                st.dataframe(buy_df, hide_index=True, use_container_width=True)
            else:
                st.info("No Buy signals generated for the selected parameters.")

        with col_sell:
            st.markdown("### 🔴 Sell Signals (EMA 1 Crossed Below EMA 2)")
            if not sell_df.empty:
                st.dataframe(sell_df, hide_index=True, use_container_width=True)
            else:
                st.info("No Sell signals generated for the selected parameters.")
