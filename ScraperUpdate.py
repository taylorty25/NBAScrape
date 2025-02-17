from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from datetime import datetime
import sqlite3
conn = sqlite3.connect('NBADataTest.db')
curr = conn.cursor()
curr.execute('select * from data where (name = :name) and (position = :pos)', {'name' : })
curr.close
#
#
#curr.execute('''CREATE TABLE IF NOT EXISTS lastGameRead(id int)''')
#curr.executemany('''INSERT INTO data VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', scrape.statSheet)