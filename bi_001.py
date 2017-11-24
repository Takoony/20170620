
#-*- coding: utf-8 -*-
#author nyang

import numpy as np
import pandas as pd
import talib
import datetime as dt
import tushare as ts
import matplotlib.pyplot as plt
from matplotlib.pylab import date2num
import matplotlib.finance as mpf
from enum import Enum


def plot_k_line(data):

    """
    data为dataframe格式，第一列为时间，第二到5列为ochl
    """
    import numpy as np
    import pandas as pd

    import datetime as dt
    import talib
    from matplotlib.pylab import date2num
    import matplotlib.pyplot as plt
    import matplotlib.finance as mpf
    def date_to_num(dates):
        num_time = []
        for date in dates:
            date_time = dt.datetime.strptime(date,'%Y-%m-%d')
            num_date = date2num(date_time)
            num_time.append(num_date)
        return num_time
    data['date']=date_to_num(data['date'])
    data=data.values
    #成交量
    fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(15,5))
    mpf.candlestick_ochl(ax1, data, width=1.0, colorup = 'g', colordown = 'r')
    ax1.set_title('nyang')
    ax1.set_ylabel('Price')
    ax1.grid(True)
    ax1.xaxis_date()
    plt.bar(data[:,0]-0.25, data[:,5], width= 0.5)
    ax2.set_ylabel('Volume')
    ax2.grid(True)
    plt.show()
class Trend(Enum):
    Down=1
    Up=2

def dealing_covers(high_series,low_series):
    """
    use czsc method calculate line
    data need contains h,l
    find valid k
    paras:high_sereis and low_series is ndarray
    """
    #dealing k
    #initialize
    pre_calculated=0
    rates_total=len(high_series)
    valid_high=high_series.copy()
    valid_low=low_series.copy()
    valid_k_line_mark=np.zeros(rates_total)
    """
    start point use up contains dealing
    """
    start_index=0
    pre_high=valid_high[start_index]
    pre_low=valid_low[start_index]
    pre_idx=start_index
    cur_idx=pre_idx
    is_found=False
    while(not is_found):
        cur_idx=cur_idx+1
        cur_high=valid_high[cur_idx]
        cur_low=valid_low[cur_idx]
        if (cur_high>pre_high and cur_low>pre_low)or (cur_high<pre_high and cur_low<pre_low):
            is_found=True
            valid_high[pre_idx]=pre_high
            valid_low[pre_idx]=pre_low
            valid_k_line_mark[pre_idx]=1
        else:
            if pre_high>cur_high:
               # first k cover second k
               pre_low=cur_low
            elif pre_high<cur_high:

                # first k be convered by second k
                pre_high=cur_high
                pre_idx=cur_idx
            else:
                # high value is equal
                pre_low=cur_low
                pre_idx=cur_idx

    # no start point dealing
    begin_idx=cur_idx+1
    for i in range(begin_idx,rates_total):
        post_high=valid_high[i]
        post_low=valid_low[i]
        post_idx=i
        #first classification: no contains
        if (cur_high>post_high and cur_low>post_low)or (cur_high<post_high and cur_low<post_low):
            valid_high[cur_idx]=cur_high
            valid_low[cur_idx]=cur_low
            valid_k_line_mark[cur_idx]=1
            pre_high=cur_high
            pre_low=cur_low
            pre_idx=cur_idx
            cur_high=post_high
            cur_low=post_low
            cur_idx=post_idx
        else:
            if pre_high<cur_high:#up contains
                if cur_high>post_high:
                    #post be coverd by cur
                    cur_low=post_low
                elif cur_high<post_high:
                    #post cover cur
                    cur_high=post_high
                    cur_idx=post_idx
                else:
                    #high be equal
                    if cur_low>post_low:
                        #cur be covered by post
                        cur_idx=post_idx
                    else:
                        #cur covers post
                        cur_low=post_low
            else:#down contains
                if cur_low>post_low:
                    #cur be covered by post
                    cur_low=post_low
                    cur_idx=post_idx
                elif cur_low<post_low:
                    #cur covers post
                    cur_high=post_high
                else:
                    # two low is equal
                    if cur_high>post_high:
                        cur_high=post_high
                    else:
                        cur_idx=post_idx
                        cur_high=post_high#I think the words can be deleted
    return valid_k_line_mark,valid_high,valid_low
