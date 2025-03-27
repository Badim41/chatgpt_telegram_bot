<p align="center">
  <img src="https://github.com/Badim41/chatgpt_telegram_bot/blob/master/Logo.png?raw=true" width="300px" height="300px"/>
</p>

<h1 align="center">ChatGPT Telegram Bot</h1>

<div align="center">

[![API-ключ](https://img.shields.io/badge/ApiKey-Get-green?style=flat&logo=googlechrome)](https://t.me/GPT4_Unlimit_bot?start=git1)
[![Example Usage Bot](https://img.shields.io/badge/Example-Telegram--BOT-0066FF?logo=probot&style=flat)](https://t.me/deepseekR1_free_bot)

</div>

---

## О боте

Здесь будет рассказано о создании собственного телеграм-бота с ChatGPT.

Бот использует [NetworkToolsAPI](https://github.com/Badim41/network_tools) для отправки запросов к ChatGPT и другим моделям

Цена на все модели в NetworkToolsAPI в **2 раза** ниже официальных

# Настройка бота
## Получение API Telegram-бота

1. Перейдите в официального телеграм-бота [BotFather](https://t.me/BotFather)
2. Напишите /newbot
3. Введите название и тэг для бота
4. Скопируйте API Token. Он ещё понадобится

## 🔑 Получение API-ключа NetworkToolsAPI

Чтобы получить API-ключ с **бесплатным балансом 1$**:
1. Перейдите в телеграм-бота [@GPT4_Unlimit_bot](https://t.me/GPT4_Unlimit_bot?start=git2)
2. Напишите /get_api
3. Скопируйте API-ключ

## Заполнение ключей
Откройте файл secret.py:

```python
from network_tools import GptModels

bot_token = "BOT_TOKEN"  # Вставьте API Token от BotFather
network_tools_api = "NETWORK_TOOLS_API_KEY"  # Вставьте API-ключ от GPT4_Unlimit_bot
owner_ids = ["YOUR_USER_ID"]  # user id пользователей, которым разрешён доступ
# Можно узнать user id тут: @FIND_MY_ID_BOT
public_bot = False  # Сделать бота доступным другим пользователям
request_limit = 10  # (если public_bot) Лимит запросов в боте.
# У пользователей из списка owner_ids бесконечные запросы.

gpt_model = GptModels.gpt_4o  # модель для генерации текста. Смотрите далее
```

### Модели для генерации текста:
- GPT-4.5 (OpenAI)
- o3-mini (OpenAI)
- o1 (OpenAI)
- GPT-4o (OpenAI)
- GPT-4o-mini (OpenAI)
- GPT-3.5 (OpenAI)
- Claude 3.7 (Anthropic)
- Claude 3.5 Sonnet (Anthropic)
- Claude 3 Opus (Anthropic)
- Claude 3 Sonnet (Anthropic)
- Claude 3 Haiku (Anthropic)
- DeepSeek R1 (DeepSeek)
- DeepSeek V3 (DeepSeek)
- Command A (Cohere)
- Command R+ (Cohere)
- Reka Flash (Reka)
- Minimax-01 (Minimax)

# 🚀 Запуск бота

Запустите main.py и напишите в вашего бота /start

### Дополнительно
- Ответ от ChatGPT выводится частями по мере генерации ответа. Для избежания ограничений на отправку сообщений Telegram выводится вначале 10, потом 30, 90, 270 (и т.д.) символов ответа.
- Напишите /check для проверки использований бота
- Бот может распознавать изображения и читать содержимое файлов
- История запросов сохраняется, чтобы очистить её, введите /clear
- База данных (SQL) хранится в папке lock_storage