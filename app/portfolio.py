import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import robin_stocks.robinhood as r

def get_portfolio_from_rh():
    holdings = r.account.build_holdings(with_dividends=True)

    portfolio = pd.DataFrame()
    for symbol, data in holdings.items():
        new_row = pd.DataFrame(data, index=[symbol])
        portfolio = pd.concat([portfolio, new_row])
    
    return portfolio

def reload_portfolio():
    st.session_state.pop("portfolio")
    st.session_state.pop("portfoliovalue")
    st.session_state.pop("transfers")
    st.session_state.pop("dividends")

def portfolio():
    st.header("Portfolio", divider="rainbow")
    with st.spinner("Fetching Portfolio Data"):
        if 'transfers' not in st.session_state:
            st.session_state.transfers = r.account.get_unified_transfers()

        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = get_portfolio_from_rh()


        if 'portfoliovalue' not in st.session_state:
            st.session_state.portfoliovalue = r.load_portfolio_profile()
            
        if st.session_state.portfoliovalue.get("extended_hours_equity") is not None:
            total_portfolio_value = float(st.session_state.portfoliovalue["extended_hours_equity"])
        else:
            total_portfolio_value = float(st.session_state.portfoliovalue["equity"])

        if 'dividends' not in st.session_state:
            st.session_state.dividends =  r.get_total_dividends()

        portfolio = st.session_state.portfolio.copy()
        total_contributions = 0

        for transfer in st.session_state.transfers:
            if transfer["direction"] == "pull" and transfer["state"] == "completed":
                total_contributions += float(transfer["amount"])

        order_history = r.get_all_stock_orders()
        orders_df = pd.DataFrame()
        for order in order_history:
            symbol = r.stocks.get_symbol_by_url(order["instrument"])

            # add instrument to portfolio
            portfolio.loc[symbol, "instrument"] = order["instrument"]

            order_type = order["side"]
            for execution in order["executions"]:
                pd_date = pd.to_datetime(execution["timestamp"]).tz_convert('America/New_York')
                new_row = pd.DataFrame({"Date": [pd_date], "Symbol": [symbol], "Price": [execution["price"]], "Shares": [execution["quantity"]], "Type": [order_type.upper()]})
                orders_df = pd.concat([orders_df, new_row])

        col1, col2, col3, col4, col5 = st.columns(5, vertical_alignment="top")
        with col1:
            st.metric("Total Portfolio Value", f"${round(float(total_portfolio_value), 2)}")
        with col2:
            st.metric("Total Contributions", f"${round(total_contributions, 2)}")
        with col3:
            st.metric("Total Gains", f"${round(float(total_portfolio_value) - total_contributions, 2)}", f"{round(((float(st.session_state.portfoliovalue["equity"]) - total_contributions) / total_contributions) * 100, 2)}%")
        with col4:
            st.metric("Total Dividends", f"${round(st.session_state.dividends, 2)}")
        with col5:
            st.button(":material/refresh:", on_click=lambda: reload_portfolio())

        fig = go.Figure(data=[go.Pie(labels=portfolio.index, values=portfolio["equity"])])
        st.plotly_chart(fig)


        with st.expander("Order History"):
            st.dataframe(orders_df, use_container_width=True)