def cal_bi_line(high_series,low_series):
    valid_mark,valid_high,valid_low=dealing_covers(high_series,low_series)
    need_k_num=8#顶底之间要求的k线数量
    new_valid_idx=0
    rates_total=len(valid_mark)
    new_valid_high=[]
    new_valid_low=[]
    true_idx=[]

    for i in xrange(0,len(valid_mark)):
        if valid_mark[i]==1:
            true_idx.append(i)
            new_valid_high.append(valid_high[i])
            new_valid_low.append(valid_low[i])
    first_valid=True
    valid_k_count=len(new_valid_high)
    bottom=np.zeros(valid_k_count)
    bottom_idx=0
    peak=np.zeros(valid_k_count)
    peak_idx=0
    trend=Trend.Up#值取1时为寻底，取2时寻顶
    for i in xrange(0,valid_k_count):
        pre_idx=i
        cur_idx=i+1
        next_idx=i+2
        if next_idx==valid_k_count:
            break
        if first_valid==True:#初始k线特殊处理
            if new_valid_high[cur_idx]>new_valid_high[next_idx]  and new_valid_high[cur_idx]>new_valid_high[pre_idx]:
                #形成顶分型
                bottom_idx=0
                bottom[bottom_idx]=2#2表示底部已经确定
                trend=Trend.Down
                peak_idx=cur_idx
                peak[peak_idx]=1#1表示该点暂未确定，可能为中继，可能为最终的顶底
                first_valid=False
                #print('bottom is sure,peak is unsure ')
            if new_valid_low[cur_idx]<new_valid_low[next_idx] and  new_valid_low[cur_idx]<new_valid_low[pre_idx]:
                #形成底分型
                peak_idx=0
                peak[peak_idx]=2
                trend=Trend.Up
                bottom_idx=cur_idx
                bottom[bottom_idx]=1
                first_valid=False
                #print('peak is sure,bottom is unsure')
        else:#非起点
            if trend==Trend.Down:

                if new_valid_high[cur_idx]>new_valid_high[next_idx] and new_valid_high[cur_idx]>new_valid_high[pre_idx]:
                    if new_valid_high[cur_idx]>new_valid_high[peak_idx]:
                        #当前新生成顶分型大于前高点
                        #print('新顶分型高点{0}，前顶分型高点{1}'.format(new_valid_high[cur_idx],new_valid_high[peak_idx]))
                        peak_idx=cur_idx
                        peak[peak_idx]=1
                        #print('顶分型创新高%d'%cur_idx)

                if new_valid_low[cur_idx]<new_valid_low[next_idx] and  new_valid_low[cur_idx]<new_valid_low[pre_idx]:
                    #print('-----》找到底分型当前索引%d'%cur_idx)
                    #print('-----》最近顶分型的索引%d'%peak_idx)
                    if cur_idx>peak_idx+need_k_num:
                        tmp=cur_idx-peak_idx
                        #print('----------->当前底分型与最近顶分型K线数量大于%d'%tmp)

                        if min(new_valid_low[cur_idx-4:cur_idx])>new_valid_low[cur_idx]:
                            #当前k线的低点是最近5根最低的
                            #print('当前k线的低点是最近5根最低的，当前索引%d'%cur_idx)
                            is_lowerest=0
                            index_lowerest=peak_idx+1
                            #寻找最低点的索引
                            for k in xrange(peak_idx+1,cur_idx+1):
                                if new_valid_low[k]< new_valid_low[index_lowerest]:
                                    index_lowerest=k
                                    #print('上一顶分型高点到当前索引的最低点索引%d'%index_lowerest)
                            if cur_idx!=index_lowerest:
                                highest_idx=index_lowerest+1
                                #寻找最高点的索引
                                for j in xrange(index_lowerest+1,cur_idx+1):
                                    if new_valid_high[j]>new_valid_high[highest_idx]:
                                        highest_idx=j
                                if cur_idx-highest_idx>3:
                                    peak[peak_idx]=2
                                    bottom[index_lowerest]=2
                                    peak[highest_idx]=1
                                    peak_idx=highest_idx
                                    bottom_idx=index_lowerest
                                    trend=Trend.Down
                                    cur_idx=highest_idx
                            else:
                                peak[peak_idx]=2
                                bottom_idx=cur_idx
                                bottom[bottom_idx]=1
                                trend=Trend.Up
                    else:
                        if new_valid_low[cur_idx]<new_valid_low[bottom_idx]:
                            #print('当前的底分型低于前低，但与最近的顶分型不足5根k线，当前索引%d'%cur_idx)

                            peak[peak_idx]=2
                            bottom_idx=cur_idx
                            bottom[bottom_idx]=1
                            trend=Trend.Up

            else:#趋势向下，寻顶
                if new_valid_low[cur_idx]<min(new_valid_low[cur_idx-1],new_valid_low[cur_idx+1]):
                    if new_valid_low[cur_idx]<new_valid_low[bottom_idx]:#创新低
                        bottom_idx=cur_idx
                        bottom[bottom_idx]=1
                if new_valid_high[cur_idx]>max(new_valid_high[cur_idx-1],new_valid_high[cur_idx+1]):
                    if cur_idx>bottom_idx+need_k_num:
                        if new_valid_high[cur_idx]>max(new_valid_high[cur_idx-4:cur_idx]):
                            is_highest=0
                            index_highest=bottom_idx+1
                            for k in xrange(bottom_idx+1,cur_idx+1):
                                if new_valid_low[k]>new_valid_low[index_highest]:
                                    index_highest=k
                            if cur_idx!=index_highest:
                                lowest_idx=index_highest+1
                                for k in xrange(index_highest+1,cur_idx+1):
                                    if new_valid_low[k]<new_valid_low[lowest_idx]:
                                        lowest_idx=k
                                if cur_idx>lowest_idx+3:
                                    bottom[bottom_idx]=2
                                    peak_idx=index_highest
                                    peak[peak_idx]=2
                                    bottom_idx=lowest_idx
                                    bottom[bottom_idx]=1
                                    trend=Trend.Up
                                    cur_idx=bottom_idx
                            else:
                                bottom[bottom_idx]=2
                                peak_idx=index_highest
                                cur_idx=index_highest
                                peak[peak_idx]=1
                                trend=Trend.Down
                    else:
                        if new_valid_high[cur_idx]>new_valid_high[peak_idx]:
                            bottom[bottom_idx]=2
                            peak_idx=cur_idx
                            peak[peak_idx]=1
                            trend=Trend.Down

    true_peak=np.zeros(len(valid_high))
    true_bottom=np.zeros(len(valid_high))
    last_peak_idx=0
    last_bottom_idx=0
    for i in xrange(len(peak)):
        if peak[i]==2:
            true_peak[true_idx[i]]=2
        if bottom[i]==2:
            true_bottom[true_idx[i]]=2
        if peak[i]==1:
            last_peak_idx=i
        if bottom[i]==1:
            last_bottom_idx=i

    if last_peak_idx>last_bottom_idx:
        idx=true_idx[last_peak_idx]
        idx_max=high_series[idx:len(high_series)].argmax()+idx
        if high_series[idx_max]>high_series[idx]:
            true_peak[idx_max]=2
        else:
            true_peak[idx]=2
            true_bottom[low_series[idx:len(low_series)].argmin()+idx]=2
    else:
        idx=true_idx[last_bottom_idx]
        idx_min=low_series[idx:len(low_series)].argmin()+idx
        if low_series[idx_min]<low_series[idx]:
            true_bottom[idx_min]=2
        else:
            true_bottom[idx]=2
            true_peak[high_series[idx:len(high_series)].argmax()+idx]=2


    return true_peak,true_bottom


