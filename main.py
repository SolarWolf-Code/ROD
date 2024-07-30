import streamlit as st
from pages.portfolio import portfolio
from pages.rod import rod
from pages.rebalancer import rebalancer

pg = st.navigation([
    st.Page(portfolio, title="Portfolio", icon=":material/pie_chart:"),
    st.Page(rod, title="Retire On Dividends", icon=":material/payments:"),
    st.Page(rebalancer, title="Rebalancer", icon=":material/autorenew:"),
    ])
pg.run()

