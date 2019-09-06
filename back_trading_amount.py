
# ######################################################################################################################
"""
绩效回测，每只股票给定固定初始资金
"""

import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果_优化/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果_优化/"


# 数据导入
df_buy_sell = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')
df_buy_sell.sort_values(by='buy_date', axis=0, ascending=True, inplace=True)

# 参数
start_date = '2010-01-01'
end_date = '2019-06-30'

unit_amount = 5e6
tax_cost = 0.001
tran_cost = 0.002
index_code = '000905.XSHG'

# 交易日列表
list_trading = get_trading_dates(start_date=start_date, end_date=end_date)

# 股票列表
list_code = df_buy_sell['code'].unique()
list_code.sort()

# 取行情数据
price_df = get_price(list_code, start_date=start_date, end_date=end_date, frequency='1d',
                     fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')
price_df = price_df.loc[:, list_code]
price_index = get_price(index_code, start_date=start_date, end_date=end_date, frequency='1d',
                        fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')

# 收益率计算
holding_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
amount_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
ratio_df = pd.DataFrame(index=list_trading[1:-1], columns=['daily_ratio', 'index_ratio', 'current_occupation',
                                                           'holding_num', 'buy_num', 'sell_num'])
for date in list_trading[1:-1]:
    date_str = date.strftime("%Y-%m-%d")
    date_pre = list_trading[list_trading.index(date) - 1]
    date_post = list_trading[list_trading.index(date) + 1]

    holding_df = df_buy_sell[(df_buy_sell['buy_date'] <= date_str) & (df_buy_sell['sell_date'] > date_str)]
    holding_code = holding_df['code'].tolist()
    holding_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
    holding_daily[holding_code] = 1

    # 日收益率
    rate_open_to_open = price_df.loc[date_post] / price_df.loc[date] - 1
    rate_index = price_index.loc[date_post] / price_index.loc[date] - 1

    # 交易信号
    series_buy = holding_daily - holding_pre
    series_buy[series_buy < 0] = 0
    series_sell = holding_daily - holding_pre
    series_sell[series_sell > 0] = 0

    # 权益计算
    amount_daily = amount_pre * rate_open_to_open + amount_pre
    amount_daily[series_buy == 1] = unit_amount * rate_open_to_open[series_buy == 1] + unit_amount
    amount_daily[series_sell == 1] = 0

    profit_daily = amount_pre * rate_open_to_open
    profit_daily[series_buy == 1] = unit_amount * rate_open_to_open[series_buy == 1]
    profit_daily[series_sell == 1] = 0

    #交易成本
    cost_buy = np.nansum(series_buy * tran_cost * unit_amount)
    cost_sell = -np.nansum(series_sell * (tran_cost + tax_cost) * amount_pre)

    profit_all = np.nansum(profit_daily) - cost_buy - cost_sell

    # 指标计算
    ratio_df.loc[date, 'current_occupation'] = unit_amount * (holding_daily != 0).sum()
    ratio_df.loc[date, 'holding_num'] = (holding_daily != 0).sum()
    ratio_df.loc[date, 'buy_num'] = ((holding_daily != 0) & (holding_pre == 0)).sum()
    ratio_df.loc[date, 'sell_num'] = ((holding_daily == 0) & (holding_pre != 0)).sum()

    if len(holding_code):
        ratio_df.loc[date, 'daily_ratio'] = profit_all / ratio_df.loc[date, 'current_occupation']
        # ratio_df.loc[date, 'index_ratio'] = rate_index * weight_daily.sum()
    else:
        ratio_df.loc[date, 'daily_ratio'] = 0
        ratio_df.loc[date, 'index_ratio'] = 0

    holding_pre = holding_daily.copy()
    amount_pre = amount_daily.copy()

# 权益计算
equity_df = pd.DataFrame(index=list_trading[1:-1], columns=['daily_equity', 'index_equity', 'excess_equity'])

equity_df.loc[:, 'daily_equity'] = (ratio_df.loc[:, 'daily_ratio'] + 1).cumprod()
equity_df.loc[:, 'index_equity'] = (ratio_df.loc[:, 'index_ratio'] + 1).cumprod()
equity_df.loc[:, 'excess_equity'] = (ratio_df.loc[:, 'daily_ratio'] - ratio_df.loc[:, 'index_ratio'] + 1).cumprod()

# 数据导出
ratio_df.to_csv(outputPath + "策略收益率换手率.csv")
equity_df.to_csv(outputPath + "策略动态权益.csv")

# ######################################################################################################################
