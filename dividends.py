# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 16:57:55 2019

Web Scraping Example

ex/div date and dividend growth calculator
Enter: a ticker symbol (e.g. JNJ, KMB, PEP)

@author: Chris
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import leastsq
import numpy as np
import datetime as dt
import requests
import pandas as pd

#selenium to deal with Nasdaq changes
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup #parsing html

####avoid implicitly registered datetime converter warning
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
####
#


def compound( cost, div, percentage ):
    '''compute the hypothetical divident, and yield on cost (later...)
    20 years out, based on an average percentage dividend increase per year
    '''
#    ndiv = div * ( 1 + percentage/100 )
    original_div = div
    print('\nstarting div: {}, cost basis: {}, average div increase of {:0.4}%'.format( original_div, cost, percentage))
    ndiv = div
    for i in range(21):
        ndiv *= 1 + percentage/100
        if i==5 or i==10 or i==20:
            print('year {}, old div {:.4}, new div {:.4}, yield on cost: {:0.4}%'.format(i, div, ndiv, 4*ndiv/cost*100) )
        div = ndiv

class Puller(object):
    def __init__(self, ticker='pm'):
        self.domain = 'https://www.nasdaq.com/symbol/'
        self.ticker = ticker
        
        
    def GetSite(self):
        self.url = '{}/dividend-history'.format( self.ticker )
        url = self.url
        #result = requests.get( ''.join( (self.domain, url) ), wait=5, stream=True )
        #self.soup = BeautifulSoup(result.content, "lxml")
        
        #get the size with selenium instead of requests
        options = Options()
        options.headless = True
        options=None  #uncomment this line for testing
        #need to change path to geckodriver
        self.browser = webdriver.Firefox( options=options, executable_path='/home/chris/Gecko/geckodriver')
        waiter = True
        if waiter:
            self.browser.implicitly_wait(20)
            self.browser.get( ''.join( (self.domain, url) ) )
            html = self.browser.page_source
            self.browser.quit()

        else:
            self.browser.get( ''.join( (self.domain, url) ) )
            element = WebDriverWait(self.browser, 25).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dividend-history__table"))
            )
            print(element.text)
        #delay = 20
        #try:
        #    myElem = WebDriverWait(self.browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME,'dividend-history__table')))
        #    print("Page is ready!")
        #except TimeoutException:
         #   print("Loading took too much time!")
       
        
        #html = self.browser.page_source
        self.soup = BeautifulSoup(html, "lxml")
        #self.soup = BeautifulSoup(element, "lxml")
        
#        productname = soup.title.text.split('|')[0]
#        print(productname)
        #self.name = self.soup.find('div', {'id': 'qwidget_pageheader'})
        self.name = self.soup.find('span', {'class': 'quote-bar__name' })
        #self.last_sale = self.soup.find('div', {'id': 'qwidget_lastsale'})
        self.last_sale = self.soup.find('span', {'class':'quote-bar__pricing-price' })
        print('name', self.name)
        print( 'last_sale', self.last_sale )
#        self.name = self.soup.find('div', {'class': 'quotebar-wrap'})
#        self.name = self.table.findChildren([ 'h1' ])
        
    def SplitTable( self ): 
        #self.tableclassname = "quotes_content_left_dividendhistoryGrid"
        #self.table = self.soup.find('table', {'id': self.tableclassname})
        self.table = self.soup.find('table', {'class': 'dividend-history__table'})
        #print('table\n', self.table)
        #print(self.soup)
        self.table_text = str( self.table.text )
        #print(repr(self.table_text))
        self.bs = self.table_text.split()
        self.href = self.table.findChildren([ 'href' ])
        #self.headers = self.table.findChildren([ 'th' ])
        self.rows = self.table.findChildren([ 'tr' ])
        self.row_text = []
        for i,row in enumerate(self.rows):
            thisrow = []
            #print(repr(row.text))
            if i==0:
                self.headers = [rr.text for rr in row.find_all( 'th' )]
            else:

                exeff = row.find('th').text
                #print(i,'ex/eff', exeff)
                cols = row.find_all('td')
                thisrow.append( exeff )
                for j,col in enumerate(cols):
                    #print(i,j, col.text)
                    thisrow.append( col.text )
                self.row_text.append( thisrow )

#        self.loop_table()
#        prs = ( bs[:3], bs[6:11], bs[11:16], bs[16:] )
#        #for b in prices: print(b)
#        return productname, prs
        
    def GetDiv(self):
        self.div = []
#        self.header_text = [rt.text.strip() for rt in self.headers]
        #self.row_text = [rt.text.strip().split() for rt in self.rows]
        #self.header_text = self.row_text.pop(0)
        print('h0', self.headers )
        self.header_text = ['Ex/Eff', 'Type', 'Amount',
            'Declaration', 'Record', 'Payment']
#        print( 'headers', self.header_text)
#        print( 'rows[0]', self.row_text[0])
        print('h1', self.header_text)
        for rt in self.row_text:
            self.div.append( dict(zip( self.header_text, rt )) )

    def SortDividendTable(self):
        self.sorted = {}
        for h in self.header_text:
            # determine the type conversion based on the key
            if h=='Ex/Eff' or h=='Declaration':
                
                self.sorted[h] = [ d[h].split('/') for d in self.div ]
                
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
                self.sorted[h] = [f(d[h].replace('$', '')) for d in self.div]
            else:
                f = str
            # convert the type, and then
            #   create a dict entry consisting of each entry for that header
                #print('d\n', d)
                self.sorted[h] = [f(d[h]) for d in self.div]

    def PlotDivHistory(self):
#        f,ax = plt.subplots()
        f,ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(10,12), gridspec_kw={'height_ratios': [3, 2]}, dpi=200)
        ax[0].set_ylabel('dividend paid ($)')
        
        ax[0].set_title(self.name.text.replace('Date &', ''))
