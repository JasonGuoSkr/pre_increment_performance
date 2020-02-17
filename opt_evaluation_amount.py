
# ######################################################################################################################
# 计算对冲后收益及策略年度分析


import pandas as pd
import datetime
import numpy as np
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191203/利润增长率下限参数优化/权重不调整/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191203/利润增长率下限参数优化/权重不调整/"

summary = pd.DataFrame(index=range(1, 11), columns=['absoluteAmount', 'capitalUse', 'absoluteRate', 'excessRate'])

for i in range(1, 11):
    # 数据导入
    ratio_df = pd.read_csv(inputPath + str(i) + "_策略收益率换手率.csv", index_col=0, engine='python')
    equity_df = pd.read_csv(inputPath + str(i) + "_策略动态权益.csv", index_col=0, engine='python')


    def max_drawdown(value_list):
        # 最大回撤
        # 结束位置
        ind = np.argmax((np.maximum.accumulate(value_list) - value_list) / np.maximum.accumulate(value_list))
        if ind == 0:
            return 0
        # 开始位置
        j = np.argmax(value_list[:ind])
        return (value_list[j] - value_list[ind]) / (value_list[j])


    # 年度收益率分析
    dateList = equity_df.index.tolist()
    yearList = [dateStr[:4] for dateStr in dateList]
    unique_yearList = np.unique(np.array(yearList)).tolist()

    yearValue_df = pd.DataFrame(index=['avg'] + unique_yearList, columns=['absoluteAmount', 'baseAmount', 'capitalUse',
                                                                          "absoluteRate", "baseRate", "excessRate",
                                                                          "dateLength", "returnValue", "maxDrawDown",
                                                                          "returnDraw"])

    for yearStr in unique_yearList:
        # yearStr = unique_yearList[-2]

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
        yearValue_df.loc[yearStr, "returnValue"] = equity_df.iloc[indexFirst + indexNum - 1, 0] / \
            equity_df.iloc[indexFirst, 0] - 1
        yearValue_df.loc[yearStr, "maxDrawDown"] = max_drawdown(equity_df.iloc[indexFirst:indexFirst + indexNum, 0])
        yearValue_df.loc[yearStr, "returnDraw"] = yearValue_df.loc[yearStr, "returnValue"] / \
            yearValue_df.loc[yearStr, "maxDrawDown"]
        yearValue_df.loc[yearStr, "dateLength"] = np.sum(ratio_df.iloc[indexFirst:indexFirst + indexNum, 2] != 0)

    yearValue_df.loc["avg", "absoluteAmount"] = np.mean(yearValue_df.iloc[2:, 0])
    yearValue_df.loc["avg", "baseAmount"] = np.mean(yearValue_df.iloc[2:, 1])
    yearValue_df.loc["avg", "capitalUse"] = np.mean(yearValue_df.iloc[2:, 2])
    yearValue_df.loc["avg", "absoluteRate"] = np.mean(yearValue_df.iloc[2:, 3])
    yearValue_df.loc["avg", "baseRate"] = np.mean(yearValue_df.iloc[2:, 4])
    yearValue_df.loc["avg", "excessRate"] = np.mean(yearValue_df.iloc[2:, 5])
    yearValue_df.loc["avg", "dateLength"] = np.mean(yearValue_df.iloc[2:, 6])
    yearValue_df.loc["avg", "returnValue"] = np.mean(yearValue_df.iloc[2:, 7])
    yearValue_df.loc["avg", "maxDrawDown"] = max_drawdown(equity_df.iloc[:, 0])
    yearValue_df.loc["avg", "returnDraw"] = np.mean(yearValue_df.iloc[2:, 9])

    summary.loc[i, "absoluteAmount"] = yearValue_df.loc["avg", "absoluteAmount"]
    summary.loc[i, "capitalUse"] = yearValue_df.loc["avg", "capitalUse"]
    summary.loc[i, "absoluteRate"] = yearValue_df.loc["avg", "absoluteRate"]
    summary.loc[i, "excessRate"] = yearValue_df.loc["avg", "excessRate"]

summary.to_csv(outputPath + "收益比较.csv")

# ######################################################################################################################
