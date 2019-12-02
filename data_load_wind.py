# ######################################################################################################################
"""
数据下载
"""


import pandas as pd
from WindPy import *

w.start()


# 文件路径
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/结果20191021/数据/"
start_date = "2017-01-01"
end_date = "2019-09-30"

# 取全A股票代码
date_now = '2019-10-20'

indexComponent_wind = w.wset("sectorconstituent", "date=" + date_now + ";sectorid=a001010100000000")
indexComponent_list = indexComponent_wind.Data[1]
indexComponent_str = ','.join(indexComponent_list)

profitNoticeDate = w.wsd(indexComponent_str, "profitnotice_date", start_date, end_date, "Period=Q;Days=Alldays")
profitNotice_netprofitMin = w.wsd(indexComponent_str, "profitnotice_netprofitmin", start_date, end_date, "unit=1;Period=Q;Days=Alldays")
profitNotice_changeMin = w.wsd(indexComponent_str, "profitnotice_changemin", start_date, end_date, "unit=1;Period=Q;Days=Alldays")

df_profitNoticeDate = pd.DataFrame(profitNoticeDate.Data, index=profitNoticeDate.Codes, columns=profitNoticeDate.Times)
df_profitNotice_netprofitMin = pd.DataFrame(profitNotice_netprofitMin.Data, index=profitNotice_netprofitMin.Codes, columns=profitNotice_netprofitMin.Times)
df_profitNotice_changeMin = pd.DataFrame(profitNotice_changeMin.Data, index=profitNotice_changeMin.Codes, columns=profitNotice_changeMin.Times)

apubliDate = w.wsd(indexComponent_str, "stm_issuingdate", start_date, end_date, "Period=Q;Days=Alldays")
estimate_apubliDate = w.wsd(indexComponent_str, "stm_predict_issuingdate", start_date, end_date, "Period=Q;Days=Alldays")

df_apubliDate = pd.DataFrame(apubliDate.Data, index=apubliDate.Codes, columns=apubliDate.Times)
df_estimate_apubliDate = pd.DataFrame(estimate_apubliDate.Data, index=estimate_apubliDate.Codes, columns=estimate_apubliDate.Times)

# 数据导出
df_profitNoticeDate.to_csv(outputPath + '业绩预告最新披露日期_wind.csv')
df_profitNotice_netprofitMin.to_csv(outputPath + '业绩预告净利润下限_wind.csv')
df_profitNotice_changeMin.to_csv(outputPath + '业绩预告净利润同比增长下限_wind.csv')
df_apubliDate.to_csv(outputPath + '季度报告披露时间_wind.csv')
df_estimate_apubliDate.to_csv(outputPath + '季度报告预计披露时间_wind.csv')

# ######################################################################################################################
