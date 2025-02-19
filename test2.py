import sqlite3
conn = sqlite3.connect('NBAData.db')
curr = conn.cursor()

print (curr.fetchall())