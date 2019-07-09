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
    Date = date.split('/')
    Date = [ int(d) for d in [Date[-1]]+Date[:-1] ]
    Date = dt.datetime( *Date )
    return Date


class GetHistoricalQuote( object ):
    def __init__( self, ticker='jnj', timeframe=('y', 10)):
        '''NASDAQ historical data'''
        self.ticker = ticker.lower()
        self.domain = 'https://www.nasdaq.com/symbol/'
    
        url = '{}/historical'.format( self.ticker )
        self.url = ''.join( (self.domain, url) )
        print('url:', self.url)
#        result = requests.get( ''.join( (self.domain, url) ) )
#        result = requests.get( site )
        
        self.s = requests.Session()
        self.r = self.s.get( self.url )
        self.soup = BeautifulSoup( self.r.content, "lxml")
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
        headers = {
            'Host': 'www.nasdaq.com',
            #'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': self.url,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Length': '12',
            'Connection': 'keep-alive',
            'Cookie': self.r.headers['Set-Cookie']
        }
        
        print('sending POST request to get {} history'.format(length))
        r = self.s.post( self.url, headers=headers, data='{}|false|{}'.format(length, self.ticker))
#        print('post response type:', type(r))  
        self.soup = BeautifulSoup(r.text, 'html.parser')
#        self.soup = BeautifulSoup(r.content, "lxml")    
        table_div = ('div', {'id': 'quotes_content_left_pnlAJAX'} )
        self.td = self.soup.find( *table_div )
        self.table_header = self.td.find('h3')
        self.table = self.td.find('table')
#        print(self.table_header.text)   
        
        print('status code returned: {}'.format( r.status_code ))
        ''' print the response header inputs
        for k,h in r.headers.items():
            print('headers[{}]: {}'.format( k,h ))
        '''
        self.rows = self.table.findChildren([ 'tr' ])
        
    def PlotRows(self):
        
        headers = self.rows.pop(0)
        self.rows.pop(0)
        
        headers = 'Date Open High Low Close Volume'.split()
        self.headers = headers
        
        self.rl = []
        for i,r in enumerate(self.rows):
            data = r.text.strip().split()
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
        
    
        f,ax = plt.subplots( figsize=(11,6) )
        ax.grid(True, axis='y')
        ax2 = ax.twinx()
        colors = np.empty( len(d['Date']) , dtype=str )
        for i,c in enumerate(colors):
            if d['Open'][i] > d['Close'][i]:
                colors[i] = 'r'
            else:
                colors[i] = 'g'
                
        ax.errorbar(d['Date'], (d['High']-d['Low'])/2+d['Low'], yerr=(d['High']-d['Low'])/2,
                    linewidth=0.4, linestyle='', color='grey', alpha=0.55)
        ax.bar(d['Date'], d['Open']-d['Close'], bottom=d['Close'], color=colors, alpha=0.75)#, align='edge')
        

        ax2.bar( d['Date'], d['Volume'] , color=colors, alpha=0.6)#, align='edge')
#        ax2.bar( range(len(d['Date'])), d['Volume'] )
        ax.set_ylim( min(d['Low'])/1.05, ax.get_ylim()[1] )
        ax2.set_ylim( 0, max(d['Volume'])*4.5 )
#        print('max here', max(d['Volume']))
        f.autofmt_xdate()
        ax.set_title( '{} Historical Price'.format( self.ticker.upper() ) )
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax2.set_ylabel('Volume')
        f.show()

       
    def ProcessRequest(self, length):
        self.GetTable(length=length)
        self.PlotRows()
        self.SortRowList()
        
if __name__=='__main__':
    
    G = GetHistoricalQuote('JNJ')
    G.GetTable(length='5y')
    G.PlotRows()
    G.SortRowList()

