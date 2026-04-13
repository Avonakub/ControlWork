import pytz
import telebot
import os
import datetime
import locale
import db_telegrambot
from random import randint, choice
from PIL import Image, ImageFilter


TOKEN = "место для токена"

try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'ru_RU')
    except:
        print("Русский язык не найден, дата будет на английском")

BUTTON_FACT = "🎓 Факт"
BUTTON_FUTURE = "🔮 Предсказание"
BUTTON_GAME_RPS = "🤜✌️✋ Камень-ножницы-бумага"


RPS_STATS = {}
LAST_BOT_QUESTION = {}
USER_CURRENT_IMAGE_PATH = {}

bot = telebot.TeleBot(TOKEN)
conn = db_telegrambot.connect_db()


def log_user_action(user_id, action_user, user_message=None, bot_response=None):
    try:
        db_telegrambot.save_user_action(conn, user_id, action_user,
                                        user_message, bot_response)
    except Exception as e:
        print(f"Ошибка логирования: {e}")


def create_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    button_fact = telebot.types.KeyboardButton(BUTTON_FACT)
    button_future = telebot.types.KeyboardButton(BUTTON_FUTURE)
    button_game_rps = telebot.types.KeyboardButton(BUTTON_GAME_RPS)
    button_clear = telebot.types.KeyboardButton("🗑️ Скрыть меню")

    keyboard.add(button_fact, button_future)
    keyboard.add(button_game_rps)
    keyboard.add(button_clear)

    return keyboard


# ============================= КЛАВИАТУРА ДЛЯ ИГРЫ =============================
def create_game_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)

    button_stone = telebot.types.InlineKeyboardButton(
        text="🤜 Камень",
        callback_data="rps_stone"
    )

    button_scissors = telebot.types.InlineKeyboardButton(
        text="✌️ Ножницы",
        callback_data="rps_scissors"
    )

    button_paper = telebot.types.InlineKeyboardButton(
        text="✋ Бумага",
        callback_data="rps_paper"
    )

    keyboard.add(button_stone, button_scissors, button_paper)

    keyboard.add(
        telebot.types.InlineKeyboardButton("📊 Статистика", callback_data="rps_stats"),
        telebot.types.InlineKeyboardButton("🔄 Сброс статистики", callback_data="rps_reset")
    )

    return keyboard


# ============================= КЛАВИАТУРА ДЛЯ ФИЛЬТРОВ =============================
def create_filters_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_gray_filter = telebot.types.InlineKeyboardButton(
        text="⚫ Черно-белый",
        callback_data="filter_grayscale"
    )

    button_binarization_filter = telebot.types.InlineKeyboardButton(
        text="⚪ Бинаризация",
        callback_data="filter_binarization"
    )

    button_pixelization_filter = telebot.types.InlineKeyboardButton(
        text="🧩 Пикселизация",
        callback_data="filter_pixelization"
    )

    button_custom_filter = telebot.types.InlineKeyboardButton(
        text="⬇️ Растяжение вниз",
        callback_data="filter_custom"
    )

    button_blur_image = telebot.types.InlineKeyboardButton(
        text="🌫️ Размытие",
        callback_data="filter_blur"
    )

    button_invert_image = telebot.types.InlineKeyboardButton(
        text="🌀 Инверсия",
        callback_data="filter_invert"
    )

    keyboard.add(button_gray_filter, button_binarization_filter, button_pixelization_filter,
                 button_custom_filter, button_blur_image, button_invert_image)
    return keyboard


# ============================= БЛОК ФУНКЦИЙ С ФИЛЬТРАМИ =============================
def apply_grayscale_filter(source_path, result_path):
    image = Image.open(source_path).convert('RGB')

    width, height = image.width, image.height
    for i in range(width):
        for j in range(height):
            r, g, b = image.getpixel((i, j))
            gray = (r + g + b) // 3 # среднее значение пикселей
            image.putpixel((i, j), (gray, gray, gray))

        image.save(result_path)


