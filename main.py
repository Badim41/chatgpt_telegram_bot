import os

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import secret
from base_funcs.base_classes import RequestType
from base_funcs.base_functions import send_generator, add_user_id, logger, clear_temp_folder, add_request
from base_funcs.logs import Color
from bot_class import bot, client, user_data

# Поддерживаемые типы файлов
SUPPORTED_TEXT_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc', '.rtf', '.py', '.java', '.png', '.jpg'}  # форматы
temp_folder = "temp"
os.makedirs(temp_folder, exist_ok=True)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user_id(message.chat.id)
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"history": [], "usage_count": 0, "is_processing": False}
    bot.reply_to(message, secret.welcome_text)


@bot.message_handler(commands=['clear'])
def command_check(message):
    user = user_data.get(message.chat.id, {"history": [], "usage_count": 0, "is_processing": False})
    user["history"] = []
    user_data[message.chat.id] = user
    bot.send_message(message.chat.id, "История запросов очищена")


# Функция отправки ошибки создателю и пользователю
def report_error(chat_id: int, error: Exception, context: str):
    error_message = f"Ошибка у пользователя {chat_id}: {str(error)}\nКонтекст: {context}"
    try:
        bot.send_message(secret.owner_ids[0], error_message)
    except Exception as e:
        logger.logging(f"Не удалось отправить ошибку создателю: {e}")
    try:
        bot.send_message(chat_id, "Произошла ошибка при обработке вашего запроса. Мы уже работаем над этим!")
    except Exception as e:
        logger.logging(f"Не удалось уведомить пользователя {chat_id}: {e}")


# Функция проверки лимита и обработки запроса
def process_request(chat_id: int, prompt: str, file_path: str = None):
    logger.logging(f"process_request: {prompt}, {file_path}, {chat_id}")
    # Получаем текущие данные пользователя
    user = user_data.get(chat_id, {"history": [], "usage_count": 0, "is_processing": False})

    # todo Для ограничения одновременных запросов
    # if user["is_processing"]:
    #     bot.send_message(chat_id, "Дождитесь выполнения предыдущего запроса")
    #     return

    # todo Для ограничения запросов
    if user["usage_count"] >= secret.request_limit and str(chat_id) not in secret.owner_ids:
        logger.logging(f"Reached limit: {prompt}, {file_path}, {chat_id}")
        bot.send_message(
            chat_id,
            f"Вы достигли лимита запросов в данном боте"
        )
        return

    add_request(user_id=chat_id, request=f"{file_path}, {prompt}", request_type=RequestType.text)
    sent_message = bot.send_message(chat_id, "⏳ Генерация ответа...")

    user["is_processing"] = True
    user_data[chat_id] = user  # Сохраняем обновленные данные

    try:
        # Вызов ChatGPT API
        generator = client.chatgpt_api(
            prompt=prompt,
            model=secret.gpt_model,
            chat_history=user["history"],
            file_path=file_path,
            internet_access=secret.internet_access,
            stream=True
        )

        sent_generator = send_generator(bot, chat_id, maybe_generator=generator, stream=True)
        # print("set chat_history", sent_generator.response_gpt.chat_history)

        # Обновляем историю и счетчик
        user["history"] = sent_generator.response_gpt.chat_history
        user["usage_count"] += 1
    except Exception as e:
        logger.logging(f"Ошибка в process_request: {e}")
        report_error(chat_id, e, "process_request")
    finally:
        user["is_processing"] = False
        user_data[chat_id] = user  # Сохраняем состояние после завершения
        bot.delete_message(chat_id, sent_message.message_id)


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not secret.public_bot and str(message.chat.id) not in secret.owner_ids:
        bot.send_message(message.chat.id, f"Вам запрещён доступ в этого бота\nВаш user ID:{message.chat.id}")
        return
    try:
        chat_id = message.chat.id
        # for k, v in user_data.items():
        #     print("k", k, "v", v)
        if chat_id not in user_data:
            user_data[chat_id] = {"history": [], "usage_count": 0, "is_processing": False}
        process_request(chat_id, message.text)
    except Exception as e:
        logger.logging(f"Ошибка в handle_text: {e}")
        report_error(message.chat.id, e, "handle_text")


# Обработчик отправки документов
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not secret.public_bot and str(message.chat.id) not in secret.owner_ids:
        bot.send_message(message.chat.id, f"Вам запрещён доступ в этого бота\nВаш user ID:{message.chat.id}")
        return
    try:
        chat_id = message.chat.id
        if chat_id not in user_data:
            user_data[chat_id] = {"history": [], "usage_count": 0, "is_processing": False}

        file_name = message.document.file_name
        print("file_name", file_name)
        file_extension = os.path.splitext(file_name)[1].lower()

        # Проверяем, является ли файл текстовым
        if file_extension in SUPPORTED_TEXT_EXTENSIONS:
            # Скачиваем файл
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Сохраняем файл временно
            file_path = f"{temp_folder}/temp_{chat_id}_{file_name}"
            with open(file_path, "wb") as f:
                f.write(downloaded_file)

            # Обрабатываем запрос с файлом
            prompt = message.caption if message.caption else " "
            process_request(chat_id, prompt, file_path)

            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            bot.reply_to(message, "Неподдерживаемый тип файла. Поддерживаются: .txt, .pdf, .docx, фото.")
    except Exception as e:
        logger.logging(f"Ошибка в handle_document: {e}")
        report_error(message.chat.id, e, "handle_document")


# Обработчик фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if not secret.public_bot and str(message.chat.id) not in secret.owner_ids:
        bot.send_message(message.chat.id, f"Вам запрещён доступ в этого бота\nВаш user ID:{message.chat.id}")
        return
    try:
        chat_id = message.chat.id
        if chat_id not in user_data:
            user_data[chat_id] = {"history": [], "usage_count": 0, "is_processing": False}

        # Получаем файл самого высокого качества
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем файл временно
        file_path = f"{temp_folder}/temp_{chat_id}_photo.jpg"
        with open(file_path, "wb") as f:
            f.write(downloaded_file)

        # Обрабатываем запрос с файлом
        prompt = message.caption if message.caption else "Опиши фото"
        process_request(chat_id, prompt, file_path)

        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.logging(f"Ошибка в handle_photo: {e}")
        report_error(message.chat.id, e, "handle_photo")


# Обработчик неподдерживаемых типов
@bot.message_handler(content_types=['audio', 'voice', 'sticker', 'video_note', 'video', 'animation'])
def handle_unsupported(message):
    bot.reply_to(message, "Неподдерживаемый тип файла. Поддерживаются: .txt, .pdf, .docx, фото, видео, анимации.")


# Запуск бота
if __name__ == "__main__":
    clear_temp_folder(temp_folder)
    clear_temp_folder("images")

    logger.logging(f"@{bot.user.username} запущен...", color=Color.GREEN)
    bot.infinity_polling()
