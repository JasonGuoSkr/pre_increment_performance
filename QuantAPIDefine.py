# -*- coding:utf-8 -*-

from ctypes import (Structure, Union, c_char, c_byte, c_bool, c_short, c_ushort, c_wchar_p, c_int, c_uint, c_longlong, c_ulonglong, c_float, c_double,c_void_p, POINTER, pointer, WinDLL,CDLL, byref,CFUNCTYPE, WINFUNCTYPE )
import pandas as pd
import numpy as np
import win32api
import sys
if sys.version_info < (3, 0):
    import _winreg as winreg
else:
    import winreg
import platform
import os
import pythoncom # necessary for proper function of the dll

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

#encode_type = "Unicode"
pragma_pack = 4  # 设置字节对齐
null_double = -1e+308
null_float = -3e+38

#错误信息码
GLERROR_SUCCESS          = 0    #成功

GLERROR_BASE_NOTLOGIN    = 2001 #帐户未登录

GLERROR_NULL_DATA        = 1001 #无有效数据
GLERROR_BASE_JSON        = 1010 # 服务器返回JSON无法解析
GLERROR_BASE_NOTSUCESS   = 1020 # 服务器返回 查询失败, 详细见日志
GLERROR_BASE_JSONERROR   = 1030 #服务器返回JSON内容错误

GLERR_NULL_PARAM         = 4001 #参数为空
GLERROR_BASE_INDICATOR   = 4002 #指标名称不存在
GLERROR_BASE_TRADINGDATE = 4003 #options 中少TradingDate参数!!
GLERROR_BASE_DATA        = 4004 #日期参数格式非法
GLERROR_BAXE_NOREPORTNAME= 4005 #无报表名

GLERROR_BASE_REPORTOPTION = 4008 # OPTION参数解析失败
GLERROR_BASE_PARAMERROR   = 4010 # indicator参数解析失败
GLERROR_BASE_CONDITION    = 4020 # condition参数解析失败
GLERROR_BASE_BASICDATA    = 4025 # 码表读取失败
GLERROR_BASE_VALUEFIELD   = 4030 #报表MAP中子查询子段名ValueField无法识别
GLERROR_BASE_GILCODE      = 4035 #无法识别的聚源代码


GLERROR_HTTP_POST = 3001# HTTPPOST失败

def is_valid_double(value_double):
    return value_double > null_double

def is_valid_float(value_float):
    return value_float > null_float

class GString(Structure):
    _pack_ = pragma_pack
    _fields_ = [("pString", c_wchar_p), ("nSize", c_int)]

class GStringArray(Structure):
    _pack_ = pragma_pack
    _fields_ = [("pGCharArray", POINTER(GString)), ("nSize", c_int)]

    def get_string(self, index):
        if index < self.nSize:
            return self.pGCharArray[index].pString  #.decode(encode_type)
        else:
            return None

(VT_null, VT_char, VT_byte, VT_bool, VT_short, VT_ushort, VT_int, VT_uInt, VT_int64, VT_uInt64, VT_float, VT_double, VT_byteArray, VT_unicodeString) = range(14)

class GValue(Union):
    _pack_ = pragma_pack
    _fields_ = [("charValue",c_char), ("byteValue", c_byte), ("boolValue", c_bool), ("shortValue", c_short),
                ("ushortValue", c_ushort),("intValue", c_int), ("uintValue", c_uint), ("int64Value", c_longlong),
                ("uint64Value", c_ulonglong), ("floatValue", c_float),("doubleValue", c_double)]

