import streamlit as st
import pandas as pd
import plotly.express as px
from pyparsing import Empty
from openai import OpenAI

from api_calls import fetch_time_series
from api_calls import fetch_crypto_data
from api_calls import process_accounts_separate
from api_calls import all_yoy_change
from api_calls import all_dataframes
from api_calls import ai_portfolio_analysis
from test2 import user_portfolio

st.title("retail.risk dashboard")

uploaded_file = st.file_uploader('Upload your CSV (must follow set format)')
user_age = st.number_input('How old are you?', max_value= 100)
user_inv_hor = st.number_input('What is your investment horizon? (years)', max_value= 100)
r_tolerance = st.selectbox('What is your risk tolerance?', ('Conservative', 'Balanced', 'Aggressive'))

st.markdown('This is not investment advice, but an application that allows you to view and analyse your current portfolio positions')

submit_button = st.button('Submit')

if submit_button:
    if not uploaded_file:
        st.error('Please upload your portfolio CSV')
    elif not user_age or not user_inv_hor or not r_tolerance:
        st.error('Please upload your investing characteristics')
    else:
        user_df = pd.read_csv(uploaded_file)
        st.session_state['submitted'] = True
        st.session_state['portfolio'] = user_df
        st.session_state['age'] = user_age
        st.session_state['inv_hor'] = user_inv_hor
        st.session_state['risk_tol'] = r_tolerance
        st.success('Inputs received. Running Portfolio Analysis ✅')

if st.session_state.get('submitted', False):
    user_portfolio = st.session_state['portfolio']
    total_portfolio_value = user_portfolio['amount'].sum()
    user_portfolio['pct_of_total'] = user_portfolio['amount']/ total_portfolio_value

    user_equities = user_portfolio[user_portfolio["type"].isin(["equity"])]
    user_crypto = user_portfolio[user_portfolio["type"].isin(["crypto"])]
    user_cash = user_portfolio[user_portfolio["type"].isin(["cash"])]
    user_savings = user_portfolio[user_portfolio["type"].isin(["savings"])]
    user_bonds = user_portfolio[user_portfolio["type"].isin(["bond"])]

    u_eq_tickers = user_equities["ticker"].dropna().str.upper().tolist()
    u_crypto_holding = user_crypto["ticker"].dropna().str.lower().str.strip().tolist()
    coin_id = user_crypto["ticker"]

    equity_list = {}
    all_equities_data = {}
    crypto_list = {}

    # st.success('Portfolio Loaded Correctly ✅')

    st.markdown('### Portfolio Overview')

    user_portfolio['pct_of_total'] = user_portfolio['amount'] / total_portfolio_value
    todays_date = pd.Timestamp.today().normalize()
    st.markdown(f" **Total Portfolio Value** {todays_date.strftime('%Y-%m-%d')}: \n\n **:green[${total_portfolio_value}]**")
    if "type" in user_portfolio.columns and "amount" in user_portfolio.columns:
        pie1 = px.pie(user_portfolio, values="amount", names="type", title="Portfolio Allocation")
        st.plotly_chart(pie1)

    st.divider()

    st.markdown('### YoY Performance')

    equity_list = {}
    all_equities_data= {}

    for symbol in u_eq_tickers:
        try:
            time_series = fetch_time_series(symbol)
            if time_series is not None and not time_series.empty:
                equity_list[symbol] = time_series
        except Exception as e:
            st.write(f'Error fetching data for {symbol}: {e}')

    for ticker, df in equity_list.items():
        df = df.copy()
        df["ticker"] = ticker
        starting_price = df.iloc[0]["close"]
        df["normalised"] = df["close"] / starting_price * 100
        all_equities_data[ticker] = df

    coin_id = user_crypto["ticker"]

    crypto_list = {}

    for coin_id in u_crypto_holding:
        try:
            crypto_time_series = fetch_crypto_data(coin_id)
            if crypto_time_series is not None and not crypto_time_series.empty:
                crypto_list[coin_id] = crypto_time_series
        except Exception as e:
            st.write(f'Error fetching data for {coin_id}: {e}')

    savings_amount = process_accounts_separate(user_savings, 'savings')
    bonds_amount = process_accounts_separate(user_bonds, 'bonds')

    user_portfolio['ticker'] = user_portfolio['ticker'].fillna(value = user_portfolio['type'])

    u_p_pct_total = user_portfolio.rename(columns={'ticker': 'asset'})

    bond_counter = 1
    sav_counter = 1

    u_p_pct_total['orig_asset'] = u_p_pct_total['asset']

    for index, row in u_p_pct_total.iterrows():
        if row['asset'] == 'bond':
            u_p_pct_total.at[index, 'asset'] = f'bond_account_{bond_counter}'
            bond_counter += 1
        if row['asset'] == 'savings':
            u_p_pct_total.at[index, 'asset'] = f'savings_account_{sav_counter}'
            sav_counter += 1


    u_p_pct_total = u_p_pct_total[['asset', 'pct_of_total']]

    all_data_dict = all_dataframes(all_equities_data, crypto_list, savings_amount, bonds_amount, user_cash)

    pct_change_yoy = all_yoy_change(all_data_dict)
    pct_change_yoy = pct_change_yoy.reset_index()
    pct_change_yoy_2 = pct_change_yoy
    pct_change_yoy = pd.melt(pct_change_yoy, id_vars ='date', var_name = 'asset', value_name = 'pct_change_yoy')
    pct_change_yoy = pd.merge(pct_change_yoy, u_p_pct_total, how = 'left', on = 'asset')
    pct_change_yoy['norm_change_yoy'] = pct_change_yoy['pct_change_yoy'] * pct_change_yoy['pct_of_total']

    yoy_perf = px.line(pct_change_yoy, y ='pct_change_yoy', x = 'date', title="Growth Drivers", color = 'asset')
    st.plotly_chart(yoy_perf)

    norm_yoy_perf = px.line(pct_change_yoy, y='norm_change_yoy', x='date', title="Growth Drivers (Portfolio Weighting)", color='asset')
    st.plotly_chart(norm_yoy_perf)

    growth_driver = pct_change_yoy_2.iloc[[-1]]
    growth_driver = growth_driver.drop(columns = 'date')
    growth_driver = growth_driver.transpose()
    growth_driver = growth_driver.rename(columns = {list(growth_driver.columns)[0]: 'growth'})
    growth_driver['pct'] = growth_driver['growth'] * 100
    growth_driver = growth_driver.sort_values(by = 'pct', ascending = False)
    top_ticker = growth_driver.index[0]
    top_pct = growth_driver['pct'].values[0]
    top_pct = top_pct.round(2)
    st.write(f"Your main growth driver over the past year was **:green[{top_ticker}]**. This asset appreciated by **:green[{top_pct}%]** over the previous 12 months")

    st.divider()

    st.markdown('### risk-bot :moneybag:')

    ai_risk_analysis = ai_portfolio_analysis(user_age, user_inv_hor, user_portfolio, r_tolerance)

    st.write(ai_risk_analysis)

