from builtins import print
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
DEBUG_BLAG = False
import itertools as it
import random
from fake_useragent import UserAgent





MAX_PAGES = 2
BASE_URL = 'https://www.emploi-public.ma/fr/'
# target url 
MAIN_URL = BASE_URL + 'concoursListe.asp?'
# path of table in html code
xContactXPATH = "/html/body/main/div/div/div[1]/div/table[1]"
# titles in table 
xTit_defaul = ['Administration et Organisation', 'Grade', 'Nombre postes', 'Delai de depot', 'Date de concours',
              'Date de publication', 'Candidats convoques pour examen  ecrit',
              'Candidats convoques pour entretien oral', 'Resultats',
              'Desistements', 'Email', 'Nom contact', 'Telephone', 'xTelephoneLabel','none','none','none','none']


#distance in talbe 
xSpacer = ' : '
xNameLabel = 'Nom'
xTelephoneLabel = 'Téléphone'
xEmailLabel = 'Email'
xContactLabel = "Pour plus d'informations :"
LAST_ELEMENT, LEFT_ELEMENT, RIGHT_ELEMENT = -1, 0, 1

# https://www.selenium.dev/documentation/webdriver/drivers/options/
#webdriver to control the behavior of web browzer
chrome_options = Options()
#opning the UI web application 
chrome_options.add_argument("--headless")
CHROME_DRIVER = r"chromedriver.exe"
#get access to ghrome 
browser = webdriver.Chrome(service=Service(CHROME_DRIVER),
                          options=chrome_options)


#function parm(curentpage=number) ==> current url  
CURRENT_URL = lambda current_page: f'{MAIN_URL}?c=0&e=0&p={current_page} '
#output file 
OutPutFileName = "Service d Etat.csv"
#remplace the letters 
textToUniCode = lambda element : element.text.replace("Ã©", "e"). \
    replace("Ã´", "o"). \
    replace("Ã\xa0", "a"). \
    replace("Ã¨", "e"). \
    replace("â\x80\x99", " "). \
    replace("ÃƒÂ‰", "e")




BeautifulSoupOption = 'html.parser'
xTableHeadMainData = 'thead'
xTableRowMainData = 'tr'
xTableDetailMainData = 'td'
xTableTitleMainData = 'th'
xTableBodyMainData = 'tbody'
xTableLinkTag = 'a'
xTableLinkHREF = 'href'
xTableLinkTitle = 'Link'
# Final CODE
#this take the titles content  from  the table and store it into a list (row_head) 
def scrapHeadersFirst(current_url : str) -> list:
    raw_html = requests.get(current_url)
    soup = BeautifulSoup(raw_html.text, BeautifulSoupOption)

    # mettre le code des données
    
    table_head = soup.find(xTableHeadMainData)
    row_head = list()
    for val_head in table_head.find_all(xTableRowMainData):
        ths = val_head.find_all(xTableTitleMainData)
        for th in ths:
            row_head.append(textToUniCode(th))
    row_head.append(xTableLinkTitle)
    return row_head


def concours_list(current_page : int, max_pages : int) -> list:
    tab_body = list()
    #while we dont arrive to last max page 
    while current_page <= max_pages:
        #visite the url ex : https://www.emploi-public.ma/fr/concoursListe.asp?c=0&e=1 <== current page 
        current_url = CURRENT_URL(current_page)
        print(current_url)
        #make a soup 
        raw_html = requests.get(current_url)
        soup = BeautifulSoup(raw_html.text, BeautifulSoupOption)
        #access to tbody of table 
        table_body = soup.find(xTableBodyMainData)
        #loup in our rows
        for val_body in table_body.find_all(xTableRowMainData):
            row_body = list()
            #store the content of the rows 
            tds = val_body.find_all(xTableDetailMainData)
            href_ = BASE_URL
            #fill the list with the tds content and remplace the letters by texttounincode function 
            for td in tds:
                row_body.append(textToUniCode(td))
                # in the href link 
                if td.find(xTableLinkTag):
                    href_ = href_ + td.find(xTableLinkTag).get(xTableLinkHREF)
            link = href_
            try:
                resultat = scrapPageAnnonce(link)
                row_body.extend([link, resultat[xEmailLabel], resultat[xNameLabel], resultat[xTelephoneLabel]])
            except:
                print("error in ", link)
            row_body.extend([link, str(), str(), str()])
            tab_body.append(row_body)
        current_page = current_page + 1
    return tab_body

def getContactDetails(soup: object) -> dict:
    table_body = soup.find(xTableBodyMainData).find_all(xTableRowMainData)
    contact_dictionary = dict.fromkeys([xEmailLabel,xNameLabel,xTelephoneLabel],str())
    contact_result = str()
    for row in table_body:
        if xContactLabel in row.text:
            contact_result = row.find(xTableDetailMainData).text
    contact_details = contact_result.split(xSpacer)
    contact_details_first_element = contact_details.pop(LEFT_ELEMENT).replace("\n", "")
    contact_details_last_element = contact_details.pop(LAST_ELEMENT).replace("\n", "")
    contact_processing_list = list()
    contact_processing_list.append(contact_details_first_element)

    #print(contact_processing_list)
    for detail in contact_details:
        valeur, tag = str(), str()
        if xNameLabel in detail:
            valeur, tag = detail.split(xNameLabel)[LEFT_ELEMENT], xNameLabel
        if xEmailLabel in detail:
            valeur, tag = detail.split(xEmailLabel)[LEFT_ELEMENT], xEmailLabel
        if xTelephoneLabel in detail:
            valeur, tag = detail.split(xTelephoneLabel)[LEFT_ELEMENT], xTelephoneLabel
        contact_processing_list.append(valeur)
        contact_processing_list.append(tag)
    contact_processing_list.append(contact_details_last_element)
    #print(contact_processing_list)

    for i in range(int(len(contact_processing_list) / 2)):
        tag = contact_processing_list[i * 2]
        valeur = contact_processing_list[i * 2 + 1]
        contact_dictionary[tag] = valeur
    return contact_dictionary

def getPageFile(soup : object) -> str():
    return ""

def scrapPageAnnonce(url : str) -> None:
    browser.get(url)
    tableOutput = browser.find_element(By.XPATH, xContactXPATH)
    inner_html = tableOutput.get_attribute('innerHTML')
    soup = BeautifulSoup(inner_html, BeautifulSoupOption)
    contactDic = getContactDetails(soup)
    #print(contactDic)
    filUrl = getPageFile(soup)
    return contactDic

def main() -> int:
    current_page = 1
    tabBody = concours_list(current_page, MAX_PAGES)
    print("Nous voila")
    df2 = pd.DataFrame(tabBody, columns=xTit_defaul)
    df2.to_csv(OutPutFileName)
    return 0

def debug_test():
    test_url = "https://www.emploi-public.ma/fr/concoursDetail.asp?c=0&e=0&id=23425"
    print(scrapPageAnnonce(test_url))

if __name__ == '__main__':
    if DEBUG_BLAG is False:
        exit(main())
    else:
        debug_test()