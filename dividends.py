# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 16:57:55 2019

Web Scraping Example

ex/div date and dividend growth calculator
Enter: a ticker symbol (e.g. )

@author: Chris
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import leastsq
import collections as coll
import numpy as np
import datetime as dt
import requests

from bs4 import BeautifulSoup #parsing html

###avoid implicitly registered datetime converter warning
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
###

def second_site():
    financials = 'https://finance.yahoo.com/quote/PM/financials?p=PM'
    balance = 'https://finance.yahoo.com/quote/PM/balance-sheet?p=PM'
    cashflow = 'https://finance.yahoo.com/quote/PM/cash-flow?p=PM'
    history = 'https://finance.yahoo.com/quote/PM/history?p=PM'
    hist_period = 'https://finance.yahoo.com/quote/PM/history?period1=1205726400&period2=1561003200&interval=1d&filter=history&frequency=1d'
    options = 'https://finance.yahoo.com/quote/PM/options?p=PM'

class Puller(object):
    def __init__(self, ticker='pm'):
        self.points = np.array(0)
        #self.domain = 'http://www.apmex.com/'
        self.domain = 'https://www.nasdaq.com/symbol/'
        #dm2 = 'https://www.nyse.com/quote/XNYS:MMM'
#        d-button-normal d-button-dropdown
#        react-datepicker__input-container
#        react-datepicker__input-container
#        class="d-button-normal"
        self.ticker = ticker
        self.url = '{}/dividend-history'.format( ticker )
        
        
        
        
        self.div = [] #{}
        self.exdiv = {}
        
    def GetSite(self):
        url = self.url
        result = requests.get( ''.join( (self.domain, url) ) )
        self.soup = BeautifulSoup(result.content, "lxml")
        
#        productname = soup.title.text.split('|')[0]
#        print(productname)
        self.name = self.soup.find('div', {'id': 'qwidget_pageheader'})
        self.last_sale = self.soup.find('div', {'id': 'qwidget_lastsale'})
#        self.name = self.soup.find('div', {'class': 'quotebar-wrap'})
#        self.name = self.table.findChildren([ 'h1' ])
        
    def SplitTable( self ): 
        self.tableclassname = "quotes_content_left_dividendhistoryGrid"
        self.table = self.soup.find('table', {'id': self.tableclassname})
#        print(self.soup)
        self.table_text = str( self.table.text )
#        print(self.table_text)
        self.bs = self.table_text.split()
        self.href = self.table.findChildren([ 'href' ])
        self.headers = self.table.findChildren([ 'th' ])
        self.rows = self.table.findChildren([ 'tr' ])
#        self.loop_table()
#        prs = ( bs[:3], bs[6:11], bs[11:16], bs[16:] )
#        #for b in prices: print(b)
#        return productname, prs
        
    def GetDiv(self):
#        self.header_text = [rt.text.strip() for rt in self.headers]
        self.row_text = [rt.text.strip().split() for rt in self.rows]
        self.header_text = self.row_text.pop(0)
        self.header_text = ['Ex/Eff', 'Type', 'Amount',
            'Declaration', 'Record', 'Payment']
#        print( 'headers', self.header_text)
#        print( 'rows[0]', self.row_text[0])
        for rt in self.row_text:
            self.div.append( dict(zip( self.header_text, rt )) )

    def SortDividendTable(self):
        self.sorted = {}
        for h in self.header_text:
            # determine the type conversion based on the key
            if h=='Ex/Eff' or h=='Declaration':
                
                self.sorted[h] = [ d[h].split('/') for d in P.div ]
                
                for i,hnew in enumerate( self.sorted[h] ):
                    date = hnew[-1:]+hnew[:2]
                    if '--' in date:
                        date = self.sorted[h][i-1]
                        continue
#                        date = [d.replace('--', '1') for d in date]
#                    print('date', self.sorted[h][i-1], self.sorted[h][i+1])
#                    else:
                    date = [int(d) for d in date]
#                    print('date type', type(hnew))
                    self.sorted[h][i] = dt.datetime(*date)
