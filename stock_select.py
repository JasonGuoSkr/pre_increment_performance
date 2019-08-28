
# ######################################################################################################################
"""
股票选择
"""

import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *

rq.init()


# 参数
hold_length = 10
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/数据/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果/"


# 数据导入
foreshow_cum_netProfitMin = pd.read_csv(inputPath + "业绩预告累计净利润下限_计算.csv", index_col=0, engine='python')
foreshow_quarterly_netProfitMin = pd.read_csv(inputPath + "业绩预告季度净利润下限_计算.csv", index_col=0, engine='python')
foreshow_infoPublDate = pd.read_csv(inputPath + "业绩预告最新披露日期_wind.csv", index_col=0, engine='python')
realized_cum_netProfit = pd.read_csv(inputPath + "财务报告累计净利润_聚源.csv", index_col=0, engine='python')
realized_quarterly_netProfit = pd.read_csv(inputPath + "季度报告净利润_聚源.csv", index_col=0, engine='python')
realized_infoPublDate = pd.read_csv(inputPath + "季度报告披露时间_wind.csv", index_col=0, engine='python')
estimate_infoPublDate = pd.read_csv(inputPath + "季度报告预计披露时间_wind.csv", index_col=0, engine='python')

foreshow_quarterly_netProfitMin = foreshow_quarterly_netProfitMin.reindex(foreshow_cum_netProfitMin.index)
foreshow_infoPublDate = foreshow_infoPublDate.reindex(foreshow_cum_netProfitMin.index)
realized_cum_netProfit = realized_cum_netProfit.reindex(foreshow_cum_netProfitMin.index)
realized_quarterly_netProfit = realized_quarterly_netProfit.reindex(foreshow_cum_netProfitMin.index)
realized_infoPublDate = realized_infoPublDate.reindex(foreshow_cum_netProfitMin.index)
estimate_infoPublDate = estimate_infoPublDate.reindex(foreshow_cum_netProfitMin.index)

foreshow_cum_netProfitMin.index = id_convert(foreshow_cum_netProfitMin.index.tolist())
foreshow_quarterly_netProfitMin.index = id_convert(foreshow_quarterly_netProfitMin.index.tolist())
foreshow_infoPublDate.index = id_convert(foreshow_infoPublDate.index.tolist())
realized_cum_netProfit.index = id_convert(realized_cum_netProfit.index.tolist())
realized_quarterly_netProfit.index = id_convert(realized_quarterly_netProfit.index.tolist())
realized_infoPublDate.index = id_convert(realized_infoPublDate.index.tolist())
estimate_infoPublDate.index = id_convert(estimate_infoPublDate.index.tolist())


# 股票选择、买入及卖出时间
quarterly_index = foreshow_cum_netProfitMin.columns[foreshow_cum_netProfitMin.columns >= "2010-03-31"].tolist()
df_code = pd.DataFrame(index=range(foreshow_cum_netProfitMin.shape[0]), columns=quarterly_index)
df_buy_date = pd.DataFrame(index=range(foreshow_cum_netProfitMin.shape[0]), columns=quarterly_index)
df_sell_date = pd.DataFrame(index=range(foreshow_cum_netProfitMin.shape[0]), columns=quarterly_index)
df_join = pd.DataFrame(columns=['code', 'buy_date', 'sell_date'])

