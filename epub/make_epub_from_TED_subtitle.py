#!/usr/bin/python3

import logging
import validators
import os
from bs4 import BeautifulSoup
from urllib.request import (urlopen, HTTPError)
from TOKEN import *
from ebooklib import epub
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CONVERT = range(1)

def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    update.message.reply_text("I will make an e-book from TED subtitle.\n \
                              Please input the web address which includes the subtitle of TED.")
    return CONVERT

def print_example_and_retry(update):
    update.message.reply_text('Please refer to the example below.')
    update.message.reply_text('ex) http://www.ted.com/talks/ken_robinson_says_schools_kill_creativity/transcript?language=en',
                              disable_web_page_preview=True)
    update.message.reply_text('Please start again by /start')


def convert(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the conversion" % (user.first_name, user.id))

    web_address = update.message.text
    logger.info("Web address : %s" % web_address)
    if not validators.url(web_address):
        update.message.reply_text('It is not a valid web address.')
        print_example_and_retry(update)
        logger.info("This is not a web address.")
        return ConversationHandler.END
    else:
        try:
            page_src=urlopen(web_address)
        except HTTPError:
            update.message.reply_text("I couldn't find the server you gave.")
            print_example_and_retry(update)
            logger.info("The server don't respond.")
            return ConversationHandler.END

    bsObj = BeautifulSoup(page_src.read(), "html.parser")

    book = epub.EpubBook()

    try:
        titleObj = bsObj.find("h4",{"class":"m5"}).a
        authorObj = bsObj.find("h4",{"class":"talk-link__speaker"})
        paraObjs = bsObj.findAll("p",{"class":"talk-transcript__para"})
    except AttributeError:
        update.message.reply_text('This is not a TED address.\n \
                                  If it is, please contact to the administrator')
        print_example_and_retry(update)
        logger.info("This is not a TED web address.")
        return ConversationHandler.END

    title = titleObj.get_text()
    book.set_title(title)

    language = titleObj['lang']
    book.set_language(language)

    author = authorObj.get_text()
    book.add_author(author)

    # create chapter
    c1 = epub.EpubHtml(title='TED', file_name='subtitle.xhtml', lang=language)
    subtitle_text = ''
    for para in paraObjs:
        subtitle_text = subtitle_text + para.data.get_text() + '<br>'
        for line in para.span.get_text().split('\n'):
            subtitle_text = subtitle_text + line + ' '
        subtitle_text = subtitle_text + '<br><br>'

    c1.content='<p>' + subtitle_text + '</p>'

    # add chapter
    book.add_item(c1)

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css",
            content=style)

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    book.spine = ['nav', c1]

    # write to the file
    try:
        os.remove(LOG_DIR + '/ted.epub')
    except FileNotFoundError:
        pass

    epub.write_epub(LOG_DIR + '/ted.epub', book, {})
    bot.sendDocument(chat_id=update.message.chat_id,document=open(LOG_DIR + '/ted.epub','rb') )

    update.message.reply_text('The job is done. Please check the file.')
    logger.info("The job requested from User %s is done." % user.first_name)
    return ConversationHandler.END

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversion." % user.first_name)
    update.message.reply_text('The conversion is cancelled.',
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
            CONVERT: [MessageHandler(Filters.text, convert)]
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
