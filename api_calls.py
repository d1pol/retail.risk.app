import requests
import json
import os
import pandas as pd
import datetime as dt
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")

def fetch_time_series(symbol):
    url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}"
    )

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "Weekly Time Series" not in data:
            print(f"No price data returned for {symbol}. Response: {data}")
            return None
    else: print (f"Error: {response.status_code}")

    time_series = data.get("Weekly Time Series", {})

    dp = []
    for date, prices in time_series.items():
        closing_price = prices["4. close"]
        dp.append({
            "date": date,
            "close": float(closing_price)
        })


    weekly_price = pd.DataFrame(dp)

    weekly_price["date"] = pd.to_datetime(weekly_price["date"])
    weekly_price = weekly_price.sort_values("date")
    weekly_price = weekly_price.set_index(weekly_price["date"])
    weekly_price = weekly_price.tail(52)
    weekly_price = weekly_price.drop('date', axis = 1)
    starting_price = weekly_price.iloc[0]["close"]
    weekly_price["pct_change_total"] = (weekly_price["close"] - starting_price)/ starting_price
    weekly_price["pct_change"] = (weekly_price["close"] - weekly_price["close"].shift(1))/ weekly_price["close"].shift(1)

    return weekly_price

CRYPTO_KEY = os.getenv("COINGECKO_KEY")