#        print('type', type(self.sorted[ 'Ex/Eff']))
#        print(self.sorted[ 'Ex/Eff'])
        ax[0].plot_date( self.sorted[ 'Ex/Eff'], self.sorted[ 'Amount' ], label='Amount vs Ex/Eff Date' )
        ax[1].set_xlabel('Date')
        self.FitDivHistory(ax[0])
        inc_dates, inc_amnts = self.FindDivIncreases()
#        ax2 = ax[0].twinx()
#        ax2 = ax[1]
        ax[1].plot(inc_dates, inc_amnts, 'x', markersize=8, color='red', label='div increase percentage')
        ax[1].set_ylabel('Percentage Increase (%)')
#        ylims = ax[1].get_ylim()
#        if ylims[0] > 0:
#            ax[1].set_ylim(0, ylims[1])
        print('last sale price {}'.format(self.last_sale.text))
        price = float(self.last_sale.text.replace('$',''))
        yoc = self.sorted[ 'Amount' ][0]*4/price*100
        print('current yield on cost = {:.4f}%'.format(yoc))
        self.PlotYearlyDivs(ax[0].twinx())
        plt.savefig(f'div_plots_{self.ticker}.pdf', encoding='pdf')
        plt.savefig(f'div_plots_{self.ticker}.png')
        plt.show()
        
    
    def PlotYearlyDivs(self, ax):
        #get yearly total numbers and number or div payments, then plot them
        self.GetYearlyDivs()
        yearkey = sorted( list( self.yearly.keys() ) )
        
        years = [dt.datetime(int(y), 12, 31) for y in yearkey] #convert year to datetime dec 31 of the year divs are added for
        yearval = [self.yearly[k][0] for k in yearkey]
        #ax3 = ax.twinx()
        
        ax3 = ax
        ax3.plot_date(years, yearval, '>', color='green', label='yearly dividend' )
        ax3.tick_params(axis='y', direction='out', labelcolor='green') #, pad=-20
        ax3.set_ylabel('yearly div ($)', color='green') # , labelpad=-30
        '''
        f2,axh = plt.subplots()

        df = pd.DataFrame(data=inc_amnts)
#        print('mean', df[0].mean() )
#        print('median', df[0].median() )
        upper_limit = 2*df[0].mean()
        axh.hist( df[0] )
#        plt.hist()
#        ax.show()
        '''

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
        
        tplFinal1,success= leastsq(ErrorFunc,tplInitial1[:],args=(x,y))
        print ('linear fit results',tplFinal1)

        yy1=func(tplFinal1,x)
        ax.plot(x, yy1)
    
    def FindDivIncreases(self):
        '''get the divdednd increase of decrease associated with 
        each change in the dividend
        
        need to add a filter to handle divs paid beyond the standard quarterly
        '''
        x = np.array( self.sorted[ 'Ex/Eff'] )
        y = np.array( self.sorted[ 'Amount' ] )
        
        for X,Y in zip( reversed(x), reversed(y) ):
            print("{} on {}".format(Y,  X.strftime("%B %d, %Y")))
#        xdif = x[:-1] - x[1:]
        ydif = y[:-1] - y[1:]

        inc_dates = []
        inc_amnts = []
#        for i,x1,y1, ye in zip( reversed(np.arange(len(x))), reversed(x), reversed(y), reversed(ydif)):
        for i,x1,y1, ye in zip(np.arange(len(x)),x,y,ydif):
            if ye != 0:
                increase = ye/y[i+1]*100
                print('div increase of ${:.4f}, from ${} to ${}. An increase of {:.2f}%, on {}'.format(ye, y[i+1], y[i], increase , x[i].strftime("%B %d, %Y")))
                inc_dates.append( x[i] )
                inc_amnts.append( increase )

        today = dt.datetime.now()
        
        print()
        if today < x[0]:
#            print('upcoming date is lower')
            word = 'next'
            ###include previous date i.e. x[1]
        else:
#            print('upcoming date is  greater')
            self.PredictedDeclarationDate()
            word =  'most recent' 
            ###include predicted next date by looking at one 'x[3]' ex/div dates ago 
            ###   (wont work for some that have erratic div payouts, but can filter by number of divs per year)
        print('{} dividend ex/div date {},  ${}\n'.format(word, x[0].strftime("%B %d, %Y"), y[0]) )
        self.avg_increase = sum(inc_amnts)/len(inc_amnts)
        
        return inc_dates, inc_amnts
    

    def GetYearlyDivs(self):
        x = np.array( self.sorted[ 'Ex/Eff'] )
        y = np.array( self.sorted[ 'Amount' ] )
        d = {} 
        for X,Y in zip(x,y):
            year, amnt = X.strftime("%Y"), Y
            if year not in d:
                d[year] = []
            d[year].append( amnt )
        self.yearly = {}
        for k,D in d.items():
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
        s = requests.Session()
        r = s.get( site )
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

    def FutureYield(self):
        
        price = float(self.last_sale.text.strip('$'))
        starting_div = self.sorted[ 'Amount'][0]
        
        compound(cost=price , div=starting_div, percentage=self.avg_increase)

    def ProcessRequest(self):
        self.GetSite()
        self.SplitTable()
        self.GetDiv()
        self.SortDividendTable()
        self.PlotDivHistory()
        self.FutureYield()
        
    
if __name__=='__main__':
    P = Puller(ticker = 'JNJ') #JNJ, KMB, PEP, MMM 
    P.GetSite()
    P.SplitTable()
    P.GetDiv()
    P.SortDividendTable()
#    P.GetYearlyDivs()
    P.PlotDivHistory()
    P.FutureYield()
#    P.FindDivIncreases()
    

    
