import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from future_divs import calculate_future_income





def rod_page():
    st.header("Retire On Dividends 💸", divider="rainbow")

    if 'ticker' not in st.session_state:
        st.session_state.ticker = "MSTY"

    ticker = st.text_input("Enter the ticker symbol", st.session_state.ticker)

    if ticker != st.session_state.ticker:
        st.session_state.ticker = ticker


    if 'period' not in st.session_state:
        st.session_state.period = "max"

    def get_data(ticker, period):
        tick = yf.Ticker(ticker)
        hist = tick.history(period=period, back_adjust=True, auto_adjust=False)
        hist.index = hist.index.tz_convert('America/New_York')  # Ensure the index is timezone-aware
        return tick, hist

    def main():
        tick, hist = get_data(ticker, "max")
        chart_data = hist

        yields = pd.DataFrame()

        if hist.get("Dividends") is not None:
            hist_div_filtered = hist[hist["Dividends"] != 0]
            yields["Price"] = hist_div_filtered["Close"]
            yields["Dividend"] = hist_div_filtered["Dividends"]
            yields["Yield"] = ((yields["Dividend"] * 12) / yields["Price"]) * 100

            tab1, tab2, tab3 = st.tabs(["Stock Price", "History", "Dividends"])
            with tab1:
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
                today = pd.Timestamp.now(tz='America/New_York')

                # Update the period in session state based on button clicks
                if col1.button("5D"):
                    st.session_state.period = "5d"
                if col2.button("1M"):
                    st.session_state.period = "1mo"
                if col3.button("3M"):
                    st.session_state.period = "3mo"
                if col4.button("6M"):
                    st.session_state.period = "6mo"
                if col5.button("1Y"):
                    st.session_state.period = "1y"
                if col6.button("5Y"):
                    st.session_state.period = "5y"
                if col7.button("YTD"):
                    st.session_state.period = "ytd"
                if col8.button("MAX"):
                    st.session_state.period = "max"

                # Filter data based on the selected period
                period_map = {
                    "5d": pd.DateOffset(days=6),
                    "1mo": pd.DateOffset(months=1),
                    "3mo": pd.DateOffset(months=3),
                    "6mo": pd.DateOffset(months=6),
                    "1y": pd.DateOffset(years=1),
                    "5y": pd.DateOffset(years=5),
                }

                if st.session_state.period in period_map:
                    if st.session_state.period == "ytd":
                        chart_data = hist.loc[hist.index >= today.replace(month=1, day=1)]
                    else:
                        chart_data = hist.loc[hist.index >= today - period_map[st.session_state.period]]
                else:
                    chart_data = hist

                line_color = "red" if chart_data.iloc[-1]["Close"] < chart_data.iloc[0]["Close"] else "green"
                raw_difference = round(chart_data.iloc[-1]['Close'] - chart_data.iloc[0]['Close'], 2)
                percent_difference = round(((chart_data.iloc[-1]['Close'] - chart_data.iloc[0]['Close']) / chart_data.iloc[0]['Close']) * 100, 2)
                if line_color == "green":
                    raw_difference = "+" + str(raw_difference)
                    percent_difference = "+" + str(percent_difference)

                fig = go.Figure(go.Scatter(x=chart_data.index, y=chart_data["Close"], mode="lines", name="Close Price", line=dict(color=line_color), fill="tozeroy"))
                fig.update_layout(yaxis_range=[chart_data["Close"].min()*0.98, chart_data["Close"].max()])
                # fig.update_layout(title_text=f"{raw_difference} ({percent_difference}%)", title_font_color=line_color, font=dict(size=50))
                fig.update_layout(title=dict(text=f"{raw_difference} ({percent_difference}%)", font=dict(size=24, color=line_color)))
                st.plotly_chart(fig)

            with tab2:
                hist_filtered = hist.drop(columns=["Dividends", "Stock Splits", "Capital Gains"])
                st.table(hist_filtered)
            
            with tab3:
                st.table(yields)

            st.divider()

            avg_purchase_price = st.number_input("Avg. Purchase Price", 0.0, 1000000.0, hist.iloc[-1]["Close"])
            capital_appreciation = hist.iloc[-1]["Close"] - avg_purchase_price

            col1, col2, col3 = st.columns(3)
            col1.metric("Avg. Stock Price", f"${round(yields['Price'].mean(), 2)}")
            col2.metric("Capital Appreciation", f"${round(capital_appreciation, 2)}", f"{round((capital_appreciation / avg_purchase_price) * 100, 2)}%")
            col3.metric("Total Return", f"${round(capital_appreciation + yields['Dividend'].sum(), 2)}", f"{round(((capital_appreciation + yields['Dividend'].sum()) / avg_purchase_price) * 100, 2)}%")

            st.divider()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Dividends", f"${round(yields['Dividend'].sum(), 2)}")
            col2.metric("Avg. Dividend Payout", f"${round(yields['Dividend'].mean(), 2)}")

            today = pd.Timestamp.today().tz_localize("America/New_York")
            three_months_ago = today - pd.DateOffset(months=3)
            last_3_months = yields[yields.index >= pd.to_datetime(three_months_ago)]
            last_3_months = last_3_months[last_3_months["Dividend"] != 0]
            col3.metric("T3 Avg. Yield", f"{round(last_3_months['Yield'].mean(), 2)}%")

            st.divider()

            age_range = st.slider("Current age/Retirement age", value=[23, 65], min_value=18, max_value=100)

            starting_investment = st.number_input("Starting Investment", 0, 1000000, 1000)
            monthly_investment = st.number_input("Monthly Investment", 0, 1000000, 500)
            tax_rate = st.selectbox("Tax Rate %", [10, 12, 22, 24, 32, 35, 37], index=2)
            expense_ratio = st.number_input("Expense Ratio %", 0.0, 5.0, 1.01)

            st.markdown("### Est. Monthly Income after fees")
            tab1, tab2 = st.tabs(["Chart", "Table"])
            future_data = calculate_future_income(age_range, last_3_months['Yield'].mean(), starting_investment, monthly_investment, capital_appreciation, tax_rate, expense_ratio)
            with tab1:
                st.plotly_chart(go.Figure(go.Scatter(x=future_data["Date"], y=future_data["Total Monthly Income"], mode="lines", name="Total Monthly Income")))
            with tab2:
                st.table(future_data)

            with st.expander("Related News"):
                news = tick.news
                for idx, item in enumerate(news):
                    st.markdown(f"### [{item['title']}]({item['link']})")
                    pub_date = pd.to_datetime(item["providerPublishTime"], unit="s")
                    if pub_date < pd.Timestamp.today() - pd.DateOffset(days=1):
                        if (pd.Timestamp.today() - pub_date).days > 30:
                            pub_date = f"{(pd.Timestamp.today() - pub_date).days // 30} month(s) ago"
                        else:
                            pub_date = f"{(pd.Timestamp.today() - pub_date).days} day(s) ago"
                    else:
                        pub_date = f"{(pd.Timestamp.today() - pub_date).seconds // 3600} hour(s) ago"

                    st.caption(f"{item['publisher']} ● {pub_date}")
                    if idx != len(news) - 1:
                        st.divider()
        else:
            st.error("No dividend data available for this stock")
    
    main()

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

            total_value = shares * symbol_data[symbol]["ask"]
            new_row = pd.DataFrame({"Ticker": [symbol], "Value": [total_value]})
            portfolio_values = pd.concat([portfolio_values, new_row], ignore_index=True)


    # calculate total returns for each symbol
    returns = pd.DataFrame()
    total_contributions = 0
    for symbol in symbols:
        capital_gains = 0
        last_price = symbol_data[symbol]["ask"]
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

pg = st.navigation([
    st.Page(portfolio, title="Portfolio", icon=":material/pie_chart:"),
    st.Page(rod_page, title="Retire On Dividends", icon=":material/payments:"),
    ])
pg.run()

