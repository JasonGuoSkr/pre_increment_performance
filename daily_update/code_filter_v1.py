import os
import math
import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *


"""
股票买卖时间整理
"""

rq.init("ricequant", "8ricequant8", ('10.29.135.119', 16010))


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_10/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_10/"

# up_date = rq.get_previous_trading_date(datetime.datetime.now(), 1).strftime('%Y-%m-%d')
up_date = '2020-03-20'

# 数据导入
df_pre = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')
df_pre.drop_duplicates(inplace=True)
df_pre = df_pre[df_pre['buy_date'] <= up_date]
df_pre.sort_values(by='buy_date', axis=0, ascending=True, inplace=True)
df_pre = df_pre.reset_index(drop=True)

df_post = pd.read_csv(inputPath + "汇总个股买卖时点_2020-03-20.csv", index_col=0, engine='python')
df_post.drop_duplicates(inplace=True)
df_post = df_post[df_post['buy_date'] >= up_date]
df_post.sort_values(by='buy_date', axis=0, ascending=True, inplace=True)
df_post = df_post.reset_index(drop=True)

# 数据整理
data_join = pd.concat([df_pre, df_post], axis=0)
data_join.drop_duplicates(inplace=True)

list_code = data_join['code'].unique()
list_code.sort()

data_final = pd.DataFrame(columns=['code', 'buy_date', 'sell_date'])
for code in list_code:
    # code = '002847.XSHE'
    data_sample = data_join[data_join['code'] == code]
    if data_sample.shape[0] != 1:
        # print(code)
        # continue
        data_sample = data_sample.sort_values(by='buy_date')
        signal_list = [1] * data_sample.shape[0]

        for ind in range(data_sample.shape[0], 1, -1):
            if data_sample.iloc[ind - 1, 1] < data_sample.iloc[ind - 2, 2]:
                data_sample.iloc[ind - 2, 2] = data_sample.iloc[ind - 1, 2]
                signal_list[ind - 1] = 0
            data_sample = data_sample[[signal == 1 for signal in signal_list]]

    data_final = pd.concat([data_final, data_sample], axis=0)

data_final = data_final.sort_values(by='buy_date')
data_final.reset_index(inplace=True, drop=True)

data_final.to_csv(outputPath + "汇总个股买卖时点.csv")

# list_code = data_final['code'].unique()
# list_code.sort()
#
# for code in list_code:
#     # code = '002847.XSHE'
#     data_sample = data_final[data_final['code'] == code]
#     if data_sample.shape[0] != 1:
#         print(code)
#         continue
#
# data_ind = data_final[data_final['code'] == '300532.XSHE']