for quarterly_adjust in quarterly_index:
    ind = (foreshow_cum_netProfitMin.columns.tolist()).index(quarterly_adjust)
    quarterly_yoy = foreshow_cum_netProfitMin.columns[ind - 4]
    # quarterly_pre = foreshow_cum_netProfitMin.columns[ind - 1]
    # quarterly_preYoy = foreshow_cum_netProfitMin.columns[ind - 5]

    # 计算相关净利润与营收数据
    list_netProfit_cum = foreshow_cum_netProfitMin[quarterly_adjust]
    list_netProfit_cum_yoy = realized_cum_netProfit[quarterly_yoy]

    list_netProfit_quarterly = foreshow_quarterly_netProfitMin[quarterly_adjust]
    list_netProfit_quarterly_yoy = realized_quarterly_netProfit[quarterly_yoy]

    # 预告财报净利润同比增速大于50%且预告财报净利润大于1000万
    list_profitRate_cum = (list_netProfit_cum - list_netProfit_cum_yoy) / abs(list_netProfit_cum_yoy)
    list_profitRate_cum_index = list_profitRate_cum > 0.5

    list_netProfit_cum_index = list_netProfit_cum > 1e7

    # 预告单季度净利润同比增速大于50%且预告单季度净利润大于1000万
    list_profitRate_quarterly = (list_netProfit_quarterly - list_netProfit_quarterly_yoy) \
        / abs(list_netProfit_quarterly_yoy)
    list_profitRate_quarterly_index = list_profitRate_quarterly > 0.5

    list_netProfit_quarterly_index = list_netProfit_quarterly > 1e7

    # df_profit = pd.DataFrame({'list_netProfit_cum': list_netProfit_cum,
    #                           'list_netProfit_cum_yoy': list_netProfit_cum_yoy,
    #                           'list_profitRate_cum': list_profitRate_cum,
    #                           'list_netProfit_quarterly': list_netProfit_quarterly,
    #                           'list_netProfit_quarterly_yoy': list_netProfit_quarterly_yoy,
    #                           'list_profitRate_quarterly': list_profitRate_quarterly})
    # df_profit.sort_values(by=['list_profitRate_cum'], ascending=False, inplace=True)

    list_filter_index = list_profitRate_cum_index & list_netProfit_cum_index & list_profitRate_quarterly_index &\
        list_netProfit_quarterly_index

    list_code_filter = list_filter_index.index[list_filter_index].tolist()

    list_foreshow_infoPublDate = foreshow_infoPublDate.loc[list_code_filter, quarterly_adjust]
    list_realized_infoPublDate = realized_infoPublDate.loc[list_code_filter, quarterly_adjust]
    list_estimate_infoPublDate = estimate_infoPublDate.loc[list_code_filter, quarterly_adjust]

    df_infoPublDate = pd.DataFrame({'foreshow_infoPublDate': list_foreshow_infoPublDate,
                                    'realized_infoPublDate': list_realized_infoPublDate,
                                    'estimate_infoPublDate': list_estimate_infoPublDate})
    df_infoPublDate = df_infoPublDate.dropna(axis=0, how='any')

    for code in df_infoPublDate.index:
        ind_foreshow_infoPublDate = get_previous_trading_date(df_infoPublDate.loc[code, 'foreshow_infoPublDate'])
        ind_foreshow_infoPublDate = get_next_trading_date(ind_foreshow_infoPublDate).strftime("%Y-%m-%d")
        pre_estimate_infoPublDate = get_previous_trading_date(
            df_infoPublDate.loc[code, 'estimate_infoPublDate'], n=hold_length).strftime("%Y-%m-%d")
        df_infoPublDate.loc[code, 'buy_date'] = max(ind_foreshow_infoPublDate, pre_estimate_infoPublDate)

    df_code.iloc[:len(df_infoPublDate), quarterly_index.index(quarterly_adjust)] = df_infoPublDate.index
    df_buy_date.iloc[:len(df_infoPublDate), quarterly_index.index(quarterly_adjust)] = \
        df_infoPublDate.loc[:, 'buy_date'].values
    df_sell_date.iloc[:len(df_infoPublDate), quarterly_index.index(quarterly_adjust)] = \
        df_infoPublDate.loc[:, 'realized_infoPublDate'].values

    df_sample = df_infoPublDate[['buy_date', 'realized_infoPublDate']]
    df_sample.reset_index(inplace=True)
    df_sample = df_sample.rename(columns={'index': 'code', 'realized_infoPublDate': 'sell_date'})
    df_sample = df_sample.sort_values(by='buy_date')

    df_join = pd.concat([df_join, df_sample])

    print(quarterly_adjust)

df_join.reset_index(inplace=True, drop=True)

# 数据导出
df_code.to_csv(outputPath + "季度股票池.csv")
df_buy_date.to_csv(outputPath + "季度个股买入时点.csv")
df_sell_date.to_csv(outputPath + "季度个股卖出时点.csv")
df_join.to_csv(outputPath + "汇总个股买卖时点.csv")

# ######################################################################################################################
