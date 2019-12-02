
# ######################################################################################################################
# 计算对冲后收益及策略年度分析
# ######################################################################################################################


import pandas as pd
import datetime
import numpy as np
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191101/持仓时间参数优化/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191101/持仓时间参数优化/"

for i in range(1,4):
    # 数据导入
    excessValue_df = pd.read_csv(inputPath + str(i) + "_策略动态权益.csv", index_col=0, engine='python')
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


    def sharpe_ratio(value_list):
        # 夏普比率
        return_list = (value_list.diff() / value_list.shift(1)).dropna()
        count = len(return_list)
        annul_return = return_list.add(1).prod() ** (250 / count) - 1
        return_std = np.std(return_list) * np.sqrt(250)
        sharperatio = (annul_return - 0.05) / return_std
        # 默认252个工作日,无风险利率为0
        return sharperatio


    # 年度收益率分析
    dateList = excessValue_df.index.tolist()
    yearList = [dateStr[:4] for dateStr in dateList]
    unique_yearList = np.unique(np.array(yearList)).tolist()

    yearValue_df = pd.DataFrame(index=['all'] + unique_yearList, columns=["absoluteRate", "baseRate",
                                                                          "excessRate", "excess_maxDrawDown",
                                                                          "excess_returnDraw", "excess_sharpRatio"])
    for yearStr in unique_yearList:
        indexFirst = yearList.index(yearStr)
        indexNum = yearList.count(yearStr)
        if indexFirst == 0:
            yearValue_df.loc[yearStr, "absoluteRate"] = excessValue_df.iloc[indexNum - 1, 0] / excessValue_df.iloc[0, 0] - 1
            yearValue_df.loc[yearStr, "baseRate"] = excessValue_df.iloc[indexNum - 1, 1] / excessValue_df.iloc[0, 1] - 1
            yearValue_df.loc[yearStr, "excess_sharpRatio"] = sharpe_ratio(excessValue_df.iloc[0:indexNum - 1, 2])
            yearValue_df.loc[yearStr, "excess_maxDrawDown"] = max_drawdown(excessValue_df.iloc[0:indexNum - 1, 2])
        else:
            yearValue_df.loc[yearStr, "absoluteRate"] = excessValue_df.iloc[indexFirst + indexNum - 1, 0] / \
                                                        excessValue_df.iloc[indexFirst - 1, 0] - 1
            yearValue_df.loc[yearStr, "baseRate"] = excessValue_df.iloc[indexFirst + indexNum - 1, 1] / \
                excessValue_df.iloc[indexFirst - 1, 1] - 1
            yearValue_df.loc[yearStr, "excess_sharpRatio"] = sharpe_ratio(excessValue_df.iloc[
                                                                          indexFirst - 1:indexFirst + indexNum - 1, 2])
            yearValue_df.loc[yearStr, "excess_maxDrawDown"] = max_drawdown(excessValue_df.iloc[
                                                                           indexFirst - 1:indexFirst + indexNum - 1, 2])

        # 超额收益
        yearValue_df.loc[yearStr, "excessRate"] = yearValue_df.loc[yearStr, "absoluteRate"] -\
            yearValue_df.loc[yearStr, "baseRate"]
        # 收益回撤比
        yearValue_df.loc[yearStr, "excess_returnDraw"] = yearValue_df.loc[yearStr, "excessRate"] /\
            yearValue_df.loc[yearStr, "excess_maxDrawDown"]


    # 整体收益分析
    all_excess_sharpRatio = sharpe_ratio(excessValue_df["excess_equity"])
    all_absoluteRate = (excessValue_df.iloc[-1, 0] / excessValue_df.iloc[0, 0]) ** (250 / excessValue_df.shape[0]) - 1
    all_baseRate = (excessValue_df.iloc[-1, 1] / excessValue_df.iloc[0, 1]) ** (250 / excessValue_df.shape[0]) - 1
    all_excess_return = all_absoluteRate - all_baseRate
    all_excess_maxDrawDown = max_drawdown(excessValue_df["excess_equity"])
    all_excess_returnDraw = all_excess_return / all_excess_maxDrawDown

    yearValue_df.loc["all", "excess_sharpRatio"] = all_excess_sharpRatio
    yearValue_df.loc["all", "absoluteRate"] = all_absoluteRate
    yearValue_df.loc["all", "baseRate"] = all_baseRate
    yearValue_df.loc["all", "excessRate"] = all_excess_return
    yearValue_df.loc["all", "excess_maxDrawDown"] = all_excess_maxDrawDown
    yearValue_df.loc["all", "excess_returnDraw"] = all_excess_returnDraw

    # 动态回撤分析
    excess_drawDown_df = -(np.maximum.accumulate(excessValue_df["excess_equity"]) - excessValue_df["excess_equity"]) \
                         / np.maximum.accumulate(excessValue_df["excess_equity"])
    excess_drawDown_df = excess_drawDown_df.to_frame()
    excess_drawDown_df.columns = ["excessDrawDown"]

    # 数据导出
    excessValue_df = excessValue_df.join(excess_drawDown_df)
    # excessValue_df.to_csv(outputPath + "策略净值曲线.csv")
    # yearValue_df.to_csv(outputPath + "策略年度收益率分析.csv")

    if i == 1:
        summary = excessValue_df["excess_equity"].to_frame()
    else:
        summary = pd.concat([summary, excessValue_df["excess_equity"].to_frame()], axis=1)

summary.columns = range(1,4)
summary.to_csv(outputPath + "策略净值曲线.csv")

# ######################################################################################################################