def apply_binarization(source_path, result_path):
    image = Image.open(source_path).convert("RGB")
    pixels = image.load()  # загрузит пиксели (это матрицы)
    width, height = image.size  # взять от картинки размер длина и ширина

    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            border = 127
            brightness =(r + g + b) // 3

            if brightness > border:
                result = 240
            else:
                result = 10
            pixels[x, y] = (result, result, result)

    image.save(result_path)

def pixelate_image(source_path, result_path, block_size=10):
    image = Image.open(source_path).convert("RGB")
    pixels = image.load()  # загрузит пиксели (это матрицы)
    width, height = image.size  # взять от картинки размер длина и ширина

    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            # Определяем границы текущего блока
            block_x_end = min(x + block_size, width)
            block_y_end = min(y + block_size, height)

            # Собираем все пиксели в блоке
            block_pixels = []
            for block_y in range(y, block_y_end):
                for block_x in range(x, block_x_end):
                    block_pixels.append(pixels[block_x, block_y])

            # Вычисляем средний цвет для блока
            if block_pixels:
                avg_color = tuple(
                    int(sum(c[i] for c in block_pixels) / len(block_pixels))
                    for i in range(3)
                )

                # Закрашиваем весь блок средним цветом
                for block_y in range(y, block_y_end):
                    for block_x in range(x, block_x_end):
                        pixels[block_x, block_y] = avg_color

    image.save(result_path)


def custom_filter(source_path, result_path):
    image = Image.open(source_path).convert("RGB")
    pixels = image.load()  # загрузит пиксели (это матрицы)
    width, height = image.size  # взять от картинки размер длина и ширина

    border = height // 2
    middle_row_pixels = []
    for x in range(width):
        middle_row_pixels.append(pixels[x, border])

    for x in range(border + 1, height):
        for j in range(width):
            pixels[j,x] = middle_row_pixels[j]


    image.save(result_path)


def blur_image(source_path, result_path):
    image = Image.open(source_path).convert("RGB")

    blurred = image.filter(ImageFilter.GaussianBlur(radius=7))
    blurred.save(result_path)


def invert_image(source_path, result_path):
    image = Image.open(source_path).convert("RGB")
    pixels = image.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # Инвертируем каждый цветовой канал
            pixels[x, y] = (255 - r, 255 - g, 255 - b)

    image.save(result_path)


def arrange_folders():
    if not os.path.exists("origins"):
        os.mkdir("origins")

    if not os.path.exists("results"):
        os.mkdir("results")


# ========================= БЛОК ФУНКЦИЙ ДЛЯ ИГРЫ =================================
def determine_winner(player_choice, bot_choice):
    # Правила, что побеждает
    rules = {
        "stone": "scissors",  # камень бьет ножницы
        "scissors": "paper",  # ножницы бьют бумагу
        "paper": "stone"  # бумага бьет камень
    }

    if player_choice == bot_choice:
        return "draw"
    elif rules[player_choice] == bot_choice:
        return "win"
    else:
        return "lose"


def get_emoji_and_name(player_choice):
    choices = {
        "stone": ("✊", "Камень"),
        "paper": ("✋", "Бумага"),
        "scissors": ("✌️", "Ножницы")
    }
    return choices.get(player_choice, ("❓", "Неизвестно"))


