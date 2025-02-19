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
conn = sqlite3.connect('NBAData.db')
curr = conn.cursor()
curr.execute('delete from data where id > 1240')
curr.execute('update sqlite_sequence SET seq = 1240 WHERE name = :data', {'data' : 'data'})
curr.execute('delete from teamAnalytics where id > 381')
curr.execute('update sqlite_sequence SET seq = 381 WHERE name = :data', {'data' : 'teamAnalytics'})
curr.execute('delete from teamARAnalytics where id > 381')
curr.execute('update sqlite_sequence SET seq = 381 WHERE name = :data', {'data' : 'teamARAnalytics'})
conn.commit()
conn.close()
#
#
#curr.execute('''CREATE TABLE IF NOT EXISTS lastGameRead(id int)''')
#curr.executemany('''INSERT INTO data VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', scrape.statSheet)