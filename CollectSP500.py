# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 2020

@author: grega



"""
# Import necessary libraries
# Import standard libraries
import pandas as pd, numpy as np
import scipy
import datetime as dt
from datetime import *
from IPython.display import clear_output
import ipywidgets as widgets
from ipywidgets import *

# Using Yahoo Finance API allows me to retrieve daily price info for equities, bonds, and options:
#    (Open, High, Low, Close, Volume, Dividends, Stock Splits)
# Compared to the AlphaVantage API, yfinance allows for unlimited calls per day, but may be less efficent
# It also has no technical indicator capability. Therfore, user-defined functions need to be utilized
import yfinance as yf

# Using AlphaVantage allows me to retrieve all types of pricing and technical indicator data
# However, with my API key, I can only make 500 calls per day and 5 per minute. 
# This limits my ability to quickly download daily price data
#import alphavantage
#from alphavantage.price_history import (
#  AdjustedPriceHistory, get_results, PriceHistory, IntradayPriceHistory,
#  filter_dividends
#)
#from alpha_vantage.timeseries import TimeSeries

# I will use this project to learn more about plotly
import plotly
import plotly.express as px
import plotly.graph_objs as go

# Create pandas IndexSlice reference
idx = pd.IndexSlice

def selection_sort(x):
    """
    selection_sort will quickly sort a NumPy array
    
    Parameters
    ----------
    x : np.aray
        NumPy aray to be sorted in ascending order.

    Returns
    -------
    x : np.aray
        NumPy aray sorted in ascending order.

    """
    for i in range(len(x)):
        swap = i + np.argmin(x[i:])
        (x[i], x[swap]) = (x[swap], x[i])
    return x

def select_str(x, str):
    """
    select_str will quickly return a list of matches from a (nessted) list
    
    Parameters
    ----------
    x : list
        List object to be searched through. `x` may be a nested list.
    str : str
        Desired string to be found (exact match).
        If str == '' then the list of the 11 SP500 sectors will be returned

    Returns
    -------
    list
        List object with all .

    """
    if str == '':
        return ['Communication Services','Consumer Discretionary','Consumer Staples',
                'Energy','Financials','Health Care','Industrials','Information Technology',
                'Materials','Real Estate','Utilities']
    # Create empty list to store matches
    y = []
    # Initiate loop through each object within `x`
    for i in x:
        # If `x` is not nested, check if selected element matches desired term
        if str in i:
            y.append(i) # Collect match
        else:
            # If `x` is nested, check if the nested list contains a match
            for n in i:
                if str in n:
                    y.append(i) # Collect match
                    break    
    return y

def ytd_Return(x1,x2):
    """
    ytd_Return will quickly calculate a simple growth rate
    Parameters
    ----------
    x1 : int or float
        First year of data.
        
    x2 : int or float
        Second year of data.

    Returns
    -------
    float
        Simple growth rate.

    """
    return round(x2/x1-1,3)

def adjustDF(df):
    """
    adjustDF will quickly adjust the selected df by:
    tranposing, resetting the index, and renaming the new column.
    Called in the Aggregate_MarketData function

    Parameters
    ----------
    df : pd.DataFrame
        Descriptive summary stats df (YTD, 5day avg's, Price).

    Returns
    -------
    df : pd.DataFrame
        Adjusted df.

    """
    df = df.transpose()
    df.reset_index(inplace=True,drop=False)
    df = df.rename(columns={'index':'Security'})
    
    return df

def identSubSect(Security, SP500):
    """
    identSubSect will determine what GICS Sub Industry the Security is listed under

    Parameters
    ----------
    Security : str
        The security name as listed on the S&P 500.
    SP500 : pd.DataFrame
        The SP500 df created from the collectSP500list function.

    Returns
    -------
    subSec : str
        GICS Sub Industry for the desired security.

    """
    subSec = SP500[SP500.Security == Security]['GICS Sub Industry'].max()
    return subSec

def collectSP500list():
    """
    collectSP500list will create a list of every stock listed on the S&P 500
    
    Credit to Graham Guthrie and his article [5 Lines of Python to Automate Getting the S&P 500](https://medium.com/wealthy-bytes/5-lines-of-python-to-automate-getting-the-s-p-500-95a632e5e567)

    Returns
    -------
    SP500 : pd.DataFrame
        Df containing securities listed on the SP500.
    Changes : pd.DataFrame
        Df containing records for securities that are replaced by new listings.
        Mostly useless, but necessary to be able extract data properly for SP500

    """
    table=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    
    SP500 = table[0]
    Changes = table[1]
    
    return SP500, Changes

def CollectSectors(SP500):
    """
    CollectSectors will create 3 lists which store the unique sectors, and sub industries fo
    
    Parameters
    ----------
    SP500 : pd.DataFrame
        Dataframe created from the collectSP500list function.

    Returns
    -------
    secs : list
        A list of the unique sectors listed on the S&P 500.
    subs : list
        A list of the unique sub industries listed on the S&P 500.
    both : list
        A list of the unique sectors and sub industries (sector,industry).

    """
    secs = selection_sort(SP500['GICS Sector'].unique()).tolist()

    subs = selection_sort(SP500['GICS Sub Industry'].unique()).tolist()

    both = SP500.set_index(['GICS Sector', 'GICS Sub Industry'])
    both = both.index.unique()
    both = both.sort_values().tolist()
    
    return secs, subs, both

# Loop through stocks listed on SP500 in 2020 to collect `Daily Closing` prices
def Collect_MarketData(SecOrSub,Results,Period,SP500):
    """
    Collect_MarketData loops through SP500 to determine if each security
    falls within the list of desired results based on the security's sector and industry.
    
    If the security is a match, a call to Yahoo Finance will be made to collect 
    the full range of YTD security info. The resulting df will be refined to just the closing price.
    
    In future revisions, this can be adjusted so that a list of column heads can be passed 
    to return a MultiIndex df.

    Parameters
    ----------
    SecOrSub : boolean
        If True, Results will be processed as a non-nested list. Assumes a list of Sec(tors) is passed
        If False, Results will be processed as a nested lists. Assumes a list of Sub (Industries) is passed
    Results : list
        A list of desired sectors, or sectors and sub industry, to be collected
    Period : str
        The period for which data will be downloaded.
        Valid Inputs = ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
    SP500 : pd.DataFrame
        Dataframe created from the collectSP500list function.

    Returns
    -------
    AllDFs : list
        A nested list containing:
            [Ticker, Security, Sector, Sub Industry, Closing-Price df],
        for each security in the Results list

    """
    # Create empty list to store symbol, company name, sector, industry, and ytd price info
    AllDFs = []

    # Define values used in loop 
    start = datetime.now()
    i = 0
    
    # Check every record of the SP500 df for matches from the Results list
    for row in SP500.index:

        # Collect row data
        temp = pd.DataFrame(SP500.loc[row])

        # Collect necessary data for historical lookups and categorizing records
        symb = temp.loc['Symbol'].max()
        secu = temp.loc['Security'].max()
        sect = temp.loc['GICS Sector'].max()
        suid = temp.loc['GICS Sub Industry'].max()
        
        if SecOrSub == True:
            # Results will be processed as a non-nested list
            if sect in Results:
                # Make call to Yahoo Finance API
                tick = yf.Ticker(symb)
                
                # Collect YTD Daily Closing Price data
                # In future revisions, the period 
                # and selected column can be passed as variables
                df = tick.history(period=Period)
                df = df['Close']
                df = df.rename(secu)    # df type = pd.Series
                
                # Add info on security to AllDFs list
                append = [symb, secu, sect, suid, df]
                AllDFs.append(append)
                
        else:
            # Results will be processed as a nested list
            temp = (sect,suid) # temp value var to use in search
            # Loop through each list in Results
            for n in Results:
                if temp == n:

                    # Make call to Yahoo Finance API
                    tick = yf.Ticker(symb)

                    # Collect YTD Daily Closing Price data
                    # In future revisions, the period 
                    # and selected column can be passed as variables
                    df = tick.history(period=Period)
                    df = df['Close']
                    df = df.rename(secu)
                    
                    # Add info on security to AllDFs list
                    append = [symb, secu, sect, suid, df]
                    AllDFs.append(append)
                    
        # Display % of SP500 rows that have been iterated over so far
        i += 1
        clear_output(wait=True)
        
        print(f"{round(i/SP500.shape[0]*100,1)}%")
        #end = datetime.now()
        #print(str(end - start))
        
    return AllDFs

# Aggregate and describe data within pricing dataframes
def Aggregate_MarketData(AllDFs, SP500):
    """
    Aggregate_MarketData will aggregate data from df's in AllDFs.
    These df's will be grouped and aggregated into two types of df's:
        SeriesDFs : Time series df's used in line plots
        DescrbDFs : Descriptive statistics of the Series data sets
    Each of the above two types will be seperated into df's for
        YTD : YTD returns
        pct : rolling 5-day moving average
        prc : daily closing prices'

    Parameters
    ----------
    AllDFs : list
        AllDFs list created in Collect_MarketData function.
    SP500 : pd.DataFrame
        Dataframe created from the collectSP500list function.

    Returns
    -------
    ytdSeries : pd.DataFrame
        Times series data of daily YTD returns.
    ytdDescrb : pd.DataFrame
        Descriptive statistics of YTD returns.
    pctSeries : pd.DataFrame
        Times series data of daily 5-day moving average returns.
    pctDescrb : pd.DataFrame
        Descriptive statistics of 5-day moving average returns.
    prcSeries : pd.DataFrame
        Times series data of daily closing prices.
    prcDescrb : pd.DataFrame
        Descriptive statistics of daily closing prices.
    ytd : pd.DataFrame
        List of YTD returns for each security.

    """
    ytdSeries = []
    ytdDescrb = []
    
    pctSeries = []
    pctDescrb = []
    
    prcSeries = []
    prcDescrb = []
    
    # Collect and store data from AllDFs for the above 3 data sets
    for i in range(len(AllDFs)):
        
        # Temporary DF, contains security price info from Yahoo
        temp = AllDFs[i][-1]
        
        # Calculate rolling YTD returns, and descriptive stats
        ytdS = temp.transform(lambda x: x/x.iloc[0] - 1)
        ytdS = ytdS[~ytdS.index.duplicated()]
        ytdD = ytdS.describe()
        
        ytdSeries.append(ytdS)
        ytdDescrb.append(ytdD)
        
        # Calculate rolling 5-day returns, and descriptive stats
        pctS = temp.pct_change(periods=5)
        pctS = pctS[~pctS.index.duplicated()]
        pctD = pctS.describe()
        
        pctSeries.append(pctS)
        pctDescrb.append(pctD)
        
        # Closing price stats
        prcS = temp.copy()
        prcS = prcS[~prcS.index.duplicated()]
        prcD = prcS.describe()
        
        prcSeries.append(prcS)
        prcDescrb.append(prcD)
        
    # Concat each list of series's to create data frames for selected securities
    ytdSeries = round(pd.concat(ytdSeries,axis=1,keys=[s.name for s in ytdSeries]),4)
    ytdDescrb = round(pd.concat(ytdDescrb,axis=1,keys=[s.name for s in ytdDescrb]),4)
    ytdDescrb = adjustDF(ytdDescrb)
    
    pctSeries = round(pd.concat(pctSeries,axis=1,keys=[s.name for s in pctSeries]),4)
    pctDescrb = round(pd.concat(pctDescrb,axis=1,keys=[s.name for s in pctDescrb]),4)
    pctDescrb = adjustDF(pctDescrb)
    
    prcSeries = round(pd.concat(prcSeries,axis=1,keys=[s.name for s in prcSeries]),4)
    prcDescrb = round(pd.concat(prcDescrb,axis=1,keys=[s.name for s in prcDescrb]),4)    
    prcDescrb = adjustDF(prcDescrb)
        
    # Create sum stats of ytd performance (from most recent closing date) for the selected sub industries
    ytd = ytdSeries.iloc[-1]
    ytd = pd.DataFrame(ytd)
    ytd.reset_index(inplace=True,drop=False)
    ytd = ytd.rename(columns={'index':'Security',ytd.columns[1]:'YTD Return'})
        
    # Append ytd returns to Sum Stats df's
    ytdDescrb = ytdDescrb.merge(ytd,
                                left_on='Security',
                                right_on='Security')
    pctDescrb = pctDescrb.merge(ytd,
                                left_on='Security',
                                right_on='Security')
    prcDescrb = prcDescrb.merge(ytd,
                                left_on='Security',
                                right_on='Security')
    
    prc = prcSeries.iloc[-1]
    prc = pd.DataFrame(prc)
    prc.reset_index(inplace=True,drop=False)
    prc = prc.rename(columns={'index':'Security',prc.columns[1]:'Price'})    
    
    # Append most recent closing price and Sub Industry to Sum Stats df's
    # These values will be added to the annotations of the plotly figures
    ytdDescrb = ytdDescrb.merge(prc,
                                left_on='Security',
                                right_on='Security')
    ytdDescrb['Sub Sector'] = ytdDescrb.apply(lambda x: identSubSect(x['Security'],SP500),axis=1)
    
    pctDescrb = pctDescrb.merge(prc,
                                left_on='Security',
                                right_on='Security')
    pctDescrb['Sub Sector'] = pctDescrb.apply(lambda x: identSubSect(x['Security'],SP500),axis=1)
    
    prcDescrb = prcDescrb.merge(prc,
                                left_on='Security',
                                right_on='Security')
    prcDescrb['Sub Sector'] = prcDescrb.apply(lambda x: identSubSect(x['Security'],SP500),axis=1)
    
    # Reset order of columns for each descriptive stats df
    keys = ['Security','Sub Sector','Price','YTD Return','mean','std','min','max']

    ytdDescrb = ytdDescrb[keys]
    pctDescrb = pctDescrb[keys]
    prcDescrb = prcDescrb[keys]
    
    return ytdSeries, ytdDescrb, pctSeries, pctDescrb, prcSeries, prcDescrb, ytd

# Create interactive plotly visuals of selected securities data
 ## Line plot (`df`). Usually the closing prices, but can be 5 day rolling average or YTD returns `series` data
 ## Scatter plot (`ss`). Should be the YTD returns `descriptive` data
def Plot_MarketData(df, ss, ytd, SearchFor, 
                    reg="ols", top10=True, pct=True, 
                    YTD=True, invert=True, regAll=True): 
    """
    

    Parameters
    ----------
    df : pd.DataFrame
        The time series df that will be used in the plotly line plot.
        
    ss : pd.DataFrame
        The descriptive stats df that will be used in the plotly scatter plot.
        
    ytd : pd.DataFrame
        The YTD summary df. 
        
    SearchFor : str
        The sector or sub industry selected by user.
        
    reg : str, optional
        Regression method for trendlines in the plotly scatter plot.
        Options : '','ols','lowess'
        The default is "ols".
        
    top10 : boolean, optional
        If True, then the top 10 YTD return performers will be returned. 
        The default is True.
        
    pct : boolean, optional
        If True, the plot will be formatted for the pct df's. 
        The default is True.
    
    YTD : boolean, optional
        If True, the plot will be formatted for the YTD df's. 
        The default is True.
    
    invert : boolean, optional
        If True, the mean-vol plot will be inverted so that 
            vol is on the x-axis, and
            mean returns are on the y-axis. 
        The default is True.
    
    regAll : boolean, optional
        If True, then trendlines will be calculated for each sub industry in plot. 
        The default is True.

    Returns
    -------
    fig : plotly line plot
        Interactive line plot showing selected time series data.
    sct : plotly scatter plot
        Interactive scatter plot showing selected descriptive stats data.

    """
    # Determine title to use in plots
    if pct == True:
        
        if YTD == True:
            title = " YTD Rolling Returns"
        else:
            title = " 5 Day Rolling Returns"
            
    else:
        
        title = " Daily Closing Prices"
            
    fig = px.line(df,
                  #x="Date", Investigate the animate features of plotly
                  title=SearchFor + title,
                  #animation_frame="Date",
                  width=1150,
                  height=750)
    
    # If the user wants an inverted view, change x and y axis's
    if invert == True:
        xdata = 'std'
        ydata = 'mean'
    else:
        xdata = 'mean'
        ydata = 'std'
    
    # Drop securities with np.nan values from mean-var dataframe
    ss = ss.dropna(axis=0)
    
    # Plot mean-var data
    if regAll == True:
        # If regAll == True, then calculate trendlines for each industry
        sct = px.scatter(ss,x=xdata,y=ydata,
                         title=SearchFor + title,
                         color='Sub Sector',
                         size='Price',
                         hover_data=['Security','Sub Sector','YTD Return','min','max'],
                         trendline=reg,  # 'ols' or 'lowess'
                         width = 1150,height=750)
        
    else:
        # If regAll == False, then calculate one trendline for all securities
        sct = px.scatter(ss,x=xdata,y=ydata,
                         title=SearchFor + title,
                         size='Price',
                         hover_data=['Security','Sub Sector','YTD Return','min','max'],
                         trendline=reg,  # 'ols' or 'lowess'
                         width = 1150,height=750)
    return fig, sct
    
# Collect `Top 10` YTD performers
def Collect_Top10(ytd,ytdSeries,ytdDescrb,pctSeries, pctDescrb,prcSeries, prcDescrb):
    """
    Collect_Top10 will refine the df's created from the Aggregate_MarketData function
    to include only the top 10 YTD return performers. All df's are refined to include 
    data for the top 10 YTD performers, as measuerd by YTD return

    Parameters
    ----------
    ytd : pd.DataFrame
        Df of current YTD returns for all selected securities.
    ytdSeries : pd.DataFrame
        Time series data for  YTD returns.
    ytdDescrb : pd.DataFrame
        Descriptive stats for YTD returns.
    pctSeries : pd.DataFrame
        Time series data for 5-day rolling avg returns.
    pctDescrb : pd.DataFrame
        Descriptive stats for 5-day rolling avg returns.
    prcSeries : pd.DataFrame
        Time series data for closing prices.
    prcDescrb : pd.DataFrame
        Descriptive stats for closing prices.

    Returns
    -------
    Top10keys : list
        DESCRIPTION.
    Top10indx : pd.Index
        DESCRIPTION.
    ytdSeries : pd.DataFrame
        Time series data for top 10 YTD returns.
    ytdDescrb : pd.DataFrame
        Descriptive stats for top 10 YTD returns.
    pctSeries : pd.DataFrame
        Time series data for top 10 5-day rolling avg returns.
    pctDescrb : pd.DataFrame
        Descriptive stats for top 10 5-day rolling avg returns.
    prcSeries : pd.DataFrame
        Time series data for top 10 closing prices.
    prcDescrb : pd.DataFrame
        Descriptive stats for top 10 closing prices.
    ytd : pd.DataFrame
        Df of current top 10 YTD returns for all selected securities.

    """
    # Identify Top 10 YTD returns across all selected securities
    ytd.sort_values(by=['YTD Return'],axis=0,ascending=False,inplace=True)
    ytd.reset_index(inplace=True,drop=True)
    ytd = ytd[0:10]
    
    # List of keys used to refine `Series` DF's 
    Top10keys = list(ytd.Security) 
    # List of index values used to refine `ytd Descriptive` DF
    Top10indx = [ytdDescrb[ytdDescrb.Security == sec].index.max() for sec in Top10keys] 
    
    # Refine the `Series` & `Descriptive` DF's to include only Top 10 performers
    ytdSeries = ytdSeries[Top10keys]
    ytdDescrb = ytdDescrb.loc[Top10indx]
    ytdDescrb.reset_index(inplace=True,drop=True)

    # List of index values used to refine `ytd Descriptive` DF
    Top10indx = [pctDescrb[pctDescrb.Security == sec].index.max() for sec in Top10keys] 
    
    pctSeries = pctSeries[Top10keys]
    pctDescrb = pctDescrb.loc[Top10indx]
    pctDescrb.reset_index(inplace=True,drop=True)
    
    # List of index values used to refine `ytd Descriptive` DF
    Top10indx = [prcDescrb[prcDescrb.Security == sec].index.max() for sec in Top10keys] 
    
    prcSeries = prcSeries[Top10keys]
    prcDescrb = prcDescrb.loc[Top10indx]
    prcDescrb.reset_index(inplace=True,drop=True)    
    
    return Top10keys, Top10indx, ytdSeries, ytdDescrb, pctSeries, pctDescrb, prcSeries, prcDescrb, ytd

def main(SecOrSub,SearchFor,Results,SP500,Period="ytd",
         SeriesPlot="Prices",DescrbPlot="YTD",reg="ols",
         top10=True,invert=True,regAll=True):
    """
    Main function to take Results list and return DF's/plotly vis's for selected industries.
    
    This function should be run after already making calls to:
        collectSP500list() for the SP500 table,
        CollectSectors() to create a list to view the unique SP500,
        & select_str() to create an iterable list of (sector, industry)

    Parameters
    ----------
    SecOrSub : boolean
        If True, Results will be processed as a non-nested list. Assumes a list of Sec(tors) is passed
        If False, Results will be processed as a nested lists. Assumes a list of Sub (Industries) is passed.
    SearchFor : str
        String to denote sector/sub industry data is being collected for.
    Results : list
        A list of desired sectors, or sectors and sub industry, to be collected
    SP500 : pd.DataFrame
        Dataframe created from the collectSP500list function.
    Period : pd.DataFrame
        String object to identify which period to use in Collect_MarketData
    SeriesPlot : str, optional
        The time series data that will be used in the line plot. 
        The default is "Prices". 
        Options : "Prices", "YTD", "PCT"
    DescrbPlot : str, optional
        The descriptive stats that will be used in the scatter plot. 
        The default is "Prices". 
        Options : "Prices", "YTD", "PCT"
    reg : str, optional
        The regression method used for the plotly trendlines. 
        The default is "ols".
        options : '','ols','lowess'
    top10 : boolean, optional
        If True, the top 10 YTD performers of the results will be returned. 
        If False, all securities that fit in the Results parameters will be returned.
        The default is True.
    invert : boolean, optional
        If True, the mean-vol plot will be inverted so that volatility is on the x axis. 
        The default is True.
    regAll : boolean, optional
        If True, a trendline will be returned for all unique sub industries.
        If False, a trendline will be returned to describe all 
        sectors/industries included in data set
        The default is True.

    Returns
    -------
    fig : plotly line plot
        A line plot showing the selected time series data.
    sct : plotly scatter plot
        A scatter plot showing the selected descriptive stats.
    ytd : pd.DataFrame
        A df that contains YTD returns of the final securities.

    """    
    # Collect the market data from Yahoo Finance
    AllDFs = Collect_MarketData(SecOrSub=SecOrSub,Results=Results,SP500=SP500, Period=Period)
    
    # Aggregate and describe data collected from Yahoo
    ytdSeries, ytdDescrb, \
    pctSeries, pctDescrb, \
    prcSeries, prcDescrb, ytd = Aggregate_MarketData(AllDFs, SP500)
    
    # Collect Top10 YTD performers if top10==True
    if top10 == True:
        Top10keys, Top10indx, \
        ytdSeries, ytdDescrb, \
        pctSeries, pctDescrb, \
        prcSeries, prcDescrb, ytd = Collect_Top10(ytd,
                                                  ytdSeries, ytdDescrb,
                                                  pctSeries, pctDescrb,
                                                  prcSeries, prcDescrb)
        
    # Determine which DF's to use as the line plot, and scatter plot
    if SeriesPlot == 'Prices':
        linePlot = prcSeries
        pct = False
        YTD = False
    elif SeriesPlot == 'PCT':
        linePlot = pctSeries
        pct = True
        YTD = False
    elif SeriesPlot == 'YTD':
        linePlot = ytdSeries
        pct = True
        YTD = True
    else: 
        # Default to the price series
        linePlot = prcSeries
        
    if DescrbPlot == 'Prices':
        scattPlot = ytdDescrb
    elif DescrbPlot == 'PCT':
        scattPlot = pctDescrb
    elif DescrbPlot == 'YTD':
        scattPlot = ytdDescrb
    else: 
        # Default to the YTD returns
        scattPlot = ytdDescrb        
    
    # Create line and scatter plots of selected data
    fig, sct = Plot_MarketData(df=linePlot,
                               ss=scattPlot,
                               ytd=ytd,
                               SearchFor=SearchFor,
                               reg=reg,
                               pct=pct,
                               YTD=YTD,
                               invert=invert,
                               regAll=regAll)
    
    return fig, sct, ytd, linePlot, scattPlot

# Call necessary functions which wil have the results passed to create widgets
SP500, temp = collectSP500list()
secs,subs,both = CollectSectors(SP500)
secs.append('')

def Create_Widgets(secs,both):
    """
    Create_Widgets will create a variety of interactive widgets that 
    enable users in jupyter notebooks to explore data. Users can:
        identify the Sector and/or Industry to collect data for, 
        select which time series and descriptive stats df's will 
        be used in the respective plots, 
        and select regression method, Top 10 YTD returns, 
        & how many trendlines should be returned
        
    Copy and paste the following code into a Jupyter notebook to create the interactive plot
    `````````````````````````````````
        SecDropD,IndDropD,SeriesDrop, \
        ScatterDrop,RegresDrop,IndCheck, \
        Top10Check,RegCheck,goButton = Create_Widgets(secs,both)
        ````````````````````
        @interact
        def change_list(sectors=SecDropD,
                        check=IndCheck,
                        industry=IndDropD,
                        series=SeriesDrop,
                        scatter=ScatterDrop,
                        regMeth=RegresDrop,
                        top10=Top10Check,
                        reg=RegCheck):

            if SecDropD.value == '':
                inds = subs
            else:
                inds = [i[1] for i in both if i[0] == SecDropD.value]
            
            IndDropD.options = inds
            
            clear_output(wait=True)
            display(goButton)        
    `````````````````````````````````

    Parameters
    ----------
    secs : list
        List of unique sectors created from CollectSectors function.
    both : list
        Nested list of unique sectors and industries.

    Returns
    -------
    SecDropD : ipywidget drop down object
        Drop down list containing unique sectors listed on SP500.
    IndDropD : ipywidget drop down object
        Drop down list containing unique industries w/in selected sector (from SecDropD).
        Using the following list comprehension,
            [i[1] for i in both if i[0] == SecDropD.value],
        with the @interact feature in jupyter notebooks, allows this drop down to be 
        refreshed with the list of unique industries in the selected sector.
    SeriesDrop : ipywidget drop down object
        Drop down list whose value is used to identify which df to use in time series plot.
    ScatterDrop : ipywidget drop down object
        Drop down list whose value is used to identify which df to use in scatter plot.
    RegresDrop : ipywidget drop down object
        Drop down list containing three available regression methods in plotly.
    PeriodDrop : ipywidget drop down object
        Drop down list containig list of valid periods to collect data for.
        1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    IndCheck : ipywidget check box object
        Check box object used to denote if a user wants to look at just one.
    Top10Check : TYPE
        DESCRIPTION.
    RegCheck : TYPE
        DESCRIPTION.
    goButton : TYPE
        DESCRIPTION.

    """
    style = {'description_width': 'initial'}
    # Create drop down list of all sectors
    SecDropD = widgets.Dropdown(options=secs,
                                value=secs[0],
                                description='Sectors: ',
                                disabled=False,
                                style=style)
    
    # Create list of sub industries for first sector, then create drop down list for these industries
    inds = [i[1] for i in both if i[0] == SecDropD.value]
    IndDropD = widgets.Dropdown(options=inds,
                                value=inds[0],
                                description='Industries:',
                                disabled=False,
                                style=style)
    
    # Create drop down list to select which series data will be provided in top plot
    SeriesDrop = widgets.Dropdown(options=['Prices','YTD','PCT'],
                                  value='Prices',
                                  disabled=False,
                                  description='Time Series Data',
                                  indent=False,
                                  style=style)
    
    # Create drop down list to select which series data will be provided in top plot
    ScatterDrop = widgets.Dropdown(options=['Prices','YTD','PCT'],
                                   value='YTD',
                                   disabled=False,
                                   description='Scatter Plot Data',
                                   indent=False,
                                   style=style)
    # Create drop down list to select which regression method should be
    # applied for trendlines in the scatterplot
    RegresDrop = widgets.Dropdown(options=['','ols','lowess'],
                                  value='ols',
                                  disabled=False,
                                  description='Regression Method',
                                  indent=False,
                                  style=style)
    # Create drop down list to select which preiod to collect data for
    PeriodDrop = widgets.Dropdown(options=["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"],
                                  value="ytd",
                                  disabled=False,
                                  description='Preiod',
                                  indent=False,
                                  style=style)
    
    # Create check box for refining data to a specific sub industry
    IndCheck = widgets.Checkbox(Value=False,
                                description='Industry Specific',
                                disabled=False,
                                indent=False,
                                style=style)
    
    # Create check box for refining data to Top10 or not
    Top10Check = widgets.Checkbox(Value=True,
                                  description='Top 10 YTD Returns:',
                                  disabled=False,
                                  indent=False,
                                  style=style)
    
    # Create check box for refining data to Top10 or not
    RegCheck = widgets.Checkbox(Value=True,
                                description='Multiple Trend Lines:',
                                disabled=False,
                                indent=False,
                                style=style)    
    
    # Create Go Button that will make calls to `md` module and create interactive plots
    goButton = widgets.Button(value=False,
                              description='Create Figures',
                              disabled=False,
                              button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                              tooltip='Description',
                              icon='check', # (FontAwesome names without the `fa-` prefix)
                              style=style)
    
    def click_button(b):
        clear_output(wait=False)
        if IndCheck.value==True:
            SearchFor = IndDropD.value
            Results = select_str(both,SearchFor)

        else:
            SearchFor = SecDropD.value
            Results = select_str(both,SearchFor)
            
            if SearchFor == '':
                Results=both
        
        global linePlot
        fig, sct, ytd, linePlot, scattPlot = main(False,SearchFor,Results,SP500,PeriodDrop.value,
                                                  SeriesPlot=SeriesDrop.value,DescrbPlot=ScatterDrop.value,
                                                  top10=Top10Check.value,reg=RegresDrop.value,regAll=RegCheck.value)
        
        fig.show()
        sct.show()
        #print(ytd)
        return linePlot
        
    goButton.on_click(click_button)
             
    return SecDropD,IndDropD,SeriesDrop,ScatterDrop,RegresDrop,PeriodDrop,IndCheck,Top10Check,RegCheck,goButton
