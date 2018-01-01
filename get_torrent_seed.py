#!/usr/bin/python3

import re
import time
import logging
import os
# import paramiko
# import shutil
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
    while not files:
        files = glob.glob(DOWN_DIR + '/*.torrent')
        time.sleep(1)

    torrent_file = glob.glob(DOWN_DIR + '/*.torrent')[0]

    if os.path.isfile(torrent_file):
        driver_torrent.quit()
        display.stop()
        return torrent_file
    else:
        logger.warning("It isn't a file! : " + torrent_file)

# def date(bot, update):
#
#     found = 0
#
#     # (valid_title_lists, valid_url_lists) = get_site_by_Google(program_name, selected_date)
#     (valid_title_lists, valid_url_lists) = get_site_by_torrentkim(program_name, selected_date)
#     if not valid_title_lists:
#         logger.warning('The proper torrent seed is not found.')
#         update.message.reply_text("토렌트 파일을 찾지 못했습니다.")
#         return ConversationHandler.END
#
#     for (title, target_url) in zip(valid_title_lists, valid_url_lists):
#
#         logger.info("title = %s" % title)
#         logger.info("target = %s" % target_url)
#         if re.search(program_name, title) and re.search(selected_date, title):
#
#             driver_torrent = webdriver.Firefox(executable_path="/usr/local/bin/geckodriver",
#                                                firefox_profile=profile)
#
#             try:
#                 element = driver_torrent.find_element_by_xpath("//table[@id='file_table']/tbody/tr[3]/td/a")
#
#                 logger.info(title)
#
#                 if update.message.chat_id == MANAGER_ID:
#                     update.message.reply_text(driver_torrent.current_url)
#
#                 element.click()
#                 time.sleep(10)
#                 found = 1
#                 break
#             except:
#                 logger.warning('There is no proper torrent link in the site.')
#                 pass
#
#             driver_torrent.quit()
#
#     display.stop()
#
#     if found:
#
#         new_file_name = DOWN_DIR + '/' + program_name + selected_date + '.torrent'
#
#         for torrent_file in glob.glob(DOWN_DIR + '/*' + selected_date + '*.torrent'):
#             shutil.move(torrent_file, new_file_name)
#             break
#
#         bot.sendDocument(chat_id=update.message.chat_id, document=open(new_file_name, 'rb'))
#         update.message.reply_text('완료')
#         logger.info('The torrent file is sent to %s' % user.first_name)
#
#         if update.message.chat_id == MANAGER_ID or update.message.chat_id == MANAGER2_ID:
#             ssh = paramiko.SSHClient()
#             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             ssh.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=RSA_KEY_LOCATION)
#             sftp = ssh.open_sftp()
#             sftp.put(new_file_name, REMOTE_DIR + '/' + program_name + selected_date + '.torrent')
#             sftp.close()
#             ssh.close()
#             logger.info('Torrent file is sent to Kodi.')
#
#         os.remove(new_file_name)
#     else:
#         logger.warning('The proper torrent seed is not found.')
#         update.message.reply_text("토렌트 파일을 찾지 못했습니다.")
#
#     return ConversationHandler.END
#
#
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
    print('Local file name : ' + file_name)


if __name__ == '__main__':
    main()