def fetch_crypto_data(coin_id, days = 365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "days": 365,
        "interval": "daily",
        "vs_currency": "USD"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "prices" not in data or not data["prices"]:
            print(f"No price data returned for {coin_id}. Response: {data}")
            return None
        prices = data["prices"]
        cryp = pd.DataFrame(prices, columns=["timestamp", "price"])
        cryp["date1"] = pd.to_datetime(cryp["timestamp"], unit='ms')
        cryp["date"] = cryp['date1'].dt.date
        cryp = cryp.set_index(cryp['date'])
        cryp = cryp.drop(columns=['timestamp', 'date1', 'date'])
        crypt_start = cryp.iloc[0]["price"]
        cryp["pct_change_total"] = (cryp["price"] - crypt_start) / crypt_start
        cryp["pct_change"] = cryp["price"].pct_change()
        return cryp
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def process_accounts(df, account_type):
    todays_date = pd.Timestamp.today().normalize()
    year_ago = todays_date - pd.DateOffset(years=1)
    dates = pd.date_range(start=year_ago, end=todays_date, freq="MS")[:: -1]
    n_months = len(dates)

    result_df = pd.DataFrame({'date': dates})
    all_ts = []

    for idx, row in df.iterrows():
        monthly_rate = row["rate"] / 12
        values = row["amount"] / (1 + monthly_rate) ** np.arange(n_months)
        values = np.round(values, 2)
        all_ts.append(values[:: -1])

    for i, values in enumerate(all_ts, start=1):
        result_df[f'{account_type}_{i}'] = values

    return result_df


def process_accounts_separate(df, account_type):
    todays_date = pd.Timestamp.today().normalize()
    year_ago = todays_date - pd.DateOffset(years=1)
    dates = pd.date_range(start=year_ago, end=todays_date, freq="MS")
    n_months = len(dates)

    all_ts_sep = {}

    for i, (idx, row) in enumerate(df.iterrows(), start = 1):
        monthly_rate = row["rate"] / 12
        values = row["amount"] / (1 + monthly_rate) ** np.arange(n_months)
        values = np.round(values, 2)
        acc_df = pd.DataFrame({'date': dates, 'values': values[:: -1]})

        acc_start = acc_df.iloc[0]["values"]
        acc_df["pct_change_total"] = (acc_df["values"] - acc_start) / acc_start
        acc_df["pct_change"] = acc_df["values"].pct_change()

        key_name = f'{account_type}_account_{i}'
        all_ts_sep[key_name] = acc_df

    return all_ts_sep

def all_dataframes(equities, crypto, savings, bonds, cash):
    return {
        'equities' : equities,
        'crypto' : crypto,
        'savings' : savings,
        'bonds' : bonds,
        'cash' : cash
    }

def all_yoy_change(all_data_dict):
    pct_from_start = None

    todays_date = pd.Timestamp.today().normalize()
    year_ago = todays_date - pd.DateOffset(months=11)
    dates = pd.date_range(start=year_ago, end=todays_date, freq="D")

    pct_from_start = pd.DataFrame({'date': dates})

    equities = all_data_dict['equities']
    crypto = all_data_dict['crypto']
    savings = all_data_dict['savings']
    bonds = all_data_dict['bonds']
    cash = all_data_dict['cash']

    for ticker in equities:
        df = pd.DataFrame(equities[ticker])
        eq_pct_yoy = df.reset_index()[['date', 'pct_change_total']]
        eq_pct_yoy['date'] = pd.to_datetime(eq_pct_yoy['date'])
        eq_pct_yoy = eq_pct_yoy.rename(columns = {'pct_change_total': ticker})
        pct_from_start = pd.merge(pct_from_start, eq_pct_yoy, how = 'outer', on = 'date')

    for coin_id in crypto:
        df = pd.DataFrame(crypto[coin_id])
        cry_pct_yoy = df.reset_index()[['date', 'pct_change_total']]
        cry_pct_yoy['date'] = pd.to_datetime(cry_pct_yoy['date'])
        cry_pct_yoy = cry_pct_yoy.rename(columns = {'pct_change_total': coin_id})
        pct_from_start = pd.merge(pct_from_start, cry_pct_yoy, how = 'outer', on = 'date')

    for key_name in savings:
        df = pd.DataFrame(savings[key_name])
        sav_pct_yoy = df.reset_index()[['date', 'pct_change_total']]
        sav_pct_yoy['date'] = pd.to_datetime(sav_pct_yoy['date'])
        sav_pct_yoy = sav_pct_yoy.rename(columns={'pct_change_total': key_name})
        pct_from_start = pd.merge(pct_from_start, sav_pct_yoy, how='outer', on='date')

    for key_name in bonds:
        df = pd.DataFrame(bonds[key_name])
        bnd_pct_yoy = df.reset_index()[['date', 'pct_change_total']]
        bnd_pct_yoy['date'] = pd.to_datetime(bnd_pct_yoy['date'])
        bnd_pct_yoy = bnd_pct_yoy.rename(columns={'pct_change_total': key_name})
        pct_from_start = pd.merge(pct_from_start, bnd_pct_yoy, how='outer', on='date')

    pct_from_start = pct_from_start.set_index('date')
    pct_from_start = pct_from_start.interpolate(method = 'time')

    return pct_from_start

OAI_KEY = os.getenv("OPEN_AI_KEY")

def ai_portfolio_analysis(age, inv_hor, portfolio, risk_tol):

    system_prompt = """
    You are a financial advisor, giving the user advice on how to maximise their portfolio returns by ingesting their risk tolerance, age, investment horizon and current portfolio
    Your roles are to do the following:
    
    1. Review the client's portfolio. Look at the weighting of assets and assess if the portfolio is defensive, balanced or aggressive. Higher savings and bonds would indicate defensive, whereas more equities and particularly crypto indicates aggressive
    2. Assess their portfolio against their stated risk tolerance. Do not let the user's stated risk tolerance impact your assessment of their portfolio. Often stated risk tolerance is different from actual
    3. Suggest three improvements they could make, with sound reasoning for each. These improvements need to be realistic, based on the amount in the user's current portfolio
    4. Consider age and investment horizon. If the user is young, with a long horizon, then they could perhaps consider assuming more risk (although explain the dangers of this)
    5. If necessary, highlight the advantages of compounding over a long period of time
    
    Please be concise and employ sound reasoning. Do not offer financial advice.
    """

    user_prompt = f"""
    User is {age} years old. 
    Their stated investment horizon is {inv_hor} years. 
    Currently their investment portfolio is {portfolio}, which is reflective of their financial situation, financial acumen and risk tolerance. 
    Their stated risk tolerance is {risk_tol}. 
    """

    client = OpenAI(api_key= OAI_KEY)
    response = client.responses.create(
        model = 'gpt-4.1-nano-2025-04-14',
        input =
        [{
            'role' : 'developer',
            'content' : system_prompt
        },
        {
            'role': 'user',
            'content': user_prompt
        }],
        temperature = 0.7,
    )
    return response.output_text