# ========================= БЛОК ДОСТУПНЫХ КОМАНД БОТА =================================
@bot.message_handler(commands=['start'])
def handle_start(message):
    response_text = ("✨ 𝓦𝓮𝓵𝓬𝓸𝓂𝓮 ✨\n"
        "Я бот для контрольной работы!\n 📌Мои команды: \n"
        "/start - Запуск бота\n"
        "/help - Помощь в навигации по боту\n"
        "/coin - Подброс монетки\n"
        "/cube - Подброс кубика\n"
        "/ask - Подумай о чем угодно и нажми эту кнопку, если не можешь определиться с выбором\n"
        "/time - Нажми, чтобы узнать текущую дату и время\n"


        "📸 У меня есть Фотофильтры (отправь фото и затем выбери нужный фильтр!):\n"
        "\n"
        "- Черно-белый - преобразует фото в оттенки серого\n"
        "- Бинаризация - делает изображение только черно-белым (без оттенков)\n"
        "- Пикселизация - создает эффект мозаики\n"
        "- Растяжение вниз - растягивает среднюю строку по вертикали\n"
        "- Размытие - делает изображение размытым\n"
        "- Инверсия - создает негатив (обратные цвета)\n")

    user = message.from_user # инфа о юзере, который отправил сообщение
    username = user.username # username в телеграме
    user_id = user.id # идентификатор пользователя (длинный айдишник)

    db_telegrambot.register_user(conn, username, user_id) # регистрируем юзера

    log_user_action( # сохраняем логи всех действий
        user_id, # айдишник юзера
        "/start", # какую команду выбрал
        "Нажатие", # какое действие произвел
        f"Ответ: {response_text}" # ответ бота
    )

    bot.send_message(
        message.chat.id,
        response_text,
        reply_markup = create_menu()
    )


@bot.message_handler(commands=['help'])
def handle_help(message):
    response_text = ("Чтобы мы начали работать, просто выбери, что тебе нужно сейчас:\n"
        "🛠 База: Узнать точное /time или перезапустить систему через /start.\n"
        "🎲 Удача: Испытай судьбу! Брось /coin или /cube, а можешь задать вопрос судьбе в /ask.\n"
        "🎨 Креатив: Пришли мне любое фото, и я превращу его в шедевр (Черно-белое, Пиксели, Инверсия и др.).\n"
        "Можешь использовать кнопки в меню 👇")

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "/help",
        "Нажатие",
        f"Ответ: {response_text}"
    )

    bot.send_message(
        message.chat.id,
        response_text,
        reply_markup = create_menu()
    )


@bot.message_handler(commands=['coin'])
def imitate_coinflip(message):
    answer = randint(0, 2)
    if answer == 0:
        result = "🦅 Орел"
    elif answer == 1:
        result = "💸 Решка"
    else:
        result = "⚡ На ребро!"

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "/coin",
        "Нажатие",
        f"Ответ: {result}"
    )

    bot.send_message(
        message.chat.id,
        result,
        reply_markup=create_menu()
    )


@bot.message_handler(commands=['cube'])
def imitate_cube(message):
    answer = randint(1, 6)

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "/cube",
        "Нажатие",
        f"Ответ: 🎲 Выпало: {answer}"
    )

    bot.send_message(
    message.chat.id,
    f"🎲 Выпало: {answer}",
    reply_markup = create_menu()
    )


@bot.message_handler(commands=['ask'])
def help_choice(message):
    answers = [
        "Да",
        "Точно да",
        "Нет",
        "Однозначно нет",
        "Не рискуй",
        "Возможно, но не факт!"]

    random_answer = choice(answers)

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "/ask",
        "Нажатие",
        f"Ответ: {random_answer}"
    )

    bot.send_message(
        message.chat.id,
        random_answer,
        reply_markup=create_menu()
    )


@bot.message_handler(commands=['time'])
def send_time(message):
    msk_tz = pytz.timezone('Europe/Moscow')
    now = datetime.datetime.now(msk_tz)

    response = (
        f"🕐 Текущее время: {now.strftime('%H:%M:%S')}\n"
        f"📅 Дата: {now.strftime('%d %B %Y года')}\n"
        f"📆 День недели: {now.strftime('%A')}\n"
        f"🌍 Часовой пояс: МСК (UTC+3)"
    )

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "/time",
        "Нажатие",
        f"Ответ: {response}"
    )

    bot.send_message(
        message.chat.id,
        response,
        reply_markup = create_menu()
    )

