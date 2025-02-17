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
import statistics


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

conn = sqlite3.connect('NBADataTest.db')
nicknames = {
    'Jimmy Butler': 'Jimmy Butler III',
    'Alexandre Sarr': 'Alex Sarr',
    'Carlton Carrington' : 'Bub Carrington'
}
PATH = "C:\Program Files (x86)\chromedriver.exe"
abPATH = "C:\Program Files (x86)\AdBlock.crx"
service = Service(executable_path=PATH)
today = datetime.now()
firstgame = 22400061
curr = conn.cursor()

statTypes = ('RA', 'Paint', 'Mid', 'Corner3', 'AB3')
statTypesTypes = ('m', 'a', 'p')
ARTypes = ('passes','assist', 'PA', 'APp', 'rebounds', 'CRB', 'CRBp', 'RBC', 'RBCp')

class Box:
    def __init__(self):
        with conn:
            curr.execute('SELECT * FROM lastGamePlayed')
            self.lastReadGame = int(curr.fetchone()[0])
        self.boxScoreUrl = f'https://www.nba.com/game/00{self.lastReadGame}/box-score'
        self.overviewUrl = f'https://www.nba.com/game/00{self.lastReadGame}'
        self.matchupUrl = f'https://www.nba.com/game/00{self.lastReadGame}/box-score?dir=D&sort=matchupMinutesSort&type=matchups'
        self.date = ''
        self.name = ''
        self.position = ''
        self.statSheet = []
        self.firstgame = 22400061
        self.n = 0
        self.driver = webdriver.Chrome(service=service)

    def DateScrape(self):
        try:
            self.driver.get(self.overviewUrl)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'MatchupCard_team__a_Pzk')))
            date_element = self.driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/div[2]/section[2]/div/div[2]/div[2]')
            self.date = datetime.strptime(date_element.text, '%B %d, %Y')
            scores = self.driver.find_elements(By.CLASS_NAME, 'MatchupCard_team__a_Pzk')
            if len(scores) >= 2:
                self.away_points = int(scores[0].text)
                self.home_points = int(scores[1].text)
                self.awayWin = self.away_points > self.home_points
                self.homeWin = self.home_points > self.away_points
                for element in self.statSheet:
                    self.home = element['home']
                    self.away = not self.home
                    self.win = ((self.away) and (self.awayWin)) or ((self.home) and (self.homeWin))
                    self.loss = not self.win
                    element['win'] = self.win
        except Exception as e:
            print(f"Error fetching game data: {e}")

    def BoxScoreScraper(self):
        try:
            self.driver.get(self.boxScoreUrl)
            teams = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'GameBoxscore_gbTableSection__zTOUg')))
            teamNames = self.driver.find_elements(By.CLASS_NAME, 'GameBoxscoreTeamHeader_gbt__b9B6g')
            self.awayTeamName = teamNames[0].text
            self.homeTeamName = teamNames[1].text
            for index, team in enumerate(teams):
                players = team.find_elements(By.TAG_NAME, 'tr')[:6]
                if index == 0:
                    self.away = True
                    self.team = self.awayTeamName
                    self.opponent = self.homeTeamName
                    self.home = not self.away
                else:
                    self.away = False
                    self.team = self.homeTeamName
                    self.opponent = self.awayTeamName
                    self.home = not self.away
                for player in players:
                    try:
                        name = player.find_element(By.CLASS_NAME, 'GameBoxscoreTablePlayer_gbpNameFull__cf_sn').text
                        position = player.find_element(By.CLASS_NAME, 'GameBoxscoreTablePlayer_gbpPos__KW2Nf').text
                        self.statSheet.append({
                            'name': name,
                            'team': self.team,
                            'opponent': self.opponent,
                            'position': position,
                            'home': self.home})
                    except Exception as e:
                        print(f"Error fetching player data: {e}")
        except Exception as e:
            print(f"Error loading box score page: {e}")     

    def MatchupScraper(self):
        try:
            for index, element in enumerate(self.statSheet):
                self.driver.get(self.matchupUrl)
                waiter = WebDriverWait(self.driver, 10)
                waiter.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                button = Select(self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div[2]/div[2]/div[1]/label/div/select"))
                self.name = element['name']
                try:
                    button.select_by_visible_text(self.name)
                    time.sleep(1)
                except Exception as e:
                    if self.name in nicknames:
                        element['name'] = nicknames[self.name]
                        index -= 1
                    else:
                        print(f'chack for nickname for player:{self.name}')
                matchups = self.driver.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div[2]/div[3]/div[2]/table/tbody/*')
                for index,match in enumerate(matchups[:2]):  # Process the first match only
                    self.matchupName = match.find_element(By.XPATH, './/td[3]').text
                    self.matchupMins = match.find_element(By.XPATH, './/td[5]').text
                    self.matchupPoints = match.find_element(By.XPATH, './/td[10]').text
                    element['matchupName' + str(index + 1)] = self.matchupName
                    element['matchupMins' + str(index + 1)] = self.matchupMins
                    element['matchupPoints' + str(index + 1)] = self.matchupPoints
        except Exception as e:
            print(f'Error fetching matchup data: {e}')

    def ShootingScraper(self):
        m, d, y = self.date.strftime("%m"), self.date.strftime("%d"), self.date.strftime("%y")
        shootingScraperUrl = f'https://www.nba.com/stats/players/shooting?DistanceRange=By+Zone&DateFrom={m}%2F{d}%2F{y}&DateTo={m}%2F{d}%2F{y}'
        wait = WebDriverWait(self.driver, 10)
        for element in self.statSheet:
            self.name = element['name']
            mtries = 3
            tries = 0
            found = False
            while tries < mtries and not found:
                try:
                    self.driver.get(shootingScraperUrl)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select')))
                        button = Select(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select'))
                        button.select_by_value('-1')
                    except Exception as e:
                        pass
                    shootingScrape = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                    shootingScraper = shootingScrape.find_elements(By.XPATH, './*')
                    for shooter in shootingScraper:
                        name = shooter.find_element(By.XPATH, './/td[1]').text
                        if self.name in name:
                            found = True
                            td = shooter.find_elements(By.TAG_NAME, 'td')
                            n = 3
                            while n <= 23:
                                for type in statTypes:
                                    for typetype in statTypesTypes:
                                        catName = type + typetype 
                                        if td[n].text == '-':   
                                            element[catName] = 0.0
                                        else:
                                            element[catName] = td[n].text      
                                        n = 18 if n == 11 else n + 1
                            break  # Break out of the inner loop
                    if found:
                        break  # Break out of the outer loop
                    else:
                        print(f'{self.name} does not exist trying again') 
                        raise Exception("Shooter not found")
                except Exception as e:
                    print('reset')
                    try:
                        close_button = self.driver.find_element(By.ID, 'bx-close')  # Adjust selector
                        close_button.click()  # Add parentheses to execute the click
                        self.driver.execute_script("arguments[0].click();", close_button)
                    except Exception as e:
                        print(f"Error handling popup: {e}")
                    tries += 1

    def AssistScraper(self):
        m, d, y = self.date.strftime("%m"), self.date.strftime("%d"), self.date.strftime("%y")
        assistScraperUrl = f'https://www.nba.com/stats/players/passing?DateFrom={m}%2F{d}%2F{y}&DateTo={m}%2F{d}%2F{y}'
        wait = WebDriverWait(self.driver, 10)
        for element in self.statSheet:
            self.name = element['name']
            mtries = 3
            tries = 0
            found = False
            while tries < mtries and not found:
                try:
                    self.driver.get(assistScraperUrl)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select')))
                        button = Select(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select'))
                        button.select_by_value('-1')
                    except Exception as e:
                        pass
                    assistScrape = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                    assistScraper = assistScrape.find_elements(By.XPATH, './*')
                    for passer in assistScraper:
                        name = passer.find_element(By.XPATH, './/td[1]').text
                        if self.name in name:
                            found = True
                            element['passes'] = passer.find_element(By.XPATH, './/td[7]').text
                            element['assists'] = passer.find_element(By.XPATH, './/td[9]').text
                            element['PA'] = passer.find_element(By.XPATH, './/td[11]').text
                            element['APp'] = passer.find_element(By.XPATH, './/td[15]').text
                            break 
                    if found:
                        break  # Break out of the outer loop
                    else:
                        print(f'{self.name} does not exist trying again')
                        if tries < 2:
                            raise Exception("AR not working")
                        else:
                            element['passes'] = '0.0'
                            element['assists'] = '0.0'
                            element['PA'] = '0.0'
                            element['APp'] = '0.0'
                            tries += 1
                except Exception as e:
                    print('reset')
                    try:
                        close_button = self.driver.find_element(By.ID, 'bx-close')  # Adjust selector
                        close_button.click()  # Add parentheses to execute the click
                        self.driver.execute_script("arguments[0].click();", close_button)
                    except Exception as e:
                        print(f"Error handling popup: {e}")
                    tries += 1

    def ReboundScraper(self):
        m, d, y = self.date.strftime("%m"), self.date.strftime("%d"), self.date.strftime("%y")
        reboundingScraperUrl = f'https://www.nba.com/stats/players/rebounding?DateFrom={m}%2F{d}%2F{y}&DateTo={m}%2F{d}%2F{y}'
        wait = WebDriverWait(self.driver, 10)
        for element in self.statSheet:
            self.name = element['name']
            mtries = 3
            tries = 0
            found = False
            while tries < mtries and not found:
                try:
                    self.driver.get(reboundingScraperUrl)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select')))
                        button = Select(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select'))
                        button.select_by_value('-1')
                    except Exception as e:
                        pass
                    reboundScrape = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                    reboundScraper = reboundScrape.find_elements(By.XPATH, './*')
                    for rebounder in reboundScraper:
                        name = rebounder.find_element(By.XPATH, './/td[1]').text
                        if self.name in name:
                            found = True
                            element['rebounds'] = rebounder.find_element(By.XPATH, './/td[7]').text
                            element['CRB'] = rebounder.find_element(By.XPATH, './/td[8]').text
                            element['CRBp'] = rebounder.find_element(By.XPATH, './/td[9]').text
                            element['RBC'] = rebounder.find_element(By.XPATH, './/td[10]').text
                            element['RBCp'] = rebounder.find_element(By.XPATH, './/td[13]').text
                            element['RBd'] = rebounder.find_element(By.XPATH, './/td[14]').text
                            break
                    if found:
                        break  # Break out of the outer loop
                    else:
                        print(f'{self.name} does not exist trying again')
                        if tries < 2:
                            raise Exception("THIS SHIT STILL DONT WORK")
                        else:
                            element['rebounds'] = '0.0'
                            element['CRB'] = '0.0'
                            element['CRBp'] = '0.0'
                            element['RBC'] = '0.0'
                            element['RBCp'] = '0.0'
                            element['RBd'] = '0.0'
                            tries += 1
                except Exception as e:
                    print('reset')
                    try:
                        close_button = self.driver.find_element(By.ID, 'bx-close')  # Adjust selector
                        close_button.click()  # Add parentheses to execute the click
                        self.driver.execute_script("arguments[0].click();", close_button)
                    except Exception as e:
                        print(f"Error handling popup: {e}")
                    tries += 1
            try:
                element['gamesPlayed'] = int(element['gamesPlayed']) + 1
            except Exception as e:
                element['gamesPlayed'] = 1
            element['gameId']  = self.lastReadGame - self.firstgame + 1
    
    def CommitStatSheet(self):
        for element in self.statSheet:
            with conn: 
                curr.execute("""INSERT INTO data (
                name, team, opponent, position, home, win, 
                matchupName1, matchupMins1, matchupPoints1, 
                matchupName2, matchupMins2, matchupPoints2, 
                RAm, RAa, RAp, Paintm, Painta, Paintp, 
                Midm, Mida, Midp, Corner3m, Corner3a, Corner3p, 
                AB3m, AB3a, AB3p, passes, assists, PA, APp, 
                rebounds, CRB, CRBp, RBC, RBCp, RBd, gamesPlayed, gameId) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    (
                element["name"], element["team"], element["opponent"], element["position"], bool(element["home"]), bool(element["win"]),
                element["matchupName1"], element["matchupMins1"], float(element["matchupPoints1"]),
                element["matchupName2"], element["matchupMins2"], float(element["matchupPoints2"]),
                float(element["RAm"]), float(element["RAa"]), float(element["RAp"]), float(element["Paintm"]), float(element["Painta"]), float(element["Paintp"]),
                float(element["Midm"]), float(element["Mida"]), float(element["Midp"]), float(element["Corner3m"]), float(element["Corner3a"]), float(element["Corner3p"]),
                float(element["AB3m"]), float(element["AB3a"]), float(element["AB3p"]), float(element["passes"]), float(element["assists"]), float(element["PA"]), 
                float(element["APp"]), float(element["rebounds"]), float(element["CRB"]), float(element["CRBp"]), float(element["RBC"]), float(element["RBCp"]),
                float(element["RBd"]), float(element['gamesPlayed']), float(element["gameId"])))

    def UpdateGameId(self):
        with conn:
            curr.execute('UPDATE lastGamePlayed set lastGameNum = :lrg', {'lrg' : self.lastReadGame + 1} )

    def TeamAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                if gp > 9:
                    results = {
                        'team' : element['opponent'],
                        'opponent' : element['name'],
                        'oppTeam' : element['team'],
                        'position' : element['position'],
                        'win' : not element['win'],
                        'home' : not element['home'],
                        'primaryDef' : element['matchupName1']
                    }
                    stats = {}
                    curr.execute('Select * from data where name = :name)', {'name': self.name})
                    logs = curr.fetchall()
                    for log in logs:
                        n = 13
                        while n <= 27:
                            for type in statTypes:
                                for typetype in statTypesTypes:
                                    catName = type + typetype 
                                    if catName not in stats:
                                        stats[catName] = []
                                    stats[catName].append(float(log[n]))
                                    n += 1
                    for type in statTypes:
                        for typetype in statTypesTypes:
                            catName = type + typetype 
                            results['Z' + catName] = (element[catName] - statistics.mean(stats[catName])) / statistics.stdev(stats[catName])
                            element['Z' + catName] = results['Z' + catName]
                    curr.execute("""INSERT INTO teamAnalytics (
                        team, opponent, oppTeam, position, win, home, primaryDef, 
                        ZRAm, ZRAa, ZRAp, ZPaintm, ZPainta, ZPaintp, 
                        ZMidm, ZMida, ZMidp, ZCorner3m, ZCorner3a, ZCorner3p, 
                        ZAB3m, ZAB3a, ZAB3p) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results["team"], results["opponent"], results['oppTeam'], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZRAm"]), float(results["ZRAa"]), float(results["ZRAp"]), 
                        float(results["ZPaintm"]), float(results["ZPainta"]), float(results["ZPaintp"]), 
                        float(results["ZMidm"]), float(results["ZMida"]), float(results["ZMidp"]), 
                        float(results["ZCorner3m"]), float(results["ZCorner3a"]), float(results["ZCorner3p"]), 
                        float(results["ZAB3m"]), float(results["ZAB3a"]), float(results["ZAB3p"])))
                    
    def TeamARAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                if gp > 9:
                    results = {
                        'team' : element['opponent'],
                        'opponent' : element['name'],
                        'oppTeam' : element['team'],
                        'position' : element['position'],
                        'win' : not element['win'],
                        'home' : not element['home'],
                        'primaryDef' : element['matchupName1']
                    }
                    stats = {}
                    curr.execute('Select * from data where name = :name', {'name': self.name})
                    logs = curr.fetchall()
                    for log in logs:
                        n = 28
                        while n <= 36:
                            for ARType in ARTypes:
                                if ARType not in stats:
                                     stats[ARType] = []
                                stats[ARType].append(log[n])
                                n += 1
                    for ARType in ARTypes:
                         results['Z' + ARType] = (element[ARType] - statistics.mean(stats[ARType])) / statistics.stdev(stats[ARType])
                         element['Z' + ARType] = results['Z' + ARType]
                    curr.execute("""INSERT INTO teamARAnalytics (
                        team, opponent, oppTeam, position, win, home, primaryDef, 
                        Zpasses, Zassists, ZPA, ZAPp, Zrebounds, 
                        ZCRB, ZCRBp, ZRBC, ZRBCp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results["team"], results["opponent"], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["Zpasses"]), float(results["Zassists"]), float(results["ZPA"]), 
                        float(results["ZAPp"]), float(results["Zrebounds"]), float(results["ZCRB"]), 
                        float(results["ZCRBp"]), float(results["ZRBC"]), float(results["ZRBCp"])))
                    
    def PlayerARAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                if gp > 9:
                    results = {
                        'name' : self.name,
                        'team' : element['team'],
                        'opponent' : element['opponent'],
                        'position' : element['position'],
                        'win' : element['win'],
                        'home' : element['home'],
                        'primaryDef' : element['matchupName1']
                    }
                    stats = {}
                    curr.execute('Select * from teamARAnalytics where (team = :name) and (position = :pos)', {'name': element['opponent'], 'pos' : element['position']})
                    logs = curr.fetchall()
                    for log in logs:
                        n = 7
                        while n <= 14:
                            for ARType in ARTypes:
                                if ARType not in stats:
                                     stats[ARType] = []
                                stats['Z' + ARType].append(log[n])
                                n += 1
                    for ARType in ARTypes:
                         results['ZZ' + ARType] = (element['Z' + ARType] - statistics.mean(stats['Z' + ARType])) / statistics.stdev(stats['Z' + ARType])
                    curr.execute("""INSERT INTO playerARAnalytics (
                        name, player, team, opponent, position, win, home, primaryDef, 
                        ZZpasses, ZZassists, ZZPA, ZZAPp, ZZrebounds, 
                        ZZCRB, ZZCRBp, ZZRBC, ZZRBCp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results['name'], results["team"], results["opponent"], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZZpasses"]), float(results["ZZassists"]), float(results["ZZPA"]), 
                        float(results["ZZAPp"]), float(results["ZZrebounds"]), float(results["ZZCRB"]), 
                        float(results["ZZCRBp"]), float(results["ZZRBC"]), float(results["ZZRBCp"])
                        ))
                    
    def PlayerAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                if gp > 9:
                    results = {
                        'name' : self.name,
                        'team' : element['team'],
                        'opponent' : element['opponent'],
                        'position' : element['position'],
                        'win' : element['win'],
                        'home' : element['home'],
                        'primaryDef' : element['matchupName1']
                    }
                    stats = {}
                    curr.execute('Select * from team Analytics where (team = :name) and (position = :pos)', {'name': element['opponent'], 'pos' : element['position']})
                    logs = curr.fetchall()
                    for log in logs:
                        n = 7
                        while n <= 20:
                            for type in statTypes:
                                for typetype in statTypesTypes:
                                    catName = type + typetype 
                                    if catName not in stats:
                                        stats['Z' + catName] = []
                                    stats['Z' + catName].append(float(log[n]))
                                    n += 1
                    for type in statTypes:
                        for typetype in statTypesTypes:
                            catName = type + typetype 
                            if statistics.stdev(stats['Z' + catName]) == 0:
                                results['ZZ' + catName] = 0
                            else:
                                results['ZZ' + catName] = (element['Z' + catName] - statistics.mean(stats['Z' + catName])) / statistics.stdev(stats['Z' + catName])
                    curr.execute("""INSERT INTO playerAnalytics (
                        name, team, opponent, position, win, home, primaryDef, 
                        ZZRAm, ZZRAa, ZZRAp, ZZPaintm, ZZPainta, ZZPaintp, 
                        ZZMidm, ZZMida, ZZMidp, ZZCorner3m, ZZCorner3a, ZZCorner3p, 
                        ZZAB3m, ZZAB3a, ZZAB3p) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results['name'], results["team"], results["opponent"], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZZRAm"]), float(results["ZZRAa"]), float(results["ZZRAp"]), 
                        float(results["ZZPaintm"]), float(results["ZZPainta"]), float(results["ZZPaintp"]), 
                        float(results["ZZMidm"]), float(results["ZZMida"]), float(results["ZZMidp"]), 
                        float(results["ZZCorner3m"]), float(results["ZZCorner3a"]), float(results["ZZCorner3p"]), 
                        float(results["ZZAB3m"]), float(results["ZZAB3a"]), float(results["ZZAB3p"])))
f = 1
while f < 100:
    scrape = Box()
    scrape.BoxScoreScraper()
    scrape.DateScrape()
    scrape.MatchupScraper()
    scrape.ShootingScraper()
    scrape.AssistScraper()
    scrape.ReboundScraper()
    scrape.CommitStatSheet()
    scrape.TeamAnalytics()
    scrape.TeamARAnalytics()
    scrape.PlayerAnalytics()
    scrape.PlayerARAnalytics()
    scrape.UpdateGameId()
    print(scrape.statSheet)
    scrape.driver.close()
    f += 1

