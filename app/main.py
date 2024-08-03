import streamlit as st
from portfolio import portfolio
from rod import rod
from rebalancer import rebalancer
from next_invest import new_invests
import robin_stocks.robinhood as r
import os

r.login(os.getenv("RH_USERNAME"), os.getenv("RH_PASSWORD"))
pg = st.navigation([
    st.Page(portfolio, title="Portfolio", icon=":material/pie_chart:"),
    st.Page(rod, title="Retire On Dividends", icon=":material/payments:"),
    st.Page(rebalancer, title="Rebalancer", icon=":material/autorenew:"),
    st.Page(new_invests, title="Next Investment", icon=":material/attach_money:"),
    ])
pg.run()

