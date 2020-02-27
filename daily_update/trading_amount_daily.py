
# ######################################################################################################################
"""
"""

import os
import math
import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init("ricequant", "8ricequant8", ('10.29.135.119', 16010))


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_10/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_10/"

start_date = "2020-01-01"
# end_date = datetime.datetime.now().strftime('%Y-%m-%d')
end_date = rq.get_previous_trading_date(datetime.datetime.now(), 1).strftime('%Y-%m-%d')

hold_length = 10
tax_cost = 0.001
tran_cost = 0.002
unit_amount = 1e6
index_code = '000905.XSHG'
index_multiplier = 200


# 数据导入
df_buy_sell = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')
df_buy_sell.drop_duplicates(inplace=True)
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


# 交易日列表
list_calendar = get_calendar(start_date, end_date)
list_trading = rq.get_trading_dates(start_date=start_date, end_date=end_date)

# 股票列表
list_code = df_buy_sell['code'].unique()
list_code.sort()

# 取行情数据
price_df = rq.get_price(list_code, start_date=start_date, end_date=end_date, frequency='1d',
                        fields=['open', 'close'], adjust_type='pre', skip_suspended=False, market='cn')
df_close = price_df.close.loc[:, list_code]
price_index = rq.get_price(index_code, start_date=start_date, end_date=end_date, frequency='1d',
                           fields=['open', 'close'], adjust_type='pre', skip_suspended=False, market='cn')


# 日收益计算
holding_pre = []
equity_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
volume_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)
index_volume_pre = 0

ratio_df = pd.DataFrame(index=list_calendar, columns=['daily_profit', 'capital_use', 'daily_ratio', 'holding_num',
                                                      'buy_num', 'sell_num', 'index_num'])

