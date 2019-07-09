# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 16:38:31 2019

@author: Chris
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import leastsq
import numpy as np
import datetime as dt
import requests

from time import time

from bs4 import BeautifulSoup #parsing html

###avoid implicitly registered datetime converter warning
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
###


headers = {
        'Host': 'www.nasdaq.com',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
'Accept': '*/*',
'Accept-Language': 'en-US,en;q=0.5',
'Accept-Encoding': 'gzip, deflate, br',
'Referer': 'https://www.nasdaq.com/symbol/nrz/historical',
'Content-Type': 'application/json',
'X-Requested-With': 'XMLHttpRequest',
'Content-Length': '12',
'Connection': 'keep-alive',
'Cookie': 'clientPrefs=||||lightg; s_pers=%20bc%3D2%7C1560630421196%3B%20s_nr%3D1560544646671-Repeat%7C1568320646671%3B; userCookiePref=false; accept-cookies=2; NSC_W.TJUFEFGFOEFS.OBTEBR.443=ffffffffc3a0f70e45525d5f4f58455e445a4a42378b; rewrite=true; c_enabled$=true; AKA_A2=A; ak_bmsc=3D1940EF480CAE86B3041025C458A25460110AA4E21E00007FF7035D11EE4C04~plp8rHqvXfruZzv4Mb1FvEtqVsXfB0r8vIT/T/ZqgJzutAcLT7W+1eGXFF4ddnuN4NwEqOk92Bw6cJKwP/y5yx9HKrltB9N+1Y5tWNSWaBIcO3xWuXHEBPBH4GHRck+Lb4eF4Gp4TFbtfdrJaDicS34xtXmfzJibQ5QG8MgP1QV54RrIQjpd87/BQBxyctb7fARAGut2W+QApEHZ9L36Hnb1bDUktepDvVlaIgxmjRelFy7cSsjhwF9+Qlpu+HUWpcTNztGje9a6POzKUgHnHBQf6D8F5iPKZX4ta0mutAkcCgaSwBYiA2rLwgLivLXcCsMu329ETyG6uaKwv3H7JIzg==; bm_sv=F55F694D757C98B43C51EF71309BF627~LWnK4EpDOtZ2zietoqVEQssPX6udiNXZj+QhYLNQ3YzCj1GihxqAd+ikbL8PBVP6x05nYEQFiBdRcX5lJZdHWk2S4EV8GfJLMuxxC2XsVezZ0AUoBwT9MM3dh4HoCgT3W7ey2NDzzKV1fLCz9X4XiTEWr8Ccowh7a/7iPa4s5e4=; s_sess=%20s_cc%3Dtrue%3B%20s_sq%3D%3B; selectedsymboltype=NRZ%2cCOMMON%20STOCK%2cNYSE; selectedsymbolindustry=NRZ,consumer_services; userSymbolList=NRZ+',
}

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
        print('url', self.url)
#        result = requests.get( ''.join( (self.domain, url) ) )
#        result = requests.get( site )
        
        self.s = requests.Session()
        self.r = self.s.get( self.url )
#        self.soup = BeautifulSoup(r.text, 'html.parser')
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
        ## get the options of the select form
        self.select = self.soup.find('select', {'id': "ddlTimeFrame"})
        print('select', self.select)
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
        
        r = self.s.post( self.url, headers=headers, data='{}|false|{}'.format(length, self.ticker))
        print('post response type:', type(r))  
        self.soup = BeautifulSoup(r.text, 'html.parser')
#        self.soup = BeautifulSoup(r.content, "lxml")    
        table_div = ('div', {'id': 'quotes_content_left_pnlAJAX'} )
        self.td = self.soup.find( *table_div )
        self.table_header = self.td.find('h3')
        self.table = self.td.find('table')
#        print(self.table_header.text)   
        
        print('status code: {}'.format( r.status_code ))
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
#            print(data)
#            d[i] = dict(zip(headers, data)) 
            self.rl.append( dict(zip(headers, data))  )
#        print('s', self.rl) 
        
#        f,ax = plt.subplots()
#        data = self.rows[-1].text.strip().split()
#        dtp = [float(b) for b in data[1:-1]]
#        ax.plot( range(len(dtp)), dtp, '.')
         
    def SortRowList(self):
        d = {}
        for h in self.headers:
            if h == 'Date':
                d[h] = [  FixDate(r[h]) for r in self.rl] 
            elif h == 'Volume':
                d[h] =  np.array( [int(r[h].replace(',','')) for r in self.rl] )
            else:
                d[h] =  np.array( [float(r[h]) for r in self.rl] )
#        print(d['Open'])
        f,ax = plt.subplots( figsize=(11,6) )
        ax.grid(True, axis='y')
        ax2 = ax.twinx()
        colors = np.empty( len(d['Date']) , dtype=str )
        for i,c in enumerate(colors):
            if d['Open'][i] > d['Close'][i]:
                colors[i] = 'r'
            else:
                colors[i] = 'g'
                
#        print(colors)
        
        ax.errorbar(d['Date'], (d['High']-d['Low'])/2+d['Low'], yerr=(d['High']-d['Low'])/2,
                    linewidth=0.4, linestyle='', color='grey', alpha=0.55)
        ax.bar(d['Date'], d['Open']-d['Close'], bottom=d['Close'], color=colors, alpha=0.75)#, align='edge')
        
#        f2,axtemp = plt.subplots()
#        axtemp.bar( d['Date'], d['Volume'] )
        #        axtemp.set_yscale('log')
#        ylims = axtemp.get_ylim()
#        f,ax3 = plt.subplots()
        ax2.bar( d['Date'], d['Volume'] , color=colors, alpha=0.6)#, align='edge')
#        ax2.bar( range(len(d['Date'])), d['Volume'] )
        ax.set_ylim( min(d['Low'])/1.05, ax.get_ylim()[1] )
        ax2.set_ylim( 0, max(d['Volume'])*4.5 )
        print('max here', max(d['Volume']))
        f.autofmt_xdate()
        ax.set_title( '{} Historical Price'.format( self.ticker.upper() ) )
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax2.set_ylabel('Volume')
        f.show()
        
#        for i,x in enumerate( d['Volume']):
#        for i,x in enumerate( d['Date']):
##            print(i,x)
#            print(i,x)
        
        
if __name__=='__main__':
    
    print('get quote')
    start = time()
    G = GetHistoricalQuote('JNJ')
    ###
    end = time()
    print('len:', end-start)
    start = time()
    
    print('get table')
    G.GetTable(length='5y')
    ###
    end = time()
    print('len:', end-start)
    start = time()
    print('get plot rows')
    ###
    end = time()
    print('len:', end-start)
    start = time()
    G.PlotRows()
    end = time()
    print('len:', end-start)
    start = time()
    print('sort rows list')
    G.SortRowList()
    end = time()
    print('len:', end-start)
#    start = time()
