import pandas as pd
import numpy as np
import datetime as dt
from datetime import *
import time
import os
import xlwings as xw

# Define function to identify the row number to add data to
def IdentRow(ACCT, ac):
    # Inputs :  [ACCT = 6 digit lvl 6 account code,
    #            ac = Account Codes dataframe collected from wkbk]
 
    result = ac[(ac.Lower <= ACCT) & (ac.Upper >= ACCT)]['Row']
    
    if len(result) == 0:
        return 0
    else:
        return result.max()
    
# Define functin to identify the sheet to add data to    
def IdentSheet(Speedtype, cl):
    # Inputs :  [Speedtype = Speedtype associated with record being processed.
    #                        Format: 8 digit ST code + " -- " + ST Description/Name,
    #            cl = Consolidation Lists dataframe collected from wkbk]
 
    result = cl[cl.Speedtype == Speedtype]['Consolidate Into']

    if len(result) == 0:
        return 'None'
    else:   
        return result.max()

# Define function to identify the Fund Balance tied to a program
def IdentFB(Speedtype, cl):
    # Inputs :  [Speedtype = Speedtype associated with record being processed.
    #                        Format: 8 digit ST code + " -- " + ST Description/Name,
    #            cl = Consolidation Lists dataframe collected from wkbk]
    
    result = cl[cl.Speedtype == Speedtype]['Fund Balance']
    
    if len(result) == 0:
        return 'None'
    else:
        return result.max()

# Define function to classify `PD` into each quarter
def IdentQuart(PD):
    # Inputs :  [PD = Period associated with record being processed]
    
    if PD < 4:
        return 1
    elif PD < 7:
        return 2
    elif PD < 10:
        return 3
    else:
        return 4

# Define function to classify data into columns w/in the Seasonal Budget report
def IdentCol(Yrs, Start, FY, Q, BudOrAct):
    # Inputs : [Yrs = # of years of historical data,
    #           Start = First FY of data,
    #           FY = FY associated with record being processed,
    #           Q = Quarter associated with record being processed,
    #           BudOrAct = True/False value to determine if
    #                      budget column or actuals column should be returned]
    
    # Adjust FY value to be just the last two digits from the record being processed
    FY = FY - 2000
    
    # Determine which column to add data to 
    if BudOrAct == True:        # Return budget column
        Col = Start + Yrs - 1 - FY
        return Col + 3
    else:                       # Return Actuals column
        Col = (Q * (Yrs + 1)) + (Start + Yrs - 1 - FY)
        return Col + 3
    
# Define the main function used to compile data from the Rev/Exp Summary file
def RnE():
    key = xw.apps.keys()
    key = xw.apps.keys()
    key = key[0]
    wb = xw.apps[key].books['Finance Board Report Generator - Python Test.xlsm']

    # Collect `Account Code` & `Consolidation Lists` references
    ac = wb.sheets('Account Codes')
    ac = ac.range('a1:f400').options(pd.DataFrame).value
    ac = ac.dropna(axis=0)

    cl = wb.sheets('Consolidation Lists')
    cl = cl.range('a1:e2000').options(pd.DataFrame).value
    cl = cl.dropna(axis=0)

    # Identify `Cost Center`, `Quarter`, `Fiscal Year`
    sht = wb.sheets['Create Report']
    CC = sht.range('e3').value
    Quarter = sht.range('e4').value
    FY = sht.range('e5').value
    
    # Collect data from the `Rev. & Exp. Summary` workbook
    # and then format and create temp file to use in VBA scripts
    cl = cl[cl['Cost Center'] == CC]
    cl.reset_index(inplace=True, drop=True)

    # Collect `Rev. & Exp. Summary` data
    path = wb.sheets['Create Report'].range('b17').value
    re = pd.read_csv(f"{path}")    

    start = datetime.now()
    re['ACCT_Code'] = re.ACCT.str[:6].astype(int)
    re = re[['ACCT', 'ACCT_Code', 'SPDTYPE', 'BUDGET',
             'ACTUALS', 'ENCUMBS', 'PRIOR YEAR ACTUALS']]
    
    # Add columns to `re` for the `Row`, `Program`, and `Fund Balance`
    # that will be used to classify data into program sheets
    re['Row'] = re.apply(lambda x: IdentRow(x['ACCT_Code'], ac), axis=1)
    re['Program'] = re.apply(lambda x: IdentSheet(x['SPDTYPE'], cl), axis = 1)
    re['Fund Balance'] = re.apply(lambda x: IdentFB(x['SPDTYPE'], cl), axis = 1)

    re = re[['Fund Balance','Program','Row',
             'BUDGET', 'ACTUALS', 'ENCUMBS','PRIOR YEAR ACTUALS',
             'SPDTYPE','ACCT_Code','ACCT']]

    # If there are unidentified speedtypes/programs ('None' values)
    # or row numbers (0 values) then resize DF for VBA scripts
    if 'None' in re.Program.unique():
        re = re[re.Program == 'None']
        
    elif 0 in re.Row.unique():
        re = re[re.Row == 0]
    
    end = datetime.now()
    
    wb.sheets['Data'].range('a1').value = re
    wb.sheets['Data'].range('a1').value = str(end - start)
    
