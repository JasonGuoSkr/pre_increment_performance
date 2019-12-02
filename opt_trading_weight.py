
# ######################################################################################################################
"""
绩效回测，个股持仓上限为5%，每日调仓，使股票间等权重
"""

import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191101/持仓时间参数优化/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191101/持仓时间参数优化/"

for i in range(1,4):
    print(i)
    # 数据导入
    df_buy_sell = pd.read_csv(inputPath + str(i) + "_汇总个股买卖时点.csv", index_col=0, engine='python')
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

    # 参数
    start_date = '2010-01-01'
    end_date = '2019-10-31'

    weight_bound = 0.1
    tax_cost = 0.001
    tran_cost = 0.0015
    index_code = '000905.XSHG'

    # 交易日列表
    list_trading = get_trading_dates(start_date=start_date, end_date=end_date)

    # 股票列表
    list_code = df_buy_sell['code'].unique()
    list_code.sort()

    # 取行情数据
    price_df = get_price(list_code, start_date=start_date, end_date=end_date, frequency='1d',
                         fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')
    df_open = price_df.loc[:, list_code]
    price_index = get_price(index_code, start_date=start_date, end_date=end_date, frequency='1d',
                            fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')

    # 持仓权重数据
    weight_df = pd.DataFrame(data=np.zeros((len(list_code), len(list_trading))), index=list_code, columns=list_trading)
    for date in list_trading:
        date_str = date.strftime("%Y-%m-%d")

        holding_df = df_buy_sell[(df_buy_sell['buy_date'] <= date_str) & (df_buy_sell['sell_date'] > date_str)]
        holding_code = holding_df['code'].tolist()

        if len(holding_code) > (1 / weight_bound):
            weight_df.loc[holding_code, date] = 1 / len(holding_code)
        elif len(holding_code) > 0:
            weight_df.loc[holding_code, date] = weight_bound
        # print(date)

    # 收益率计算
    ratio_df = pd.DataFrame(index=list_trading[1:-1], columns=['daily_ratio', 'index_ratio', 'turn_ratio',
                                                               'holding_num', 'buy_num', 'sell_num'])
    for date in list_trading[1:-1]:
        date_str = date.strftime("%Y-%m-%d")
        date_pre = list_trading[list_trading.index(date) - 1]
        date_post = list_trading[list_trading.index(date) + 1]
        weight_daily = weight_df[date]
        weight_pre = weight_df[date_pre]

        # if date == list_trading[-1]:
        #     weight_post = pd.Series(data=np.zeros(len(list_code)), index=list_code)
        # else:
        #     date_post = list_trading[list_trading.index(date) + 1]
        #     weight_post = weight_df[date_post]

        # 日收益率
        rate_open_to_open = df_open.loc[date_post] / df_open.loc[date] - 1
        rate_index = price_index.loc[date_post] / price_index.loc[date] - 1

        # 指标计算
        ratio_df.loc[date, 'turn_ratio'] = sum(abs(weight_daily - weight_pre))
        ratio_df.loc[date, 'holding_num'] = (weight_daily != 0).sum()
        ratio_df.loc[date, 'buy_num'] = ((weight_daily != 0) & (weight_pre == 0)).sum()
        ratio_df.loc[date, 'sell_num'] = ((weight_daily == 0) & (weight_pre != 0)).sum()

        series_buy = weight_daily - weight_pre
        series_buy[series_buy < 0] = 0
        series_sell = weight_daily - weight_pre
        series_sell[series_sell > 0] = 0
        cost_buy = np.nansum(series_buy * tran_cost)
        cost_sell = -np.nansum(series_sell * (tran_cost + tax_cost))

        ratio_all = np.nansum(rate_open_to_open * weight_daily) - cost_buy - cost_sell
        ratio_df.loc[date, 'daily_ratio'] = ratio_all
        ratio_df.loc[date, 'index_ratio'] = rate_index * weight_daily.sum()

    # 权益计算
    equity_df = pd.DataFrame(index=list_trading[1:-1], columns=['daily_equity', 'index_equity', 'excess_equity'])

    equity_df.loc[:, 'daily_equity'] = (ratio_df.loc[:, 'daily_ratio'] + 1).cumprod()
    equity_df.loc[:, 'index_equity'] = (ratio_df.loc[:, 'index_ratio'] + 1).cumprod()
    equity_df.loc[:, 'excess_equity'] = (ratio_df.loc[:, 'daily_ratio'] - ratio_df.loc[:, 'index_ratio'] + 1).cumprod()

    # 数据导出
    ratio_df.to_csv(outputPath + str(i) + "_策略收益率换手率.csv")
    equity_df.to_csv(outputPath + str(i) + "_策略动态权益.csv")

# ######################################################################################################################
