
# ######################################################################################################################
"""
股指期货收益计算:
    按持仓计算股指期货当日损益
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
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191209/权重不调整_100/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191209/权重不调整_100/"

start_date = '2010-01-01'
end_date = '2019-11-20'

hold_length = 5
unit_amount = 1e6
tax_cost = 0.001
tran_cost = 0.002
index_code = '000905.XSHG'
index_multiplier = 200


# 数据导入
ratio_df = pd.read_csv(inputPath + str(hold_length) + "_策略收益率换手率.csv", index_col=0, engine='python')
equity_df = pd.read_csv(inputPath + str(hold_length) + "_策略动态权益.csv", index_col=0, engine='python')


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


# 取行情数据
price_index = rq.get_price(index_code, start_date=start_date, end_date=end_date, frequency='1d',
                           fields=['open', 'close'], adjust_type='pre', skip_suspended=False, market='cn')


future_profit = pd.DataFrame(index=ratio_df.index, columns=['profit', 'index_num'])




# ######################################################################################################################
