
# ######################################################################################################################
"""
股票交易流水
"""

import pandas as pd
import numpy as np
import datetime
import rqdatac as rq
from rqdatac import *
from QuantAPIDefine import QuantAPI

rq.init("ricequant", "8ricequant8", ('10.29.135.119', 16010))
g = QuantAPI()


def id_wind(code_list):
    code_return = list(range(len(code_list)))
    for ind in range(len(code_list)):
        if code_list[ind][0] == '6':
            code_return[ind] = code_list[ind][:6] + '.SH'
        else:
            code_return[ind] = code_list[ind][:6] + '.SZ'
    return code_return


# 参数
inputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_5/"
outputPath = "E:/中泰证券/策略/潜伏业绩预增策略/每日跟踪调整202002/结果_5/"

# 数据导入
df_code = pd.read_csv(inputPath + "汇总个股买卖时点.csv", index_col=0, engine='python')

start_date = "2020-01-01"
end_date = datetime.datetime.now().strftime('%Y-%m-%d')

# 交易日列表
list_trading = rq.get_trading_dates(start_date=start_date, end_date=end_date)

# 买入与卖出股票筛选
for date_ind in list_trading:
    date_str = date_ind.strftime('%Y-%m-%d')

    list_buy = df_code[df_code['buy_date'] == date_str]['code'].tolist()
    list_sell = df_code[df_code['sell_date'] == date_str]['code'].tolist()

    if list_buy:
        # 剔除ST、停牌及涨跌停股票
        list_st_index = is_st_stock(list_buy, date_str, date_str).T

        list_suspended_index = pd.DataFrame(index=list_buy)
        for codes in list_buy:
            try:
                suspended_index = is_suspended(codes, start_date=date_str, end_date=date_str)
            except ValueError:
                list_suspended_index.loc[codes, date_str] = True
            else:
                if suspended_index is not None:
                    list_suspended_index.loc[codes, date_str] = suspended_index.loc[date_str, codes]
                else:
                    list_suspended_index.loc[codes, date_str] = True

        list_price = get_price(list_buy, start_date=date_str, end_date=date_str, frequency='1d',
                               fields=['open', 'limit_up', 'limit_down'])
        list_open = list_price['open'].T
        list_up = list_price['limit_up'].T
        list_down = list_price['limit_down'].T

        list_maxupordown_index = (list_open == list_up) | (list_open == list_down)
        list_maxupordown_index.columns = list_suspended_index.columns
        # list_maxupordown = g.gss(','.join(id_wind(list_buy)), 'S_DQ_PTLIMIT', 'TradingDate=' + date_str)
        # list_maxupordown = pd.Series(list_maxupordown)
        # list_maxupordown = pd.Series([ind[0] for ind in list_maxupordown], list_buy)
        # list_maxupordown_index = list_maxupordown != ''
        # list_maxupordown_index = pd.DataFrame(list_maxupordown_index, columns=list_suspended_index.columns)

        list_st_index.columns = list_suspended_index.columns
        list_final_index = list_st_index + list_suspended_index + list_maxupordown_index
        list_code_filter = list_final_index[list_final_index.values == False].index.tolist()

        df_buy = pd.DataFrame({'code': list_code_filter, 'signal': np.ones(len(list_code_filter))})
    else:
        df_buy = pd.DataFrame()

    if list_sell:
        df_sell = pd.DataFrame({'code': list_sell, 'signal': np.zeros(len(list_sell))})
    else:
        df_sell = pd.DataFrame()

    df_trading = pd.concat([df_buy, df_sell], axis=0)

    if not df_trading.empty:
        df_trading.to_csv(outputPath + date_str + "_交易明细.csv")

    print(date_str)

# ######################################################################################################################
