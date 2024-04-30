from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import time
import datetime as dt
import json
import os

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


service = Service(executable_path='/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=options)

time.sleep(1)

google_url = "https://www.cnbc.com/finance/"
driver.get(google_url)
time.sleep(.5)


print("we're in")

login = os.environ.get('CNBC_LOGIN')
password = os.environ.get('CNBC_PASSWORD')

time.sleep(.5)


def sign_in_func(login, password):
    sign_in_link = driver.find_element(By.XPATH, "//a[text()='SIGN IN']")
    # sign_in_link = driver.find_element(By.LINK_TEXT, 'SIGN IN')
    sign_in_link.click()
    time.sleep(1.5)
    email = driver.find_element(By.NAME, 'email')
    email.send_keys(login)
    pas = driver.find_element(By.NAME, 'password')
    pas.send_keys(password)
    click = driver.find_element(By.NAME, "signin")
    click.click()
    time.sleep(1)


print("user verified, time to scrape")

# silly way to check for paywall
got_u = 'Despite a murky macroeconomic environment and heightened fears around the health of the banking sector, the nation’s largest financial institutions all reported earnings beats for the third quarter.'

# nested dictionary with dates, and articles
collection = []

load_more_button = driver.find_element(
    By.CLASS_NAME, "LoadMoreButton-loadMore")
load_more_button.click()
time.sleep(.5)

find_elements = driver.find_elements(By.CLASS_NAME, "Card-titleContainer")

# open a second tab, where the article will be scraped
driver.execute_script("window.open('');")

print(len(login))
print(len(password))

# go through new articles which were published this week
for each_item in find_elements:
    try:
        item = each_item.find_element(By.CLASS_NAME, "Card-title")
        print(item.text)
        name = item.text
        url = item.get_attribute("href")

        # toggle the other tab, with the article url
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)

        # sign in and get article elements
        sign_in_func(login, password)
        time_element = driver.find_element(
            By.CSS_SELECTOR, 'time[data-testid="published-timestamp"]')
        datetime_value = time_element.get_attribute('datetime')
        formatted_datetime = dt.datetime.strptime(
            datetime_value, "%Y-%m-%dT%H:%M:%S%z")
        date = formatted_datetime.date().__str__()

        # get paragraphs
        text_elements = driver.find_elements(By.CSS_SELECTOR, 'p')

        news_set = {item.text for item in text_elements}

        assert got_u not in news_set
        
        text = '\n'.join(news_set)
        
        data = {
            "title": name,
            "link": url,
            "date": date,
            "text": text
        }
        collection.append(data)
        
        print(len(collection))
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print(e)
        driver.switch_to.window(driver.window_handles[0])
        continue


file_path = 'cnbc_data.json'

try:
    with open(file_path, 'r') as json_file:
        existing_data = json.load(json_file)
except FileNotFoundError:
    existing_data = {}

print(collection)

try:
    existing_data.extend(collection)

    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, cls=SetEncoder)
        
except Exception as e:
    print(e)
