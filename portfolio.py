from NewsToGod import *

ACCOUNT_ID = 11509188

class Portfolio:

    def __init__(self,trade_station,market_sentiment,sector_sentiment):
        self.trade_station = trade_station
        self.cash = get_cash(trade_station)
        self.market_sentiment = market_sentiment
        self.sector_sentiment = sector_sentiment
        self.holdings = get_holdings(trade_station)

    def buy(self,symbol,quantity,order_type='Market'):
        #order_type = "Limit" "StopMarket" "Market" "StopLimit"
        url = "https://api.tradestation.com/v3/orderexecution/orders"
        payload = {
            "AccountID": ACCOUNT_ID,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": order_type,
            "TradeAction": "BUY",
            "TimeInForce": {"Duration": "DAY"},
            "Route": "Intelligent"
        }
        headers = {
            "content-type": "application/json",
            "Authorization": f'Bearer {self.trade_station.TOKENS.access_token}'
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)



def get_cash(trade_station):
    try:
        url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
        headers = {"Authorization":f'Bearer {trade_station.TOKENS.access_token}'}
        account_details = requests.request("GET", url, headers=headers)
        account_details = json.loads(account_details.text)
        if(account_details['Balances'][0]['AccountID'] == ACCOUNT_ID):
            return account_details['Balances'][0]['CashBalance']
        else: 
            print("PROBLEM WITH FINDING YOUR TRADE STATION ACCOUNT - PROBLEM ACCURED IIN 'get_cash' function")
            return 0
    except Exception:
        print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
        return 0

def get_holdings(trade_station):
    holdings = {}
    try:
        url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/positions"
        headers = {"Authorization":f'Bearer {trade_station.TOKENS.access_token}'}
        account_details = requests.request("GET", url, headers=headers)
        account_details = json.loads(account_details.text)
        for position in account_details['Positions']:
            if(position['AccountID'] != ACCOUNT_ID):
                continue
            position_id = position["PositionID"]
            quantity = position["Quantity"]
            long_short = position["LongShort"]
            average_price = position["AveragePrice"]
            trade_yield = position["UnrealizedProfitLossPercent"]
            total_cost = position["TotalCost"]
            market_value = position["MarketValue"]
            holdings[position["Symbol"]] = {"PositionID":position_id,"Quantity":quantity,"LongShort":long_short,
                "AveragePrice":average_price,"UnrealizedProfitLossPercent":trade_yield,"TotalCost":total_cost,"MarketValue":market_value}
        return holdings
    except Exception:
        print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
        return holdings