#                    print('date type', type(hnew))
                    
                continue
            elif h == 'Amount':
                f = float  
            else:
                f = str
            # convert the type, and then
            #   create a dict entry consisting of each entry for that header
            self.sorted[h] = [f(d[h]) for d in P.div]

    def PlotDivHistory(self):
        f,ax = plt.subplots()
        ax.set_title(self.name.text)
#        print('type', type(self.sorted[ 'Ex/Eff']))
#        print(self.sorted[ 'Ex/Eff'])
        ax.plot_date( self.sorted[ 'Ex/Eff'], self.sorted[ 'Amount' ], label='Amount vs Ex/Eff Date' )
        
        self.FitDivHistory(ax)
        xs, ys = self.FindDivIncreases()
        ax2 = ax.twinx()
        ax2.plot(xs, ys, 'x', markersize=8, color='red', label='div increase percentage')
        ax2.set_ylabel('(%)')
        ylims = ax2.get_ylim()
        if ylims[0] > 0:
            ax2.set_ylim(0, ylims[1])
        print('last sale price {}'.format(P.last_sale.text))
        price = float(self.last_sale.text.replace('$',''))
        yoc = self.sorted[ 'Amount' ][0]*4/price*100
        print('current yield on cost = {:.4f}%'.format(yoc))
        #get yearly total numbers and number or div payments, then plot them
        self.GetYearlyDivs()
        yearkey = sorted( list( self.yearly.keys() ) )
        
        years = [dt.datetime(int(y), 12, 31) for y in yearkey] #convert year to datetime dec 31 of the year divs are added for
        yearval = [self.yearly[k][0] for k in yearkey]
        ax3 = ax.twinx()
        ax3.plot_date(years, yearval, '>', color='green', label='yearly dividend' )
        ax3.tick_params(axis='y', direction='in', pad=-20, labelcolor='green')
        ax3.set_ylabel('yearly div ($)', color='green', labelpad=-30)
#        ax.show()

    def FitDivHistory(self, ax):
        x = np.array( self.sorted[ 'Ex/Eff'] )
        x = mdates.date2num( x )
        y = np. array( self.sorted[ 'Amount' ] )
        funcLine=lambda tpl,x : tpl[0]*x+tpl[1]
#        funcQuad=lambda tpl,x : tpl[0]*x**2+tpl[1]*x+tpl[2]
        # func is going to be a placeholder for funcLine,funcQuad or whatever 
        # function we would like to fit
        func=funcLine
        # ErrorFunc is the diference between the func and the y "experimental" data
        ErrorFunc=lambda tpl,x,y: func(tpl,x)-y
        #tplInitial contains the "first guess" of the parameters 
        tplInitial1=(1.0,2.0)
        # leastsq finds the set of parameters in the tuple tpl that minimizes
        # ErrorFunc=yfit-yExperimental
        tplFinal1,success= leastsq(ErrorFunc,tplInitial1[:],args=(x,y))
        print (" linear fit ",tplFinal1)
#        xx1=np.linspace(x.min(),x.max(),50)
        yy1=func(tplFinal1,x)
        ax.plot(x, yy1)
    
    def FindDivIncreases(self):
        '''edit to find dividened cuts as well
        "FindDivChange()"
        '''
        x = np.array( self.sorted[ 'Ex/Eff'] )
        y = np.array( self.sorted[ 'Amount' ] )
        for X,Y in zip( reversed(x), reversed(y) ):
            print("{} on {}".format(Y,  X.strftime("%B %d, %Y")))
#        xdif = x[:-1] - x[1:]
        ydif = y[:-1] - y[1:]
#        print('ydif', ydif)
#        xy = zip(x,y)
#        print('xy', xy)
        inc_dates = []
        inc_amnts = []
        for i,x1,y1, ye in zip(np.arange(len(x)),x,y,ydif):
#            print(i, x1, y1, ydif)
            
            if ye != 0:
                increase = ye/y[i+1]*100
                print('div increase of ${:.4f}, from ${} to ${}. An increase of {:.2f}%, on {}'.format(ye, y[i+1], y[i], increase , x[i].strftime("%B %d, %Y")))
                inc_dates.append( x[i] )
                inc_amnts.append( increase )
        