# ============================ ОБРАБОТЧИКИ ДЛЯ КНОПОЧНЫХ ФУНКЦИЙ ==============================
@bot.message_handler(func=lambda message: message.text == BUTTON_FUTURE)
def handle_button_future(message):
    predictions = [
        "🔮 Завтра тебя ждет нечто удивительное!",
        "🌙 Сегодня вечером будет удачным",
        "☀️ На следующей неделе случится что-то хорошее",
        "💫 Остерегайся неожиданных расходов в пятницу",
        "🍀 Удача улыбнется тебе после обеда",
        "🌠 Падающая звезда ждет твой запрос",
        "💵 Неожиданная прибыль на горизонте",
        "⭐ В ближайшее время получишь приятное сообщение",
        "🪐 Космос посылает тебе лучи добра",
        "💸 Трать с умом, но себя не ограничивай",
        "🌌 Вселенная сегодня за тебя",
        "🌀 Энергия переполняет",
        "⚡ Будь как молния - быстрым и ярким",
        "🔥 Ты сегодня в огне (в хорошем смысле)",
        "💧 Будь как вода - текучим и спокойным",
        "🎲 Сегодня твой счастливый день",
        "🎰 Джекпот не за горами",
        "🌸 Эта неделя будет особенно продуктивной",
        "🎯 Цель будет достигнута",
        "📝 Экзамен сдашь отлично",
        "💰 Найдешь денежку (или хотя бы копеечку)",
        "💻 Компьютер сегодня не будет зависать",
        "🚴 Велопрогулка ждет тебя",
        "🍣 Роллы сами захотят к тебе в рот",
        "🍫 Сладкое сегодня не повредит фигуре",
        "💎 Инвестируй в себя - это окупится",
        "🤔 Сегодня ты вспомнишь что-то важное",
    ]

    prediction = choice(predictions)

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "🔮 Предсказание",
        "Нажатие",
        f"Ответ: {prediction}"
    )

    bot.send_message(
        message.chat.id,
        prediction,
        reply_markup=create_menu()
    )


@bot.message_handler(func=lambda message: message.text == BUTTON_FACT)
def handle_button_fact(message):
    facts = [
        "⚡ Нервный импульс от мозга движется со скоростью 274 км/ч",
        "🪵 Дятел может обкрутить голову высунутым языком",
        "🦒 У жирафа и человека одинаковое количество позвонков",
        "👁️ Глаз страуса размером как и его мозг",
        "✋ 11% человек на земле левши",
        "👅 Отпечаток языка уникален у каждого человека, как и отпечатки пальцев",
        "🇨🇦 Канада имеет больше озер, чем все остальные страны вместе взятые",
        "🖱️ Первая компьютерная мышь была сделана из дерева",
        "🍅 Помидор - это ягода, а не овощ",
        "🌋 Самый большой вулкан - Мауна-Лоа на Гавайях",
        "☁️ Облака могут весить больше миллиона килограмм",
        "🍫 Белый шоколад технически не является шоколадом",
        "🦁 Лев может спариваться до 50 раз в день",
        "💡 Лампочку изобрел не Эдисон, а Лодыгин (до Эдисона)",
        "🔢 0 не является ни положительным, ни отрицательным числом",
        "🐝 Пчелы узнают человеческие лица",
        "🍌 Бананы радиоактивны из-за содержания калия-40",
    ]

    fact = choice(facts)

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "🎓 Факт",
        "Нажатие",
        f"Ответ: {fact}"
    )

    bot.send_message(
        message.chat.id,
        fact,
        reply_markup=create_menu()
    )


@bot.message_handler(func=lambda message: message.text == "🗑️ Скрыть меню")
def hide_menu(message):
    response_text = "😎 Меню скрыто. Нажмите /start чтобы вернуть меню."
    # Удаляем клавиатуру
    markup = telebot.types.ReplyKeyboardRemove()

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "️ Скрыть меню",
        "Нажатие",
        f"Ответ: {response_text}"
    )

    bot.send_message(
        message.chat.id,
        response_text,
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == BUTTON_GAME_RPS)
def handle_game_rps(message):
    response_text = "Игра камень-ножницы бумага! Выбери свой ход!"
    chat_id = message.chat.id
    if chat_id not in RPS_STATS:
        RPS_STATS[chat_id] = {"wins": 0, "losses": 0, "draws": 0, "total": 0}

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    log_user_action(
        user_id,
        "️🤜✌️✋ Камень-ножницы-бумага",
        "Нажатие",
        f"Ответ: {response_text}"
    )

    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode="Markdown",
        reply_markup=create_game_keyboard()
    )


