from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time
import requests
import urllib.request
import json
from elasticsearch import Elasticsearch
import configparser

"""
https://www.overdrive.com/robots.txt -> https://search.overdrive.com/sitemap.xml
https://www.overdrive.com/subjects
https://www.overdrive.com/subjects/law
https://www.overdrive.com/subjects/law?page=2
1283 pages in total
"""

config = configparser.ConfigParser()
config.read('mfp_elastic.ini')

# Elasticsearch client instance
es_client = Elasticsearch(
    cloud_id=config['ELASTIC']['cloud_id'],
    basic_auth=("elastic", config['ELASTIC']['password'])
)

es_client.info()
def send_books_to_elasticsearch(book_entry):
    if book_entry:
        es_client.index(
            index='online_library_index',
            document=book_entry
        )
    return

def book_landing_page(landing_page):
    firefox_options = Options()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options)
    driver.get(landing_page)

    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Each Document will follow the structure below:
    # Title
    # Author
    # Narrator
    # Publisher
    # Release
    # Description

    doc = {}

    target_labels = ["Format", "Author", "Narrator", "Publisher", "Release"]
    labels = soup.findAll("div", {"class": "metadata_container"})

    title = soup.find("h1", {"class": "title-page__title"})
    doc["Title"] = title.text
    for label in labels:
        format_key = label.find("h3", {"class": "metadata_label"})
        format_value = label.find("p", {"class": "metadata_text"}) or label.find("a")
        if format_key.text in target_labels:
            doc[format_key.text] = format_value.text
    
    about_section = soup.find("div", {"class": "title-page__blurb"})
    about_section = about_section.text
    about_section = about_section.strip()

    doc["Description"] = about_section

    json_object = json.dumps(doc)
    listings_json = json.loads(json_object)

    with open("book_listings.json", 'a') as json_file:
        json.dump(listings_json, json_file, 
                        indent=4,  
                        separators=(" , ", " : "))

    driver.close()
    

def browse_law_books(book_link):
    firefox_options = Options()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options)
    driver.get(book_link)

    time.sleep(5)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")
    
    law_books = []
    for a in soup.findAll("a"):
        if "/media/" in a["href"] and a["href"] not in law_books:
            law_books.append("https://www.overdrive.com" + a["href"])

    remove_dup_law_books = tuple(set(law_books))
   
    for book in remove_dup_law_books:
        book_landing_page(book)

    driver.close()

def page_tracer(link):
    firefox_options = Options()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options)
    driver.get(link)

    time.sleep(5)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    count = 1
    while count < 300:
        for a in soup.findAll("a"):
            if a["href"] == "/subjects/law":
                law_url = "https://www.overdrive.com" + a["href"] + "?page=" + str(count)
                
        browse_law_books(law_url)
        count += 1

    driver.close()


def main():
    r = requests.get("https://search.overdrive.com/sitemap.xml")
    soup = BeautifulSoup(r.content, 'xml')
    urls = soup.find_all('loc')

    for link in urls:
        if "/subjects" in link.text:
            subjects = link.text

    page_tracer(subjects)

if __name__ == "__main__":
    main()