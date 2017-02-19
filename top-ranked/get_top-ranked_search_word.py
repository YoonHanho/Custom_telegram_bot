#!/usr/bin/python3

import logging
import re
from telegram.ext import Updater, CommandHandler
from bs4 import BeautifulSoup
from urllib.request import urlopen
from TOKEN import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

address       = {'Daum' :'http://www.daum.net/',
                 'Naver':'http://www.naver.com/'}
query_address = {'Daum' :'http://search.daum.net/search?w=tot&q=',
                 'Naver':'https://search.naver.com/search.naver?query='}

def get_rank_string(portal_site, bsObj):
    if(portal_site == 'Daum'):
        try:
            searching_word = bsObj.find("ol",{"id":"realTimeSearchWord"}).li.div.div.find("span",{"class":"txt_issue"}).a.strong.get_text()
            return searching_word
        except:
            logger.info("%s : parsing error" % portal_site)
    elif(portal_site == 'Naver'):
        try:
            searching_word = bsObj.find("ol",{"id":"realrank"}).li.a.span.get_text()
            return searching_word
        except:
            logger.info("%s : parsing error" % portal_site)

    return None

def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    update.message.reply_text("Hello, I will let you know the top-ranked real-time search word \
                              on Korean portals now.")
    update.message.reply_text("The command is /first.")

def first(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the rank" % (user.first_name, user.id))

    for portal_site in ['Daum','Naver']:
        page_src = urlopen(address[portal_site])
        bsObj = BeautifulSoup(page_src.read(), "html.parser")

        real_rank_item = get_rank_string(portal_site,bsObj)

        update.message.reply_text("Top-ranked real-time search word on " + portal_site)
        real_rank_wo_whitespace = re.sub('\s+', '+', real_rank_item)
        html_tag = '<a href="' + query_address[portal_site] + real_rank_wo_whitespace + '">' + real_rank_item + '</a>'
        bot.sendMessage(parse_mode='HTML', chat_id=update.message.chat_id, text=html_tag)

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(CommandHandler('first',first))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
