#!/usr/bin/python3

import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
from TOKEN import *
import urllib.parse
from top_ranked_word import *
import get_alio_notification
import make_epub_from_TED_subtitle
# from urllib.request import urlopen
# import ssl
import validators
from ebooklib import epub
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

SUB_CONVERT, PROGRAM, DATE = range(3)


def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    update.message.reply_text("안녕하세요 빵돼지 봇입니다.")
    update.message.reply_text("Command는 /first, /job, /sub, /tor 입니다.")


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


def job(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the job" % (user.first_name, user.id))

    job_list = get_alio_notification.get_alio_notification()

    for item in job_list:
        string = ""
        for key in item.keys():
            string = string + key + ' : ' + item[key] + "\n"
        update.message.reply_text(string)



def sub(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the conversion of TED subtitle." % (user.first_name, user.id))
    update.message.reply_text("TED 자막을 ebook(epub format)으로 변환해 드립니다. TED 자막 사이트의 URL을 알려주세요.")
    update.message.reply_text('아래 예시를 참고하세요.')
    update.message.reply_text('ex) http://www.ted.com/talks/ken_robinson_says_schools_kill_creativity/transcript?language=en',
                              disable_web_page_preview=True)
    return SUB_CONVERT


def print_example_and_retry(update):
    update.message.reply_text('아래 예시를 참고하세요.')
    update.message.reply_text('ex) http://www.ted.com/talks/ken_robinson_says_schools_kill_creativity/transcript?language=en',
                              disable_web_page_preview=True)
    update.message.reply_text('/sub 부터 다시 시작해주세요.')


def convert(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the conversion" % (user.first_name, user.id))

    web_address = update.message.text
    logger.info("Web address : %s" % web_address)

    subtitle = make_epub_from_TED_subtitle.get_subtitle_from_TED(web_address)

    if subtitle == None:
        update.message.reply_text("자막을 가져오지 못했습니다.")
        update.message.reply_text('적절한 TED 자막 사이트가 아닙니다. 혹시 맞다면 k11tos@nate.com 으로 알려주세요.')
        logger.info("This is not a TED web address.")
        return ConversationHandler.END

    book = epub.EpubBook()

    book.set_title(subtitle['title'])

    # book.set_language(language)

    book.add_author(subtitle['author'])

    # create chapter
    c1 = epub.EpubHtml(title='TED', file_name='subtitle.xhtml')
    subtitle_text = ''
    for time_step in subtitle['subtitle'].keys():
        subtitle_text = subtitle_text + time_step + '<br>'
        subtitle_text = subtitle_text + subtitle['subtitle'][time_step] + "<br><br>"

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

    update.message.reply_text('변환이 완료되었습니다. 파일을 확인해주세요.')
    logger.info("The job requested from User %s is done." % user.first_name)
    return ConversationHandler.END


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversion." % user.first_name)
    update.message.reply_text('변환이 취소되었습니다.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def get_firefox_profile_for_autodownload():

    profile = webdriver.FirefoxProfile()

    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWN_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "file/unknown")

    return profile


def torrent_start(bot, update):
    reply_keyboard = [['무한도전', '썰전', '마이 리틀 텔레비전', '차이나는 클라스', '라디오스타']]

    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))

    update.message.reply_text("토렌트 파일을 다운 받아 드립니다. 프로그램을 선택해주세요.",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return PROGRAM


def torrent_program(bot, update, user_data):
    user_data['program_name'] = update.message.text
    update.message.reply_text(user_data['program_name'] + '를 선택하셨습니다.')
    logger.info("Selected program : %s" % user_data['program_name'])

    update.message.reply_text("프로그램이 방영된 날짜를 선택해주세요. ex) 170209")

    return DATE


def torrent_date(bot, update, user_data):

    # user = update.message.from_user
    user_data['date'] = update.message.text

    try:
        date_in_format = parse(user_data['date']).date()
        today = datetime.date.today()
        if date_in_format > today:
            raise ValueError
    except:
        update.message.reply_text("날짜를 잘못 입력하셨습니다. /torrent 부터 다시 시작해주세요.")
        return ConversationHandler.END

    update.message.reply_text("선택하신 날짜는 " + str(date_in_format) + "입니다.")
    update.message.reply_text("잠시만 기다려주세요. 몇 분 정도 걸릴 수 있습니다.")
    logger.info("Selected date : %s" % date_in_format)

    display = Display(visible=0, size=(800, 600))
    display.start()

    profile = get_firefox_profile_for_autodownload()
    found = 0

    torrents = get_seedsite_by_torrentkim(user_data['program_name'], user_data['date'])
    if torrents == None:
        logger.warning('The proper torrent seed is not found.')
        update.message.reply_text("토렌트 파일을 찾지 못했습니다.")
        return ConversationHandler.END

    for torrent_title in torrents.keys():
        if re.search(r'720p-NEXT', torrent_title):
            logger.info("title = %s" % torrent_title)
            logger.info("target = %s" % torrents[torrent_title])

            driver_torrent = webdriver.Firefox(executable_path="/usr/local/bin/geckodriver",
                                               firefox_profile=profile)
            driver_torrent.get(torrents[torrent_title])
            logger.info("I am trying to connect to %s..." % torrents[torrent_title])

            try:
                driver_torrent.switch_to.alert.accept()
                logger.info('There is an alert for redirection.')
            except NoAlertPresentException:
                pass

            time.sleep(10)
            logger.info("torrent url : %s" % driver_torrent.current_url)

            try:
                element = driver_torrent.find_element_by_xpath("//table[@id='file_table']/tbody/tr[3]/td/a")

                logger.info(torrent_title)

                if update.message.chat_id == MANAGER_ID:
                    update.message.reply_text(driver_torrent.current_url)

                element.click()
                time.sleep(20)
                found = 1
                break
            except:
                logger.warning('There is no proper torrent link in the site.')
                pass

            driver_torrent.quit()

    display.stop()

    # if found:
    #     try:
    #         os.remove(DOWN_DIR + '/*.torrent')
    #     except FileNotFoundError:
    #         pass
    #
    #     new_file_name = DOWN_DIR + '/' + program_name + selected_date + '.torrent'
    #
    #     for torrent_file in glob.glob(DOWN_DIR + '/*' + selected_date + '*.torrent'):
    #         shutil.move(torrent_file, new_file_name)
    #         break
    #
    #     bot.sendDocument(chat_id=update.message.chat_id, document=open(new_file_name, 'rb'))
    #     update.message.reply_text('완료')
    #     logger.info('The torrent file is sent to %s' % user.first_name)
    #
    #     if update.message.chat_id == MANAGER_ID or update.message.chat_id == MANAGER2_ID:
    #         ssh = paramiko.SSHClient()
    #         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #         ssh.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=RSA_KEY_LOCATION)
    #         sftp = ssh.open_sftp()
    #         sftp.put(new_file_name, REMOTE_DIR + '/' + program_name + selected_date + '.torrent')
    #         sftp.close()
    #         ssh.close()
    #         logger.info('Torrent file is sent to Kodi.')
    #
    #     os.remove(new_file_name)
    # else:
    #     logger.warning('The proper torrent seed is not found.')
    #     update.message.reply_text("토렌트 파일을 찾지 못했습니다.")

    return ConversationHandler.END


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('first', first))
    dp.add_handler(CommandHandler('job', job))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    sub_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('sub', sub)],

        states={
            SUB_CONVERT: [MessageHandler(Filters.text, convert)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(sub_conv_handler)

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    tor_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('tor', torrent_start)],

        states={
            PROGRAM: [RegexHandler('^(썰전|무한도전|마이 리틀 텔레비전|차이나는 클라스|라디오스타)$', torrent_program, pass_user_data=True)],

            DATE: [MessageHandler(Filters.text, torrent_date, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(tor_conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling(poll_interval=10.,timeout=100.)

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
