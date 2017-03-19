#!/usr/bin/python3

import re

import time
import datetime
from dateutil.parser import parse

import logging
import os
import paramiko
import shutil
import glob
import urllib.parse
from urllib.parse import urljoin
from selenium.common.exceptions import NoAlertPresentException
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
from TOKEN import *
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

PROGRAM, DATE = range(2)


def start(bot, update):
    reply_keyboard = [['무한도전', '썰전', '마이 리틀 텔레비전', '차이나는 클라스']]

    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))

    update.message.reply_text("토렌트 파일을 다운 받아 드립니다. 프로그램을 선택해주세요.",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return PROGRAM


def program(bot, update):
    global program_name
    global selected_program

    program_name = update.message.text
    update.message.reply_text(program_name + '를 선택하셨습니다.')
    logger.info("Selected program : %s" % program_name)

    update.message.reply_text("프로그램이 방영된 날짜를 선택해주세요. ex) 170209")

    return DATE


def get_firefox_profile_for_autodownload():

    profile = webdriver.FirefoxProfile()

    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWN_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "file/unknown")

    return profile


def get_site_by_Google(program_name, selected_date):

    driver = webdriver.PhantomJS()

    query_string = program_name + ' ' + selected_date + ' 토렌트'
    query_string = urllib.parse.quote_plus(query_string)
    search_url = 'https://www.google.co.kr/webhp?hl=ko#q=' + query_string + '&newwindow=1&hl=ko&tbs=li:1'
    logger.info("search_url = %s" % search_url)

    driver.get(search_url)
    time.sleep(5)
    page_sources = driver.page_source
    driver.quit()

    bsObj = BeautifulSoup(page_sources, "html.parser")

    valid_title_lists = []
    valid_url_lists = []

    try:
        search_lists = bsObj.find("div", {"id": "ires"}).ol.children
    except AttributeError:
        logger.info("Parsing error at searching in google(search_list)")
        return False, False

    for search_item in search_lists:
        try:
            target_url = search_item.find("div", {"class": "kv"}).cite.get_text()
            title = search_item.find("a").get_text()
        except AttributeError:
            logger.info("Parsing error at searching in google(search_item)")
            return False, False

        if re.search('torrentkim', target_url):
            valid_title_lists.append(title)
            valid_url_lists.append(target_url)

    return valid_title_lists, valid_url_lists


def get_site_by_torrentkim(program_name, selected_date):

    driver = webdriver.PhantomJS()

    query_string = program_name + ' ' + selected_date
    query_string = urllib.parse.quote_plus(query_string)
    search_url = 'https://torrentkim5.net/bbs/s.php?k=' + query_string + '&b=&q='
    logger.info("search_url = %s" % search_url)

    driver.get(search_url)
    time.sleep(5)
    page_sources = driver.page_source
    driver.quit()

    bsobj = BeautifulSoup(page_sources, "html.parser")

    valid_title_lists = []
    valid_url_lists = []

    tables = bsobj.findAll("tr", {"class": "bg1"})

    lists = []
    for table in tables:
        lists.append(table.find("td",{"class":"subject"}))

    search_lists = []
    for list_item in lists:
        items = list_item.findAll("a")
        for item in items:
            search_lists.append(item)

    for search_item in search_lists:

        if re.search('제휴사이트', search_item.get_text()) \
                or re.search('예능', search_item.get_text()):
            continue

        try:
            target_url = search_item.attrs['href']
            title = search_item.get_text()

            target_url = urljoin(search_url, target_url)
            title = title.strip()
        except AttributeError:
            logger.warning('It looks like there is no href in "a" tag.')
            continue

        valid_title_lists.append(title)
        valid_url_lists.append(target_url)

    if len(valid_url_lists) == 0 or len(valid_title_lists) == 0:
        return False, False
    else:
        return valid_title_lists, valid_url_lists


def date(bot, update):
    global selected_program
    global selected_date
    global program_name

    user = update.message.from_user
    selected_date = update.message.text

    try:
        date_in_format = parse(selected_date).date()
        today = datetime.date.today()
        if date_in_format > today:
            raise ValueError
    except:
        update.message.reply_text("날짜를 잘못 입력하셨습니다. /start 부터 다시 시작해주세요.")
        return ConversationHandler.END

    update.message.reply_text("선택하신 날짜는 " + str(date_in_format) + "입니다.")
    update.message.reply_text("잠시만 기다려주세요. 몇 분 정도 걸릴 수 있습니다.")
    logger.info("Selected date : %s" % date_in_format)

    display = Display(visible=0, size=(800, 600))
    display.start()

    profile = get_firefox_profile_for_autodownload()
    found = 0

    # (valid_title_lists, valid_url_lists) = get_site_by_Google(program_name, selected_date)
    (valid_title_lists, valid_url_lists) = get_site_by_torrentkim(program_name, selected_date)
    if not valid_title_lists:
        logger.warning('The proper torrent seed is not found.')
        update.message.reply_text("토렌트 파일을 찾지 못했습니다.")
        return ConversationHandler.END

    for (title, target_url) in zip(valid_title_lists, valid_url_lists):

        logger.info("title = %s" % title)
        logger.info("target = %s" % target_url)
        if re.search(program_name, title) and re.search(selected_date, title):

            driver_torrent = webdriver.Firefox(executable_path="/usr/local/bin/geckodriver",
                                               firefox_profile=profile)
            driver_torrent.get(target_url)
            logger.info("I am trying to connect to %s..." % target_url)

            try:
                driver_torrent.switch_to.alert.accept()
                logger.info('There is an alert for redirection.')
            except NoAlertPresentException:
                pass

            time.sleep(10)
            logger.info("torrent url : %s" % driver_torrent.current_url)

            try:
                element = driver_torrent.find_element_by_xpath("//table[@id='file_table']/tbody/tr[3]/td/a")

                logger.info(title)

                if update.message.chat_id == MANAGER_ID:
                    update.message.reply_text(driver_torrent.current_url)

                element.click()
                time.sleep(10)
                found = 1
                break
            except:
                logger.warning('There is no proper torrent link in the site.')
                pass

            driver_torrent.quit()

    display.stop()

    if found:
        try:
            os.remove(DOWN_DIR + '/*.torrent')
        except FileNotFoundError:
            pass

        new_file_name = DOWN_DIR + '/' + program_name + selected_date + '.torrent'

        for torrent_file in glob.glob(DOWN_DIR + '/*' + selected_date + '*.torrent'):
            shutil.move(torrent_file, new_file_name)
            break

        bot.sendDocument(chat_id=update.message.chat_id, document=open(new_file_name, 'rb'))
        update.message.reply_text('완료')
        logger.info('The torrent file is sent to %s' % user.first_name)

        if update.message.chat_id == MANAGER_ID or update.message.chat_id == MANAGER2_ID:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=RSA_KEY_LOCATION)
            sftp = ssh.open_sftp()
            sftp.put(new_file_name, REMOTE_DIR + '/' + program_name + selected_date + '.torrent')
            sftp.close()
            ssh.close()
            logger.info('Torrent file is sent to Kodi.')

        os.remove(new_file_name)
    else:
        logger.warning('The proper torrent seed is not found.')
        update.message.reply_text("토렌트 파일을 찾지 못했습니다.")

    return ConversationHandler.END


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the download." % user.first_name)
    update.message.reply_text('작업이 취소되었습니다.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            PROGRAM: [RegexHandler('^(썰전|무한도전|마이 리틀 텔레비전|차이나는 클라스)$', program)],

            DATE: [MessageHandler(Filters.text, date)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
