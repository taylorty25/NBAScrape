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
# Connect to database
conn = sqlite3.connect('NBADataTest.db')

# Dictionary of names that are stored differently between the two NBA Databases(Adv & BoxScore)
# Used to find names that are stored in DB as something different
nicknames = {
    'Jimmy Butler': 'Jimmy Butler III',
    'Alexandre Sarr': 'Alex Sarr',
    'Carlton Carrington' : 'Bub Carrington',
    'Tidjane Salaün': 'Tidjane Salaun',
    #'Luka Dončić' : 'Luka Doncic',
}
# Path to driver
PATH = "C:\\Program Files (x86)\\chromedriver.exe"
service = Service(executable_path=PATH)
# First game of the season id in NBA Database
firstgame = 22400061
curr = conn.cursor()
# NBA Zone Stat Types
statTypes = ('RA', 'Paint', 'Mid', 'Corner3', 'AB3', 'FT')
# The Stat Types for each Stat Type(makes, attempts, percentage)
statTypesTypes = ('m', 'a', 'p')
# NBA Assist and Rebound Stat Types
ARTypes = ('passes','assists', 'PA', 'APp', 'rebounds', 'CRB', 'CRBp', 'RBC', 'RBCp')


# each child of class Box will step through the current game id (given by scanning the database) and webscrape the game page to find out basic game information
# such as score, teams, wins, date, then the box score page to gather more information such as position and freethrows. Next we scrape the matchup page to get
# matchups stas for opposing players. Then the advanced shooting, assists and rebound metrics and commit them into a datatbase. We then pull every players history 
# of stats from our database, and perform even more advanced analytics.
class Box:
    #constructor
    def __init__(self):
        # connect to DB and read the last game read from the database
        with conn:
            curr.execute('SELECT * FROM lastGamePlayed')
            # assign self id
            self.lastReadGame = int(curr.fetchone()[0])
        # assign urls to self for future use using game id
        self.boxScoreUrl = f'https://www.nba.com/game/00{self.lastReadGame}/box-score'
        self.overviewUrl = f'https://www.nba.com/game/00{self.lastReadGame}'
        self.matchupUrl = f'https://www.nba.com/game/00{self.lastReadGame}/box-score?dir=D&sort=matchupMinutesSort&type=matchups'
        self.date = ''
        self.name = ''
        self.position = ''
        # assign empty dictionary to self to retain information through scanning
        self.statSheet = []
        self.firstgame = 22400061
        self.n = 0
        self.driver = webdriver.Chrome(service=service)
    
    # scrape dat and team information for future use
    def DateScrape(self):
        try:
            # open url via driver
            self.driver.get(self.overviewUrl)
            # wait for s to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'MatchupCard_team__a_Pzk')))
            # assign date element via webdriver
            date_element = self.driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[3]/div[2]/div[2]/section[2]/div/div[2]/div[2]')
            # parse date element, store as self date variable
            self.date = datetime.strptime(date_element.text, '%B %d, %Y')
            # assign scores pointer via webdriver
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

    # obtain personal data such as name, position, and FreeThrow information
    def BoxScoreScraper(self):
        try:
            # get url via driver
            self.driver.get(self.boxScoreUrl)
            # wait for elements to load
            WebDriverWait(self.driver, 10).until(EC.visibility_of_all_elements_located((By.TAG_NAME, 'td')))
            # assign team names pointer via webdriver
            teamNames = self.driver.find_elements(By.CLASS_NAME, 'GameBoxscoreTeamHeader_gbt__b9B6g')
            # assign team pointer via webdriver
            teams = self.driver.find_elements(By.CLASS_NAME, 'GameBoxscore_gbTableSection__zTOUg')
            # assing away and home teams from the perspective of each player in current game
            self.awayTeamName = teamNames[0].text
            self.homeTeamName = teamNames[1].text
            # parse through the teams
            for index, team in enumerate(teams):
                players = team.find_elements(By.XPATH, './/div[2]/div[2]/div/table/tbody/*')[:5]
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
                # parse through each player
                for player in players:
                    try:
                        name = player.find_element(By.CLASS_NAME, 'GameBoxscoreTablePlayer_gbpNameFull__cf_sn').text
                        position = player.find_element(By.CLASS_NAME, 'GameBoxscoreTablePlayer_gbpPos__KW2Nf').text
                        self.statSheet.append({
                            'name': name,
                            'team': self.team,
                            'opponent': self.opponent,
                            'position': position,
                            'home': self.home,
                            'FTm' : player.find_element(By.XPATH, './/td[9]').text,
                            'FTa' : player.find_element(By.XPATH, './/td[10]').text,
                            'FTp' : player.find_element(By.XPATH, './/td[11]').text,})
                    except Exception as e:
                        print(f"Error fetching player data: {e}")
        except Exception as e:
            print(f"Error loading box score page: {e}")     

    # obtain personal matchup data including name, mins, and points
    def MatchupScraper(self):
        try:
            # for each player in the statsheet find the top matchup's data
            for index, element in enumerate(self.statSheet):
                # get matchup url via driver
                self.driver.get(self.matchupUrl)
                waiter = WebDriverWait(self.driver, 10)
                # wait for elements to load
                waiter.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                button = Select(self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div[2]/div[2]/div[1]/label/div/select"))
                self.name = element['name']
                try:
                    # try to open website dropdown in order to find matchups
                    button.select_by_visible_text(self.name)
                    time.sleep(1)
                except Exception as e:
                    # if it doesnt work try searching for a nickname
                    if self.name in nicknames:
                        element['name'] = nicknames[self.name]
                        index -= 1
                    else:
                        # or else notify me to add nickname
                        print(f'chack for nickname for player:{self.name}')
                matchups = self.driver.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div[2]/div[3]/div[2]/table/tbody/*')
                for index,match in enumerate(matchups[:2]):  # Process the first matchup only
                    self.matchupName = match.find_element(By.XPATH, './/td[3]').text
                    self.matchupMins = match.find_element(By.XPATH, './/td[5]').text
                    self.matchupPoints = match.find_element(By.XPATH, './/td[10]').text
                    element['matchupName' + str(index + 1)] = self.matchupName
                    element['matchupMins' + str(index + 1)] = self.matchupMins
                    element['matchupPoints' + str(index + 1)] = self.matchupPoints
        except Exception as e:
            print(f'Error fetching matchup data: {e}')

    # obtain zone shooting stats
    def ShootingScraper(self):
        # load date into variables
        m, d, y = self.date.strftime("%m"), self.date.strftime("%d"), self.date.strftime("%y")
        # shorten advanced stats of full season shooting to one performance by using date variables in url
        shootingScraperUrl = f'https://www.nba.com/stats/players/shooting?DistanceRange=By+Zone&DateFrom={m}%2F{d}%2F{y}&DateTo={m}%2F{d}%2F{y}'
        wait = WebDriverWait(self.driver, 10)
        # for every player in statsheet try to collect advanced shooting information
        for element in self.statSheet:
            self.name = element['name']
            mtries = 3
            tries = 0
            found = False
            # repeat search a max of three times
            while tries < mtries and not found:
                try:
                    # get shooting stats url via driver
                    self.driver.get(shootingScraperUrl)
                    try:
                        # wait for elements to load
                        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select')))
                        button = Select(self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select'))
                        # select load all pages button to iterate through every player's stats that day
                        button.select_by_value('-1')
                    except Exception as e:
                        pass
                    shootingScrape = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                    shootingScraper = shootingScrape.find_elements(By.XPATH, './*')
                    # for every player in the Nba Database look for the current players name to find their stats
                    for shooter in shootingScraper:
                        name = shooter.find_element(By.XPATH, './/td[1]').text
                        # if found collect data
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
                        print(f'{self.name} does not exist shooting trying again') 
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

    # obtain advanced assist stats
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

    # obtain advanced rebound stats
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
                        print(tries)
                        if tries < 2:
                            tries
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
                    continue
            with conn:
                curr.execute('Select * from data where name = :name', {'name': element['name']})
                element['gamesPlayed'] = len(curr.fetchall()) + 1
            element['gameId']  = self.lastReadGame - self.firstgame + 1
    
    # commit all stats to database
    def CommitStatSheet(self):
        for element in self.statSheet:
            with conn: 
                curr.execute("""INSERT INTO data (
                name, team, opponent, position, home, win, 
                matchupName1, matchupMins1, matchupPoints1, 
                matchupName2, matchupMins2, matchupPoints2, 
                RAm, RAa, RAp, Paintm, Painta, Paintp, 
                Midm, Mida, Midp, Corner3m, Corner3a, Corner3p, 
                AB3m, AB3a, AB3p, FTm, FTa, FTp, passes, assists, PA, APp, 
                rebounds, CRB, CRBp, RBC, RBCp, RBd, gamesPlayed, gameId) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    (
                element["name"], element["team"], element["opponent"], element["position"], bool(element["home"]), bool(element["win"]),
                element["matchupName1"], element["matchupMins1"], float(element["matchupPoints1"]),
                element["matchupName2"], element["matchupMins2"], float(element["matchupPoints2"]),
                float(element["RAm"]), float(element["RAa"]), float(element["RAp"]), float(element["Paintm"]), float(element["Painta"]), float(element["Paintp"]),
                float(element["Midm"]), float(element["Mida"]), float(element["Midp"]), float(element["Corner3m"]), float(element["Corner3a"]), float(element["Corner3p"]),
                float(element["AB3m"]), float(element["AB3a"]), float(element["AB3p"]), float(element["FTm"]), float(element["FTa"]), float(element["FTp"]), float(element["passes"]), float(element["assists"]), float(element["PA"]), 
                float(element["APp"]), float(element["rebounds"]), float(element["CRB"]), float(element["CRBp"]), float(element["RBC"]), float(element["RBCp"]),
                float(element["RBd"]), float(element['gamesPlayed']), float(element["gameId"])))

    # update game id in DB
    def UpdateGameId(self):
        with conn:
            curr.execute('UPDATE lastGamePlayed set lastGameNum = :lrg', {'lrg' : self.lastReadGame + 1} )

    # create a seperate statsheet based on the performance on a player based on their averages via a z score to capture the teams defensive performance
    def TeamAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                # if the player has played more than three games
                if gp > 3:
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
                    # get all player's data from DB
                    curr.execute('Select * from data where name = :name', {'name': self.name})
                    logs = curr.fetchall()
                    # for every game player has played
                    for log in logs:
                        # ignore first 13 items of DB entry/ non statistical information
                        n = 13
                        while n <= 30:
                            for type in statTypes:
                                for typetype in statTypesTypes:
                                    catName = type + typetype 
                                    # if category Name is not in stats then create a dictionary for it
                                    if catName not in stats:
                                        stats[catName] = []
                                    # append current stat to stats
                                    stats[catName].append(float(log[n]))
                                    n += 1
                    for type in statTypes:
                        for typetype in statTypesTypes:
                            catName = type + typetype 
                            # if the standard deviation of the category of stats is zero, record the Z score as zero
                            if statistics.stdev(stats[catName]) == 0:
                                results['Z' + catName] = 0
                                element['Z' + catName] = results['Z' + catName]
                            # else take the current performance, substract the mean of all performances and then divide by the 
                            # standard deviation of all performances to find z score
                            else:
                                results['Z' + catName] = (float(element[catName]) - statistics.mean(stats[catName])) / statistics.stdev(stats[catName])
                                element['Z' + catName] = results['Z' + catName]
                    # commit into DB
                    curr.execute("""INSERT INTO teamAnalytics (
                        team, opponent, oppTeam, position, win, home, primaryDef, 
                        ZRAm, ZRAa, ZRAp, ZPaintm, ZPainta, ZPaintp, 
                        ZMidm, ZMida, ZMidp, ZCorner3m, ZCorner3a, ZCorner3p, 
                        ZAB3m, ZAB3a, ZAB3p, ZFTm, ZFTa, ZFTp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results["team"], results["opponent"], results['oppTeam'], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZRAm"]), float(results["ZRAa"]), float(results["ZRAp"]), 
                        float(results["ZPaintm"]), float(results["ZPainta"]), float(results["ZPaintp"]), 
                        float(results["ZMidm"]), float(results["ZMida"]), float(results["ZMidp"]), 
                        float(results["ZCorner3m"]), float(results["ZCorner3a"]), float(results["ZCorner3p"]), 
                        float(results["ZAB3m"]), float(results["ZAB3a"]), float(results["ZAB3p"]),
                        float(results["ZFTm"]), float(results["ZFTa"]), float(results["ZFTp"])))

    # create a seperate statsheet based on the assist and roubound performance on a player based on their 
    # averages via a z score to capture the teams defensive performance          
    def TeamARAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                # if the player has played more than three games
                if gp > 3:
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
                    # get all player's data from DB
                    curr.execute('Select * from data where name = :name', {'name': self.name})
                    logs = curr.fetchall()
                    # for every game player has played
                    for log in logs:
                        n = 31
                        while n <= 39:
                            for ARType in ARTypes:
                                if ARType not in stats:
                                     stats[ARType] = []
                                stats[ARType].append(log[n])
                                n += 1
                    for ARType in ARTypes:
                        # if the standard deviation of the category of stats is zero, record the Z score as zero
                        if statistics.stdev(stats[ARType]) == 0:
                            results['Z' + ARType] = 0
                            element['Z' + ARType] = results['Z' + ARType]
                        else:
                            # else take the current performance, substract the mean of all performances and then divide by the 
                            # standard deviation of all performances to find z score
                            results['Z' + ARType] = (float(element[ARType]) - statistics.mean(stats[ARType])) / statistics.stdev(stats[ARType])
                            element['Z' + ARType] = results['Z' + ARType]
                    # commit into DB
                    curr.execute("""INSERT INTO teamARAnalytics (
                        team, opponent, oppTeam, position, win, home, primaryDef, 
                        Zpasses, Zassists, ZPA, ZAPp, Zrebounds, 
                        ZCRB, ZCRBp, ZRBC, ZRBCp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results["team"], results["opponent"], results['oppTeam'], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["Zpasses"]), float(results["Zassists"]), float(results["ZPA"]), 
                        float(results["ZAPp"]), float(results["Zrebounds"]), float(results["ZCRB"]), 
                        float(results["ZCRBp"]), float(results["ZRBC"]), float(results["ZRBCp"])))
                    
    # create a seperate statsheet based on the assist and roubound performance on a team based on their 
    # Z score averages via another  z score to capture the players offensive performance
    def PlayerARAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                curr.execute('Select * from teamARAnalytics where team = :name and position = :pos', {'name': element['opponent'], 'pos' : element['position']})
                # if the defensive team has five games against players that have more than 3 games
                if gp > 5 and (len(curr.fetchall()) >= 2):
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
                    # get all teams defensive zscore entries at this position
                    curr.execute('Select * from teamARAnalytics where team = :name and position = :pos', {'name': element['opponent'], 'pos' : element['position']})
                    logs = curr.fetchall()
                    for log in logs:
                        # ignore non statistical data
                        n = 8
                        while n <= 16:
                            for ARType in ARTypes:
                                # if the zscore type doesnt exist, create the dictionary for it
                                if ('Z' + ARType) not in stats:
                                     stats['Z' + ARType] = []
                                # append current data to stats zscore type
                                stats['Z' + ARType].append(log[n])
                                n += 1
                    # for each type of z score type
                    for ARType in ARTypes:
                        # if the standard deviation of the z score type is 0, record zero
                        if statistics.stdev(stats['Z' + ARType]) == 0:
                                results['ZZ' + ARType] = 0
                        # else substract the mean zscore type from the current z score type, then divide that by the standard deviation to get another layer 
                        # of abstraction z score
                        else:
                            results['ZZ' + ARType] = (float(element['Z' + ARType]) - statistics.mean(stats['Z' + ARType])) / statistics.stdev(stats['Z' + ARType])
                    # commit
                    curr.execute("""INSERT INTO playerARAnalytics (
                        name, team, opponent, position, win, home, primaryDef, 
                        ZZpasses, ZZassists, ZZPA, ZZAPp, ZZrebounds, 
                        ZZCRB, ZZCRBp, ZZRBC, ZZRBCp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results['name'], results["team"], results["opponent"], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZZpasses"]), float(results["ZZassists"]), float(results["ZZPA"]), 
                        float(results["ZZAPp"]), float(results["ZZrebounds"]), float(results["ZZCRB"]), 
                        float(results["ZZCRBp"]), float(results["ZZRBC"]), float(results["ZZRBCp"])
                        ))
    
    # create a seperate statsheet based on the shooting performance on a team based on their 
    # Z score averages via another z score to capture the players offensive performance
    def PlayerAnalytics(self):
        for element in self.statSheet:
            self.name = element['name']
            with conn:
                gp = element['gamesPlayed']
                curr.execute('Select * from teamAnalytics where team = :name and position = :pos', {'name': element['opponent'], 'pos' : element['position']})
                if gp > 5 and (len(curr.fetchall()) >= 2):
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
                    # get all teams defensive zscore entries at this position
                    curr.execute('Select * from teamAnalytics where team = :name and position = :pos', {'name': element['opponent'], 'pos' : element['position']})
                    logs = curr.fetchall()
                    for log in logs:
                        # ignore non statistical data
                        n = 8
                        while n <= 25:
                            for type in statTypes:
                                for typetype in statTypesTypes:
                                    catName = type + typetype 
                                    # if the zscore type doesnt exist, create the dictionary for it
                                    if ('Z' + catName) not in stats:
                                        stats['Z' + catName] = []
                                    # append current data to stats zscore type
                                    stats['Z' + catName].append(float(log[n]))
                                    n += 1
                    # for each type of z score type
                    for type in statTypes:
                        for typetype in statTypesTypes:
                            catName = type + typetype 
                            # if the standard deviation of the z score type is 0, record zero
                            if statistics.stdev(stats['Z' + catName]) == 0:
                                results['ZZ' + catName] = 0
                            # else substract the mean zscore type from the current z score type, then divide that by the standard deviation to get another layer 
                            # of abstraction z score
                            else:
                                results['ZZ' + catName] = (float(element['Z' + catName]) - statistics.mean(stats['Z' + catName])) / statistics.stdev(stats['Z' + catName])
                    # commit
                    curr.execute("""INSERT INTO playerAnalytics (
                        name, team, opponent, position, win, home, primaryDef, 
                        ZZRAm, ZZRAa, ZZRAp, ZZPaintm, ZZPainta, ZZPaintp, 
                        ZZMidm, ZZMida, ZZMidp, ZZCorner3m, ZZCorner3a, ZZCorner3p, 
                        ZZAB3m, ZZAB3a, ZZAB3p, ZZFTm, ZZFTa, ZZFTp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",    
                        (
                        results['name'], results["team"], results["opponent"], results["position"], 
                        bool(results["win"]), bool(results["home"]), results["primaryDef"],  
                        float(results["ZZRAm"]), float(results["ZZRAa"]), float(results["ZZRAp"]), 
                        float(results["ZZPaintm"]), float(results["ZZPainta"]), float(results["ZZPaintp"]), 
                        float(results["ZZMidm"]), float(results["ZZMida"]), float(results["ZZMidp"]), 
                        float(results["ZZCorner3m"]), float(results["ZZCorner3a"]), float(results["ZZCorner3p"]), 
                        float(results["ZZAB3m"]), float(results["ZZAB3a"]), float(results["ZZAB3p"]),
                        float(results["ZZFTm"]), float(results["ZZFTa"]), float(results["ZZFTp"])))
f = 1
while f <= 200:
    # create child of box
    scrape = Box()
    # obtain
    scrape.BoxScoreScraper()
    # obtain date and team information
    scrape.DateScrape()
    # obtain matchup data including opposing player, mins, and points
    scrape.MatchupScraper()
    # obtain game specific zone shooting statistics
    scrape.ShootingScraper()
    # obtain game specific advanced assist statistics
    scrape.AssistScraper()
    # obtain game specific advanced rebound statistics
    scrape.ReboundScraper()
    # make sure every games statsheet has all 10 starter's information, if not exit the data gathering loop
    if len(scrape.statSheet) != 10:
        break
    br = False
    for en in scrape.statSheet:
        if len(en) != 42:
            br = True
            break
    if br:
        print('slow ass internet')
        break
    # check if game id to be saved already exist in database
    curr.execute('select * from data where gameId = :id', {'id' : scrape.statSheet[0]['gameId']})
    check = curr.fetchall()
    # if so break from data gathering loop
    if check:
        print(f'game {scrape.statSheet[0]['gameId']} already exists')
        break
    # commit current statsheet to DB
    scrape.CommitStatSheet()
    # obtain defensive team shooting advanced analytics if available
    scrape.TeamAnalytics()
    # obtain defensive team AR advanced analytics if available
    scrape.TeamARAnalytics()
    # obtain offensive player shooting advanced analytics if available
    scrape.PlayerAnalytics()
    # obtain offensive player AR advanced analytics if available
    scrape.PlayerARAnalytics()
    # print currrent statsheet to terminal
    print(scrape.statSheet)
    # update game id
    scrape.UpdateGameId()
    # close driver
    scrape.driver.close()
    f += 1

