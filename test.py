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
curr.execute('CREATE TABLE IF NOT EXISTS lastGamePlayed(lastGameNum int)')
curr.execute('insert into lastGamePlayed (lastGameNum) values (?)', (22400061,))
curr.execute('''CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    team TEXT,
    opponent TEXT,
    position TEXT,
    home BOOLEAN,
    win BOOLEAN,
    matchupName1 TEXT,
    matchupMins1 TEXT,
    matchupPoints1 real,
    matchupName2 TEXT,
    matchupMins2 TEXT,
    matchupPoints2 real,
    RAm REAL,
    RAa REAL,
    RAp REAL,
    Paintm REAL,
    Painta REAL,
    Paintp REAL,
    Midm REAL,
    Mida REAL,
    Midp REAL,
    Corner3m REAL,
    Corner3a REAL,
    Corner3p REAL,
    AB3m REAL,
    AB3a REAL,
    AB3p REAL,
    passes rael,
    assists real,
    PA real,
    APp REAL,
    rebounds real,
    CRB real,
    CRBp REAL,
    RBC real,
    RBCp REAL,
    RBd REAL,
    gamesPlayed INTEGER,
    gameId INTEGER
)''')
curr.execute('''create table if not exists teamAnalytics(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             team text,
             opponent text,
             oppTeam text,
             position text,
             win boolean,
             home boolean,
             primaryDef text,
             ZRAm real,
             ZRAa real,
             ZRAp real,
             ZPaintm real,
             ZPainta real,
             ZPaintp real,
             ZMidm real,
             ZMida real,
             ZMidp real,
             ZCorner3m real,
             ZCorner3a real,
             ZCorner3p real,
             ZAB3m real,
             ZAB3a real,
             ZAB3p real)''')
curr.execute('''create table if not exists playerARAnalytics(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name text,
             team text,
             opponent text,
             position text,
             win boolean,
             home boolean,
             primaryDef text,
             ZZpasses real,
             ZZassists real,
             ZZPA real,
             ZZAPp real,
             ZZrebounds real,
             ZZCRB real,
             ZZCRBp real,
             ZZRBC real,
             ZZRBCp real)''')
curr.execute('''create table if not exists teamARAnalytics(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             team text,
             opponent text,
             oppTeam text,
             position text,
             win boolean,
             home boolean,
             primaryDef text,
             Zpasses real,
             Zassists real,
             ZPA real,
             ZAPp real,
             Zrebounds real,
             ZCRB real,
             ZCRBp real,
             ZRBC real,
             ZRBCp real)''')
curr.execute('''create table if not exists playerAnalytics(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             player text,
             team text,
             opponent text,
             position text,
             win boolean,
             home boolean,
             primaryDef text,
             ZZRAm real,
             ZZRAa real,
             ZZRAp real,
             ZZPaintm real,
             ZZPainta real,
             ZZPaintp real,
             ZZMidm real,
             ZZMida real,
             ZZMidp real,
             ZZCorner3m real,
             ZZCorner3a real,
             ZZCorner3p real,
             ZZAB3m real,
             ZZAB3a real,
             ZZAB3p real)''')
conn.commit()
curr.execute('select * from lastGamePlayed')
print(curr.fetchone()[0])
conn.close()
#
#
#curr.execute('''CREATE TABLE IF NOT EXISTS lastGameRead(id int)''')
#curr.executemany('''INSERT INTO data VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', scrape.statSheet)