import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yfinance as yf
from portfolio import get_portfolio_from_rh


def rebalancer():
    st.header("Portfolio Rebalancing Tool", divider="rainbow")

    # Cache the portfolio data
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = get_portfolio_from_rh()

    portfolio = st.session_state.portfolio

    if 'rebalance' not in st.session_state:
        df = pd.DataFrame({
            'Ticker': portfolio.index,
            'Shares': portfolio['quantity'].astype(float).values,
            'Target Weight %': 0.0
        })

        st.session_state.rebalance = df

    col1, col2 = st.columns([6, 2])
    with col1:
        current_portfolio = st.data_editor(st.session_state.rebalance, num_rows="dynamic", use_container_width=True)

    with col2:
        deposit_amount = st.number_input("Deposit Amount", value=500, min_value=0, step=5)
        min_investment = st.number_input("Minimum Fractional Investment", value=1, min_value=0, step=1)

    st.divider()

    # Check if the DataFrame is not empty
    if not current_portfolio.empty:
        # Check if all required data is provided
        if not current_portfolio.isnull().values.any():

            # Ensure the sum of target weights is equal to 100
            if current_portfolio['Target Weight %'].sum() == 100:
                edited_df = current_portfolio.copy()
                st.session_state.rebalance = current_portfolio.copy()

                # print(edited_df)
                tickers = yf.Tickers(" ".join(edited_df['Ticker'].tolist()))
                edited_df['Price'] = st.session_state.portfolio['price'].values.astype(float)

                # Calculate the current value and weight of each asset
                edited_df['current_value'] = edited_df['Shares'] * edited_df['Price']
                total_portfolio_value = edited_df['current_value'].sum()
                new_total_portfolio_value = total_portfolio_value + deposit_amount

                # Calculate current weights and target values
                edited_df['current_weight'] = round(edited_df['current_value'] / total_portfolio_value * 100, 3)
                edited_df['target_value'] = (edited_df['Target Weight %'] / 100) * new_total_portfolio_value
                edited_df['shortfall'] = np.maximum(0, edited_df['target_value'] - edited_df['current_value'])

                # Calculate the total shortfall and additional investments
                total_shortfall = edited_df['shortfall'].sum()
                edited_df['additional_investment'] = np.where(total_shortfall > 0, 
                                    (edited_df['shortfall'] / total_shortfall) * deposit_amount, 
                                    0)

                # Ensure additional investment is at least $5 and divisible by $5
                edited_df['additional_investment'] = np.where(edited_df['additional_investment'] < min_investment, 
                                    0, 
                                    (edited_df['additional_investment'] // min_investment) * min_investment)

                # Adjust remaining funds
                remaining_deposit = deposit_amount - edited_df['additional_investment'].sum()
                while remaining_deposit >= min_investment:
                    for idx in edited_df.index:
                        if edited_df.loc[idx, 'shortfall'] > 0 and remaining_deposit >= min_investment:
                            edited_df.loc[idx, 'additional_investment'] += min_investment
                            remaining_deposit -= min_investment

                # Calculate the future weights
                edited_df['future_value'] = edited_df['current_value'] + edited_df['additional_investment']
                edited_df['future_weight'] = round(edited_df['future_value'] / new_total_portfolio_value * 100, 3)

                # Calculate the number of shares to be bought
                edited_df['shares_to_buy'] = edited_df['additional_investment'] / edited_df['Price']

                # Create dataframes for additional investments, current weights, future weights, and shares to buy
                additional_investments_df = edited_df[['Ticker', 'additional_investment', 'shares_to_buy']].rename(columns={'additional_investment': 'Additional Investment', 'shares_to_buy': 'Shares to Buy'})
                additional_investments_df = additional_investments_df[additional_investments_df['Additional Investment'] != 0]
                additional_investments_df = additional_investments_df.sort_values(by='Additional Investment', ascending=False).reset_index(drop=True)

                current_weights_df = edited_df[['Ticker', 'current_weight']].rename(columns={'current_weight': 'Current Weight'})
                future_weights_df = edited_df[['Ticker', 'future_weight']].rename(columns={'future_weight': 'Future Weight'})

                # Print out the results
                st.header("Buy Orders:")
                st.table(additional_investments_df)

                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(current_weights_df, values='Current Weight', names='Ticker', title='Current Weights')
                    st.plotly_chart(fig)            

                with col2:
                    fig = px.pie(future_weights_df, values='Future Weight', names='Ticker', title='Weights after Orders')
                    st.plotly_chart(fig)

                
                st.divider()

                with st.expander("Show Future Dividends"):
                    # calculate future dividends using the future weights
                    future_dividends = pd.DataFrame({
                        'Date': pd.Series(dtype='datetime64[ns]'),
                        'Ticker': pd.Series(dtype='str'),
                        'Dividends': pd.Series(dtype='float'),
                        'Yield': pd.Series(dtype='float'),
                    })

                    for idx in edited_df.index:
                        ticker = edited_df.loc[idx, 'Ticker']
                        historical_divs = tickers.tickers[ticker].history(period='max').loc[tickers.tickers[ticker].history(period='max')['Dividends'] != 0]
                        historical_divs['Yield'] = (historical_divs['Dividends'] / historical_divs['Close']) * 100

                        # get averagey yield from the last 3 months. we need to use date time because some divs are paid quarterly
                        last_3_months = historical_divs[historical_divs.index.tz_localize(None) > (pd.Timestamp.now().tz_localize(None) - pd.DateOffset(months=3))]
                        avg_yield = last_3_months['Yield'].mean()
                        
                        # calculate future dividends. use concat to add the new row to the dataframe
                        dividend_growth = tickers.tickers[ticker].dividends.pct_change().mean()

                        # calculate the future dividends for the next year
                        last_div = historical_divs.iloc[-1]['Dividends']
                        for i in range(1, 13):
                            future_dividends = pd.concat([future_dividends, pd.DataFrame({
                                'Date': [pd.Timestamp.today().date() + pd.DateOffset(months=i)],
                                'Ticker': [ticker],
                                'Dividends': [last_div * (edited_df.loc[idx, 'Shares'] + edited_df.loc[idx, 'shares_to_buy'])],
                                'Yield': [avg_yield]
                            })], ignore_index=True)

                            last_div = last_div * (1 + dividend_growth)


                    future_dividends = future_dividends.sort_values(by='Date')
                    # # Merge hover texts with the summed dividends
                    future_dividends_sum = future_dividends[['Date', 'Dividends']].groupby('Date').sum().reset_index()


                    # Prepare hover text
                    hover_texts = future_dividends.groupby('Date').apply(
                        lambda df: '<br>'.join([f"{row['Ticker']}: {row['Dividends']:.2f}" for _, row in df.iterrows()] + [f"<br>Total: {df['Dividends'].sum():.2f}"]), include_groups=False
                    ).reset_index(name='HoverText')

                    # Merge hover texts with the summed dividends
                    future_dividends_sum = future_dividends[['Date', 'Dividends']].groupby('Date').sum().reset_index()
                    future_dividends_sum = future_dividends_sum.merge(hover_texts, on='Date')

                    # Plotly bar chart
                    fig = go.Figure(data=[go.Bar(
                        x=future_dividends_sum['Date'],
                        y=future_dividends_sum['Dividends'],
                        text=future_dividends_sum['Dividends'].round(2),
                        textposition='outside',
                        hovertext=future_dividends_sum['HoverText'],
                        hoverinfo='none',
                        hovertemplate='%{hovertext}<extra></extra>',
                        marker_color='darkgreen'
                    )])

                    # Customize layout
                    fig.update_layout(
                        title='Future Dividends',
                        xaxis_title='Date',
                        yaxis_title='Dividends',
                        xaxis=dict(
                            tickformat='%Y-%m-%d',
                            tickangle=45,  # Rotate labels 90 degrees
                            tickfont=dict(size=10),
                            tickmode='linear',
                            tick0=future_dividends_sum['Date'].min(),
                            dtick=2629746000  # One day in milliseconds
                        )
                    )

                    # Display the figure
                    st.plotly_chart(fig)


            else:
                st.error("The sum of target weights should be equal to 100.")
        else:
            st.error("Please enter data in all the columns.")
    else:
        st.error("Please enter some data to calculate the rebalancing.")



