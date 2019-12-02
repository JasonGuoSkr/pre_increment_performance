
# ######################################################################################################################

"""
获取上市公司财务数据，归母净利润
"""

import os
import pandas as pd
import numpy as np
import datetime
import time
from WindPy import *
from QuantAPIDefine import QuantAPI

w.start()
g = QuantAPI()


# 文件路径
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/数据/"
if not os.path.exists(outputPath):
    os.makedirs(outputPath)
    print(outputPath + '创建成功')

start_date = "2009-01-01"
end_date = "2019-09-30"

# 取全A股票代码
# date_now = datetime.now().strftime('%Y-%m-%d')
date_now = '2019-11-20'

indexComponent_wind = w.wset("sectorconstituent", "date=" + date_now + ";sectorid=a001010100000000")
indexComponent_list = indexComponent_wind.Data[1]
indexComponent_str = ','.join(indexComponent_list)


# 季度日历日期
quarterlyDate_wind = w.tdays(start_date, end_date, "Days=Alldays;Period=Q")
quarterlyDate_list = quarterlyDate_wind.Data[0]

# 财务报告归母净利润
realized_cum_netProfit = pd.DataFrame(index=indexComponent_list)

for quarterlyDate in quarterlyDate_list:
    quarterlyDate = quarterlyDate.strftime("%Y-%m-%d")

    # 归母净利润
    netProfit_dict = g.gss(indexComponent_str, 'S_E_IS_NPPARENT', 'ReportDate=' + quarterlyDate + ',ReportType=0')

    netProfit_df = pd.DataFrame(netProfit_dict).T
    netProfit_df.columns = [quarterlyDate]
    netProfit_df[quarterlyDate] = [ind[0] for ind in netProfit_df[quarterlyDate]]
    realized_cum_netProfit = realized_cum_netProfit.join(netProfit_df)

    print(quarterlyDate)

# 单季数据
realized_quarterly_netProfit = pd.DataFrame(index=realized_cum_netProfit.index, columns=realized_cum_netProfit.columns)

for ind in reversed(range(len(realized_quarterly_netProfit.columns))):
    monthIndex = quarterlyDate_list[ind].month
    columnIndex = realized_quarterly_netProfit.columns[ind]

    if monthIndex in [6, 9, 12]:
        pre_columnIndex = realized_quarterly_netProfit.columns[ind - 1]
        realized_quarterly_netProfit[columnIndex] = realized_cum_netProfit[columnIndex] - \
            realized_cum_netProfit[pre_columnIndex]
    else:
        realized_quarterly_netProfit[columnIndex] = realized_cum_netProfit[columnIndex]

# 数据导出
realized_cum_netProfit.to_csv(outputPath + "财务报告累计净利润_聚源.csv")
realized_quarterly_netProfit.to_csv(outputPath + "季度报告净利润_聚源.csv")

# ######################################################################################################################
