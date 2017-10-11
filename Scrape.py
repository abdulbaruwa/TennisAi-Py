# pylint: disable=missing-docstring
import time
import json
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

"""
Init the function
"""

class LtaTennisTournamentScraper(object):
    def __init__(self):
        self.filename = '/home/datadrive/lta_dump/tournaments_main.csv'
        self.filename_json = '/home/datadrive/lta_dump/tournaments_main.json'
        self.lta_base_url = 'https://www3.lta.org.uk/Competitions/Search/Search/#/?gen=/3&status=/4/5&grade=/1/2/3&page='
        header = 'tournament_details_link' + ' , ' + 'tournament' + ',' + 'tournament_code' + ',' + 'tournament_type ' + ',' + 'tournament_date' + ',' + 'tournament_gender' + ',' + 'tournament_grade' + ',' + 'tournament_rating'
        self.header = header + ', Grade , Rating guide , Payment info , Timings info , Provisional Draw Size , Open for entries , Closed for entries , Withdrawal deadline , Start date , End date:\n'
        self.driver = webdriver.PhantomJS()
        self.driver.set_window_size(1120, 550)


    def replace_coma(self, value):
        return value.replace(',', '')

    def getTournaments(self, tournament_section_div):
        tournament = tournament_section_div.a.text
        tournament_code = tournament_section_div.span.text
        tournament_location_div = tournament_section_div.findAll('div',{'class':'di'})[0].text
        tournament_type = tournament_section_div.findAll('div', {'class':'dk'})[0].text
        tournament_date = tournament_section_div.findAll('div', {'class':'dl'})[0].text
        tournament_gender = tournament_section_div.findAll('div', {'class':'dp'})[0].text
        tournament_grade = tournament_section_div.findAll('div', {'class':'d2'})[0].span.text
        tournament_details_link = 'https://www3.lta.org.uk' + tournament_section_div.findAll('a', {'class':'titled'})[0]['href']
        tournament_rating = tournament_section_div.findAll('div', {'class':'d2'})[0].div.text
        # print(tournament_details_link)# + ' , ' + tournament + ',' + tournament_code + ',' + tournament_type #  + ',' + tournament_date + ',' + tournament_gender + ',' + tournament_grade + ',' + tournament_rating)

        return tournament_details_link, self.replace_coma(tournament_details_link) +  \
                                       ' , ' + self.replace_coma(tournament) + \
                                       ',' + self.replace_coma(tournament_code) + ',' + self.replace_coma(tournament_type)  + \
                                       ',' + self.replace_coma(tournament_date) + ',' + self.replace_coma(tournament_gender) + \
                                       ',' + self.replace_coma(tournament_grade) + ',' + self.replace_coma(tournament_rating)

    def get_tournaments_json(self, tournament_section_div):
        data = {}
        data['tournament'] = tournament_section_div.a.text
        data['tournament_code'] = tournament_section_div.span.text
        tournament_location_div = tournament_section_div.findAll('div',{'class':'di'})[0].text
        data['tournament_type'] = tournament_section_div.findAll('div', {'class':'dk'})[0].text
        data['tournament_date'] = tournament_section_div.findAll('div', {'class':'dl'})[0].text
        data['tournament_gender'] = tournament_section_div.findAll('div', {'class':'dp'})[0].text
        data['tournament_grade'] = tournament_section_div.findAll('div', {'class':'d2'})[0].span.text
        data['tournament_rating'] = tournament_section_div.findAll('div', {'class':'d2'})[0].div.text

        tournament_details_link = 'https://www3.lta.org.uk' + tournament_section_div.findAll('a', {'class':'titled'})[0]['href']
        # print(tournament_details_link)# + ' , ' + tournament + ',' + tournament_code + ',' + tournament_type #  + ',' + tournament_date + ',' + tournament_gender + ',' + tournament_grade + ',' + tournament_rating)

        return tournament_details_link, data        

    def get_tournament_details_json(self, page_source, json_data_to_append_to):
        header = 'Grade , Rating guide , Payment info , Timings info , Provisional Draw Size , ' \
                 'Open for entries , Closed for entries , Withdrawal deadline , Start date , End date:\n'
        body = soup(page_source, 'html.parser')
        tournament_containers = body.body.findAll('div',{'class':'lta-key-info'})
        rows = tournament_containers[0].table.tbody.findAll('tr')        
        data = {}
        for i in range(1,11):
            value = rows[i].td.text.strip()
            header = rows[i].th.text.strip().replace(':','')
            json_data_to_append_to[header] = value
            
        return json_data_to_append_to

    def get_tournament_details(self, page_source):
        header = 'Grade , Rating guide , Payment info , Timings info , Provisional Draw Size , ' \
                 'Open for entries , Closed for entries , Withdrawal deadline , Start date , End date:\n'
        body = soup(page_source, 'html.parser')
        tournament_containers = body.body.findAll('div',{'class':'lta-key-info'})
        rows = tournament_containers[0].table.tbody.findAll('tr')
        csv_line = ''
        for i in range(1,11):
            csv_line += self.replace_coma(rows[i].td.text.strip())
            if i < 10:
                csv_line += ' , '

            else:
                csv_line += '\n'
        return csv_line

    def get_tournament_players_json(self, page_source):
        body = soup(page_source, 'html.parser')
        entrants_container = body.body.findAll('div', {
            'id': 'ctl00_ctl00_MainContentPlaceHolder_MainContentPlaceHolder_EventEntrants_EntrantsRecieved_lvEntrants_pnlEntrants'})
        if len(entrants_container) == 0:
            print('No entrants found for the policy')
            return []
        # print(entrants_container[0].table.tbody.findAll('tr'))
        rows = entrants_container[0].table.tbody.findAll('tr')
        players = []
        for i in range(len(rows)):
            data = {}
            tds = rows[i].findAll('td')
            data['player_name'] = tds[1].a.text
            data['player_link'] = tds[1].a['href']
            data['player_rating'] = tds[3].text
            data['player_county'] = tds[4].text
            players.append(data)
        # entrants_data = {}
        # entrants_data['entrants'] = players
