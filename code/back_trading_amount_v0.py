
# ######################################################################################################################
"""
绩效回测V0:
    根据真实持股数量计算组合及指数收益率，组合及指数买入数量一致
    个股投入固定金额，持仓不调整
"""

import os
import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()

# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/权重无调整/"
if not os.path.exists(outputPath):
    os.makedirs(outputPath)
    print(outputPath + '创建成功')

start_date = '2010-01-01'
end_date = '2019-10-31'

unit_amount = 5e5
tax_cost = 0.001
tran_cost = 0.0015
index_code = '000905.XSHG'


def getEveryDay(begin_date,end_date):
    # 前闭后闭
    date_list = []
    begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list


# 交易日列表
list_trading = get_trading_dates(start_date=start_date, end_date=end_date)
list_date = getEveryDay(start_date, end_date)

# 数据导入
df_buy_sell = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')
df_buy_sell.sort_values(by='buy_date', axis=0, ascending=True, inplace=True)
df_buy_sell = df_buy_sell.reset_index(drop=True)

# 剔除停牌及建仓日涨跌停个股
list_suspended_index = pd.DataFrame(index=df_buy_sell.index, columns=['index'])
for ind in df_buy_sell.index:
    ind_code = df_buy_sell.loc[ind, 'code']
    ind_date = df_buy_sell.loc[ind, 'buy_date']
    try:
        suspended_index = rq.is_suspended(ind_code, start_date=ind_date, end_date=ind_date)
    except:
        list_suspended_index.loc[ind, 'index'] = True
    else:
        if suspended_index is None:
            list_suspended_index.loc[ind, 'index'] = True
        else:
            list_suspended_index.loc[ind, 'index'] = suspended_index.loc[ind_date, ind_code]

list_limit_index = pd.DataFrame(index=df_buy_sell.index, columns=['index'])
for ind in df_buy_sell.index:
    ind_code = df_buy_sell.loc[ind, 'code']
    ind_date = df_buy_sell.loc[ind, 'buy_date']

    stocks_price = rq.get_price(ind_code, start_date=ind_date, end_date=ind_date, frequency='1d',
                                fields=['open', 'limit_up', 'limit_down'], adjust_type='pre',
                                skip_suspended=False, market='cn')

    if stocks_price is not None:
        if stocks_price.loc[ind_date, 'open'] == stocks_price.loc[ind_date, 'limit_up'] or \
                stocks_price.loc[ind_date, 'open'] == stocks_price.loc[ind_date, 'limit_down']:
            list_limit_index.loc[ind, 'index'] = True
        else:
            list_limit_index.loc[ind, 'index'] = False
    else:
        list_limit_index.loc[ind, 'index'] = True

list_filter_index = list_suspended_index + list_limit_index
stocks_list = list_filter_index[list_filter_index.values == False].index.tolist()
df_buy_sell = df_buy_sell.loc[stocks_list]

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
cash_port = 0
cash_index = 0
year_pre = '2009'
holding_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
amount_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
index_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
ratio_df = pd.DataFrame(index=list_date, columns=['daily_ratio', 'index_ratio', 'daily_profit', 'index_profit',
                                                  'holding_num', 'buy_num', 'sell_num', 'cash_port'])