#                print('inc dates {}, in amnts {}'.format( inc_dates, inc_amnts))
#        print(24, x[1], y[-1], 0)
        today = dt.datetime.now()
        
        print()
        if today < x[0]:
#            print('upcoming date is lower')
            word = 'next'
            ###include previous date i.e. x[1]
        else:
#            print('upcoming date is  greater')
            P.PredictedDeclarationDate()
            word =  'most recent' 
            ###include predicted next date by looking at one 'x[3]' ex/div dates ago 
            ###   (wont work for some that have erratic div payouts, but can filter by number of divs per year)
        print('{} dividend ex/div date {},  ${}\n'.format(word, x[0].strftime("%B %d, %Y"), y[0]) )
        return inc_dates, inc_amnts
    

    def GetYearlyDivs(self):
        x = np.array( self.sorted[ 'Ex/Eff'] )
        y = np.array( self.sorted[ 'Amount' ] )
        d = {}
#        c = coll.Counter()  
        for X,Y in zip(x,y):
            year, amnt = X.strftime("%Y"), Y
#            print('year {}, amount {}'.format(year, amnt))
            if year not in d:
                d[year] = []
            d[year].append( amnt )
        self.yearly = {}
        for k,D in d.items():
#            print('year {} total payed ${:.4} in {} div payments'.format(k, sum(D), len(D)))
            self.yearly[k] = (sum(D), len(D))
        for k, yt in reversed(list( self.yearly.items() )):
            print('year {} total payed ${:.4} in {} div payments'.format(k, yt[0], yt[1]))
        
    
    def SelectTimeFrame(self):
        #    options = "5d", "1m", "3m", "6m", "1y", "18m", "2y", "3y", "4y", "5y", "6y", "7y", "8y", "9y", "10y"
        options = "5d 1m 3m 6m 1y 18m 2y 3y 4y 5y 6y 7y 8y 9y 10y".split()
        return options 
    
    
    def loop_table(self):
        for row in self.rows:
            cells = row.findChildren('td')
            try:
#                print()
                for c in cells:
                    print(  c.text.strip() )
            except Exception as e:
                print('Exception: ', e)
    
    def GetHistoricalQuote(self, timeframe=('y', 10) ):
        '''NASDAQ historical data'''
        self.domain = 'https://www.nasdaq.com/symbol/'
        
        url = '{}/historical'.format( self.ticker )
        site = ''.join( (self.domain, url) )
#        result = requests.get( ''.join( (self.domain, url) ) )
#        result = requests.get( site )
        
        s = requests.Session()
        r = s.get( site )
#        self.soup = BeautifulSoup(r.text, 'html.parser')
        self.soup = BeautifulSoup(r.content, "lxml")
        print( 'soup2 ', self.soup )
        
        self.select = self.soup.find('select', {'id': "ddlTimeFrame"})
        
        
        print(self.select)
        
        print()
        r.post()
        print('status code: {}'.format( r.status_code ))
        print('headers: {}'.format( r.headers ))
    
    def PredictedDeclarationDate(self):
        '''called in the case that the upcoming ex/eff date has not been announced yet'''
        dates = self.sorted[ 'Declaration']
        print('next date, a year ago: Declaration:', dates[3].strftime("%A %B %d, %Y") )
        print('                       Ex/Eff:', self.sorted[ 'Ex/Eff'][3].strftime("%A %B %d, %Y") )
        date = dates[3]
        return date

def compound( div, percentage=5.0 ):
    '''compute the hypothetical divident, and yield on cost (later...)
    20 years out, based on an average percentage dividend increase per year
    '''
#    ndiv = div * ( 1 + percentage/100 )
    original_div = div
    ndiv = div
    for i in range(20):
        ndiv *= 1 + percentage/100
        print('year {}, old div {:.4}, new div {:.4}, '.format(i, div, ndiv) )
        div = ndiv
        

    
if __name__=='__main__':
    P = Puller(ticker = 'JNJ') #abbv, mo, pm, 
    P.GetSite()
    P.SplitTable()
    P.GetDiv()
    P.SortDividendTable()
#    P.GetYearlyDivs()
    P.PlotDivHistory()
#    P.FindDivIncreases()
    

    