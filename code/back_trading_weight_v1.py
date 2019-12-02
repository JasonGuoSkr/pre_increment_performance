
# ######################################################################################################################
"""
绩效回测V1:
    根据真实持股数量计算组合及指数收益率，组合及指数买入权重一致，持股组合无变化时不调仓
    个股持仓上限为5%，每日调仓，使股票间等权重
"""

import os
import math
import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/权重调整/"
if not os.path.exists(outputPath):
    os.makedirs(outputPath)
    print(outputPath + '创建成功')

start_date = '2010-01-01'
end_date = '2019-10-31'

weight_bound = 0.1
tax_cost = 0.001
tran_cost = 0.0015
initial_amount = 1e8
index_code = '000905.XSHG'
index_multiplier = 200


# 数据导入
df_buy_sell = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')
df_buy_sell.sort_values(by='buy_date', axis=0, ascending=True, inplace=True)
df_buy_sell = df_buy_sell.reset_index(drop=True)


def get_calendar(begin_date, off_date):
    # 获取日历日序列，前闭后闭
    date_list = []
    begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
    off_date = datetime.datetime.strptime(off_date, "%Y-%m-%d")
    while begin_date <= off_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list


# 剔除停牌及建仓日涨跌停个股
list_suspended_index = pd.DataFrame(index=df_buy_sell.index, columns=['index'])
list_limit_index = pd.DataFrame(index=df_buy_sell.index, columns=['index'])

stocks_price = rq.get_price(df_buy_sell['code'].unique(), start_date=df_buy_sell.iloc[0, 1],
                            end_date=df_buy_sell.iloc[-1, 1], frequency='1d',
                            fields=['open', 'limit_up', 'limit_down', 'volume'], adjust_type='pre',
                            skip_suspended=False, market='cn')

stocks_open = stocks_price.open
stocks_up = stocks_price.limit_up
stocks_down = stocks_price.limit_down
stocks_volume = stocks_price.volume

for ind in df_buy_sell.index:
    ind_code = df_buy_sell.loc[ind, 'code']
    ind_date = df_buy_sell.loc[ind, 'buy_date']

    if stocks_open.loc[ind_date, ind_code] is not np.nan:
        if stocks_open.loc[ind_date, ind_code] == stocks_up.loc[ind_date, ind_code] or \
                stocks_open.loc[ind_date, ind_code] == stocks_down.loc[ind_date, ind_code]:
            list_limit_index.loc[ind, 'index'] = True
        else:
            list_limit_index.loc[ind, 'index'] = False
        if stocks_volume.loc[ind_date, ind_code] == 0:
            list_suspended_index.loc[ind, 'index'] = True
        else:
            list_suspended_index.loc[ind, 'index'] = False
    else:
        list_limit_index.loc[ind, 'index'] = True
        list_suspended_index.loc[ind, 'index'] = True

list_filter_index = list_suspended_index | list_limit_index
stocks_list = list_filter_index[list_filter_index.values == False].index.tolist()
df_buy_sell = df_buy_sell.loc[stocks_list]


# 交易日列表
list_calendar = get_calendar(start_date, end_date)
list_trading = rq.get_trading_dates(start_date=start_date, end_date=end_date)

# 股票列表
list_code = df_buy_sell['code'].unique()
list_code.sort()

# 取行情数据
price_df = rq.get_price(list_code, start_date=start_date, end_date=end_date, frequency='1d',
                        fields=['open', 'close'], adjust_type='pre', skip_suspended=False, market='cn')
df_open = price_df.open.loc[:, list_code]
df_close = price_df.close.loc[:, list_code]
price_index = rq.get_price(index_code, start_date=start_date, end_date=end_date, frequency='1d',
                           fields=['open', 'close'], adjust_type='pre', skip_suspended=False, market='cn')


# 日收益计算
holding_pre = []
equity_pre = 0
index_equity_pre = 0
volume_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
index_volume_pre = 0

