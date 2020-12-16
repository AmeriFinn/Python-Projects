# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 23:44:52 2020

@author: grega
"""

# Say Hello
print("Hello World")

## Import the standard libraries
import pandas as pd
import datetime as dt
import numpy as np
from IPython.display import clear_output
import ipywidgets as widgets
import plotly
import plotly.express as px

# Using Yahoo Finance API allows me to retrieve daily price info for equities, 
# bonds, and options: (Open, High, Low, Close, Volume, Dividends, Stock Splits)
# Compared to the AlphaVantage API, yfinance allows for unlimited calls per 
# day, but may be less efficent. It also has no technical indicator capability.
# Therfore, user-defined functions need to be utilized.
import yfinance as yf

# Create a pandas `IndexSlice` reference
idx = pd.IndexSlice

class Data:
    
    def __init__(self, tickers, shares, period="1y", interval="1wk"):
        """
        When `Data` is initialized, the list of tickers, the period, 
        and the desired interval will be be appended to the `Data` 
        class as attribute references.

        Parameters
        ----------
        tickers : list
            The list of ticker symbols that will be passed to the 
            yahoo finance `download` class. 
            
        shares : list
            A list denoting how many shares of each asset are held.
            This list must be the same lenght as the `tickers` list.
            
            If this list is too short, it will be expanded until it 
            is of equal length to `tickers`. The value that is appended 
            to this list will be the last value provided in the user input.
            
            If this list is too long, it will be trimmed to the length
            of `tickers` list.
            
        period : string, optional
            A string that can be passed to the `download` class,
            denoting what timeframe the data pull needs to span. 
            
            The default is "1y".
            
            Options = ["1d", "5d",
                       "1mo", "3mo", "6mo",
                       "1y", "2y", "5y", "10y",
                       "ytd", "max"]
        
        interval : TYPE, optional
            A string denoting the interval for which data will be downloaded. 
            
            The default is "1wk".

            Options = ["1m", "2m", "5m", "15m", "30m", "90m",
                       "1h",
                       "1d", "5d",
                       "1wk",
                       "1mo", "3mo"]

        Returns
        -------
        None.

        """
        
        # Say Hello
        print("Hello World")
        
        ## Check user inputs for validity
        
        ## Check the `shares` inputs
        # Convert share inputs to integers
        shares = [int(a) if isinstance(a, (float, int)) == True else 1 for a in shares]
        # Check if `shares` and `tickers` are the same lengths
        if len(shares) > len(tickers):
            shares = shares[:len(tickers)]
        elif len(shares) < len(tickers):
            while len(shares) != len(tickers):
                shares.append(shares[-1])
        # Zip the tickers and shares lists
        shares = dict(zip(tickers,shares))
        
        # Create initial attributes for the `Data` class.
        self.tickers    =  tickers
        self.tick_count = len(tickers)
        self.shares     = shares
        self.period     = period
        self.interval   = interval
        
        
    def Collect(self, DataType):
        
        if (DataType.upper() == "PRICES") | \
            (DataType.upper() == "BOTH"):
            
            # Download the price data for the given tickers
            PriceData = yf.download(tickers  = self.tickers,
                                    period   = self.period,
                                    interval = self.interval)[['Adj Close',
                                                               'Volume']] \
                        .sort_index(ascending=True)
            
            PriceData.fillna(method='bfill', inplace=True)
            

            # Add a total price column
            PriceData['Adj Close', 'Total'] = \
                PriceData['Adj Close'].sum(axis=1)
                
            # Create columns for portfolio prices by multiplying the 
            # Adj Close and number of shares held
            for col in [c for c in PriceData['Adj Close'].columns if c != 'Total']:
                PriceData[[('Portfolio_Value', col)]] = \
                   PriceData[[('Adj Close', col)]] * self.shares[col]
            
            # Add a total portfolio value column
            PriceData['Portfolio_Value', 'Total'] = \
                PriceData['Portfolio_Value'].sum(axis=1)
                
            for col in PriceData.columns:
                
                # Create columns for YTD or Start-To-Now returns
                PriceData[[('YTD_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                    .apply(lambda x: x/x.iloc[0] - 1) *100
            
            for col in PriceData.columns:
                
                # Create columns for a rolling % over prior 5 periods
                PriceData[[('5per_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                    .pct_change(periods=5) * 100
                
            for col in PriceData.columns:
            
                # Create columns for a rolling % change over prior period
                PriceData[[('PCT_Change', col[1])]] = \
                    PriceData[[('Adj Close', col[1])]] \
                    .pct_change(periods=1) * 100
            
            self.PriceData = round(PriceData,4)
            
            """
            return px.line(data_frame = PriceData.loc[:,'YTD_Change'] \
                           .dropna(axis=0))
            """
            
        if (DataType.upper() == "BALANCE SHEET") | (DataType.upper() == "BOTH"):
            
            # Create empty storage lists for the Balance Sheet
            # and Cash FLow df's
            quarterly_financials = []
            quarterly_cashflows  = []
            annual_financials    = []
            annual_cashflows     = []
            
            # Initiate loop to collect B-S data for all tickers
            for tick in self.tickers:
                
                
                # Create a yfinance Ticker object for the given ticker
                yfTick = yf.Ticker(tick)
                
                if yfTick.info['quoteType'].upper() == 'EQUITY':
                    
                    ## Collect Balance Sheet (B-S) data
                    
                    # Collect the quartelry financial data
                    qFins = yfTick.quarterly_financials
                    
                    # Create Multi-Index object for the quarterly
                    # financials data relative to the given ticker
                    qMIDX = pd.MultiIndex.from_tuples([(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in qFins.columns])
                    qFins.columns = qMIDX
                    
                    # Collect the annual report financial data
                    aFins = yfTick.financials
                    # Create Multi-Index object for the annual
                    # financials data relative to the given ticker
                    aMIDX = pd.MultiIndex.from_tuples([(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in aFins.columns])
                    aFins.columns = aMIDX                
                    
                    # Append B-S reults to `Game` class object
                    quarterly_financials.append(qFins)
                    annual_financials.append(aFins)
                    
                    ## Collect Cash Flow (CF) data
                    
                    # Collect quarterly CF's data
                    qCFS = yfTick.quarterly_cashflow
                    
                    # Create Multi-Index object for the quarterly
                    # CF's data relative to the given ticker
                    qMIDX = pd.MultiIndex.from_tuples([(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in qCFS.columns])
                    qCFS.columns = qMIDX
                    
                    # Collect annuals CF's data
                    aCFS = yfTick.cashflow
                    
                    # Create Multi-Index object for the annual
                    # CF's data relative to the given ticker
                    aMIDX = pd.MultiIndex.from_tuples([(tick, dt.date.strftime(d, format="%Y-%m-%d")) for d in aCFS.columns])
                    aCFS.columns = aMIDX                
                    
                    # Append CF reults to `Game` class object
                    quarterly_cashflows.append(qCFS)
                    annual_cashflows.append(aCFS)
                    
                else:
                    print(f"{tick} is not a known equity and must be an index, ETF, or non-existent. \nNo Balance Sheet Data will be collected.")
                
            
            # Append data results to the `Data` object
            self.quarterly_financials = pd.concat(quarterly_financials, axis=1)
            self.annual_financials    = pd.concat(annual_financials, axis=1)


class Plot:
    
    def __init__(self, Data, PlotColumn, PlotType="Line"):
        """
        On initiation, inputs will be assigned as class attributes
        

        Parameters
        ----------
        Data : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.Data       = Data
        self.PlotColumn = PlotColumn
        self.PlotType   = PlotType
        
    def Plot(self):
        if self.PlotType.upper() == 'LINE':
            return px.line(data_frame = self.Data.loc[:,self.PlotColumn].dropna(axis=0),
                           y =  [col for col in self.Data.loc[:,self.PlotColumn] if col != 'Total'],
                           hover_data = 'Total')
        
        elif self.PlotType.upper() == 'AREA':
             return px.area(data_frame = self.Data.loc[:,self.PlotColumn].dropna(axis=0),
                            y = [col for col in self.Data.loc[:,self.PlotColumn] if col != 'Total'],
                            hover_data = 'Total')
    
        