@bot.message_handler(content_types=['text', ])
def handle_any_text(message):
    text = message.text.strip().lower()
    chat_id = message.chat.id

    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    if any(phrase in text for phrase in ["как дела", "как ты", "как настроение", "как жизнь", "how are you"]):
        responses = [
            "😊 У меня всё отлично! Спасибо, что спросил! А у тебя?",
            "🌟 Отлично! Спасибо! Расскажи, как у тебя?",
            "💫 У меня всё замечательно! А у тебя как?"
        ]

        answer = choice(responses)

        log_user_action(
            user_id,
            "️Текстовое сообщение",
            f"Отправлено сообщение: \"{text}\"",
            f"Ответ: {answer}"
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=create_menu()
        )
        LAST_BOT_QUESTION[chat_id] = True
        return

    greetings = [
        "привет", "здравствуй", "здравствуйте", "hello", "hi", "hey",
        "добрый день", "дд", "доброе утро", "добрый вечер", "салют", "хай", "здарова"
    ]

    if any(greet in text for greet in greetings):
        responses = [
            "👋 Привет! Как дела?",
            "😊 Здравствуй! Рад тебя видеть! Как настроение?",
            "🤗 О, привет! Давно не виделись!",
            "💫 Здравствуй, друг! Нажми /start для запуска или /help, если нужна помощь."
        ]

        answer = choice(responses)

        log_user_action(
            user_id,
            "️Текстовое сообщение",
            f"Отправлено сообщение: \"{text}\"",
            f"Ответ: {answer}"
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=create_menu()
        )
        LAST_BOT_QUESTION[chat_id] = True
        return

    goodbyes = [
        "пока", "до свидания", "до встречи", "ухожу", "выйти",
        "бб", "прощай", "bye", "goodbye", "до скорого", "аривидерчи",
        "всего хорошего", "всего доброго", "покеда", "чао",
        "удачи", "счастливо", "бывай", "до завтра"
    ]

    if any(bye in text for bye in goodbyes):
        responses = [
            "👋 Пока! Возвращайся скорее!",
            "🎈 Счастливого пути! Заходи ещё!",
        ]

        answer = choice(responses)

        log_user_action(
            user_id,
            "️Текстовое сообщение",
            f"Отправлено сообщение: \"{text}\"",
            f"Ответ: {answer}"
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=create_menu()
        )
        LAST_BOT_QUESTION.pop(chat_id, None)
        return

    if LAST_BOT_QUESTION.get(chat_id):
        if any(word in text for word in ["отлично", "хорошо", "нормально", "супер", "класс"]):
            responses = [
                "🎉 Здорово! У меня тоже всё отлично!",
                "🌟 Класс! Что нового?",
            ]
            chosen_response = choice(responses)

            log_user_action(
                user_id,
                "️Текстовое сообщение",
                f"Отправлено сообщение: \"{text}\"",
                f"Ответ: {chosen_response}"
            )

            bot.send_message(chat_id, chosen_response, reply_markup=create_menu())

            if "Что нового?" in chosen_response:
                LAST_BOT_QUESTION[chat_id] = True
            else:
                LAST_BOT_QUESTION.pop(chat_id, None)
            return

        elif any(word in text for word in ["ничего", "нечего", "так себе", "всё норм", "все норм", "нормально", "неплохо"]):
            responses = [
                "😊 Понятно! Если будет скучно — поиграем!",
                "🎮 Может, сыграем во что-нибудь? Нажми кнопку ниже, чтобы начать."
            ]

            answer = choice(responses)

            log_user_action(
                user_id,
                "️Текстовое сообщение",
                f"Отправлено сообщение: \"{text}\"",
                f"Ответ: {answer}"
            )

            keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                telebot.types.InlineKeyboardButton("🎮 Играть", callback_data="offer_game"),
            )
            bot.send_message(
                chat_id,
                answer,
                reply_markup=keyboard
            )
            LAST_BOT_QUESTION.pop(chat_id, None)
            return

        elif any(word in text for word in ["плохо", "так себе", "не очень", "грустно"]):
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                telebot.types.InlineKeyboardButton("🎮 Играть", callback_data="offer_game"),
            )

            answer = "😔 Мне жаль. Хочешь, поиграем? Если да, нажми кнопку ниже."
            # Сохраняем информацию о кнопке в ответе
            bot_response_with_button = f"{answer} [Кнопка: 🎮 Играть → callback_data: offer_game]"

            log_user_action(
                user_id,
                "️Текстовое сообщение",
                f"Отправлено сообщение: \"{text}\"",
                f"Ответ: {bot_response_with_button}"
            )

            bot.send_message(
                chat_id,
                answer,
                reply_markup=keyboard
            )
            LAST_BOT_QUESTION.pop(chat_id, None)
            return

        else:
            responses = [
            f"😊 Понятно!",
            ]

            chosen_response = choice(responses)

            log_user_action(
                user_id,
                "️Текстовое сообщение",
                f"Отправлено сообщение: \"{text}\"",
                f"Ответ: {chosen_response}"
            )

            bot.send_message(chat_id, chosen_response, reply_markup=create_menu())
            LAST_BOT_QUESTION.pop(chat_id, None)
            return

    if any(word in text for word in ["не хочу", "не хочу играть", "неа", "нет(", "нет"]):
        responses = [
            "😔 Понимаю. Если передумаешь — я всегда здесь!",
            "💫 Как скажешь. Обращайся, если что-то понадобится!",
        ]

        answer = choice(responses)

        log_user_action(
            user_id,
            "️Текстовое сообщение",
            f"Отправлено сообщение: \"{text}\"",
            f"Ответ: {answer}"
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=create_menu()
        )
        LAST_BOT_QUESTION.pop(chat_id, None)
        return

    if any(word in text for word in ["да", "ага", "конечно", "хочу", "давай", "давай поиграем", "играть"]):
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            telebot.types.InlineKeyboardButton("🎮 Играть", callback_data="offer_game"),
        )

        answer = "🎉 Отлично! Нажми кнопку, чтобы начать!"

        # Сохраняем информацию о кнопке в ответе
        bot_response_with_button = f"{answer} [Кнопка: 🎮 Играть → callback_data: offer_game]"

        log_user_action(
            user_id,
            "️Текстовое сообщение",
            f"Отправлено сообщение: \"{text}\"",
            f"Ответ: {bot_response_with_button}"
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=keyboard
        )
        return

    if message.text and message.text.startswith('/'):
        return

    if message.text in [BUTTON_FACT, BUTTON_FUTURE, BUTTON_GAME_RPS]:
        return

    response_text = ("🤔 *Я тебя не понял*\n\n"
        "Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Помощь в навигации по боту\n"
        "/coin - Подброс монетки\n"
        "/cube - Подброс кубика\n"
        "/ask - Подумай о чем угодно и нажми эту кнопку, если не можешь определиться с выбором\n"
        "/time - Нажми, чтобы узнать текущую дату и время\n\n"
        "Или используй кнопки в меню 👇")

    log_user_action(
        user_id,
        "Текстовое сообщение",
        "Отправлено нераспознанное ботом сообщение: \"{text}\" ",
        f"Ответ: {response_text}"
    )

    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown',
        reply_markup=create_menu()
    )


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    arrange_folders()

    chat_id = message.chat.id
    user = message.from_user
    username = user.username
    user_id = user.id

    db_telegrambot.register_user(conn, username, user_id)

    photo_info = message.photo[len(message.photo) - 1]

    file_info = bot.get_file(photo_info.file_id)
    # в оперативе
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = f"origins/{chat_id}_source.jpg"
    # на диске
    with open(image_path, "wb") as image_file:
        image_file.write(downloaded_file)

    USER_CURRENT_IMAGE_PATH[chat_id] = image_path

    answer = "Картинка получена, выберите фильтр"

    log_user_action(
        user_id,
        "Отправка изображения",
        f"Отправлено изображение: {image_path}",
        f"Ответ: {answer}"
    )
    bot.send_message(
        chat_id,
        text=answer,
        reply_markup=create_filters_keyboard()
    )

