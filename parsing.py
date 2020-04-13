from bs4 import BeautifulSoup
import requests


def get_html(url):
    r = requests.get(url)
    return r.text


def get_content(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    title = soup.find('title')
    return title.string