class GVariant(Structure):
    _pack_ = pragma_pack
    _fields_ = [("vtype", c_int), ("stringValue", GString), ("value", GValue)]

    def get_value(self):
        if self.vtype == VT_null:
            return np.nan
        elif self.vtype==VT_char:
            return self.value.charValue
        elif self.vtype == VT_byte:
            return self.value.byteValue
        elif self.vtype == VT_bool:
            return self.value.boolValue
        elif self.vtype == VT_short:
            return self.value.shorValue
        elif self.vtype == VT_ushort:
            return self.value.ushortValue
        elif self.vtype == VT_int:
            return self.value.intValue
        elif self.vtype == VT_uInt:
            return self.value.uintValue
        elif self.vtype == VT_int64:
            return self.value.int64Value
        elif self.vtype == VT_uInt64:
            return self.value.uint64Value
        elif self.vtype == VT_float:
            result = self.value.doubleValue
            if is_valid_float(result):
                return round(result, 6)
            else:
                return np.nan
        elif self.vtype == VT_double:
            result = self.value.doubleValue
            if is_valid_double(result):
                return round(result, 6)
            else:
                return np.nan
        elif self.vtype == VT_byteArray:
            return np.nan
        elif self.vtype == VT_unicodeString:
            str = self.stringValue.pString
            if str is None:
                str = ''
            return str
        else:
            return np.nan

    def __repr__(self):
        return str(self.get_value())


class GVariantArray(Structure):
    _pack_ = pragma_pack
    _fields_ = [("pVariant", POINTER(GVariant)), ("nSize", c_int)]

    def __str__(self):
        result = []
        for index in range(self.nSize):
            result.extend(self.pVariant[index])
        return str(result)

class GData(Structure):
    _pack_ = pragma_pack
    _fields_ = [("codeArray", GStringArray), ("indicatorArray",GStringArray), ("dateArray",GStringArray), ("valueArray", GVariantArray)]

    def get_value(self, codeIndex, indicatorIndex, dateIndex):
        #对于实时行情， 没有日期。 self.dateArray.nSize==0
        if (self.valueArray.nSize <=0) or ((self.dateArray.nSize>0) and (self.valueArray.nSize !=  self.codeArray.nSize * self.indicatorArray.nSize * self.dateArray.nSize)) :
            return None

        if (codeIndex < self.codeArray.nSize) and (indicatorIndex < self.indicatorArray.nSize) and((self.dateArray.nSize ==0) or (dateIndex < self.dateArray.nSize)):
            if self.dateArray.nSize ==0 :
                index = codeIndex * self.indicatorArray.nSize + indicatorIndex
            else:
                index = self.indicatorArray.nSize * self.dateArray.nSize * codeIndex + self.indicatorArray.nSize * dateIndex + indicatorIndex
            result = self.valueArray.pVariant[index]
            return result
        else:
            return None

    def get_2value(self, indicatorIndex, RowIndex):
        if (self.valueArray.nSize <=0) or (self.indicatorArray.nSize <=0 ) or (self.valueArray.nSize % self.indicatorArray.nSize != 0):
            return None

        index = self.indicatorArray.nSize * RowIndex + indicatorIndex
        result = self.valueArray.pVariant[index]
        return result

    def __repr__(self):
        result = ""
        dateSize=self.dateArray.nSize
        if (dateSize == 0) : #对于实时行情self.dateArray.nSize==0
            dateSize = 1
        for code in range(self.codeArray.nSize):
            for date in range(dateSize):
                result +="code: %s date: %s \t" % (self.codeArray.get_string(code), self.dateArray.get_string(date))
                for indicator in range(self.indicatorArray.nSize):
                    result += "%s: %s \t" % (self.indicatorArray.get_string(indicator) , str(self.get_value(code, indicator, date)) )
                result +="\n"
        return result

#实时行情回调函数
c_DataCallback= CFUNCTYPE(c_int, c_int, POINTER(GData))
#回调函数字典
QUAN_FUNCTIONS_DICT= {}
QUAN_PANDAS_DICT={}