# ============================ ОБРАБОТЧИК ДЛЯ ФИЛЬТРА ==============================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    callback_data = call.data

    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    db_telegrambot.register_user(conn, username, user_id)

    if callback_data.startswith("filter"):
        if chat_id not in USER_CURRENT_IMAGE_PATH:
            bot.answer_callback_query(call.id, "Сначала отправьте картинку")

            log_user_action(
                user_id,
                f"Попытка применить фильтр {callback_data} без отправленного изображения",
                "Нажатие",
                "Ответ: \"Сначала отправьте картинку\""
            )
            return

        source_path = USER_CURRENT_IMAGE_PATH[chat_id]
        result_path = f"results/{chat_id}.jpg"

        filter_name = "" # определяем название фильтра для логирования
        if callback_data == "filter_grayscale":
            apply_grayscale_filter(source_path, result_path)
            filter_name = "Черно-белый фильтр"
        elif callback_data == "filter_binarization":
            apply_binarization(source_path, result_path)
            filter_name = "Бинаризация"
        elif callback_data == "filter_pixelization":
            pixelate_image(source_path, result_path)
            filter_name = "Пикселизация"
        elif callback_data == "filter_custom":
            custom_filter(source_path, result_path)
            filter_name = "Растяжение вниз"
        elif callback_data == "filter_blur":
            blur_image(source_path, result_path)
            filter_name = "Размытие"
        elif callback_data == "filter_invert":
            invert_image(source_path, result_path)
            filter_name = "Инверсия"

        answer = "✅ Готово!"

        log_user_action(
            user_id,
            "Применение фильтра после загрузки картинки",
            f"Применен фильтр {filter_name} к картинке {source_path}",
            f"Ответ: {answer}"
        )

        with open(result_path, "rb") as image_file:
            bot.send_photo(
                chat_id,
                image_file,
                caption=answer,
                reply_markup=create_menu()
            )

        USER_CURRENT_IMAGE_PATH.pop(chat_id)
        bot.answer_callback_query(call.id, "Фильтр применен!")
        return


