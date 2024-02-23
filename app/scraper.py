from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin, urlparse
from vector_db import upsert_to_vector_db
from dotenv import load_dotenv
import os
import time

load_dotenv()

chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
base_url = os.getenv('BASE_URL', 'https://www.promptior.ai/')

def categorize_url(url):
    if 'about' in url:
        return 'About Us'
    elif 'contact' in url:
        return 'Contact'
    elif 'services' in url:
        return 'Services'
    else:
        return 'General'
    

def get_page_title(soup):
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    for header_tag in ['h1', 'h2', 'h3']:
        header = soup.find(header_tag)
        if header:
            return header.text.strip()
    return "No Title"


def scrape_page(driver, url):
    url, _ = urldefrag(url)
    
    driver.get(url)
    time.sleep(2) 
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except Exception as e:
        print(f"Error waiting for page elements to load: {e}")
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    title = get_page_title(soup)
    paragraphs = [p.text.strip() for p in soup.find_all(['p', 'li', 'h2', 'h3'])] 
    content = "\n".join(paragraphs)
    
    category = categorize_url(url)
    
    data = {
        "title": title,
        "content": content,
        "url": url,
        "category": category,
    }
    upsert_to_vector_db(data)
    
    links = set()
    for link in soup.find_all('a', href=True):
        full_url, frag = urldefrag(urljoin(url, link['href'])) 
        if urlparse(full_url).netloc == urlparse(url).netloc:
            links.add(full_url)
    return links


def scrape_website(base_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(executable_path=chromedriver_path) 
    
    visited_urls = set()
    urls_to_visit = {base_url}
    
    try:
        with webdriver.Chrome(service=service, options=chrome_options) as driver:
            while urls_to_visit:
                current_url = urls_to_visit.pop()
                if current_url not in visited_urls:
                    visited_urls.add(current_url)
                    new_links = scrape_page(driver, current_url)
                    urls_to_visit.update(new_links - visited_urls)
    except Exception as e:
        print(f"An error occurred: {e}")


scrape_website(base_url)