ratio_df = pd.DataFrame(index=list_calendar[1:-1], columns=['daily_profit', 'index_profit', 'capital_use',
                                                            'holding_num', 'buy_num', 'sell_num', 'index_num'])

for date in list_calendar[1:-1]:
    # date = list_calendar[189]
    date_pre = list_calendar[list_calendar.index(date) - 1]
    date_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if date_date in list_trading:
        date_date_pre = list_trading[list_trading.index(date_date) - 1]
        date_date_post = list_trading[list_trading.index(date_date) + 1]

        holding_code = df_buy_sell[(df_buy_sell['buy_date'] <= date) &
                                   (df_buy_sell['sell_date'] > date)]['code'].tolist()
        code_buy = df_buy_sell[df_buy_sell['buy_date'] == date]['code'].tolist()
        code_sell = df_buy_sell[df_buy_sell['sell_date'] == date]['code'].tolist()

        if len(holding_code) and len(holding_pre):
            if holding_code == holding_pre:
                volume_daily = volume_pre
                index_volume_daily = index_volume_pre
            else:
                weight_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)

                if len(holding_code) > (1 / weight_bound):
                    weight_daily.loc[holding_code] = 1 / len(holding_code)
                elif len(holding_code) > 0:
                    weight_daily.loc[holding_code] = weight_bound

                volume_daily = np.tile(equity_pre, (len(list_code))) * weight_daily / df_close.loc[date_date_pre]
                volume_daily.fillna(0, inplace=True)
                volume_daily = np.floor(volume_daily / 100) * 100

                index_volume_daily = index_equity_pre * np.sum(weight_daily) / price_index.loc[date_date_pre, 'close']
                index_volume_daily = np.floor(index_volume_daily / index_multiplier)

            # 股票组合计算
            volume_diff = volume_daily - volume_pre

            volume_buy = volume_diff.copy()
            volume_buy[volume_buy < 0] = 0
            cost_buy = np.nansum(volume_buy * df_open.loc[date_date] * tran_cost)

            volume_sell = volume_diff.copy()
            volume_sell[volume_sell > 0] = 0
            cost_sell = - np.nansum(volume_sell * df_open.loc[date_date] * (tran_cost + tax_cost))

            daily_profit = np.nansum(volume_daily * (df_open.loc[date_date_post] - df_open.loc[date_date])) - \
                cost_buy - cost_sell
            daily_use = initial_amount
            equity_pre = equity_pre + daily_profit

            # 指数计算
            index_volume_diff = index_volume_daily - index_volume_pre

            index_cost = abs(index_volume_diff) * index_multiplier * price_index.loc[date_date, 'open'] * tran_cost
            index_daily_profit = index_volume_daily * \
                index_multiplier * (price_index.loc[date_date_post, 'open'] - price_index.loc[date_date, 'open']) - \
                index_cost
            index_equity_pre = index_equity_pre + index_daily_profit

        elif len(holding_code) and not len(holding_pre):
            # 股票组合计算
            equity_pre = initial_amount

            weight_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            if len(holding_code) > (1 / weight_bound):
                weight_daily.loc[holding_code] = 1 / len(holding_code)
            elif len(holding_code) > 0:
                weight_daily.loc[holding_code] = weight_bound

            volume_daily = np.tile(equity_pre, (len(list_code))) * weight_daily / df_close.loc[date_date_pre]
            volume_daily.fillna(0, inplace=True)
            volume_daily = np.floor(volume_daily / 100) * 100
            volume_diff = volume_daily - volume_pre

            volume_buy = volume_diff.copy()
            volume_buy[volume_buy < 0] = 0
            cost_buy = np.nansum(volume_buy * df_open.loc[date_date] * tran_cost)

            daily_profit = np.nansum(volume_daily * (df_open.loc[date_date_post] - df_open.loc[date_date])) - cost_buy
            daily_use = initial_amount
            equity_pre = equity_pre + daily_profit

            # 指数计算
            index_equity_pre = initial_amount
            index_volume_daily = index_equity_pre * np.sum(weight_daily) / price_index.loc[date_date_pre, 'close']
            index_volume_daily = np.floor(index_volume_daily / index_multiplier)
            index_volume_diff = index_volume_daily - index_volume_pre

            index_cost = abs(index_volume_diff) * index_multiplier * price_index.loc[date_date, 'open'] * tran_cost
            index_daily_profit = index_volume_daily * \
                index_multiplier * (price_index.loc[date_date_post, 'open'] - price_index.loc[date_date, 'open']) - \
                index_cost
            index_equity_pre = index_equity_pre + index_daily_profit

        elif len(holding_pre) and not len(holding_code):
            # 股票组合计算
            volume_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            volume_diff = volume_daily - volume_pre

            volume_sell = volume_diff.copy()
            volume_sell[volume_sell > 0] = 0
            cost_sell = - np.nansum(volume_sell * df_open.loc[date_date] * (tran_cost + tax_cost))

            daily_profit = np.nansum(volume_daily * (df_open.loc[date_date_post] - df_open.loc[date_date])) - cost_sell
            daily_use = initial_amount
            equity_pre = 0

            # 指数计算
            index_volume_daily = 0
            index_volume_diff = index_volume_daily - index_volume_pre

            index_cost = abs(index_volume_diff) * index_multiplier * price_index.loc[date_date, 'open'] * tran_cost
            index_daily_profit = index_volume_daily * \
                index_multiplier * (price_index.loc[date_date_post, 'open'] - price_index.loc[date_date, 'open']) - \
                index_cost
            index_equity_pre = 0

        else:
            # 股票组合计算
            volume_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            volume_diff = volume_daily - volume_pre

            daily_profit = 0
            daily_use = 0
            equity_pre = 0

            # 指数计算
            index_volume_daily = 0
            index_volume_diff = index_volume_daily - index_volume_pre

            index_daily_profit = 0
            index_equity_pre = 0

    else:
        # 股票组合计算
        holding_code = holding_pre.copy()
        volume_daily = volume_pre.copy()
        volume_diff = volume_daily - volume_pre

        daily_profit = 0
        if holding_code:
            daily_use = initial_amount
        else:
            daily_use = 0

        # 指数计算
        index_volume_daily = index_volume_pre
        index_daily_profit = 0

    holding_pre = holding_code.copy()
    volume_pre = volume_daily.copy()
    index_volume_pre = index_volume_daily

    # 指标计算
    ratio_df.loc[date, 'daily_profit'] = daily_profit
    ratio_df.loc[date, 'index_profit'] = index_daily_profit
    ratio_df.loc[date, 'capital_use'] = daily_use
    ratio_df.loc[date, 'holding_num'] = (volume_daily != 0).sum()
    ratio_df.loc[date, 'buy_num'] = (volume_diff > 0).sum()
    ratio_df.loc[date, 'sell_num'] = (volume_diff < 0).sum()
    ratio_df.loc[date, 'index_num'] = index_volume_daily


# 权益计算
equity_df = pd.DataFrame(index=list_calendar[1:-1], columns=['daily_equity', 'index_equity',
                                                             'cum_profit', 'index_cum_profit', 'excess_profit'])

equity_df.loc[:, 'cum_profit'] = ratio_df.loc[:, 'daily_profit'].cumsum()
equity_df.loc[:, 'index_cum_profit'] = ratio_df.loc[:, 'index_profit'].cumsum()
equity_df.loc[:, 'excess_profit'] = (ratio_df.loc[:, 'daily_profit'] - ratio_df.loc[:, 'index_profit']).cumsum()
equity_df.loc[:, 'daily_equity'] = equity_df.loc[:, 'cum_profit'] / initial_amount + 1
equity_df.loc[:, 'index_equity'] = equity_df.loc[:, 'index_cum_profit'] / initial_amount + 1


# 数据导出
ratio_df.to_csv(outputPath + "策略收益率换手率.csv")
equity_df.to_csv(outputPath + "策略动态权益.csv")

# ######################################################################################################################
