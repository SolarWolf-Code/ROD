import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf


def portfolio():
    st.header("Portfolio", divider="rainbow")
    portfolio = pd.read_csv("portfolio.csv").sort_values("Date", ascending=False)

    symbols = set(portfolio["Ticker"].tolist())

    tickers = yf.Tickers(" ".join(symbols))

    # calculate percent of portfolio by mulitplying the number of shares by the current price
    portfolio_values = pd.DataFrame()
    symbol_data = {}
    div_data = {}
    with st.spinner("Fetching data..."):
        for symbol in symbols:
            symbol_data[symbol] = tickers.tickers[symbol].info
            div_data[symbol] = tickers.tickers[symbol].dividends
            shares = portfolio[portfolio["Ticker"] == symbol]["Shares"].sum()
            sell = portfolio[portfolio["Ticker"] == symbol]["Type"].str.contains("Sell")
            sell_shares = portfolio[portfolio["Ticker"] == symbol][sell]["Shares"].sum()
            shares -= sell_shares

            total_value = shares * symbol_data[symbol]["previousClose"]
            new_row = pd.DataFrame({"Ticker": [symbol], "Value": [total_value]})
            portfolio_values = pd.concat([portfolio_values, new_row], ignore_index=True)


    # calculate total returns for each symbol
    returns = pd.DataFrame()
    total_contributions = 0
    for symbol in symbols:
        capital_gains = 0
        last_price = symbol_data[symbol]["regularMarketPreviousClose"]
        for _, row in portfolio[portfolio["Ticker"] == symbol].iterrows():
            if row["Type"] != "Sell":            
                capital_gains += (last_price - row["Price"]) * row["Shares"]
                if row["Type"] == "Buy":
                    total_contributions += row["Price"] * row["Shares"]
            
        new_row = pd.DataFrame({"Ticker": [symbol], "Capital Gains": [capital_gains], "Total Dividends": [0.0]})
        returns = pd.concat([returns, new_row], ignore_index=True)

    # calculate dividends for each symbol
    # this is a bit more involved because we need to determine the number of shares before that dividend was paid
    for symbol in symbols:
        divs = div_data[symbol]
        # loop through the divs series 
        for ddate, div in divs.items():
            for _, row in portfolio[portfolio["Ticker"] == symbol].iterrows():
                pdate = pd.to_datetime(row["Date"]).tz_localize('America/New_York')
                if pdate < ddate:
                    returns.loc[returns["Ticker"] == symbol, "Total Dividends"] += div * row["Shares"]
        
    # calculate total returns
    total_returns = returns["Capital Gains"].sum() + returns["Total Dividends"].sum()
    
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Portfolio Value", f"${round(portfolio_values['Value'].sum(), 2)}", f"{round((total_returns / total_contributions) * 100, 2)}%")
    with col2:
        st.metric("Total Contributions", f"${round(total_contributions, 2)}")
    with col3:
        st.metric("Total Gains", f"${round(returns["Capital Gains"].sum(), 2)}")
    with col4:
        st.metric("Total Dividends", f"${round(returns['Total Dividends'].sum(), 2)}")

    # st.table(returns)

    fig = go.Figure(data=[go.Pie(labels=portfolio_values["Ticker"], values=portfolio_values["Value"])])
    st.plotly_chart(fig)

    with st.expander("Purchase History"):
        st.table(portfolio)