import datetime
import json
import os
import re
import shutil
import threading
import time

from network_tools._types import GptResponse
from telebot import types

import secret
from base_funcs.base_classes import RequestType
from base_funcs.logs import Logs, Color
from base_funcs.soft_wrapper import limit_soft_wraps_stream, soft_wraps

logger = Logs(warnings=True, name="base-func")
file_lock = threading.Lock()
request_text_lock = threading.Lock()


def try_remove(image_path: [str, list, None]):
    if not image_path:
        return
    if isinstance(image_path, str):
        image_paths = [image_path]
    else:
        image_paths = image_path

    for image_path_rm in image_paths:
        if os.path.exists(image_path_rm):
            try:
                os.remove(image_path_rm)
            except Exception as e:
                logger.logging(f"Warn: path {image_path_rm} cant be removed: {e}", color=Color.RED)
        else:
            logger.logging(f"Warn: path {image_path_rm} not exists", color=Color.RED)


def clear_temp_folder(temp_folder):
    if not os.path.exists(temp_folder):
        return
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Удаление файла или символической ссылки
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Удаление вложенной папки
        except Exception as e:
            logger.logging(f"Ошибка при удалении {file_path}: {e}")


def add_user_id(user_id):
    file_name = 'data.json'
    with file_lock:
        try:
            if not os.path.exists(file_name):
                with open(file_name, 'w') as writer:
                    writer.write("[]")

            # Чтение JSON из файла
            with open(file_name, 'r') as file:
                config_data = json.load(file)

            all_ids = [element["id"] for element in config_data]
            for chat_id in all_ids:
                if chat_id == user_id:
                    return True

            # Добавление нового элемента

            new_element = {
                "id": user_id
            }

            # Проверка, является ли конфиг списком
            if isinstance(config_data, list):
                config_data.append(new_element)
            else:
                # Если конфиг не является списком, создаем новый список
                config_data = [config_data, new_element]

            # Преобразование обновленных данных в JSON
            updated_json = json.dumps(config_data, indent=2)

            # Сохранение обновленного JSON в файл
            with open(file_name, 'w') as file:
                file.write(updated_json)
        except FileNotFoundError:
            logger.logging(f"Ошибка: файл {file_name} не найден")
        except json.JSONDecodeError:
            logger.logging(
                f"Ошибка декодирования JSON в файле {file_name}. Пожалуйста, убедитесь, что файл содержит корректный JSON."
            )
        except Exception as e:
            logger.logging(f"Произошла ошибка: {e}")


class GeneratorResult:
    def __init__(self, response_gpt: GptResponse, full_answer: str):
        self.response_gpt = response_gpt
        self.full_answer = full_answer


def send_generator(bot, user_id, maybe_generator, stream) -> GeneratorResult:
    last_response = None
    full_answer_text = ""
    error_occurred = False  # Флаг, указывающий, что произошла ошибка

    def generator_wrapper():
        nonlocal last_response, full_answer_text
        for response in maybe_generator:
            last_response = response
            full_answer_text += response.response.text
            yield response.response.text

    sent_messages = []  # Каждый элемент: {"message_id": ..., "text": ...}
    retry_after = 5

    try:
        for messages in limit_soft_wraps_stream(generator_wrapper(),
                                                max_length=3950,
                                                split_threshold=3500,
                                                min_length_yield=10 if stream else 10 ** 10,
                                                func_each_yield=lambda x: x * 3):
            # Фильтруем и нормализуем входящие куски (удаляем лишние пробелы)
            normalized_chunks = [chunk.strip() for chunk in messages if chunk.strip()]
            logger.logging("normalized_chunks", normalized_chunks)
            for i, new_text in enumerate(normalized_chunks):
                if error_occurred:
                    # Если ошибка уже произошла, прерываем обработку yield
                    break
                if i < len(sent_messages):
                    old_text = sent_messages[i]["text"]
                    # Если содержимое не изменилось — пропускаем редактирование
                    if old_text == new_text:
                        continue

                    try:
                        bot.edit_message_text(chat_id=user_id,
                                              message_id=sent_messages[i]["message_id"],
                                              text=new_text,
                                              parse_mode="Markdown" if "```" in new_text else None)
                        sent_messages[i]["text"] = new_text
                    except Exception as e:
                        err_msg = str(e)
                        logger.logging("err_msg", err_msg)
                        if "can't parse entities" in err_msg:
                            try:
                                bot.edit_message_text(chat_id=user_id,
                                                      message_id=sent_messages[i]["message_id"],
                                                      text=new_text)
                                sent_messages[i]["text"] = new_text
                            except Exception as inner_e:
                                logger.logging(f"Ошибка при редактировании без Markdown: {inner_e}")
                        elif "message is not modified" in err_msg:
                            # Если сообщение не изменилось, просто пропускаем редактирование
                            continue
                        elif "429" in err_msg:
                            logger.logging(f"Получен 429: {err_msg}. Прерываем отправку по частям.")
                            match = re.search(r"retry after (\d+)", err_msg)
                            if match:
                                retry_after = int(match.group(1))
                                logger.logging(f"Нужно подождать {retry_after} секунд.")
                                error_occurred = True
                                break
                        else:
                            logger.logging(f"Ошибка при редактировании сообщения: {e}")
                else:
                    try:
                        sent = bot.send_message(chat_id=user_id,
                                                text=new_text,
                                                parse_mode="Markdown" if "```" in new_text else None)
                        sent_messages.append({"message_id": sent.message_id, "text": new_text})
                    except Exception as e:
                        err_msg = str(e)
                        logger.logging(err_msg)
                        if "can't parse entities" in err_msg:
                            try:
                                sent = bot.send_message(
                                    chat_id=user_id,
                                    text=new_text
                                )
                                sent_messages.append({"message_id": sent.message_id, "text": new_text})
                            except Exception as inner_e:
                                logger.logging(f"Ошибка при отправке без Markdown: {inner_e}")
                        elif "429" in err_msg:
                            logger.logging(f"Получен 429: {err_msg}. Прерываем отправку по частям.")
                            match = re.search(r"retry after (\d+)", err_msg)
                            if match:
                                retry_after = int(match.group(1))
                                logger.logging(f"Нужно подождать {retry_after} секунд.")
                                error_occurred = True
                                break
                        else:
                            logger.logging(f"Ошибка при отправке сообщения: {e}")
            if error_occurred:
                break  # Выходим из внешнего цикла, если произошла ошибка
    except Exception as outer_e:
        logger.logging(f"Внешняя ошибка при обработке yield: {outer_e}")

    # Если произошла ошибка, отправляем весь собранный текст одним сообщением
    if error_occurred:
        try:
            time.sleep(retry_after)
            for msg in sent_messages:
                try:
                    bot.delete_message(chat_id=user_id, message_id=msg["message_id"])
                except Exception as delete_e:
                    logger.logging(f"Ошибка при удалении сообщения {msg['message_id']}: {delete_e}")

            messages = soft_wraps(full_answer_text, max_length=3900, split_threshold=3500)
            for message in messages:
                bot.send_message(
                    user_id,
                    message
                )
                time.sleep(3)
        except Exception as e:
            logger.logging("Ошибка при отправке полного сообщения:", e)

    # if stream and not error_occurred:
    #     try:
    #         bot.send_message(
    #             user_id,
    #             self.translates.stream_end_action
    #         )
    #     except Exception as e:
    #         logger.logging(f"Ошибка при добавлении reply_markup: {e}")

    return GeneratorResult(response_gpt=last_response, full_answer=full_answer_text)


