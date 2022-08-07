from importlib.metadata import entry_points
from msilib import sequence
from backtestingbase import *
from sequencing import SequenceMethod
import talib as ta

class BacktestLongOnly(BacktestBase):

    def run_seq_strategy(self, SMA1, SMA2):
        ''' Backtesting a SMA-based strategy.

        Parameters
        ==========
        SMA1, SMA2: int
            shorter and longer term simple moving average (in days)
        '''
        msg = f'\n\nRunning SEQ strategy | SMA1={SMA1} & SMA2={SMA2}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        avg_weekly_trend = self.sequence.get_avg_up_return('week')
        self.position = 0  # initial neutral position
        self.trades = 0  # no trades yet
        self.amount = self.initial_amount  # reset initial capital
        self.symbol_data_1d[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1d['Close'],timeperiod=13)
        self.symbol_data_1d[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1d[f'SMA {SMA1}'], timeperiod=5)
        self.symbol_data_1wk[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1wk['Close'],timeperiod=13)
        self.symbol_data_1wk[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1wk[f'SMA {SMA1}'], timeperiod=5)
        self.symbol_data_1mo[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1mo['Close'],timeperiod=13)
        self.symbol_data_1mo[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1mo[f'SMA {SMA1}'], timeperiod=5)
        self.symbol_data_1d = self.symbol_data_1d.dropna()
        trade_yield = 0
        for bar in range(SMA2, len(self.symbol_data_1d)):
            last_close = self.symbol_data_1d.Close.iloc[bar]
            seq_month = check_seq_by_date_monthly(self, self.symbol_data_1d.index[bar])
            index_week,seq_week = check_seq_by_date_weekly(self, self.symbol_data_1d.index[bar])
            index_day, seq_day = check_seq_by_date_daily(self, self.symbol_data_1d.index[bar])
            if self.position == 0:
                if(seq_month == 1 and seq_week == 1 and seq_day == 1): 
                    self.place_buy_order(bar, amount=self.amount)
                    self.position = 1  # long position
                    self.stoploss = self.sequence.sequence_1wk.loc[index_week,'Entry Price']
                    self.entry_price = last_close
            elif self.position == 1:
                trade_yield = (last_close - self.entry_price)/self.entry_price*100
                if seq_month == -1 or (seq_day == -1 and seq_week == -1)  or trade_yield > 16:
                    self.place_sell_order(bar, units=self.units)
                    self.position = 0  # market neutral
        self.close_out(bar)


    def run_momentum_strategy(self, momentum):
        ''' Backtesting a momentum-based strategy.

        Parameters
        ==========
        momentum: int
            number of days for mean return calculation
        '''
        msg = f'\n\nRunning momentum strategy | {momentum} days'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        self.position = 0  # initial neutral position
        self.trades = 0  # no trades yet
        self.amount = self.initial_amount  # reset initial capital
        self.data['momentum'] = self.data['return'].rolling(momentum).mean()
        for bar in range(momentum, len(self.data)):
            if self.position == 0:
                if self.data['momentum'].iloc[bar] > 0:
                    self.place_buy_order(bar, amount=self.amount)
                    self.position = 1  # long position
            elif self.position == 1:
                if self.data['momentum'].iloc[bar] < 0:
                    self.place_sell_order(bar, units=self.units)
                    self.position = 0  # market neutral
        self.close_out(bar)

    def run_mean_reversion_strategy(self, SMA, threshold):
        ''' Backtesting a mean reversion-based strategy.

        Parameters
        ==========
        SMA: int
            simple moving average in days
        threshold: float
            absolute value for deviation-based signal relative to SMA
        '''
        msg = f'\n\nRunning mean reversion strategy | '
        msg += f'SMA={SMA} & thr={threshold}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        self.position = 0
        self.trades = 0
        self.amount = self.initial_amount

        self.data['SMA'] = self.data['price'].rolling(SMA).mean()

        for bar in range(SMA, len(self.data)):
            if self.position == 0:
                if (self.data['price'].iloc[bar] <
                        self.data['SMA'].iloc[bar] - threshold):
                    self.place_buy_order(bar, amount=self.amount)
                    self.position = 1
            elif self.position == 1:
                if self.data['price'].iloc[bar] >= self.data['SMA'].iloc[bar]:
                    self.place_sell_order(bar, units=self.units)
                    self.position = 0
        self.close_out(bar)


def check_seq_by_date_monthly(self,date):
        previous_row = 0
        for index,row in self.sequence.sequence_1mo.iterrows():
            if(row["Date"] < date ):
                previous_row = row
            else: break
        return previous_row['Sequence']

def check_seq_by_date_weekly(self,date):
        previous_row = 0
        for index,row in self.sequence.sequence_1wk.iterrows():
            if(row["Date"] < date ):
                previous_row = row
            else: break
        return index, previous_row['Sequence']

def check_seq_by_date_daily(self,date):
        previous_row = 0
        for index,row in self.sequence.sequence_1d.iterrows():
            if(row["Date"] < date ):
                previous_row = row
            else: break
        return index, previous_row['Sequence']

        

if __name__ == '__main__':
    def run_strategies():
        lobt.run_seq_strategy(13, 5)
        # lobt.run_momentum_strategy(60)
        # lobt.run_mean_reversion_strategy(50, 5)

    lobt = BacktestLongOnly('QQQ', '2000-1-1', '2022-08-01',1000000, 2, 0.01,
                            verbose=True)
    run_strategies()
    # # transaction costs: 10 USD fix, 1% variable
    # lobt = BacktestLongOnly('AAPL.O', '2010-1-1', '2019-12-31',
    #                         10000, 10.0, 0.01, False)
    # run_strategies()
