import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Define the symbols
symbols = [
    "TSLY", "OARK", "APLY", "NVDY", "AMZY", "FBY", "GOOY", "CONY", "NFLY", "DISO",
    "MSFO", "XOMO", "JPMO", "AMDY", "PYPY", "SQY", "MRNY", "AIYY", "YMAX", "YMAG",
    "MSTY", "ULTY", "YBIT", "CRSH", "GDXY", "SNOY", "ABNY",
]

def new_invests():
    # Fetch ticker data
    tickers = yf.Tickers(" ".join(symbols))

    if "period" not in st.session_state:
        st.session_state.period = "max"


    # 1mo, 3mo, 6mo, 1y, ytd, max
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("1M"):
        st.session_state.period = "1mo"
    if col2.button("3M"):
        st.session_state.period = "3mo"
    if col3.button("YTD"):
        st.session_state.period = "ytd"
    if col4.button("MAX"):
        st.session_state.period = "max"

    with st.spinner("Fetching data..."):
        ticker_data = {}
        for symbol in symbols:
            ticker_data[symbol] = tickers.tickers[symbol].history(period=st.session_state.period)

        # Initialize an empty DataFrame for the overall data
        overall_df = pd.DataFrame()

        # Loop through each symbol to calculate variance and dividend yield
        for symbol, data in ticker_data.items():
            std = np.std(data["Close"])

            div_data = ticker_data[symbol]
            div_data = div_data[div_data["Dividends"] > 0]
            if len(div_data) > 0:
                latest_div = div_data.iloc[-1]
                latest_div_amount = latest_div["Dividends"]
                div_yield = (latest_div_amount / latest_div["Close"] * 12) * 100

                # calculate the sharpe ratio
                sharpe_ratio = (data["Close"].iloc[-1] - data["Close"].iloc[0]) / std

                # calculate the average yield for the last 3 months
                three_month_div_data = div_data.iloc[-3:]
                average_yield = ((three_month_div_data["Dividends"].sum() / three_month_div_data["Close"].mean() * 12) * 100) / 3 

                # only store the price and not the date
                new_row = pd.DataFrame({"Symbol": [symbol], "Dividend Yield": [average_yield], "Sharpe Ratio": [sharpe_ratio], "Variance": [np.var(data["Close"])], "Close Price": [data["Close"].tolist()]})

                overall_df = pd.concat([overall_df, new_row], ignore_index=True)



        # Display the DataFrame with line charts
        st.dataframe(
            overall_df,
            column_config={
                "Close Price": st.column_config.LineChartColumn("Close Price"),
            },
            hide_index=True,
            use_container_width=True,
        )
