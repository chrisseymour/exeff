# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 19:09:27 2019

ex/div date and dividend growth calculator

Enter the ticker symbol for a dividend growth company (e.g. JNJ, KMB, PEP)

@author: Chris
"""

from dividends import Puller
from historical_quote import GetHistoricalQuote
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

        
def HistoricalYieldOnCost(divs, prices, ticker, axis, output=False):
    '''plot the historical, forward yield on cost
    get this by multiplying the most recently announced div at the time by four
    then dividing by the share price at that time
    note: will not work for monthly div payers, 
        possible workaround is to check the number of divs they pay each year
    '''
    d = prices
    exp_yield = []
    
    ###check to see what dividend investors were expecting at each moment in the past
    for date in  d['Date']:  ###loop over each day we have a price for
        mdif = dt.timedelta(days=100)
        exdate = 0
        ###loop through possible dividend dates, to find the closest one, and the size of the div at that time
#        for x,amnt in zip(divs['Ex/Eff'], divs['Amount']):  
        for x,amnt in zip(divs['Declaration'], divs['Amount']):  
            '''loop to determine the dividend investors are expecting to recieve for the next year
            at the time of purchase'''
            
            dif = abs( date-x )
            #print( 'date {}, amnt {}, dif {}'.format(x, amnt, dif) )
            if dif < mdif:
                mdif = dif
                exdate = x
                amount = amnt
        try:
            exp_yield.append(amount)
        except:
            print('no "amount", does this cause incorrect behavior?')
            print('mdif {}, exdiv {}, date {}, dif {}'.format(mdif, exdate, date, dif) )
        if output:
            print('for {} the best Ex/Div-date  is {}: dif={}; div={}'.format(date, exdate, mdif, amount))
    
    
    exp_yield = np.array(exp_yield)
#    plt.plot(d['Date'], exp_yield, '.')  #test plot to verify correct div information
    
#    f,ax = plt.subplots( figsize=(11,6) ) #on desktop... figsize=(11,6)
    f, ax = axis
    ax.set_title( '{} Historical Expected Yield on Cost'.format( ticker.upper() ) )
    ax.set_xlabel('Date')
    ax.set_ylabel('Expected Yield (%)')
    ax.grid(True, axis='y')
    ax2 = ax.twinx()
    ax2.set_ylabel('Volume')

    ###green = stock price increases on the day, red = stock price decreased
    colors = np.empty( len(d['Date']) , dtype=str )
    for i,c in enumerate(colors):
        if d['Open'][i] > d['Close'][i]:
            colors[i] = 'r'
        else:
            colors[i] = 'g'
#    return exp_yield, d['Open'], d['Close']
    ######Expected YOC is 4*div at that time divided by the current trading price
    ###calculate the 'top' positions (i.e. the hieight) for each bar graph   
    tops = (4*exp_yield/d['Open']-4*exp_yield/d['Close'])*100
    bots = 4*exp_yield/d['Close']*100
    ### create the skinny "trading range" bars for the strip chart (yoc range in this case)
    mids = (4*exp_yield/d['High']-4*exp_yield/d['Low'])/2+(4*exp_yield/d['Low'])
    trading_ranges = (4*exp_yield/d['High']-4*exp_yield/d['Low'])/2
    mids *= 100
    trading_ranges *= 100
    
#    print(bots, mids, trading_ranges)
    ###plot the skiny YOC ranges
    ax.errorbar(d['Date'], mids, yerr=trading_ranges,
                linewidth=0.4, linestyle='', color='grey', alpha=0.55)
    ###plot the open/close YOC bars
    ax.bar(d['Date'], tops, bottom=bots, color=colors, alpha=0.65)#, align='edge')
    ###plot the volume bars, green for price increase, red for price decrease
    ax2.bar( d['Date'], d['Volume'] , color=colors, alpha=0.5)#, align='edge')
    
    ###adjust the y-limits, so the volume and YOC lines don't overlap
    ax.set_ylim( min(bots)/1.1, ax.get_ylim()[1] )
    ax2.set_ylim( 0, max(d['Volume'])*4.5 )
    
    f.autofmt_xdate()  ###datetime x-axis plotting
    plt.tight_layout()
    plt.savefig(f'historic_yield_{ticker}.pdf', encoding='pdf')
    plt.savefig(f'historic_yield_{ticker}.png')
    plt.show()
    
        
if __name__=='__main__':
    ticker = 'JNJ'  #e.g. JNJ, PEP, KMB, MMM
    
    P = Puller(ticker = ticker)
    P.ProcessRequest()
#    f,ax = plt.subplots( figsize=(11,6) )
    G = GetHistoricalQuote( ticker )
    f,lower_subplot = G.ProcessRequest(length = '6y') ###'6y' standard for typical NASDAQ div history
    res = HistoricalYieldOnCost(P.sorted, G.d, ticker=ticker, axis=(f,lower_subplot))
    