
# ######################################################################################################################
"""
收益风险分析V1:
    计算策略净值曲线及年度收益分析，根据back_v1
"""


import pandas as pd
import datetime
import numpy as np
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
hold_length = 10
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191201/权重不调整/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191201/权重不调整/"


# 数据导入
ratio_df = pd.read_csv(inputPath + str(hold_length) + "_策略收益率换手率.csv", index_col=0, engine='python')
# equalValue_df = equalValue_df.drop(equalValue_df.index[equalValue_df.index < "2009-12-31"])
# equalValue_df = equalValue_df / equalValue_df.iloc[0, 0]


def max_drawdown(value_list):
    # 最大回撤
    # 结束位置
    i = np.argmax((np.maximum.accumulate(value_list) - value_list) / np.maximum.accumulate(value_list))
    if i == 0:
        return 0
    # 开始位置
    j = np.argmax(value_list[:i])
    return (value_list[j] - value_list[i]) / (value_list[j])


# 年度收益率分析
dateList = ratio_df.index.tolist()
yearList = [dateStr[:4] for dateStr in dateList]
unique_yearList = np.unique(np.array(yearList)).tolist()

yearValue_df = pd.DataFrame(index=['avg'] + unique_yearList, columns=['absoluteAmount', 'baseAmount', 'capitalUse',
                                                                      "absoluteRate", "baseRate", "excessRate",
                                                                      "dateLength"])

for yearStr in unique_yearList:
    # yearStr = unique_yearList[0]

    indexFirst = yearList.index(yearStr)
    indexNum = yearList.count(yearStr)

    yearValue_df.loc[yearStr, "absoluteAmount"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 0])
    yearValue_df.loc[yearStr, "baseAmount"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 1])
    yearValue_df.loc[yearStr, "capitalUse"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 2]) / indexNum
    yearValue_df.loc[yearStr, "absoluteRate"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 0]) / \
        (np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 2]) / indexNum)
    yearValue_df.loc[yearStr, "baseRate"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 1]) / \
        (np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 2]) / indexNum)
    yearValue_df.loc[yearStr, "excessRate"] = yearValue_df.loc[yearStr, "absoluteRate"] - \
        yearValue_df.loc[yearStr, "baseRate"]
    yearValue_df.loc[yearStr, "dateLength"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 2] != 0)


yearValue_df.loc["avg", "absoluteAmount"] = np.mean(yearValue_df.iloc[2:, 0])
yearValue_df.loc["avg", "baseAmount"] = np.mean(yearValue_df.iloc[2:, 1])
yearValue_df.loc["avg", "capitalUse"] = np.mean(yearValue_df.iloc[2:, 2])
yearValue_df.loc["avg", "absoluteRate"] = np.mean(yearValue_df.iloc[2:, 3])
yearValue_df.loc["avg", "baseRate"] = np.mean(yearValue_df.iloc[2:, 4])
yearValue_df.loc["avg", "excessRate"] = np.mean(yearValue_df.iloc[2:, 5])
yearValue_df.loc["avg", "dateLength"] = np.mean(yearValue_df.iloc[2:, 6])


# 数据导出
yearValue_df.to_csv(outputPath + str(hold_length) + "_年度收益分析.csv")

# ######################################################################################################################
