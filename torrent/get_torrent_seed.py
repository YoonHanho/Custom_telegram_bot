#!/usr/bin/python3

import re
import time
from datetime import datetime
import pyvirtualdisplay
import logging
import os
import paramiko
import shutil
import glob
from dateutil.parser import *
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
from TOKEN import (TOKEN, RSA_KEY_LOCATION, DOWN_DIR, REMOTE_HOST, REMOTE_USER, REMOTE_DIR,
        MANAGER_ID)
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='./log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

PROGRAM, DATE = range(2)

def start(bot, update):
    reply_keyboard = [['무한도전', '썰전']]

    update.message.reply_text("I will download the torrent file.\nPlease select the program.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return PROGRAM

def get_html_special_chars(program_name):
    if(program_name == '썰전'):
        return '%EC%8D%B0%EC%A0%84'
    elif(program_name == '무한도전'):
        return '%EB%AC%B4%ED%95%9C%EB%8F%84%EC%A0%84'
    #return unicode(program_name, "utf-8")

def program(bot, update):
    global program_name
    global selected_program

    program_name = update.message.text
    update.message.reply_text('You choose ' + program_name)
    logger.info("Selected program : %s" % program_name)

    selected_program = get_html_special_chars(program_name)

    update.message.reply_text("Please select the date.\nex) 170209")

    return DATE

def get_firefox_profile_for_autodownload():
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", '~')
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "file/unknown")

    return profile

def date(bot, update):
    global selected_program
    global selected_date
    global program_name

    user = update.message.from_user
    selected_date = update.message.text

    try:
        date_in_format = parse(selected_date)
        logger.info("Selectd date : %s" % date_in_format)
    except:
        update.message.reply_text("The selected date is not valid.\nPlease start again by /start.")
        return ConversationHandler.END

    if(date_in_format > datetime.now()):
        update.message.reply_text("The selected date is not valid.\nPlease start again by /start.")
        return ConversationHandler.END

    driver = webdriver.PhantomJS()
    driver.get("https://www.google.co.kr/search?q="
               + selected_program + "+" + selected_date
               +"+720p+NEXT+torrent")
    time.sleep(10)
    page_sources = driver.page_source
    driver.quit()

    bsObj = BeautifulSoup(page_sources, "html.parser")

    try:
        search_lists = bsObj.find("div",{"id":"ires"}).ol.children
    except AttributeError:
        logger.info("Parsing error at searching in google")
        update.message.reply_text('Please check the name and the date of the program.')
        return ConversationHandler.END

    profile = get_firefox_profile_for_autodownload()
    display = Display(visible=0, size=(800, 600))
    display.start()

    found = 0

    for search_item in search_lists:
        try:
            target_address = search_item.find("div",{"class":"kv"}).cite.get_text()
            title = search_item.find("a").get_text()
        except AttributeError:
            logger.info("Parsing error at searching in google")
            update.message.reply_text('Please check the name and the date of the program.')
            return ConversationHandler.END

        if re.search('torrentkim',target_address) \
                and re.search(program_name, title) \
                and re.search(selected_date, title):

            try:
                driver_torrent = webdriver.Firefox(executable_path = "/usr/local/bin/geckodriver",
                                               firefox_profile = profile)
                driver_torrent.get(target_address)
            except FileNotFoundError:
                continue

            try:
                element = driver_torrent.find_element_by_xpath("//table[@id='file_table']/tbody/tr[3]/td/a")
                logger.info(title)
                logger.info("torrent address : %s" % target_address)

                if(update.message.chat_id == MANAGER_ID):
                    update.message.reply_text(target_address)

                element.click()
                time.sleep(10)
                found = 1
                break
            except:
                pass

            driver_torrent.quit()

    display.stop()

    if(found):
        new_file_name = DOWN_DIR + '/' + program_name + selected_date + '.torrent'

        for torrent_file in glob.glob(DOWN_DIR + '/*' + selected_program + '*' + selected_date + '*.torrent'):
            shutil.move(torrent_file, new_file_name)
            break

        bot.sendDocument(chat_id=update.message.chat_id,document=open(new_file_name,'rb') )
        update.message.reply_text('Done')
        logger.info('The torrent file is send to %s' % user.first_name)

        if(update.message.chat_id == MANAGER_ID):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(REMOTE_HOST, username = REMOTE_USER, key_filename = RSA_KEY_LOCATION)
            sftp = ssh.open_sftp()
            sftp.put(new_file_name, REMOTE_DIR +'/' + program_name + selected_date + '.torrent')
            sftp.close()
            ssh.close()
            logger.info('Torrent file is send to Kodi.')

        os.remove(new_file_name)
    else:
        update.message.reply_text("I couldn't find the torrent file.")

    return ConversationHandler.END

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the download." % user.first_name)
    update.message.reply_text('The download is cancelled.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            PROGRAM: [RegexHandler('^(썰전|무한도전)$', program)],

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
