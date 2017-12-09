#!/usr/bin/python3

import logging
import re
from telegram.ext import Updater, CommandHandler
from bs4 import BeautifulSoup
from urllib.request import urlopen
from TOKEN import *
import urllib.parse

import sys
sys.path.append('../../custom_function')
from get_top_ranked_search_word import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    update.message.reply_text("안녕하세요 각 포탈 사이트의 실시간 검색어 1위를 알려드립니다.")
    update.message.reply_text("Command는 /first 입니다.")


def first(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the rank" % (user.first_name, user.id))

    for portal_site in ['Daum', 'Naver']:
        real_rank_item = get_rank_string(portal_site)

        if real_rank_item is not None:
            update.message.reply_text(portal_site + " 실시간 검색어 1위")
            real_rank_wo_whitespace = urllib.parse.quote_plus(real_rank_item)
            html_tag = '<a href="' + query_address[
                portal_site] + real_rank_wo_whitespace + '">' + real_rank_item + '</a>'
            bot.sendMessage(parse_mode='HTML', chat_id=update.message.chat_id, text=html_tag)
        else:
            logger.info("%s : parsing error" % portal_site)
            update.message.reply_text(portal_site + " site가 수정되어 봇 업데이트가 필요합니다. 최대한 빨리 업데이트 하겠습니다.")
            bot.sendMessage(chat_id=MANAGER_ID, text = "실시간 검색어 봇에서 " + portal_site + "에 대한 업데이트가 필요합니다.")


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('first', first))

    # Start the Bot
    updater.start_polling(poll_interval=10.,timeout=10.)

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