code='600446'
begin='2014-01-11'
over='2017-11-20'

data=ts.get_k_data(code,start=begin,end=over)
data.reset_index(drop=True,inplace=True)
peak,bottom=cal_bi_line(data['high'].values,data['low'].values)
data['peak']=peak;data['bottom']=bottom
#plot_k_line(data)
print(data[['peak','bottom']])


def date_to_num(dates):
    num_time = []
    for date in dates:
        date_time = dt.datetime.strptime(date,'%Y-%m-%d')
        num_date = date2num(date_time)
        num_time.append(num_date)
    return num_time

new_line=[]
for i in xrange(len(data)):
    if data.ix[i,'peak']>0:
        new_line.append(data.ix[i,'high'])
    elif data.ix[i,'bottom']>0:
        new_line.append(data.ix[i,'low'])
    else:
        new_line.append(0)

data['bi']=new_line
valid_bi_data=data[data['bi']>0]
valid_bi_data['date']=date_to_num(valid_bi_data['date'])
valid_bi_data.index=valid_bi_data['date']
data['date']=date_to_num(data['date'])
data=data.values
fig,ax1= plt.subplots(1,  figsize=(15,5))
mpf.candlestick_ochl(ax1, data, width=1.0, colorup = 'g', colordown = 'r')

valid_bi_data['bi'].plot(ax=ax1)
ax1.set_title(code)
ax1.set_ylabel('Price')
ax1.grid(True)
ax1.xaxis_date()
plt.show()







