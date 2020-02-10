# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 16:38:31 2019

@author: Chris
"""

import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import requests

from bs4 import BeautifulSoup #parsing html

###avoid implicitly registered datetime converter warning
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
###


def FixDate(date):
    if ',' in date:
        date = date.strip(',')
    Date = date.split('/')
    Date = [ int(d) for d in [Date[-1]]+Date[:-1] ]
    Date = dt.datetime( *Date )
    return Date


class GetHistoricalQuote( object ):
    def __init__( self, ticker='jnj', timeframe=('y', 6)):
        '''NASDAQ historical data'''
        self.ticker = ticker.lower()
        ''' # no longer works...table doesn't load...need to use download link
        self.domain = 'https://www.nasdaq.com/symbol/'
        
        url = '{}/historical'.format( self.ticker )
        self.url = ''.join( (self.domain, url) )
        print('url:', self.url)
        '''
        #one month history
        #https://www.nasdaq.com/api/v1/historical/JNJ/stocks/2020-01-09/2020-02-09
        #5 year history link
        #https://www.nasdaq.com/api/v1/historical/JNJ/stocks/2015-02-09/2020-02-09
        #make sure to handle leap-year, otherwise use the same 'day' minus 5 years
        today = dt.date.today()
        if timeframe[0] == 'y':
            nyears = timeframe[1]
            nmonths = 0
        elif timeframe[0] == 'm':
            nyears = 0
            nmonths = timeframe[1]
        else:
            nyears = 0
            nmonths = 1
        
        end = dt.date(  today.year-nyears, today.month-nmonths, today.day ) 
        start, end =  end.isoformat(), today.isoformat()
        print('start date:', start, 'end date:', end)
        ##create the url with the ticker and time frame
        self.url = f'https://www.nasdaq.com/api/v1/historical/{self.ticker}/stocks/{start}/{end}'
        print(self.url)
        #possibly take longer than 5 years to match up with div history...
        self.r = requests.get(  self.url )
        
        #self.s = requests.Session()
        #self.r = self.s.get( self.url )
        self.soup = BeautifulSoup( self.r.content, "lxml")
        
        #print( self.soup.prettify() )
#        print( 'soup2 ', self.soup )
        ''' print the response header inputs
        for k,h in self.r.headers.items():
            print('headers[{}]: {}'.format( k,h ))
        '''
        
        
#        print( 'soup2 ', self.soup )
        
    def GetTable(self, length):
        ''' Use an html POST method to get a differnt time range
        **ticker must be lower case in order for post to work**
        '''
        ## get the options from the 'TimeFrame' <select> form
#        self.select = self.soup.find('select', {'id': "ddlTimeFrame"})
#        print('select', self.select)  #list the possible timeframe options
        table = self.soup.find( 'p' ).text
        
        lines = table.split('\n')
        self.rows = [line for line in lines if line]
        #print( repr(table) )
        #print( len( lines ) )
        
        
    def PlotRows(self):
        
        headers = self.rows.pop(0).split(', ')
        headers[1] = headers[1].replace('/Last', '') #change 'Close/Last' to just 'Close'
        #self.rows.pop(0)
        self.headers = headers
        #print('headers', headers)
                
        #print('rows', self.rows)
        
        self.rl = []
        for i,r in enumerate(self.rows):
            #data = r.text.strip().split()  #format change...
            data = r.split(', ')
            data = [d.replace('$', '') if '$' in d else d for d in data]
            self.rl.append( dict(zip(headers, data))  )


    def SortRowList(self):
        d = {}
        for h in self.headers:
            if h == 'Date':
                d[h] = [  FixDate(r[h]) for r in self.rl] 
            elif h == 'Volume':
                d[h] =  np.array( [int(r[h].replace(',','')) for r in self.rl] )
            else:
                d[h] =  np.array( [float(r[h]) for r in self.rl] )
        self.d = d
        
    
#        f,ax = plt.subplots( figsize=(11,6) ) ###on desktop... figsize=(11,6)
        f, axs = plt.subplots( nrows=2, ncols=1, figsize=(14,10), dpi=200 )
        ax = axs[0]
        ax.grid(True, axis='y')
        ax2 = ax.twinx()
        colors = np.empty( len(d['Date']) , dtype=str )
        for i,c in enumerate(colors):
            if d['Open'][i] > d['Close'][i]:
                colors[i] = 'r'
            else:
                colors[i] = 'g'
        alpha = 0.7      
        ax.errorbar(d['Date'], (d['High']-d['Low'])/2+d['Low'], yerr=(d['High']-d['Low'])/2,
                    linewidth=0.4, linestyle='', color='grey', alpha=alpha )
        ax.bar(d['Date'], d['Open']-d['Close'], bottom=d['Close'], color=colors, alpha=alpha, linewidth=1.0 )#, align='edge')
        

        ax2.bar( d['Date'], d['Volume'] , color=colors, alpha=alpha )#, align='edge')
#        ax2.bar( range(len(d['Date'])), d['Volume'] )
        ax.set_ylim( min(d['Low'])/1.05, ax.get_ylim()[1] )
        ax2.set_ylim( 0, max(d['Volume'])*4.5 )
#        print('max here', max(d['Volume']))
        f.autofmt_xdate()
        ax.set_title( '{} Historical Price'.format( self.ticker.upper() ) )
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax2.set_ylabel('Volume')
        #plt.savefig('testplot.pdf', encoding='pdf')
        #plt.savefig('testplot.png')
        #plt.show()
        return f,axs[1]

       
    def ProcessRequest(self, length):
        '''complete historical quote puller and analysis algorithm
        returns the subplot to add the "Historical (Starting) Yield on Cost"'''
        self.GetTable(length=length)
        self.PlotRows()
        return self.SortRowList()
        
if __name__=='__main__':
    
    G = GetHistoricalQuote('JNJ')
    G.GetTable(length='5y')
    G.PlotRows()
    G.SortRowList()