#         json_data = json.dumps(entrants_data)
        return players

    def get_url_body(self, url, driver, func):
        wait = WebDriverWait(driver, 10)
        driver.get(url)
        try:
            wait.until(func)
            return driver.page_source
        except Exception as e:
            print('next_page exception: ' + str(e))

    def match_details_loaded(self, driver):
        return EC.element_to_be_clickable(driver.find_element_by_class_name('lta-fancy-select-value'))


    def scrape(self):
        # filename = '/home/datadrive/lta_dump/tournaments.csv'
        # lta_base_url = 'https://www3.lta.org.uk/Competitions/Search/Search/#/?gen=/3&status=/4/5&grade=/1/2/3/4&page='
        # header = 'tournament_details_link' +  ' , ' + 'tournament' + ',' + 'tournament_code' + ',' + 'tournament_type ' + ',' + 'tournament_date' + ',' + 'tournament_gender' + ',' + 'tournament_grade' + ',' + 'tournament_rating'
        # header = header + ', Grade , Rating guide , Payment info , Timings info , Provisional Draw Size , Open for entries , Closed for entries , Withdrawal deadline , Start date , End date:\n'
        # selfdriver = webdriver.PhantomJS()
        # selfdriver.set_window_size(1120, 550)
        
        f = open(self.filename, 'w')
        f.write(self.header)
        page = 0

        def next_page(driver):
            pagerNum = driver.find_element_by_id(str(page + 1))
            return pagerNum.get_attribute('class') == 'normal active'

        tournaments_on_page = 10
        while (tournaments_on_page > 0):
            url = self.lta_base_url + str(page)
            #print(url)
            response = self.get_url_body(url, self.driver, next_page)
            if response == None:
                break
            body = soup(response, 'html.parser')
            tournament_containers = body.body.findAll('div',{'class':'dd'})
            tournaments_on_page = len(tournament_containers)
            print(tournaments_on_page)
            page +=1
            time.sleep(1)
            for container in tournament_containers:
                detail_link, file_line = self.getTournaments(container)
                print(detail_link)
                detail_response = self.get_url_body(detail_link, self.driver, self.match_details_loaded)
                detail_line = self.get_tournament_details(detail_response)
                file_line = file_line + ', ' + detail_line
                # print(file_line)
                f.write(file_line)
            print('page ' + str(page) + ' done!')
        f.close()
        self.driver.quit()

    def scrape_to_json(self):
        f = open(self.filename_json, 'w')
        page = 0

        def next_page(driver):
            pagerNum = driver.find_element_by_id(str(page + 1))
            return pagerNum.get_attribute('class') == 'normal active'

        tournaments_on_page = 10
        tournaments = []
        while (tournaments_on_page > 0):
            url = self.lta_base_url + str(page)
            #print(url)
            response = self.get_url_body(url, self.driver, next_page)
            if response is None:
                break

            body = soup(response, 'html.parser')
            tournament_containers = body.body.findAll('div',{'class':'dd'})
            tournaments_on_page = len(tournament_containers)
            print(tournaments_on_page)
            page +=1
            time.sleep(1)

            for container in tournament_containers:
                detail_link, json_data = self.get_tournaments_json(container)
                print(detail_link)
                detail_response = self.get_url_body(detail_link, self.driver, self.match_details_loaded)
                json_result  = self.get_tournament_details_json(detail_response, json_data)
                json_result['entrants'] = self.get_tournament_players_json(detail_response)
                # print(file_line)
                tournaments.append(json_result)
            print('page ' + str(page) + ' done!')

        root_json_output = {}
        root_json_output['tournaments'] = tournaments

        f.write(json.dumps(root_json_output))
        f.close()
        self.driver.quit()
if __name__ == '__main__':
    lta_scraper = LtaTennisTournamentScraper()
    lta_scraper.scrape_to_json()