from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
import yfinance
import matplotlib.pyplot as plt

class Database:
    def __init__(self, uri):
        self.uri = uri
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client.get_database("Database1")
        self.collection = self.db["MyCollection"]

    def send_to_mongo(self, data):
        timestamp = datetime.now()
        upload = {"dateRecorded": timestamp, "price": data}
        self.collection.insert_one(upload)

    def collect_data(self):
        x_many_days_ago = datetime.now() - timedelta(days=50)
        results = self.collection.find({"dateRecorded": {"$gte": x_many_days_ago}}).sort("dateRecorded", -1)
        prices = [{"price": item['price'], "dateRecorded": item['dateRecorded']} for item in results]
        return prices




class Strategy():

    def twenty_four_hour_rolling_average(self, price_list):
        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        recent_prices = [price["price"] for price in price_list if price['dateRecorded'] >= twenty_four_hours_ago]
        if len(recent_prices) > 0:
            return price_list[0]["price"] > (sum(item['price'] for item in price_list) / len(price_list))

    def nineteen_day_rolling_average(self, price_list):
        now = datetime.now()
        nineteen_days_ago = now - timedelta(days=19)
        recent_prices = [price["Price"] for price in price_list if price["dateRecorded"] >= nineteen_days_ago]
        if len(recent_prices) > 0:
            return price_list[0] > (sum(item['price'] for item in price_list) / len(price_list))

    def rolling_average_selling(self, current_price, bought_price):
        return (current_price / bought_price) > 1.05 or (current_price / bought_price) < .95




class Trading:
    def __init__(self, buying_strategy, selling_strategy):
        self.buying_strategy = buying_strategy
        self.selling_strategy = selling_strategy
        self.db_util = Database("mongodb+srv://ethanjerelowe:Thenims123@cluster0.4t4pyyk.mongodb.net/Database1")
        self.holdings = []

    def process_trades(self, total_funds):
        the_list = self.db_util.collect_data()
        price = the_list[0]["price"]

        for item in self.holdings:
            if item["Profit"] == 0 and self.selling_strategy(price, item["Buy Price"]):
                item["Sell Price"] = price["price"]
                item["Profit"] = item["Sell Price"] - item["Buy Price"]
                total_funds += item["Profit"]
                print("sale!")
        if self.buying_strategy(the_list) and total_funds >= price:
            self.holdings.append({"Buy Price": price, "Sell Price": None, "Profit": 0})
            total_funds -= price
        return total_funds


    def main_loop(self):
        total_funds = 100000
        while True:
            price = yfinance.Ticker("AAPL").info['currentPrice']
            if price:
                print(price)
                self.db_util.send_to_mongo(price)
                total_funds = self.process_trades(total_funds)
                net_profit = sum(item["Profit"] for item in self.holdings)
                print(f"You have a total net profit of: {net_profit}")



class BackTesting:
    def __init__(self, buying_strategy, selling_strategy):
        self.buying_strategy = buying_strategy
        self.selling_strategy = selling_strategy
        self.db_util = Database("mongodb+srv://ethanjerelowe:Thenims123@cluster0.4t4pyyk.mongodb.net/Database1"
)
        self.holdings = []
        self.trades = []

    def simulate_trading(self, total_funds, price, index):
        the_list = self.db_util.collect_data()

        for item in self.holdings:
            if item["Profit"] == 0 and self.selling_strategy(price, item["Buy Price"]):
                item["Sell Price"] = price["price"]
                item["Profit"] = item["Sell Price"] - item["Buy Price"]
                self.trades.append({"Profit": item["Profit"], "SequenceNum": index})
                total_funds += item["Profit"]

        if self.buying_strategy(the_list) and total_funds >= the_list[0]["price"]:
            self.holdings.append({"Buy Price" : price, "Sell Price": None, "Profit": 0})
            total_funds -= the_list[0]["price"]

    def unload_simulated_buys(self, total_funds):
        for item in self.holdings:
            if item["Profit"] == 0:
                item["Sell Price"] = self.db_util.collect_data()[0]['price']
                item["Profit"] = item["Sell Price"] - item["Buy Price"]
                self.trades.append({"Profit": item["Profit"], "SequenceNum": self.db_util.collect_data()[-1]})
                total_funds += item["Profit"]

    def main_backtest_loop(self):
        total_funds = 100000
        price_list = self.db_util.collect_data()

        for index, item in enumerate(price_list):
            print("WE SIMULATING")
            self.simulate_trading(total_funds, item["price"], index)
        self.unload_simulated_buys(total_funds)
        print(f"You have a total profit of: {total_funds-100000}")
        return total_funds

    def create_backtest_chart(self):
        x = []
        y = []
        net_profit = 0
        for item in self.trades:
            index = item["SequenceNum"]
            profit = item["Profit"]
            net_profit += profit
            x.append(index)
            y.append(net_profit)
        fig, ax = plt.subplots()
        x.reverse()
        ax.plot(x, y)
        plt.show()


