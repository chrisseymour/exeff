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

        
def HistoricalYieldOnCost(divs, prices):
    '''plot the historical, forward yield on cost
    get this by multiplying the most recently announced div at the time by four
    then dividing by the share price at that time
    note: will not work for monthly div payers, 
        possible workaround is to check the number of divs they pay each year
    '''
#    print(divs)
#    print(prices)
    d = prices
    f,ax = plt.subplots( figsize=(11,6) )
    ax.set_title("Historical Yield on Cost")
#    print('date len', len(d["Date"]))
#    print('date len', len(divs['Ex/Eff']))

    for date in d['Date']:
        mdif = dt.timedelta(days=89)
        exdate = 0
        for x,amnt in zip(divs['Ex/Eff'], divs['Amount']):
            dif = abs( date-x )
            if dif < mdif:
                mdif = dif
                exdate = x
                amount = amnt
        print('for {} the best Ex/Div-date  is {}: dif={}; div={}'.format(date, exdate, mdif, amount))
            
    print('amnt', divs['Amount'])
#    for it in d.items():
#        print(it)
#    for items in d.items():
#        print(items)
#    ax.grid(True, axis='y')
#    ax2 = ax.twinx()
#    colors = np.empty( len(d['Date']) , dtype=str )
#        for i,c in enumerate(colors):
#            if d['Open'][i] > d['Close'][i]:
#                colors[i] = 'r'
#            else:
#                colors[i] = 'g'
#
#        ax.errorbar(d['Date'], (d['High']-d['Low'])/2+d['Low'], yerr=(d['High']-d['Low'])/2,
#                    linewidth=0.4, linestyle='', color='grey', alpha=0.55)
#        ax.bar(d['Date'], (d['Open']-d['Close']), bottom=d['Close'], color=colors, alpha=0.75)#, align='edge')
#        
#
#        ax2.bar( d['Date'], d['Volume'] , color=colors, alpha=0.6)#, align='edge')
##        ax2.bar( range(len(d['Date'])), d['Volume'] )
#        ax.set_ylim( min(d['Low'])/1.05, ax.get_ylim()[1] )
#        ax2.set_ylim( 0, max(d['Volume'])*4.5 )
##        print('max here', max(d['Volume']))
#        f.autofmt_xdate()
#        f.show()
        
if __name__=='__main__':
    ticker = 'JNJ'  #e.g. JNJ, PEP, KMB 
    G = GetHistoricalQuote( ticker )
    G.ProcessRequest(length = '6y')
    P = Puller(ticker = ticker)
    P.ProcessRequest()
    
    HistoricalYieldOnCost(P.sorted, G.d)
    