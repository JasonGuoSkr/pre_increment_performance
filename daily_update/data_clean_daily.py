
# ######################################################################################################################
"""
数据清洗及处理
"""


import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202001/数据/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202001/数据/"


# 数据导入
foreshow_infoPublDate = pd.read_csv(inputPath + "业绩预告最新披露日期_wind.csv", index_col=0, engine='python')
foreshow_cum_netProfitMin = pd.read_csv(inputPath + "业绩预告净利润下限_wind.csv", index_col=0, engine='python')
foreshow_cum_netProfit_changeMin = pd.read_csv(inputPath + "业绩预告净利润同比增长下限_wind.csv", index_col=0, engine='python')
foreshow_cum_netProfitMin = foreshow_cum_netProfitMin.replace(0, np.nan)
foreshow_cum_netProfit_changeMin = foreshow_cum_netProfit_changeMin.replace(0, np.nan)
foreshow_cum_netProfit_changeMin = foreshow_cum_netProfit_changeMin.div(100)

realized_infoPublDate = pd.read_csv(inputPath + "季度报告披露时间_wind.csv", index_col=0, engine='python')
realized_cum_netProfit = pd.read_csv(inputPath + "财务报告累计净利润_聚源.csv", index_col=0, engine='python')
realized_infoPublDate = realized_infoPublDate.reindex(foreshow_infoPublDate.index)
realized_cum_netProfit = realized_cum_netProfit.reindex(foreshow_infoPublDate.index)


# 业绩预告数据补充
foreshow_cum_netProfitMin_add = pd.DataFrame(index=foreshow_cum_netProfitMin.index,
                                             columns=foreshow_cum_netProfitMin.columns)

for ind in range(4, len(foreshow_cum_netProfitMin_add.columns)):
    columnIndex = foreshow_cum_netProfitMin_add.columns[ind]
    columnIndex_datetime = datetime.datetime.strptime(columnIndex, "%Y-%m-%d")
    yearIndex = columnIndex_datetime.year
    monthIndex = columnIndex_datetime.month

    columnIndex_pre = foreshow_cum_netProfitMin_add.columns[ind-4]
    foreshow_cum_netProfitMin_add[columnIndex] = realized_cum_netProfit[columnIndex_pre].abs() * \
        foreshow_cum_netProfit_changeMin[columnIndex] + realized_cum_netProfit[columnIndex_pre]

foreshow_cum_netProfitMin = foreshow_cum_netProfitMin.replace(np.nan, foreshow_cum_netProfitMin_add)


# 预告季度净利润下限
foreshow_quarterly_netProfitMin = pd.DataFrame(index=foreshow_cum_netProfitMin.index,
                                               columns=foreshow_cum_netProfitMin.columns)

for ind in reversed(range(len(foreshow_quarterly_netProfitMin.columns))):
    monthIndex = datetime.datetime.strptime(foreshow_quarterly_netProfitMin.columns[ind], "%Y-%m-%d").month
    columnIndex = foreshow_quarterly_netProfitMin.columns[ind]

    if monthIndex in [6, 9, 12]:
        pre_columnIndex = realized_cum_netProfit.columns[ind - 1]
        foreshow_quarterly_netProfitMin[columnIndex] = foreshow_cum_netProfitMin[columnIndex] - \
            realized_cum_netProfit[pre_columnIndex]
    else:
        foreshow_quarterly_netProfitMin[columnIndex] = foreshow_cum_netProfitMin[columnIndex]


# 数据导出
foreshow_cum_netProfitMin.to_csv(outputPath + "业绩预告累计净利润下限_计算.csv")
foreshow_quarterly_netProfitMin.to_csv(outputPath + "业绩预告季度净利润下限_计算.csv")

# ######################################################################################################################
