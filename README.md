## Project Description
retail.risk is an application that allows retail investors and normal people to punch in a few numbers and calculate classic portfolio analysis metrics used by asset managers etc, to do with their own portfolios. Displaying these metrics is MVP1, but ultimately the goal is to suggest areas in which they can take on more risk/ reduce their risk based on tolerance and age profiles.

# Link to project
https://retailrisk.streamlit.app/


## CSV Restrictions
The CSV file has the following restrictions (to ensure data is pulled/ script executes smoothly): 
	- The CSV should follow the format of the table below
 	- Only the asset types below are accepted
  	- Bonds/ savings accounts must include an interest rate in decimals
 	- API data cannot be pulled for funds/ indexes
  	- Tickers for Crypto should be pulled from https://www.coingecko.com/. Look for API ID.
   	- Incorrect tickers result in no data being pulled

type		amount	ticker		rate
equity		2800	NVDA	
equity		700		PLTR	
cash		200		
savings		2200				0.06
bond		1000				0.03
crypto		2000	bitcoin		
<img width="257" height="141" alt="image" src="https://github.com/user-attachments/assets/6c0bad1f-0ca4-44f7-b1b3-884dc8a53fbd" />


## App Features
MVP1
Include ability to add in amounts invested into various vehicles. These should include:
	Cash
	Savings accounts (and associated rate)
	Bonds (and associated rate)
	Equity portfolios (including individual stocks)
	Crypto portfolios
	~Commodities
	~LISA accounts
Once entered, a total portfolio dashboard should be available, detailing the amounts involved in each and showing a percentage view of the portfolio
There should be visualisations showing the performance of the asset class over the previous year. For MVP 1, this will be rudimentary and only show performance of particular assets in general (time weighted return), rather than money weighted return
	~Maybe showing projected performance
SHow risk metrics alongside performance metrics
Performance metrics should include:
	Return
	Annualised Return
	Excess return over S&P 500
Risk metrics
	Volatility
	Beta


MVP 2
Show a view of, at the current YoY RoR, future expected performance
	Below this, show what this performance (and risk) would be, if weightings in the asset class were shifted around