def quan_callback_func(reqid, pdata):
    callback = QUAN_FUNCTIONS_DICT.get(reqid, None)
    if callable(callback):
        data=pdata.contents
        args=QUAN_PANDAS_DICT.get(reqid, None)
        if not (args != None and "ISPANDAS" in args[1] and args[1]["ISPANDAS"] == "1"):
            callback(reqid, data)
            return 0
        else:
            code_list = []
            data_list = []
            indictor_list = ["CODES"]
            for ind in range(data.indicatorArray.nSize):
                data_list.append([])
                indictor_list.extend([data.indicatorArray.get_string(ind)])

            for code_index in range(0, data.codeArray.nSize):
                code =data.codeArray.get_string(code_index)
                code_list.append(code)
                for cIndex in range(0, data.indicatorArray.nSize):
                    item=data.get_value(code_index,cIndex,1).get_value()
                    data_list[cIndex].append(item)

            data_list.insert(0, code_list)
            table = pd.DataFrame(data_list, indictor_list)
            table = table.T
            table = table.sort_values(by=["CODES"]).set_index(["CODES"])
            with pd.option_context('display.float_format', lambda x: '%.3f' % x):
                callback(reqid, table)
            return 0

quan_callback= c_DataCallback(quan_callback_func)

def gmc_callback_func(reqid, pdata):
    print('gmc call back reqid{0}'.format(reqid))
    callback = QUAN_FUNCTIONS_DICT.get(reqid, None)
    if callable(callback):
        data=pdata.contents
        args=QUAN_PANDAS_DICT.get(reqid, None)
        if not (args != None and "ISPANDAS" in args[1] and args[1]["ISPANDAS"] == "1"):
            callback(reqid, data)
            return 0
        else:
            code_list = []
            date_list = []
            data_list = []

            #生成指标列表
            indictor_list = ["CODES", "DATES"]
            for ind in range(data.indicatorArray.nSize):
                indictor_list.extend([data.indicatorArray.get_string(ind)])

            for code_index in range(0, data.codeArray.nSize):
                code =data.codeArray.get_string(code_index)

                for j in range(data.dateArray.nSize):
                    date_list.append(data.dateArray.get_string(j))
                    code_list.append(code)

                for j in range(data.indicatorArray.nSize):
                    tempData = []
                    for k in range(data.dateArray.nSize):
                        tempData.append(data.get_value(code_index, j, k).get_value())

                    data_list.append(tempData)


            data_list.insert(0, date_list)
            data_list.insert(0, code_list)
            table = pd.DataFrame(data_list, indictor_list)

            table = table.T
            table = table.sort_values(by=["CODES", "DATES"]).set_index(["CODES"])

            for i in range(data.indicatorArray.nSize):
                a = table.iloc[0, 1 + i]
                if isinstance(a, float) or pd.isnull(a):
                    table[indictor_list[2 + i]] = table[indictor_list[2 + i]].astype(np.float64)

            with pd.option_context('display.float_format', lambda x: '%.3f' % x):
                callback(reqid, table)
            return 0

gmc_callback=  c_DataCallback(gmc_callback_func)