for date_str in list_date:
    date_datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    date = datetime.date(date_datetime.year, date_datetime.month, date_datetime.day)
    year_str = date_str[:4]

    if date not in list_trading[:-1]:
        if year_str == year_pre:
            holding_daily = holding_pre.copy()
            profit_daily = 0
            profit_index = 0
        else:
            holding_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            profit_daily = 0
            profit_index = 0
    else:
        date_post = list_trading[list_trading.index(date) + 1]

        holding_df = df_buy_sell[(df_buy_sell['buy_date'] <= date_str) & (df_buy_sell['sell_date'] > date_str)]
        holding_code = holding_df['code'].tolist()
        holding_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
        holding_daily[holding_code] = 1

        # 日收益率
        rate_open_to_open = price_df.loc[date_post] / price_df.loc[date] - 1
        rate_index = price_index.loc[date_post] / price_index.loc[date] - 1
        rate_open_to_open = rate_open_to_open.fillna(0)

        # 交易信号
        series_buy = holding_daily - holding_pre
        series_buy[series_buy < 0] = 0
        series_sell = holding_daily - holding_pre
        series_sell[series_sell > 0] = 0

        # 组合当日权益
        cost_buy = series_buy * tran_cost * unit_amount
        cost_sell = -(series_sell * (tran_cost + tax_cost) * amount_pre)

        amount_pre[series_buy == 1] = unit_amount
        amount_daily = amount_pre * rate_open_to_open + amount_pre
        amount_daily = amount_daily - cost_buy - cost_sell
        amount_daily[series_sell == -1] = 0

        profit_daily = amount_pre * rate_open_to_open
        profit_daily[series_sell == -1] = 0
        profit_daily = profit_daily - cost_buy - cost_sell

        # 指数当日权益
        cost_buy_index = series_buy * tran_cost * unit_amount
        cost_sell_index = -series_sell * (tran_cost + tax_cost) * index_pre

        index_pre[series_buy == 1] = unit_amount
        index_daily = index_pre * rate_index + index_pre
        index_daily = index_daily - cost_buy_index - cost_sell_index
        index_daily[series_sell == -1] = 0

        profit_index = index_pre * rate_index
        profit_index[series_sell == -1] = 0
        profit_index = profit_index - cost_buy_index - cost_sell_index

        amount_pre = amount_daily.copy()
        index_pre = index_daily.copy()

        if any(np.isnan(amount_daily)):
            print(date)
            break

    # 资金占用
    if year_str == year_pre:
        cash_port = np.nansum(holding_daily) * unit_amount
    else:
        cash_port = 0

    # 指标计算
    ratio_df.loc[date_str, 'holding_num'] = np.nansum(holding_daily)
    ratio_df.loc[date_str, 'buy_num'] = ((holding_daily != 0) & (holding_pre == 0)).sum()
    ratio_df.loc[date_str, 'sell_num'] = ((holding_daily == 0) & (holding_pre != 0)).sum()
    ratio_df.loc[date_str, 'daily_profit'] = np.nansum(profit_daily)
    ratio_df.loc[date_str, 'index_profit'] = np.nansum(profit_index)
    ratio_df.loc[date_str, 'cash_port'] = cash_port

    holding_pre = holding_daily.copy()
    year_pre = year_str

# 收益率计算
year_index = [date_str[:4] for date_str in list_date]
ratio_df['year_index'] = year_index

unique_year_index = list(set(year_index))
unique_year_index.sort()

for year_ind in unique_year_index:
    ratio_df['daily_ratio'][ratio_df['year_index'] == year_ind] = \
        ratio_df['daily_profit'][ratio_df['year_index'] == year_ind] / \
        sum(ratio_df['cash_port'][ratio_df['year_index'] == year_ind]) * 365

    ratio_df['index_ratio'][ratio_df['year_index'] == year_ind] = \
        ratio_df['index_profit'][ratio_df['year_index'] == year_ind] / \
        sum(ratio_df['cash_port'][ratio_df['year_index'] == year_ind]) * 365

# 权益计算
equity_df = pd.DataFrame(index=list_date, columns=['daily_equity', 'index_equity', 'excess_equity',
                                                   'cum_profit', 'index_cum_profit', 'excess_profit'])

equity_df.loc[:, 'daily_equity'] = (ratio_df.loc[:, 'daily_ratio'] + 1).cumprod()
equity_df.loc[:, 'index_equity'] = (ratio_df.loc[:, 'index_ratio'] + 1).cumprod()
equity_df.loc[:, 'excess_equity'] = (ratio_df.loc[:, 'daily_ratio'] - ratio_df.loc[:, 'index_ratio'] + 1).cumprod()
equity_df.loc[:, 'cum_profit'] = ratio_df.loc[:, 'daily_profit'].cumsum()
equity_df.loc[:, 'index_cum_profit'] = ratio_df.loc[:, 'index_profit'].cumsum()
equity_df.loc[:, 'excess_profit'] = (ratio_df.loc[:, 'daily_profit'] - ratio_df.loc[:, 'index_profit']).cumsum()

# 数据导出
ratio_df.to_csv(outputPath + "策略收益率换手率.csv")
equity_df.to_csv(outputPath + "策略动态权益.csv")

# ######################################################################################################################
