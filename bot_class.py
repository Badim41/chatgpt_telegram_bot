import telebot
from base_funcs.logs import Logs
from base_funcs.base_functions import activate_commands
from network_tools.sql_storage import DictSQL
from network_tools import NetworkToolsAPI

import secret

bot = telebot.TeleBot(secret.bot_token, threaded=True, num_threads=50)

telebot.apihelper.RETRY_ON_ERROR = True
telebot.apihelper.MAX_RETRIES = 5
telebot.apihelper.RETRY_TIMEOUT = 3
telebot.apihelper.RETRY_ENGINE = 1

activate_commands(bot)
client = NetworkToolsAPI(secret.network_tools_api)

# Хранилище данных пользователей
user_data = DictSQL("user_data")
logger = Logs(warnings=True, name="bot")