def FD():
    key = xw.apps.keys()
    key = key[0]
    wb = xw.apps[key].books['Finance Board Report Generator - Python Test.xlsm']
    
    # Collect `Account Code` & `Consolidation Lists` references
    ac = wb.sheets('Account Codes')
    ac = ac.range('a1:f400').options(pd.DataFrame).value
    ac = ac.dropna(axis=0)

    cl = wb.sheets('Consolidation Lists')
    cl = cl.range('a1:e2000').options(pd.DataFrame).value
    cl = cl.dropna(axis=0)

    # Identify `Cost Center`, `Quarter`, `Fiscal Year`
    sht = wb.sheets['Create Report']
    CC = sht.range('e8').value
    YRS = sht.range('e9').value
    START = sht.range('e10').value

    # Collect `Financial Detail II` data
    path = wb.sheets['Create Report'].range('b17').value
    fd = pd.read_csv(f"{path}")

    start = datetime.now()  # Start timer
    
    # Concat ST columns to match CL table
    fd['SPDTYPE'] = fd['SPDTYPE CODE'].astype(str) + " -- " + fd['SPDTYPE DESC']

    # Remove unnecessary columns, fill empty ranges with `0`
    fd = fd[['ACCT CODE', 'ACCT', 'SPDTYPE', 'BUDGET', 'ACTUALS', 'FY', 'PD']]
    fd.fillna(0,axis=1,inplace=True)

    # Add columns to `fd` for the `Quarter`, `Fund Balance`, `Program`,
    # `Row`, and `Column` that will be used to add data to classify data
    # into program sheets, rows and columns
    fd['Quarter'] = fd.apply(lambda x: IdentQuart(x['PD']), axis=1)
    fd.drop(['PD'], axis=1, inplace=True)

    # Group `fd` to condense its size (1)
    fd = fd.groupby(by=['SPDTYPE', 'FY', 'Quarter', 'ACCT CODE', 'ACCT']).sum()
    fd.reset_index(inplace=True)

    # Apply functions for `Fund Balance` and `Program` 
    fd['Fund Balance'] = fd.apply(lambda x: IdentFB(x['SPDTYPE'], cl), axis=1)
    fd['Program'] = fd.apply(lambda x: IdentSheet(x['SPDTYPE'], cl), axis=1)

    # Group `fd` again to further reduce the table size (2)
    fd = fd.groupby(by=['Fund Balance','Program','SPDTYPE',
                        'FY','Quarter','ACCT CODE','ACCT']).sum()
    fd.reset_index(inplace=True)

    # Apply function to determine corresponding row for all records
    fd['Row'] = fd.apply(lambda x: IdentRow(x['ACCT CODE'], ac), axis=1)
    fd.drop(['ACCT CODE'],axis=1,inplace=True)

    # Group `fd` again to further reduce the table size (3)
    fd = fd.groupby(by=['Fund Balance','Program','SPDTYPE',
                        'FY','Quarter','Row','ACCT']).sum()
    fd.reset_index(inplace=True)

    # Apply function to determine corresponding budget
    # and actuals column for all records
    fd['BudColumn'] = fd.apply(lambda x:
                               IdentCol(YRS, START, x['FY'], x['Quarter'], True), axis=1)
    fd['ActColumn'] = fd.apply(lambda x:
                               IdentCol(YRS, START, x['FY'], x['Quarter'], False), axis=1)

    # Group `fd` again to further reduce the table size (4)
    fd = fd.groupby(by=['Fund Balance', 'Program', 'SPDTYPE',
                        'FY', 'Quarter','Row', 'BudColumn',
                        'ActColumn', 'ACCT']).sum()
    fd.reset_index(inplace=True)
                               
    # Reorder columns to match VBA scripts
    fd = fd[['Fund Balance','Program','FY','Quarter','Row','BudColumn',
             'ActColumn','BUDGET', 'ACTUALS','SPDTYPE','ACCT']]

    # If there are unidentified speedtypes/programs ('None' values)
    # or row numbers (0 values) then resize DF for VBA scripts
    if 'None' in fd.Program.unique():
        fd = fd[fd.Program == 'None']
        
    elif 0 in fd.Row.unique():
        fd = fd[fd.Row == 0]
        
    end = datetime.now()    # Stop timer
    
    wb.sheets['Data'].range('a1').value = fd                # Add `fd` dataframe to excel
    wb.sheets['Data'].range('a1').value = str(end - start)  # Add processing time to excel