def add_request(user_id, request, request_type: str):
    os.makedirs("configs", exist_ok=True)
    if request_type not in RequestType.__dict__.values():
        raise Exception(f"requests_type {request_type} not in RequestType: {RequestType.__dict__.values()}")

    request = f"(type={request_type}) " + request

    history_txt = f"configs/{user_id}.txt"
    if not os.path.exists(history_txt):
        with open(history_txt, "w", encoding="utf-8"):
            pass

    # очистка запросов за день
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")

    with open(history_txt, "a", encoding="utf-8") as file:
        file.write(request + "\n=====Next=====\n")

    with request_text_lock:
        file_name = f"stats_{request_type}.txt"

        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8"):
                pass

        with open(file_name, encoding="utf-8") as reader:
            lines = reader.readlines()
            content = ''.join(lines)
            if not str(current_datetime) in content:
                with open(file_name, "a", encoding="utf-8") as writer:
                    writer.write("\n" + str(current_datetime) + "\n")
                    writer.write("Использование=1")
            else:
                last_line_number = lines[len(lines) - 1]
                last_line_number = int(last_line_number[last_line_number.find("=") + 1:])
                lines.pop()

                # Заменяем последнюю строку
                new_last_line = f"Использование={last_line_number + 1}"
                lines.append(new_last_line)

                # Открываем файл для записи с обновленным содержимым
                with open(file_name, "w", encoding="utf-8") as file:
                    file.writelines(lines)


def activate_commands(bot):
    @bot.message_handler(commands=['check'])
    def command_check(message: types.Message):
        if str(message.chat.id) in secret.owner_ids:
            file_name = 'data.json'
            with open(file_name, 'r') as file:
                config_data = json.load(file)

            send_number = len([element["id"] for element in config_data])
            bot.send_message(message.chat.id, f"всего {send_number} пользователей")

            used_today_all = 0
            all_message_text = ""
            for stat_name in RequestType.__dict__.values():
                file_stats = f"stats_{stat_name}.txt"
                if os.path.exists(file_stats):
                    try:
                        with open(file_stats, "r", encoding="utf-8") as reader:
                            content = ''.join(reader.readlines()[-14:])
                            all_message_text += stat_name + ":\n\n" + content + "\n\n"

                            if datetime.datetime.now().strftime("%Y-%m-%d") in content:
                                used_today_temp = int(content[content.rfind("=") + 1:])
                                used_today_all += used_today_temp
                    except Exception as e:
                        logger.logging(e)
            bot.send_message(message.chat.id, all_message_text[:3950])
            bot.send_message(message.chat.id, f"Всего использований сегодня:{used_today_all}")

        else:
            bot.send_message(message.chat.id, "У вас нет прав чтобы сделать это")
