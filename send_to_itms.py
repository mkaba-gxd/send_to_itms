import os
import sys
import argparse
import pymysql
import pandas as pd
import datetime
import warnings
from pathlib import Path
from modules import *

VERSION="v2.1.0"

def main():

    if '--help' in sys.argv or '-h' in sys.argv:
        print(f"version: {VERSION}")

    parser = argparse.ArgumentParser(description="Data Creation Tool for iTMS Sending.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--listfile","-f", required=False, help="List of samples to be transferred.", default=None)
    parser.add_argument("--sample","-s", required=False, help="sample ID", default=None)
    parser.add_argument("--directory","-d", required=False, help="parent analytical directory", default="/data1/data/result")
    parser.add_argument("--transfer","-t", required=False, help="working directory", default="/data1/work/send_to_ITMS")
    parser.add_argument("--preparation","-p", required=False, help="Preparation only", action='store_true')
    parser.add_argument('--version','-v', action='version', version=f'%(prog)s {VERSION}')
    args = parser.parse_args()
    run_sendData(args)

if __name__ == "__main__":

    main()

