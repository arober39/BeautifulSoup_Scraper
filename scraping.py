from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time
import requests
import urllib.request
import json
from gzip import decompress


def page_tracer(link):

    firefox_options = Options()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options)
    driver.get(link)

    time.sleep(5)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1", {"class": "listing-right-title"})
    title = title.text

    location = soup.find("span", {"class": "location"})
    location = location.text
    location = location.strip()

    listing_price = soup.find("span", {"class": "listing-price"})
    listing_price = listing_price.text
    listing_price = listing_price.strip()

    listing_type = soup.find("span", {"class": "capitalize"})
    listing_type = listing_type.text

    about_section = soup.find("div", {"class": "listing-details-item"})
    about_section = about_section.text
    about_section = about_section.strip()

    features_list = []
    features = soup.find("ul", {"class": "listing-features"})
    if features:
        for item in soup.find("ul", {"class": "listing-features"}):
            features_list.append(item.text.strip())
    while("" in features_list):
        features_list.remove("")

    doc = {"title": "", "location": "", "listing_price": "", "listing_type": "", "about_section":"", "features_list": [], "image_link":""}
    doc["title"] = title
    doc["image_link"] = link
    doc["location"] = location
    doc["listing_price"] = listing_price
    doc["listing_type"] = listing_type
    doc["about_section"] = about_section
    doc["features_list"] = features_list

    json_object = json.dumps(doc)
    listings_json = json.loads(json_object)
    
    with open("tiny_house_listings.json", 'a') as json_file:
        json.dump(listings_json, json_file, 
                        indent=4,  
                        separators=(',',': '))

    driver.close()

def main():
    r = requests.get("https://tinyhouselistings.com/sitemap.xml.gz")
    soup = BeautifulSoup(decompress(r.content), 'xml')
    urls = soup.find_all('loc')
    
    for url in urls:
        if "/listings/" in url.text:
            new_url = url.text

    site = requests.get(new_url)
    soupy = BeautifulSoup(decompress(site.content), 'xml')
    listing_urls = soupy.find_all('loc')

    final_listings = []
    for listing in listing_urls:
        if "tinyhouselistings.com" in listing.text:
            final_listings.append(listing.text)


    for final in final_listings:
        page_tracer(final)

if __name__ == "__main__":
    main()

"""
https://tinyhouselistings.com/sitemaps/listings/sitemap.xml.gz
https://tinyhouselistings.com/sitemaps/dreamlists/sitemap.xml.gz
https://tinyhouselistings.com/sitemaps/countries/sitemap.xml.gz
https://tinyhouselistings.com/sitemaps/states/sitemap.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap1.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap2.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap3.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap4.xml.gz
https://tinyhouselistings.com/sitemaps/users/sitemap5.xml.gz
"""