for date in list_calendar:
    # date = list_calendar[36]
    date_pre = list_calendar[list_calendar.index(date) - 1]
    date_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if date_date in list_trading:
        date_date_pre = list_trading[list_trading.index(date_date) - 1]

        holding_code = df_buy_sell[(df_buy_sell['buy_date'] <= date) &
                                   (df_buy_sell['sell_date'] > date)]['code'].tolist()

        code_buy = df_buy_sell[df_buy_sell['buy_date'] == date]['code'].tolist()
        code_sell = df_buy_sell[df_buy_sell['sell_date'] == date]['code'].tolist()

        if len(code_buy):
            # 剔除ST、停牌及涨跌停股票
            list_st_index = is_st_stock(code_buy, date_date_pre, date_date_pre).T

            list_suspended_index = pd.DataFrame(index=code_buy)
            for codes in code_buy:
                try:
                    suspended_index = is_suspended(codes, start_date=date_date_pre, end_date=date_date_pre)
                except ValueError:
                    list_suspended_index.loc[codes, date_date_pre] = True
                else:
                    if suspended_index is not None:
                        list_suspended_index.loc[codes, date_date_pre] = suspended_index.loc[date_date_pre, codes]
                    else:
                        list_suspended_index.loc[codes, date_date_pre] = True

            list_price = get_price(code_buy, start_date=date_date_pre, end_date=date_date_pre, frequency='1d',
                                   fields=['open', 'limit_up', 'limit_down'])
            list_open = list_price['open'].T
            list_up = list_price['limit_up'].T
            list_down = list_price['limit_down'].T

            list_maxupordown_index = (list_open == list_up) | (list_open == list_down)
            list_maxupordown_index.columns = list_suspended_index.columns

            list_st_index.columns = list_suspended_index.columns
            list_final_index = list_st_index + list_suspended_index + list_maxupordown_index
            code_buy = list_final_index[list_final_index.values == False].index.tolist()

        if len(holding_code) and len(holding_pre):
            if not code_buy:
                volume_daily = volume_pre
                volume_daily.loc[code_sell] = 0
            else:
                equity_pre.loc[code_buy] = unit_amount
                equity_pre.loc[code_sell] = 0

                volume_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
                volume_daily.loc[holding_code] = volume_pre.loc[holding_code]
                volume_daily.loc[code_buy] = unit_amount / df_close.loc[date_date_pre, code_buy]
                volume_daily.fillna(0, inplace=True)
                volume_daily = np.floor(volume_daily / 100) * 100

            index_volume_daily = np.nansum(volume_daily * df_close.loc[date_date_pre]) / \
                price_index.loc[date_date_pre, 'close']
            index_volume_daily = np.floor(index_volume_daily / index_multiplier)

            # 股票组合计算
            volume_diff = volume_daily - volume_pre

            volume_buy = volume_diff.copy()
            volume_buy[volume_buy < 0] = 0
            cost_buy = np.nansum(volume_buy * df_close.loc[date_date_pre] * tran_cost)

            volume_sell = volume_diff.copy()
            volume_sell[volume_sell > 0] = 0
            cost_sell = - np.nansum(volume_sell * df_close.loc[date_date_pre] * (tran_cost + tax_cost))

            daily_profit = np.nansum(volume_daily * (df_close.loc[date_date] - df_close.loc[date_date_pre])) - \
                cost_buy - cost_sell
            daily_use = (len(holding_code) + len(code_sell)) * unit_amount
            daily_ratio = daily_profit / np.nansum(equity_pre)
            equity_pre = equity_pre + volume_daily * (df_close.loc[date_date] - df_close.loc[date_date_pre]) - \
                volume_buy * df_close.loc[date_date_pre] * tran_cost

        elif len(holding_code) and not len(holding_pre):
            # 股票组合计算
            equity_pre.loc[code_buy] = unit_amount

            volume_daily = equity_pre / df_close.loc[date_date_pre]
            volume_daily.fillna(0, inplace=True)
            volume_daily = np.floor(volume_daily / 100) * 100
            volume_diff = volume_daily - volume_pre

            volume_buy = volume_diff.copy()
            volume_buy[volume_buy < 0] = 0
            cost_buy = np.nansum(volume_buy * df_close.loc[date_date_pre] * tran_cost)

            volume_sell = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            daily_profit = np.nansum(volume_daily * (df_close.loc[date_date] - df_close.loc[date_date_pre])) - cost_buy
            daily_ratio = daily_profit / np.nansum(equity_pre)
            daily_use = len(holding_code) * unit_amount
            equity_pre = equity_pre + volume_daily * (df_close.loc[date_date] - df_close.loc[date_date_pre]) - \
                volume_buy * df_close.loc[date_date_pre] * tran_cost

            # 指数计算
            index_volume_daily = np.nansum(volume_daily * df_close.loc[date_date_pre]) / \
                price_index.loc[date_date_pre, 'close']
            index_volume_daily = np.floor(index_volume_daily / index_multiplier)

        elif len(holding_pre) and not len(holding_code):
            # 股票组合计算
            volume_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            volume_diff = volume_daily - volume_pre

            volume_buy = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            volume_sell = volume_diff.copy()
            volume_sell[volume_sell > 0] = 0
            cost_sell = - np.nansum(volume_sell * df_close.loc[date_date_pre] * (tran_cost + tax_cost))

            daily_profit = np.nansum(volume_daily * (df_close.loc[date_date] - df_close.loc[date_date_pre])) - cost_sell
            daily_ratio = daily_profit / np.nansum(equity_pre)
            daily_use = len(code_sell) * unit_amount
            equity_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            # 指数计算
            index_volume_daily = 0

        else:
            # 股票组合计算
            volume_daily = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            volume_diff = volume_daily - volume_pre

            volume_buy = pd.Series(data=np.zeros(len(list_code)), index=list_code)
            volume_sell = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            daily_profit = 0
            daily_ratio = 0
            daily_use = 0
            equity_pre = pd.Series(data=np.zeros(len(list_code)), index=list_code)

            # 指数计算
            index_volume_daily = 0

    else:
        # 股票组合计算
        holding_code = holding_pre.copy()
        volume_daily = volume_pre.copy()
        volume_diff = volume_daily - volume_pre

        volume_buy = pd.Series(data=np.zeros(len(list_code)), index=list_code)
        volume_sell = pd.Series(data=np.zeros(len(list_code)), index=list_code)

        daily_profit = 0
        daily_ratio = 0
        if holding_code:
            daily_use = len(holding_code) * unit_amount
        else:
            daily_use = 0

        # 指数计算
        index_volume_daily = index_volume_pre

    df_trading = pd.DataFrame({'num': volume_diff})
    df_trading = df_trading[df_trading['num'] != 0]

    if not df_trading.empty:
        # pass
        df_trading.loc['IF'] = index_volume_pre - index_volume_daily
        df_trading.to_csv(outputPath + date + "_交易明细.csv")

    holding_pre = holding_code.copy()
    volume_pre = volume_daily.copy()
    index_volume_pre = index_volume_daily

    # 指标计算
    # ratio_df.loc[date, 'daily_profit'] = daily_profit
    # ratio_df.loc[date, 'capital_use'] = daily_use
    # ratio_df.loc[date, 'daily_ratio'] = daily_ratio
    # ratio_df.loc[date, 'holding_num'] = (volume_daily != 0).sum()
    # ratio_df.loc[date, 'buy_num'] = (volume_diff > 0).sum()
    # ratio_df.loc[date, 'sell_num'] = (volume_diff < 0).sum()
    # ratio_df.loc[date, 'index_num'] = index_volume_daily


# 数据导出
# ratio_df.to_csv(outputPath + str(hold_length) + "_策略收益率换手率.csv")

# ######################################################################################################################
