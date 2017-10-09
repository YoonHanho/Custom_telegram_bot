#!/usr/bin/python3

import logging
from telegram.ext import Updater, CommandHandler
from TOKEN import *
import thingspeak
import json
import datetime
import pytz

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=LOG_DIR + '/log.txt',
                    level=logging.INFO)

logger = logging.getLogger(__name__)



def start(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) started the bot." % (user.first_name, user.id))
    if user.id == MANAGER_ID or user.id == MANAGER2_ID:
        update.message.reply_text("Command는 /status 입니다.")
    else:
        update.message.reply_text("이 bot은 특정 사용자에게만 지원됩니다.")


def status(bot, update):
    user = update.message.from_user
    logger.info("%s(%s) wants the status" % (user.first_name, user.id))

    channel_esp8266 = thingspeak.Channel(id=ESP8266_CHANNEL_ID, api_key=ESP8266_READ_KEY)

    dict = json.loads(channel_esp8266.get_field_last(field='field1'))

    created_at = dict['created_at']
    local = pytz.timezone('Asia/Seoul')
    utc_dt = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    created_at = local.localize(utc_dt, is_dst=None)

    pm1_0 = dict['field1']
    dict = json.loads(channel_esp8266.get_field_last(field='field2'))
    pm2_5 = dict['field2']
    dict = json.loads(channel_esp8266.get_field_last(field='field3'))
    pm10_0 = dict['field3']
    dict = json.loads(channel_esp8266.get_field_last(field='field5'))
    temperature = dict['field5']
    dict = json.loads(channel_esp8266.get_field_last(field='field6'))
    humidity = dict['field6']

    channel_rp = thingspeak.Channel(id=RP_CHANNEL_ID, api_key=RP_READ_KEY)
    dict = json.loads(channel_rp.get_field_last(field='field1'))
    kodi_temp = dict['field1']
    dict = json.loads(channel_rp.get_field_last(field='field2'))
    rp_temp = dict['field2']

    update.message.reply_text("* 측정 시간 : " + str(created_at) + '\n'
                            + "- PM1.0 : " + pm1_0 + " ㎍/m³" + '\n'
                            + "- PM2.5 : " + pm2_5 + " ㎍/m³" + '\n'
                            + "- PM10.0 : " + pm10_0 + " ㎍/m³" + '\n'
                            + "- 온도 : " + str(float(temperature)) + " ℃" + '\n'
                            + "- 습도 : " + str(float(humidity)) + " %" + '\n'
                            + "- KODI CPU 온도 : " + kodi_temp + " ℃" + '\n'
                            + "- Raspberry Pi CPU 온도 : " + rp_temp + " ℃")


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('status', status))

    # Start the Bot
    updater.start_polling(poll_interval=10.,timeout=10.)

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
