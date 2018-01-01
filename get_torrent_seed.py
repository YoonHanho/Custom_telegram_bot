#!/usr/bin/python3

import re
import time
import logging
import os
import paramiko
import glob
import urllib.parse
from urllib.parse import urljoin
from selenium.common.exceptions import NoAlertPresentException
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import requests
from selenium import webdriver
from pyvirtualdisplay import Display
from TOKEN import *
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    #filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def get_firefox_profile_for_autodownload():

    profile = webdriver.FirefoxProfile()

    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWN_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "file/unknown")

    return profile


def get_torrentkim_site():
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
    url = 'https://www.google.co.kr/search?q=torrentkim'
    req = session.get(url, headers=headers)
    bsObj = BeautifulSoup(req.text, 'lxml')
    try:
        site = bsObj.find("cite",{"class":"_Rm"}).get_text()
    except:
        site = 'https://torrentkim12.com/'

    return site


def get_seedsite_by_torrentkim(program_name, selected_date):

    driver = webdriver.PhantomJS()
    torrent_site = get_torrentkim_site()

    query_string = program_name + ' ' + selected_date
    query_string = urllib.parse.quote_plus(query_string)
    search_url = torrent_site + 'bbs/s.php?k=' + query_string + '&b=&q='
    logger.info("search_url = %s" % search_url)

    driver.get(search_url)
    # time.sleep(5)
    page_sources = driver.page_source
    driver.quit()

    bsobj = BeautifulSoup(page_sources, "lxml")
    tables = bsobj.findAll("tr", {"class": "bg1"})

    lists = []
    for table in tables:
        lists.append(table.find("td",{"class":"subject"}))

    search_lists = []
    for list_item in lists:
        items = list_item.findAll("a")
        for item in items:
            search_lists.append(item)

    valid_lists = {}

    for search_item in search_lists:

        if re.search('제휴사이트', search_item.get_text()) \
                or re.search('예능', search_item.get_text()):
            continue

        try:
            if search_item.attrs['style'] == "text-decoration:line-through":
                continue
        except KeyError:
            pass

        try:
            target_url = search_item.attrs['href']
            title = search_item.get_text()

            target_url = urljoin(search_url, target_url)
            title = title.strip()
        except AttributeError:
            logger.warning('It looks like there is no href in "a" tag.')
            continue

        valid_lists[title] = target_url

    if len(valid_lists) == 0:
        return None
    else:
        return valid_lists


def get_torrent_seed_file(url):
    for file in glob.glob(DOWN_DIR + '/*.torrent'):
        os.remove(file)
    logger.info('Previous files were removed.')

    # binary = FirefoxBinary('/Applications/Firefox.app/Contents/MacOS/firefox-bin')
    display = Display(visible=0, size=(800, 600))
    display.start()
    profile = get_firefox_profile_for_autodownload()
    driver_torrent = webdriver.Firefox(executable_path=FIREFOX_DRIVER,
                                       firefox_profile=profile)
                                       # firefox_profile=profile,
                                       # firefox_binary=binary)
    driver_torrent.get(url)
    logger.info("I am trying to connect to " + url)

    try:
        driver_torrent.switch_to.alert.accept()
        logger.info('There is an alert for redirection.')
    except NoAlertPresentException:
        logger.info('There is no redirection.')
        pass

    logger.info("torrent url : %s" % driver_torrent.current_url)

    try:
        element = driver_torrent.find_element_by_xpath("//table[@id='file_table']/tbody/tr[3]/td/a")
    except:
        logger.warning('There is no proper torrent link in the site.')
        driver_torrent.quit()
        display.stop()
        return None

    element.click()

    files = None
    timeout = 100
    while not files and timeout > 0:
        files = glob.glob(DOWN_DIR + '/*.torrent')
        time.sleep(1)
        timeout = timeout - 1

    if timeout == 0:
        logger.warning('Time out for downloading')
        return None
    else:
        torrent_file = glob.glob(DOWN_DIR + '/*.torrent')[0]

    if os.path.isfile(torrent_file):
        driver_torrent.quit()
        display.stop()
        return torrent_file
    else:
        logger.warning("It isn't a file! : " + torrent_file)
        return None


def send_file_to_remote(host, user, key, file):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, key_filename=key)
    sftp = ssh.open_sftp()
    sftp.put(file, REMOTE_DIR + '/' + os.path.basename(file))
    sftp.close()
    ssh.close()


def main():
    torrents = get_seedsite_by_torrentkim('무한도전','171223')

    title = None
    url = None
    for torrent_title in torrents.keys():
        if re.search(r'720p-NEXT', torrent_title):
            title = torrent_title
            url = torrents[torrent_title]
            logger.info(title + ' : ' + url)
            break

    file_name = get_torrent_seed_file('https://torrentkim12.com/torrent_variety/852373.html')
    if file_name == None:
        logger.warning('Please check the downloading of torrent file.')
        return

    logger.info('Local file name : ' + file_name)

    send_file_to_remote(REMOTE_HOST, REMOTE_USER, RSA_KEY_LOCATION, file_name)


if __name__ == '__main__':
    main()
