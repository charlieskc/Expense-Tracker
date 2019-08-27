from selenium import webdriver
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import platform
from sqlalchemy import create_engine, types
import pandas as pd
import logging
from logging.config import fileConfig
import sys
from bs4 import BeautifulSoup
import util

def getWebDriver():
    os = platform.system()

    if os == 'Windows':
        path = "chromedriver.exe"
    else:
        path = "/usr/local/bin/chromedriver"

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options.add_argument("--no-sandbox")

    return webdriver.Chrome(executable_path=path, options=options)

def submitLoginInfo(driver, username, password):
    """
        submit the account info
    """
    # input login details
    account = driver.find_element_by_id("eliloUserID")
    account.send_keys(username)

    pass2 = driver.find_element_by_id("eliloPassword")
    pass2.send_keys(password)

    driver.find_element_by_id("loginSubmit").click()

def loginWebsite(url):
    """
        login website
    """
    driver = getWebDriver()
    driver.get(url)
    time.sleep(0.5)
    html = driver.page_source

    # login the website
    submitLoginInfo(driver, 'username', 'password')

    print("logging in..")
    return driver

def parseExpense(page_index):
    statement_url = "https://global.americanexpress.com/transactions?BPIndex="+str(page_index)
    print("getting " + statement_url)
    driver.get(statement_url)
    time.sleep(1)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    #parse grouped transation
    table = soup.find('table', {'class': 'table data-table'})
    df = pd.read_html(str(table))[0]
    df['Date'] = date_list[page_index].split('to')[1].lstrip()
    df['Date'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
    df['Range'] = date_list[page_index]
    #df['Debits'] = df['Debits'].map(lambda x: x.strip('HK$'))
    #df['Credits'] = df['Credits'].map(lambda x: x.strip('HK$'))
    df[['Debits']] = df[['Debits']].replace('[HK$]', '', regex=True).replace('[,]', '', regex=True).astype(float)
    df[['Credits']] = df[['Credits']].replace('[HK$]', '', regex=True).replace('[,]', '', regex=True).astype(float)
    div = soup.findAll('div', {'class': "axp-transactions__index__transaction___2xwam"})
    for x in div:
        x.find('div', {'class': 'txn-col col-xs-1 col-md-1'})
        for name in x:
            print(name.text)

    #drop last row as it is subtotal
    print(df[:-1])

    #parse individual transation



    return df[:-1]

def saveDB(df):
    engine = create_engine(util.getDBConnStr())
    conn = engine.connect()
    df.to_sql("expense", con=engine, if_exists="append", chunksize=1000,
              dtype={'Date': types.DATE, 'Credits': types.DECIMAL, 'Debits': types.DECIMAL})
    conn.close()

if __name__ == '__main__':

    login_url = "https://global.americanexpress.com/login/zh-HK"
    statement_url = "https://global.americanexpress.com/transactions?BPIndex=0"
    driver = loginWebsite(login_url)
    time.sleep(1.5)
    driver.get(statement_url)
    time.sleep(1.5)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    #get activity dates
    select = soup.find('select', {'id': 'statement-cycle-selector'})
    date_list = []
    for option in select:
        date_list.append(option.text)

    spending_df = pd.DataFrame(columns=["Date", "Card Member", "Debits", "Credits"])
    for i in range(len(date_list)):
        if i == 0:
            continue
        spending_df = spending_df.append(parseExpense(i), ignore_index=True, sort=False)

    saveDB(spending_df)
