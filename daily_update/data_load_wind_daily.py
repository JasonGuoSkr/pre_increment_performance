# ######################################################################################################################
"""
数据下载
"""


import os
import datetime
import pandas as pd
from WindPy import *

w.start()


# 文件路径
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整/数据/"
if not os.path.exists(outputPath):
    os.makedirs(outputPath)
    print(outputPath + '创建成功')

start_date = "2019-09-30"
end_date = "2019-09-30"

# 历史数据导入
foreshow_infoPublDate = pd.read_csv(outputPath + "业绩预告最新披露日期_wind.csv", index_col=0, engine='python')
realized_infoPublDate = pd.read_csv(outputPath + "季度报告披露时间_wind.csv", index_col=0, engine='python')
estimate_infoPublDate = pd.read_csv(outputPath + "季度报告预计披露时间_wind.csv", index_col=0, engine='python')
foreshow_cum_netProfitMin = pd.read_csv(outputPath + "业绩预告净利润下限_wind.csv", index_col=0, engine='python')
foreshow_cum_netProfit_changeMin = pd.read_csv(outputPath + "业绩预告净利润同比增长下限_wind.csv", index_col=0, engine='python')

# 取全A股票代码
# date_now = '2019-10-20'
date_now = datetime.now().strftime("%Y-%m-%d")

indexComponent_wind = w.wset("sectorconstituent", "date=" + date_now + ";sectorid=a001010100000000")
indexComponent_list = indexComponent_wind.Data[1]
indexComponent_str = ','.join(indexComponent_list)

# 数据下载
profitNoticeDate = w.wsd(indexComponent_str, "profitnotice_date", start_date, end_date, "Period=Q;Days=Alldays")
profitNotice_netprofitMin = w.wsd(indexComponent_str, "profitnotice_netprofitmin", start_date, end_date, "unit=1;Period=Q;Days=Alldays")
profitNotice_changeMin = w.wsd(indexComponent_str, "profitnotice_changemin", start_date, end_date, "unit=1;Period=Q;Days=Alldays")
apubliDate = w.wsd(indexComponent_str, "stm_issuingdate", start_date, end_date, "Period=Q;Days=Alldays")
estimate_apubliDate = w.wsd(indexComponent_str, "stm_predict_issuingdate", start_date, end_date, "Period=Q;Days=Alldays")

df_profitNoticeDate = pd.DataFrame(profitNoticeDate.Data[0], index=profitNoticeDate.Codes, columns=profitNoticeDate.Times)
df_profitNotice_netprofitMin = pd.DataFrame(profitNotice_netprofitMin.Data[0], index=profitNotice_netprofitMin.Codes, columns=profitNotice_netprofitMin.Times)
df_profitNotice_changeMin = pd.DataFrame(profitNotice_changeMin.Data[0], index=profitNotice_changeMin.Codes, columns=profitNotice_changeMin.Times)
df_apubliDate = pd.DataFrame(apubliDate.Data[0], index=apubliDate.Codes, columns=apubliDate.Times)
df_estimate_apubliDate = pd.DataFrame(estimate_apubliDate.Data[0], index=estimate_apubliDate.Codes, columns=estimate_apubliDate.Times)

# 数据聚合
if df_profitNoticeDate.columns[0].strftime("%Y-%m-%d") == foreshow_infoPublDate.columns[-1]:
    foreshow_infoPublDate.drop(columns=foreshow_infoPublDate.columns[-1], inplace=True)
    realized_infoPublDate.drop(columns=realized_infoPublDate.columns[-1], inplace=True)
    estimate_infoPublDate.drop(columns=estimate_infoPublDate.columns[-1], inplace=True)
    foreshow_cum_netProfitMin.drop(columns=foreshow_cum_netProfitMin.columns[-1], inplace=True)
    foreshow_cum_netProfit_changeMin.drop(columns=foreshow_cum_netProfit_changeMin.columns[-1], inplace=True)

df_profitNoticeDate = pd.concat([foreshow_infoPublDate, df_profitNoticeDate], axis=1, join='outer', sort=True)
df_apubliDate = pd.concat([realized_infoPublDate, df_apubliDate], axis=1, join='outer', sort=True)
df_estimate_apubliDate = pd.concat([estimate_infoPublDate, df_estimate_apubliDate], axis=1, join='outer', sort=True)
df_profitNotice_netprofitMin = pd.concat([foreshow_cum_netProfitMin, df_profitNotice_netprofitMin], axis=1, join='outer', sort=True)
df_profitNotice_changeMin = pd.concat([foreshow_cum_netProfit_changeMin, df_profitNotice_changeMin], axis=1, join='outer', sort=True)

# 数据导出
df_profitNoticeDate.to_csv(outputPath + '业绩预告最新披露日期_wind.csv')
df_profitNotice_netprofitMin.to_csv(outputPath + '业绩预告净利润下限_wind.csv')
df_profitNotice_changeMin.to_csv(outputPath + '业绩预告净利润同比增长下限_wind.csv')
df_apubliDate.to_csv(outputPath + '季度报告披露时间_wind.csv')
df_estimate_apubliDate.to_csv(outputPath + '季度报告预计披露时间_wind.csv')

# ######################################################################################################################