#the folowing 2 classes are their own thing, no Mongo interface

class FiveYearStrategy():

    def five_year_backtest_buying_strat(self, price_list, index):
        if index < 19:
            pass
        else:
            rolling_nineteen_mean = (sum(price_list[(index - 19): index]) / 19)
            return price_list[index] > rolling_nineteen_mean

    def five_year_backtest_selling_strat(self, current_price, bought_price):
        return (current_price / bought_price) > 1.05 or (current_price / bought_price) < .95



class FiveYearBacktesting():
    def __init__(self, buying_strategy, selling_strategy):
        self.buying_strategy = buying_strategy
        self.selling_strategy = selling_strategy
        self.holdings = []
    def get_five_years_data(self):
        data = yfinance.Ticker("AAPL").history(period='5y')
        open_prices = [price for price in data["Open"]]
        return open_prices

    def run_five_year_backtest(self):
        total_funds = 100000
        portfolio_values = []
        five_years_of_prices = self.get_five_years_data()

        for index, current_price in enumerate(five_years_of_prices):
            for holding in self.holdings:
                if holding["Sell Price"] is None and self.selling_strategy(current_price, holding["Buy Price"]):
                    holding["Sell Price"] = current_price
                    holding["Profit"] = current_price - holding["Buy Price"]
                    total_funds += current_price

            if self.buying_strategy(five_years_of_prices, index) and total_funds >= current_price:
                self.holdings.append({"Buy Price": current_price, "Sell Price": None, "Profit": 0})
                total_funds -= current_price

            current_holdings_value = sum([h["Buy Price"] for h in self.holdings if h["Sell Price"] is None])
            portfolio_values.append(total_funds + current_holdings_value)

        return portfolio_values

    def run_five_year_index_backtest(self):
        total_funds = 100000
        shares = 0
        portfolio_values = []  # To track portfolio value over time
        five_years_of_prices = self.get_five_years_data()

        for price in five_years_of_prices:
            if total_funds >= price:
                shares += 1
                total_funds -= price

            portfolio_values.append(total_funds + (shares * price))

        return portfolio_values

    def graph_active_strategy_backtest(self):
        portfolio_values = self.run_five_year_backtest()

        plt.figure(figsize=(10, 6))
        plt.plot(portfolio_values, label='Total Portfolio Value')
        plt.title('Active Strategy Portfolio Value Over Time')
        plt.xlabel('Time Steps')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.show()

    def graph_index_strategy_backtest(self):
        portfolio_values = self.run_five_year_index_backtest()

        plt.figure(figsize=(10, 6))
        plt.plot(portfolio_values, label='Total Portfolio Value')
        plt.title('Index Strategy Portfolio Value Over Time')
        plt.xlabel('Time Steps')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.show()

    def create_combined_backtest_chart(self):
        active_portfolio_values = self.run_five_year_backtest()
        index_portfolio_values = self.run_five_year_index_backtest()

        time_steps = list(range(len(active_portfolio_values)))

        plt.figure(figsize=(12, 8))
        plt.plot(time_steps, active_portfolio_values, label='Active Strategy Portfolio Value', marker='o',
                 linestyle='-', markersize=4)
        plt.plot(time_steps, index_portfolio_values, label='Index Strategy Portfolio Value', marker='x', linestyle='--',
                 markersize=4)

        plt.title('Comparison of Active and Index Strategy Portfolio Values Over Time')
        plt.xlabel('Time Steps')
        plt.ylabel('Portfolio Value ($)')
        plt.legend(loc='upper left')
        plt.grid(True)

        plt.show()


#db_uri = "mongodb+srv://ethanjerelowe:Thenims123@cluster0.4t4pyyk.mongodb.net/Database1"
#strategy = Strategy()
#database = Database(db_uri)
#backtesting = BackTesting(strategy.twenty_four_hour_rolling_average, strategy.rolling_average_selling)
#trading = Trading(strategy.twenty_four_hour_rolling_average, strategy.rolling_average_selling)

five_year_strategy = FiveYearStrategy()
five_year_backtesting = FiveYearBacktesting(five_year_strategy.five_year_backtest_buying_strat, five_year_strategy.five_year_backtest_selling_strat)
var = five_year_backtesting.run_five_year_backtest()
print(var)

var2 = five_year_backtesting.run_five_year_index_backtest()
print(var2)

five_year_backtesting.graph_active_strategy_backtest()
five_year_backtesting.graph_index_strategy_backtest()
five_year_backtesting.create_combined_backtest_chart()


