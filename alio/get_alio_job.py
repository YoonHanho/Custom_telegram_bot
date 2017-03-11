#!/usr/bin/python3

import logging
import re
from telegram.ext import Updater, CommandHandler
from bs4 import BeautifulSoup
from urllib.request import urlopen
from TOKEN import *
import urllib.parse

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    update.message.reply_text("Command는 /job 입니다.")


def job(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the job" % (user.first_name, user.id))

    page_src = \
        urlopen(
            'http://job.alio.go.kr/recruit.do?pageNo=1&param=&idx=&recruitYear=&recruitMonth=&detail_code=R600019&detail_code=R600020&location=R3010&location=R3017&work_type=R1010&career=R2020&replacement=N&s_date=&e_date=&org_name=&ing=2&title=&order=TERM_END')
    bsObj = BeautifulSoup(page_src.read(), "html.parser")

    theadList = []
    for headitem in bsObj.find("table", {"class": "tbl type_03"}).thead.findAll("th",{"scope": "col"}):
        theadList.append(headitem)

    for contentsList in bsObj.find("table", {"class": "tbl type_03"}).tbody.findAll("tr"):
        contents = contentsList.findAll("td")

        string = ""
        for thead, content in zip(theadList, contents):
            if thead.get_text().strip() != "" and content.get_text().strip() != "":
                string = string + thead.get_text().strip() + ' : ' + content.get_text().strip() + "\n"
        update.message.reply_text(string)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('job', job))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
