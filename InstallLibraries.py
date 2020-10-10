# This module will help users install the necessary python libraries.
# In order for this to work properly, the user must have already downloaded
# and installed Python 3.7.8 or later.
import pip, os
import sys
import subprocess

from pip._internal import main as pipmain

def install(package):
    #os.system(f"python -m pip install {package}")
    subprocess.check_output(f"{sys.executable} -m pip install {package}",shell=True)
    #pipmain(['install', package])
"""
    #subprocess.call([sys.executable,
                           '-m',
                           'pip',
                           'install',
                           package])
"""
def main():
    #install('pywin32')
    install('comtypes==1.1.4')
    install('xlwings==0.19.5')
    install('pip')
    install('pandas')
    install('numpy')
    install('datetime')

def test():
    #import pywin
    #import comtypes
    import xlwings
    
    os.system('date')
    

main()
test()
