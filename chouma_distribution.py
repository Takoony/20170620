
#-*- coding: utf-8 -*-
#author nyang

import numpy as np
import pandas as pd
import datetime as dt
import talib
import matplotlib.pyplot as plt
import tushare as ts
"""计算筹码分布算法"""
class ChouMA():
    @staticmethod
    def cal_chouma_distribution(data):
        #筹码分布算法
        '''先处理初始值'''
        _cost=[]
        _count=[]
        _cost.append(data.ix[0,'open'])
        _count.append(100)
        for idx in range(0,len(data)):
            pre_total_ratio=0.01*(100-data.ix[idx,'turnover_ratio'])
            _cost.append(data.ix[idx,'close'])
            _count=np.array(_count)
            _count=list(_count*pre_total_ratio)
            #_count=[v*pre_total_ratio for v in _count]
            _count.append(data.ix[idx,'turnover_ratio'])
        chouma=pd.DataFrame()
        chouma['close']=_cost
        chouma['count_ratio']=_count
        return chouma
    @staticmethod
    def cal_winner_ratio(code,date):
        '''
        step one :获取数据
        '''
        df = ts.get_stock_basics()
        begin_date = df.ix[code,'timeToMarket']
        begin_date=str(begin_date)
        begin_date=begin_date[0:4]+'-'+begin_date[4:6]+'-'+begin_date[6:8]
        over_date=date
        circulating_cap=df.ix[code]['outstanding']
        data=ts.get_k_data(code,start=begin_date,end=over_date)
        data.index=pd.to_datetime(data['date'])
        data.drop(['date'],axis=1,inplace=True)
        if len(data)>500:
            data=data[len(data)-500:len(data)]
        elif len(data)<200:
            return 10000
        need_date=data.index
        data['turnover_ratio']=data['volume']*0.0001/circulating_cap
        data=np.round(data,2)
        data['turnover_ratio'].fillna(0,inplace=True)
        '''
        step two:
        '''
        chouma=ChouMA.cal_chouma_distribution(data)
        chouma=chouma.sort(['close'],ascending=True)
        chouma.reset_index(inplace=True)
        chouma['cumsum_ratio']=chouma['count_ratio'].cumsum()
        threhold=data.ix[-1,'close']
        winner_ratio=chouma[chouma.close<threhold]
        if len(winner_ratio)==0:
            return 0.0
        return round(winner_ratio.ix[len(winner_ratio)-1,'cumsum_ratio'],3)
code='002008'
cur_date='2017-11-13'
all_stocks=ts.get_stock_basics()
all_stocks_code=all_stocks.index
for code in all_stocks_code:
    result=ChouMA.cal_winner_ratio(code,cur_date)
    if result<1.0:
        print('code:{0} winner_ratio:{1}'.format(code,result))