class QuantAPI(object):
    def __init__(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\GilData")

        path, type = winreg.QueryValueEx(key, "QuantPath")
        if path == '':
            print('注册表中QuantPath路径丢失，请先使用auth.exe登录!!')
        else:
            arch = platform.architecture()
            if arch[0] == '64bit':
                path += 'win64\\'
            else:
                path += 'win32\\'

            path = str(path)

            self.__dll = WinDLL(path + "QuantAPI.dll")

            self.__gsd = self.__dll.gsd
            self.__gsd.restype = c_int
            self.__gsd.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            self.__gss = self.__dll.gss
            self.__gss.restype = c_int
            self.__gss.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            self.__gset = self.__dll.gset
            self.__gset.restype = c_int
            self.__gset.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            self.__gsq=self.__dll.gsq
            self.__gsq.restype= c_int
            self.__gsq.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_DataCallback, POINTER(c_int)]

            self.__gsqsnapshot=self.__dll.gsqsnapshot
            self.__gsqsnapshot.restype= c_int
            self.__gsqsnapshot.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_DataCallback, POINTER(c_int)]

            self.__gsqcancel = self.__dll.gsqcancel
            self.__gsqcancel.restype = c_int
            self.__gsqcancel.argtypes = [c_int]

            self.__gedb = self.__dll.gedb
            self.__gedb.restype = c_int
            self.__gedb.argtypes = [c_wchar_p, c_wchar_p, c_void_p]

            self.__geqs = self.__dll.geqs
            self.__geqs.restype = c_int
            self.__geqs.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            # 日期序列函数：gtradedates
            self.__gtradedates = self.__dll.gtradedates
            self.__gtradedates.restype = c_int
            self.__gtradedates.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            # 日期偏移函数
            self.__gdatesoffset = self.__dll.gdatesoffset
            self.__gdatesoffset.restype = c_int
            self.__gdatesoffset.argtypes = [c_wchar_p, c_int, c_wchar_p, c_void_p]

            # 交易日统计函数：gdayscount
            self.__gdayscount = self.__dll.gdayscount
            self.__gdayscount.restype = c_int
            self.__gdayscount.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            # 板块函数：gcomponents
            self.__gcomponents = self.__dll.gcomponents
            self.__gcomponents.restype = c_int
            self.__gcomponents.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            # //历史分钟 k 线：ghmc
            self.__ghmc = self.__dll.ghmc
            self.__ghmc.restype = c_int
            self.__ghmc.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_void_p]

            # //实时分钟 k 线：gmc
            self.__gmc = self.__dll.gmc
            self.__gmc.restype = c_int
            self.__gmc.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, POINTER(c_int), c_DataCallback]


            self.Codes = []
            self.Indicators = []
            self.Dates = []
            # self.Datas = []
            self.Data = dict()

            self.__functions_dict = {}

            self.__setlanguage = self.__dll.setlanguage
            self.__setlanguage.argtypes = [c_wchar_p]

            self.__stop = self.__dll.stop
            self.__releasedata = self.__dll.ReleaseData
            self.__releasedata.argtypes = [c_void_p]

            self.__setlanguage(c_wchar_p('python'))

    def __del__(self):
        self.__stop()
        win32api.FreeLibrary(self.__dll._handle) 

    def __clear(self):
        self.Codes=[]
        self.Indicators=[]
        self.Dates= []
        self.Data.clear()
        # self.Datas.clear()

    def __resolve3RankData(self, indicatorData, **arga):

        for i in range(indicatorData.codeArray.nSize):
            self.Codes.append(indicatorData.codeArray.get_string(i))

        for k in range(indicatorData.indicatorArray.nSize):
            self.Indicators.append(indicatorData.indicatorArray.get_string(k))

        for j in range(indicatorData.dateArray.nSize):
            self.Dates.append(indicatorData.dateArray.get_string(j))

        for i in range(len(self.Codes)):
            stockCode = self.Codes[i]
            self.Data[stockCode] = []

            for j in range(len(self.Indicators)):
                tempData = []
                for k in range(len(self.Dates)):
                    tempData.append(indicatorData.get_value(i, j, k).get_value())
                self.Data[stockCode].append(tempData)

    def __resolveReportData(self, indicatorData, **arga):
        """
        二维数据导出
        :param indicatorData:
        :param arga:
        :return:
        """
        for k in range(indicatorData.indicatorArray.nSize):
            self.Indicators.append(indicatorData.indicatorArray.get_string(k))

        Lrowcount = indicatorData.valueArray.nSize // indicatorData.indicatorArray.nSize

        for r in range(Lrowcount):
            listl =[]
            for n in range(indicatorData.indicatorArray.nSize):
                listl.append(indicatorData.get_2value(n, r).get_value())
            self.Data[str(r)] = listl

    @staticmethod
    def __resolveOption(arg=""):
        # Ispandas=1，RowIndex=1   范围0--1，缺省值：0， 非pandas格式：0   pandas格式：1
        result_list = []
        pdDict = {}
        up_str = arg.upper()
        pos = up_str.find("ISPANDAS")
        if (pos >= 0):
            item = up_str[pos:pos + 10]
            pdDict["ISPANDAS"] = item[9:10]
            arg = arg[0:pos] + arg[pos + 10:]
        else:
            pdDict["ISPANDAS"] = "0"
        up_str = arg.upper()
        pos = up_str.find("ROWINDEX")
        if (pos >= 0):
            item = up_str[pos:pos + 10]
            pdDict[item[0:8]] = item[9:10]
            arg = arg[0:pos] + arg[pos + 10:]
        else:
            pdDict["ROWINDEX"] = "1"
        result_list.append(arg)
        result_list.append(pdDict)
        return result_list


    def __tryResolvePandas(self, args={}, fun_name=None):

        if not (args != None and "ISPANDAS" in args[1] and args[1]["ISPANDAS"] == "1"):
            return self.Data

        code_list = []
        date_list = []
        data_list = []

        indictor_list = ["CODES", "DATES"]
        indictor_list.extend(self.Indicators)

        for ind in self.Indicators:
            data_list.append([])


        for code_index in range(0, len(self.Codes)):
            code = self.Codes[code_index]
            date_list.extend(self.Dates)
            for nIndex in range(0, len(self.Dates)):
                code_list.append(code)
            for cIndex in range(0, len(self.Data[code])):
                data_list[cIndex].extend(self.Data[code][cIndex])

        data_list.insert(0, date_list)
        data_list.insert(0, code_list)
        table = pd.DataFrame(data_list, indictor_list)

        table = table.T
        table = table.sort_values(by=["CODES", "DATES"]).set_index(["CODES"])

        for i in range(0, len(self.Indicators)):
          a = table.iloc[0, 1 + i]
          if isinstance(a, float) or pd.isnull(a):
              table[self.Indicators[i]] = table[self.Indicators[i]].astype(np.float64)

        return table

    #将二维表转换成Pandas DateFrame
    def __tryResolvePandas_2(self, indicatorData, hascode, args={}):


        #先设置好列名
        data_list = []
        LCodes = []
        indictor_list = []

        if hascode == 1 :
            indictor_list.append("code")


        for k in range(indicatorData.indicatorArray.nSize):
            indictor_list.append(indicatorData.indicatorArray.get_string(k))
            data_list.append([])

        Lrowcount = indicatorData.valueArray.nSize // indicatorData.indicatorArray.nSize

        for n in range(indicatorData.indicatorArray.nSize):
            listCol =[]
            for r in range(Lrowcount):
                listCol.append(indicatorData.get_2value(n, r).get_value())
                if hascode == 1 or r == 0:
                    LCodes.append(indicatorData.codeArray.get_string(r))

            data_list[n].extend(listCol)

        if hascode == 1:
            data_list.insert(0, LCodes)


        table = pd.DataFrame(data_list, indictor_list)

        table = table.T

        for i in range(0, len(indictor_list)):
          a = table.iloc[0, i]
          if isinstance(a, float) or pd.isnull(a):
              table[indictor_list[i]] = table[indictor_list[i]].astype(np.float64)

        return table

    def gsq(self, secucode, indicator, option, callback):
        """
            获取实时行情数据
        Parameters
        ------
            codes:string
                股票代码 e.g. '600570SH,000002.SZ'
            indicators:string
                指标代码 e.g. '

            options : string,
                其它参数 e.g. 'ISPANDAS=1'
                ISPANDAS   输出格式   0:非PANDAS  1：PANDAS
         return 请求
         -------
        """
        global  QUAN_FUNCTIONS_DICT
        global QUAN_FUNCTIONS_DICT
        global quan_callback
        error_no=c_int(0)
        reqId= self.__gsq(c_wchar_p(secucode), c_wchar_p(indicator), c_wchar_p(option), quan_callback, byref(error_no))
        QUAN_FUNCTIONS_DICT[reqId] =callback
        QUAN_PANDAS_DICT[reqId]=self.__resolveOption(option)
        return (reqId, error_no.value)

    def gsqsnapshot(self, secucode , indicator, option, callback):
        """
            获取行情快照数据
        Parameters
        ------
            secucode:string
                股票代码 e.g. '600570SH,000002.SZ'
            indicator:string
                指标代码 e.g. '

            option : string,
                其它参数 e.g. 'ISPANDAS=1'
                ISPANDAS   输出格式   0:非PANDAS  1：PANDAS
         return 请求
         -------
        """
        global quan_callback
        global QUAN_FUNCTIONS_DICT
        global QUAN_PANDAS_DICT
        error_no = c_int(0)
        reqId= self.__gsqsnapshot(c_wchar_p(secucode), c_wchar_p(indicator), c_wchar_p(option), quan_callback, byref(error_no))
        QUAN_FUNCTIONS_DICT[reqId] =callback
        QUAN_PANDAS_DICT[reqId]=self.__resolveOption(option)
        return (reqId, error_no.value)

    def gsqcancel(self, reqid):
        self.__gsqcancel(reqid)

    def gsd(self, secucode, indicator, startdate, enddate, option):
        """
            获取行情序列数据
        Parameters
        ------
            secucode:string
                股票代码 e.g. '600570SH,000002.SZ'
            indicator:string
                指标代码 e.g. 'SeqClosePrice,SeqRiseAndFall,SeqTurnoverValue'
            startdate : string,
                开始日期e.g. '2018-05-04'
            enddate : string,
                线束日期e.g. '2018-05-06'

            option : string,
                其它参数 e.g. 'TimePeriod=0,Complex=1,ISPANDAS=1'
                TimePeriod 时间周期   0:日 1：周 2：月 3：年
                Complex    复权方式   0：不复权 1：前复权 2：后复权
                ISPANDAS   输出格式   0:非PANDAS  1：PANDAS
         return
         -------
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gsd(c_wchar_p(secucode), c_wchar_p(indicator), c_wchar_p(startdate), c_wchar_p(enddate),
                               c_wchar_p(option), ref_result)
        if (self.errorinfo == 0):
            self.__clear()
            self.__resolve3RankData(ref_result._obj.contents)
            self.__releasedata(ref_result)

            return self.__tryResolvePandas(self.__resolveOption(option))
        else:
            print(self.errorinfo)
            return None;


    def gss(self, secucode,indicator, option):
        """
        :param codes : string  代码列表        如: '600570SH,000002.SZ'
        :param indicators: string 指标名称列表  如：'S_DQ_HIGH,S_DQ_OPEN'

        :param options    : string 其它参数,如: 'TradingDate=2018-07-18,Complex=0'
                                                TradingDate 交易日
                                                Complex 表示复权 0：不复权 1：前复权 2：后复权
        :return: 操作结果 各个指标函数的值，None 表示失败 其它值请参见手册
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gss(c_wchar_p(secucode), c_wchar_p(indicator), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            # self.__clear()
            #
            # self.__resolve3RankData(ref_result._obj.contents)
            # self.__releasedata(ref_result)
            #
            # return self.__tryResolvePandas(self.__resolveOption(option))
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 1, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;

    def gset(self,gestName,indicator,option):
        """
        :param gestName:聚源专题报表名称，详细见聚源指标手册
        :param indicator:指标名称列表 传空或匹配不到时展示报表全部字段
        :param option:   报表参数明细，详见聚源指标手册
        :return:操作结果 各个指标函数的值，None 表示失败 其它值请参见手册
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gset(c_wchar_p(gestName), c_wchar_p(indicator), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;

    def gedb(self,gedbids,option):
        """
        :param gedbids:宏观ID编码，详细见聚源指标手册
        :param option:   报表参数明细，详见聚源指标手册
        :return:操作结果 各个指标函数的值，None 表示失败 其它值请参见手册
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gedb(c_wchar_p(gedbids), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;

    def geqs(self, code ,indicator , condition, option):
        """
        :param code : string  代码列表        如: '[1101001]'
        :param indicator: string 指标名称列表  如：'#1,S_DQ_OPEN,TradingDate=2018-09-25,Complex=0;#2,S_DQ_OPEN,TradingDate=2018-09-25,Complex=0'

        :param condition : string 其它参数,如: '#1>53 and #2 < 56'

        :return: 操作结果 各个指标函数的值，None 表示失败 其它值请参见手册
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__geqs(c_wchar_p(code), c_wchar_p(indicator), c_wchar_p(condition), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()

            self.__resolve3RankData(ref_result._obj.contents)
            self.__releasedata(ref_result)

            return self.__tryResolvePandas(self.__resolveOption(option))
        else:
            print(self.errorinfo)
            return None;

    def gtradedates(self, startdate, enddate, option):
        """
        :param startdate: 起始日期
        :param enddate:   截止日期
        :param option:   可选参数，详见聚源指标手册
        :return:操作结果   日期序列
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gtradedates(c_wchar_p(startdate), c_wchar_p(enddate), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;

    def gdatesoffset(self, TradingDate, offday, option):
        """
        :param TradingDate: 起始日期
        :param offday:      偏移天数
        :param option:   可选参数，详见聚源指标手册
        :return:操作结果   交易日期
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gdatesoffset(c_wchar_p(TradingDate), c_int(offday), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data

            return self.Data
        else:
            print(self.errorinfo)
            return None;

    def gdayscount(self, startdate, enddate, option):
        """
        :param tradingdate: 起始日期
        :param enddate:     截止日期
        :param option:   可选参数，详见聚源指标手册
        :return:操作结果   返回交易天数.
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gdayscount(c_wchar_p(startdate), c_wchar_p(enddate), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;

    def __NeedDataFrame(self, option):
        args = self.__resolveOption(option)
        return "ISPANDAS" in args[1] and args[1]["ISPANDAS"] == "1"

    def gcomponents(self, SectorNums, TradingDate, option):
        """
        :param SectorNums: 板块ID
        :param TradingDate:截止日期
        :param option:   可选参数，详见聚源指标手册
        :return:操作结果   返回交易天数.
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__gcomponents(c_wchar_p(SectorNums), c_wchar_p(TradingDate), c_wchar_p(option), ref_result)
        if (self.errorinfo == 0) :
            self.__clear()
            if self.__NeedDataFrame(option):
                df = self.__tryResolvePandas_2(ref_result._obj.contents, 0, self.__resolveOption(option))
            else:
                self.__resolveReportData(ref_result._obj.contents)

            self.__releasedata(ref_result)

            if self.__NeedDataFrame(option):
                return df
            else:
                return self.Data
        else:
            print(self.errorinfo)
            return None;


    def ghmc(self, secucode, indicators, startdate, enddate, option):
        """
        :param secucode : string  代码        如: '600570.SH'
        :param indicators 指标
        :param startdate: 起始日期
        :param enddate:截止日期
        :param option:   可选参数，详见聚源指标手册
        :return:操作结果 各个指标函数的值，None 表示失败 其它值请参见手册
        """
        result = GData()
        ref_result = byref(pointer(result))
        self.errorinfo = self.__ghmc(c_wchar_p(secucode), c_wchar_p(indicators), c_wchar_p(startdate),c_wchar_p(enddate),c_wchar_p(option), ref_result)
        if (self.errorinfo == 0):
            self.__clear()
            self.__resolve3RankData(ref_result._obj.contents)
            self.__releasedata(ref_result)

            return self.__tryResolvePandas(self.__resolveOption(option))
        else:
            print(self.errorinfo)
            return None;

        #######

    def gmc(self, secucode, indicators, option, callback):
        """
           获取实时分钟K线数据

        :param secucode : string  代码        如: '600570.SH'
        :param indicators:指标
        :param option:   可选参数，详见聚源指标手册
        :param callback 接收结果 回调函数
        :return:操作结果 各个指标函数的值，None 表示失败 其它值请参见手册

        """
        global quan_callback
        global QUAN_FUNCTIONS_DICT
        global QUAN_PANDAS_DICT
        error_no = c_int(0)
        reqId= self.__gmc(c_wchar_p(secucode), c_wchar_p(indicators), c_wchar_p(option), byref(error_no), gmc_callback)
        QUAN_FUNCTIONS_DICT[reqId] =callback
        QUAN_PANDAS_DICT[reqId]=self.__resolveOption(option)
        return (reqId, error_no.value)