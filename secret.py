from network_tools import GptModels

bot_token = "BOT_TOKEN"  # Вставьте API Token от BotFather
network_tools_api = "NETWORK_TOOLS_API_KEY"  # Вставьте API-ключ от GPT4_Unlimit_bot
owner_ids = ["YOUR_USER_ID"]  # user id пользователей, которым разрешён доступ
# Можно узнать user id тут: @FIND_MY_ID_BOT
public_bot = False  # Сделать бота доступным другим пользователям
request_limit = 10  # (если public_bot) Лимит запросов в боте.
# У пользователей из списка owner_ids бесконечные запросы.

gpt_model = GptModels.gpt_4o  # модель для генерации текста. Смотрите далее
internet_access = True  # доступ в интренет. Не приведёт к дополнительным тратам на моделях gpt_4o, claude, deepseek, minimax

welcome_text = f"""Добро пожаловать! В нашем боте вы можете воспользоваться {gpt_model}!

📖 Что умеет бот?
- Создавать тексты и статьи
- Писать и редактировать код
- Переводить тексты
- Решать домашнее задание
- Распознавать фотографии
- Распознавать файлы

💬 Чтобы получить текстовый ответ, отправьте ваш запрос в чат
Бот поддерживает распознавание файлов:
• Текст (.txt | .docx | .pdf | .py | .java)
• Изображения (.png | .jpg)"""