# ============================ ОБРАБОТЧИК ДЛЯ ИГРЫ ==============================
    if callback_data == "offer_game":
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            telebot.types.InlineKeyboardButton("🤜✌️✋ Камень-ножницы-бумага", callback_data="start_rps")
        )

        bot.edit_message_text(
            "🎮 Начинаем!",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if callback_data == "start_rps":

        log_user_action(
            user_id,
            "Начало игры",
            "Пользователь нажал на кнопку 🤜✌️✋ Камень-ножницы-бумага",
            "Предложен выбор игры: Камень-ножницы-бумага"
        )

        if chat_id not in RPS_STATS:
            RPS_STATS[chat_id] = {"wins": 0, "losses": 0, "draws": 0, "total": 0}
        bot.edit_message_text(
            "🎮 **Камень, ножницы, бумага**\n\nВыбери свой ход:",
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=create_game_keyboard()
        )
        bot.answer_callback_query(call.id)
        return

    if callback_data == "rps_stats":
        stats = RPS_STATS.get(chat_id, {"wins": 0, "losses": 0, "draws": 0, "total": 0})
        total = stats["total"]

        log_user_action(
            user_id,
            "Пользователь выбрал просмотр статистики игр",
            f"Всего игр: {total}, Побед: {stats['wins']}, "
            f"Поражений: {stats['losses']}, Ничьих: {stats['draws']}",
            "Ответ: Показана статистика игр"
        )

        if total == 0:
            stats_text = "📊 *Твоя статистика:*\n"
            stats_text += "Ты еще не сыграл ни одной игры!\n"
            stats_text += "Нажми на кнопку с ходом, чтобы начать."
        else:
            win_rate = (stats["wins"] / total) * 100
            title = "📊 *Твоя статистика:*"
            stats_text = f"{title}\n"
            stats_text += f"  ──── ୨୧ ────\n"
            stats_text += f"𒆙 Всего игр: *{total}*\n"
            stats_text += f"✅ Побед: *{stats['wins']}*\n"
            stats_text += f"❌ Поражений: *{stats['losses']}*\n"
            stats_text += f"⚔️ Ничьих: *{stats['draws']}*\n"
            stats_text += f"📈 Процент побед: *{win_rate:.1f}%*\n"

        bot.edit_message_text(
            stats_text,
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=create_game_keyboard()
        )
        bot.answer_callback_query(call.id)
        return

    if callback_data == "rps_reset":
        if chat_id in RPS_STATS:
            old_stats = RPS_STATS.get(chat_id, {"wins": 0, "losses": 0, "draws": 0, "total": 0})
            message = "✅ Статистика сброшена!"
        else:
            message = "📊 Статистика и так пуста."

        log_user_action(
            user_id,
            "Пользователь сбросил статистику игр",
            f"Было: Всего игр: {old_stats['total']}, "
            f"Побед: {old_stats['wins']}, Поражений: {old_stats['losses']}, Ничьих: {old_stats['draws']}",
            f"Ответ: {message}"
        )

        bot.answer_callback_query(call.id, message)
        bot.delete_message(chat_id, call.message.message_id)

        bot.send_message(
            chat_id,
            "**Камень, ножницы, бумага**\n\nСтатистика сброшена. Выбери ход:",
            parse_mode="Markdown",
            reply_markup=create_game_keyboard()
        )
        return

    if callback_data not in ["rps_stone", "rps_paper", "rps_scissors"]:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return

    player_map = {
        "rps_stone": "stone",
        "rps_paper": "paper",
        "rps_scissors": "scissors"
    }
    player_choice = player_map[callback_data]

    # Случайный выбор бота
    bot_choice = choice(["stone", "paper", "scissors"])

    # Получаем эмодзи и названия
    player_emoji, player_name = get_emoji_and_name(player_choice)
    bot_emoji, bot_name = get_emoji_and_name(bot_choice)

    # Определяем победителя
    result = determine_winner(player_choice, bot_choice)

    # Обновляем статистику
    if chat_id not in RPS_STATS:
        RPS_STATS[chat_id] = {"wins": 0, "losses": 0, "draws": 0, "total": 0}

    RPS_STATS[chat_id]["total"] += 1

    # Формируем сообщение о результате
    result_message = f"𒆙 *Камень, ножницы, бумага*\n\n"
    result_message += f"👤 Твой ход: {player_emoji} {player_name}\n"
    result_message += f"✌︎㋡ Мой ход: {bot_emoji} {bot_name}\n\n"

    if result == "win":
        result_message += "🎉 *Ты победил!* 🎉"
        RPS_STATS[chat_id]["wins"] += 1
    elif result == "lose":
        result_message += "⚡️ *Я победил!* Попробуй еще раз!"
        RPS_STATS[chat_id]["losses"] += 1
    else:
        result_message += "⚔️ *Ничья!* Давай еще раз?"
        RPS_STATS[chat_id]["draws"] += 1
    log_user_action(
        user_id,
        "Игра",
        f"Пользователь выбрал: {player_name}, Бот выбрал: {bot_name}",
        f"Ответ: {result_message}"
    )

    bot.edit_message_text(
        result_message,
        chat_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=create_game_keyboard()
    )

    bot.answer_callback_query(call.id)


bot.infinity_polling()