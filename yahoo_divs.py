# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 19:09:27 2019

ex/div date and dividend growth calculator

Enter the ticker symbol for a dividend growth company (e.g. JNJ, KMB, PEP)

@author: Chris
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import leastsq
import collections as coll
import numpy as np
import datetime as dt
import requests

from bs4 import BeautifulSoup 

from dividends import Puller

###avoid implicitly registered datetime converter warning
#from pandas.plotting import register_matplotlib_converters
#register_matplotlib_converters()
####


class YahooDivHist(object):
    '''class to scrape dividend history, yahoo has a longer available history,
        but lacks ex/div date, and declaration date info, 
        which is needed for the historical yield on cost'''
    def __init__(self, ticker='HRL'):
        self.domain = 'https://www.nasdaq.com/symbol/'
        self.ticker = ticker
        self.url_history = '{}/dividend-history'.format( ticker )
        
    def GetPriceHistory(self, start_date='Jul 08, 2000' , end_date='Jul 09, 2019', interval='1d', filt='div', frequency='1mo' ):
        '''get the hisorical data from yahoo finance
        includes dividends and stock splits
        can choose different period for different fineness
        optiond = 1d 1wk 1mo
        '''
        start_date = int( dt.datetime.strptime( start_date, '%b %d, %Y' ).timestamp() )
        end_date = int( dt.datetime.strptime( end_date, '%b %d, %Y' ).timestamp() )
        print(start_date, end_date)
#        start_date = int( start_date.timestamp() )
#        print('start', start_date)
#        hist_url = 'https://finance.yahoo.com/quote/PM/history?period1=1205726400&period2=1561003200&interval=1d&filter=history&frequency=1d'
#        start_date, end_date, interval, frequency = '1205726400', '1561003200', '1d', '1d'
        hist_url_entry = 'https://finance.yahoo.com/quote/{}/history?period1={}&period2={}&interval={}&filter={}&frequency={}'.format(self.ticker, start_date, end_date, interval, filt, frequency )
#        print('hist_url', hist_url_entry)
#        hist_url_entry = 'https://finance.yahoo.com/quote/HRL/history?period1=1205726400&period2=1561003200&interval=1d&filter=history&frequency=1mo'
        print('hist_url', hist_url_entry)
#        result = requests.get( hist_url )
        result = requests.get( hist_url_entry )
        self.soup = BeautifulSoup(result.content, "lxml")
    
    def ReadTable(self):
        '''read the table produced over the period provided in GetPriceHistory'''
        ###get the historical data table, whose class='W(100%) M(0)'
        self.table = self.soup.find('table', {'class': 'W(100%) M(0)'}) 
        ###get the table headers
        self.thead = self.table.find([ 'thead' ]) #get the table headers
        
        self.spans = self.thead.find_all([ 'th' ]) #get the html <th> objects
        # extract the text from the html "th" objects 
        self.headers = [s.text.strip('*').replace(' ', '_') for s in self.spans]
#        print('headers', self.headers)
        
        ###get the table body
        self.tbody= self.table.find([ 'tbody' ])
        self.ProcessTableBody()

        ###get the table footer
        self.tfoot = self.table.find([ 'tfoot' ])
        self.foot = self.tfoot.find_all([ 'span' ]) #good
#        print('foot text', self.foot)
      
    def ProcessTableBody(self):
        '''organize the historical data table into dictionaries
        containing the price history, dividend history, and price history'''
        self.rows = self.tbody.find_all([ 'tr' ])
        
        self.div_headers = 'Date Amnt Type'.split()
        self.split_headers = 'Date Ratio Type'.split()
        self.pricel = []
        self.divl = []
        self.splitl = []
        
        for i,row in enumerate(self.rows):
            row_list = [span.text for span in row.find_all( ['span', 'strong'] )]
            row_list[0] = dt.datetime.strptime( row_list[0], '%b %d, %Y' ) #convert the date string to a datetime object

            if 'Dividend' in row.text:
                self.divl.append( dict(zip( self.div_headers, row_list )) )
                
            elif 'Split' in row.text:
                self.splitl.append(  dict(zip( self.split_headers, row_list )) )
                
            else:
                self.pricel.append( dict(zip( self.headers, row_list )) )
        
#        print('divl', self.divl)
#        print('splitl', self.splitl)
       
    def SortPriceList(self):
        self.priced = {}
        for h in self.headers:
            if h == 'Date':
                self.priced[h] = [ r[h] for r in self.pricel ] 
            elif h == 'Volume':
                self.priced[h] =  np.array( [int(r[h].replace(',','')) for r in self.pricel] )
            else:
                self.priced[h] =  np.array( [float(r[h]) for r in self.pricel] )
#        print( self.priced['Date'] )
                
        
    def SortDivs( self ):
        self.divd = {}
        for h in self.div_headers:
            if h == 'Date':
                self.divd[h] = [ r[h] for r in self.divl ] 
            elif h == 'Amnt':
                self.divd[h] =  np.array( [float(r[h]) for r in self.divl] )
            else:
                self.divd[h] =  np.array( [r[h] for r in self.divl] )
        return self.divd
        
    def FindDivIncreases(self, output=False):
        '''get the divdednd increase of decrease associated with 
        each change in the dividend
        '''
        x = np.array( self.divd['Date'] )
        y = np.array( self.divd['Amnt'] )
        if output:
            for X,Y in zip( reversed(x), reversed(y) ):
                print("{} on {}".format(Y,  X.strftime("%B %d, %Y")))
#        xdif = x[:-1] - x[1:]
        ydif = y[:-1] - y[1:]

        inc_dates = []
        inc_amnts = []
        for i,x1,y1, ye in zip(np.arange(len(x)),x,y,ydif):
            
            if ye != 0:
                increase = ye/y[i+1]*100
                if output: print('div increase of ${:.4f}, from ${} to ${}. An increase of {:.2f}%, on {}'.format(ye, y[i+1], y[i], increase , x[i].strftime("%B %d, %Y")))
                inc_dates.append( x[i] )
                inc_amnts.append( increase )

        return inc_dates, inc_amnts
    
    def GetDivDist(self):
        self.GetPriceHistory()
        self.ReadTable()
        self.SortPriceList()
        dd = self.SortDivs()
        inc_dates, incs = self.FindDivIncreases( )
        plt.hist( incs, bins=25 )
    
if __name__=='__main__':
    YH = YahooDivHist(ticker = 'pep')
    YH.GetPriceHistory()
    YH.ReadTable()
    YH.SortPriceList()
    dd = YH.SortDivs()
    f,ax = plt.subplots()
    ax.plot(dd['Date'], dd['Amnt'], '.')
#    print(dd['Amnt'])
    inc_dates, incs = YH.FindDivIncreases( )
#    ax2 = ax.twinx()
#    ax2.plot( inc_dates, incs, 'o')
    
    f2,ax3 = plt.subplots()
    plt.hist( incs, bins=25 )
    plt.title('div increase distribution')
    plt.xlabel('increase (%)')
    plt.ylabel('occurances')
#    print( sum(incs)/len(incs))
    