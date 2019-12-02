# ######################################################################################################################
"""
每只股票持仓超额收益分析
"""

import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()

# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191003/结果/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191003/"

start_date = '2010-01-01'
end_date = '2019-09-30'

unit_amount = 5e5
tax_cost = 0.001
tran_cost = 0.0015
index_code = '000905.XSHG'

# 交易日列表
list_trading = get_trading_dates(start_date=start_date, end_date=end_date)

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
df_buy_sell = df_buy_sell.reset_index(drop=True)

per_ratio = df_buy_sell.copy()
per_ratio['ratio_code'] = np.nan
per_ratio['ratio_index'] = np.nan
per_ratio['period'] = np.nan

for ind in df_buy_sell.index:
    ind_code = df_buy_sell.loc[ind, 'code']
    ind_start = df_buy_sell.loc[ind, 'buy_date']
    ind_end = df_buy_sell.loc[ind, 'sell_date']

    price_df = get_price(ind_code, start_date=ind_start, end_date=ind_end, frequency='1d',
                         fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')
    price_index = get_price(index_code, start_date=ind_start, end_date=ind_end, frequency='1d',
                            fields=['open'], adjust_type='pre', skip_suspended=False, market='cn')

    period = len(get_trading_dates(start_date=ind_start, end_date=ind_end))

    ratio_code = price_df.iloc[-1] / price_df.iloc[0] - 1
    ratio_index = price_index.iloc[-1] / price_index.iloc[0] - 1

    per_ratio.loc[ind, 'ratio_code'] = ratio_code
    per_ratio.loc[ind, 'ratio_index'] = ratio_index
    per_ratio.loc[ind, 'period'] = period

per_ratio[ 'ratio_excess'] = per_ratio['ratio_code'] - per_ratio['ratio_index']

# 数据导出
per_ratio.to_csv(outputPath + "个股收益率.csv")

# ######################################################################################################################
