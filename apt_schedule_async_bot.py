import asyncio
import calendar
import datetime
import time
import pendulum
import requests
import telebot
from pyppeteer import launch
from telebot.async_telebot import AsyncTeleBot
import sqlite3
from bs4 import BeautifulSoup
from telebot import types, asyncio_filters
from telebot.asyncio_handler_backends import State, StatesGroup
import configure

global GROUP_ID
CHAT_BY_DATETIME = {}
GROUP_ID = {
    'АВ221': 957,
    'АМ221': 950,
    'АМ223': 950,
    'АМ222': 949,
    'БУР221': 961,
    'БУР222': 962,
    'БУХ221': 947,
    'БУХ222': 947,
    'ГФ221': 960,
    'ИС221': 953,
    'СТ221': 955,
    'СТ222': 956,
    'СТ223': 954,
    'ИС222': 952,
    'ИС223': 971,
    'МЕХ221': 959,
    'АВ211': 827,
    'АМ211': 828,
    'АМ212': 829,
    'БУР211': 830,
    'БУР212': 831,
    'БУХ211': 832,
    'ГФ211': 833,
    'ИС211': 834,
    'ИС212': 835,
    'ИС213': 727,
    'МЕХ211': 836,
    'СА211': 846,
    'СА212': 846,
    'СМ211': 837,
    'СТ211': 838,
    'СТ212': 839,
    'СТ213': 840,
    'ЭКС211': 841,
    'ЭКС213': 841,
    'ЭКС212': 842,
    'ЭЛ211': 844,
    'ЭЛ212': 844,
    'ЭЛ1212': 845,
    'АВ201': 702,
    'АВ202': 702,
    'АД201': 698,
    'АМ201': 695,
    'АМ202': 694,
    'БУР201': 687,
    'БУР202': 688,
    'БУХ201': 692,
    'ГФ201': 689,
    'ИС201': 697,
    'ИС202': 696,
    'ИС203': 697,
    'МЕХ201': 690,
    'СМ201': 693,
    'СТ201': 701,
    'СТ202': 700,
    'СТ203': 699,
    'ЭКС201': 684,
    'ЭКС204': 684,
    'ЭКС202': 685,
    'ЭКС1203': 704,
    'ЭЛ201': 691,
    'ЭЛ202': 691,
    'ЭЛ1202': 703,
    'АВ191': 620,
    'АВ192': 620,
    'АД191': 548,
    'АМ191': 628,
    'АМ192': 629,
    'БУР191': 622,
    'БУР192': 625,
    'БУР193': 625,
    'ГФ191': 626,
    'ИС191': 547,
    'ИС192': 619,
    'МЕХ191': 549,
    'СМ191': 627,
    'CТ194': 544,
    'CТ191': 544,
    'СТ192': 617,
    'СТ193': 618,
    'ЭКС191': 621,
    'ЭКС192': 624,
    'ЭКС193': 631,
    'ЭКС195': 631,
    'ЭЛ191': 546,
    'ЭЛ192': 546,
}
HELP_TEXT = """Привет, это бот в котором ты можешь увидеть расписание своей группы в АПТ.
Сначала нужно указать свою группу, нажав кнопку "Изменить группу📎" и ввести группу без лишних букв и дефисов, например ИС211, МЕХ201.
Расписание на сегодня/завтра🗓 выводит расписание в виде текста.
Расписание на сегодня/завтра📱 выводит расписание в виде картинки.
Кнопка "Расписание на понедельник📅" работает только в субботу и воскресенье и выводит расписание на понедельник в виде текста, если расписание вышло.
Нажав кнопку "Изменить группу📎" еще раз, ты можешь поменять свою группу.
Нажав кнопку "Профиль📌" ты можешь увидеть свой id и группу.
Чтобы увидеть это сообщение еще раз, нажми кнопку "Помощь❓"
Может понадобиться несколько секунд для получения расписания!"""

bot = AsyncTeleBot(configure.config["token"], parse_mode='HTML')

conn = sqlite3.connect('db_main.db', check_same_thread=False)
cursor = conn.cursor()

bot.add_custom_filter(telebot.asyncio_filters.TextMatchFilter())
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.ChatFilter())


class UserState(StatesGroup):
    group = State()


@bot.message_handler(commands=["start"])
async def start(message, res=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button1 = types.KeyboardButton("Изменить группу📎")
    button2 = types.KeyboardButton("Помощь❓")

    markup.add(button1, button2)

    async def db_table_val(user_id, nickname, username):
        register_user = "INSERT OR IGNORE INTO test (user_id, nickname, username) VALUES (?, ?, ?)"
        columns = (user_id, nickname, username)
        cursor.execute(register_user, columns)
        conn.commit()

    us_id = message.from_user.id
    us_name = message.from_user.first_name
    username = message.from_user.username

    await db_table_val(user_id=us_id, nickname=us_name, username=username)
    await bot.reply_to(message, HELP_TEXT, reply_markup=markup)


# Форматирование спарсенного расписания
async def format_result(result):
    result = result.split("Консультации преподавателей")[0]
    result = result.split("График учебного процесса")[0]
    result = result.replace("\n\n\n\n\n\n", " ")
    result = result.replace("\n\n\n\n", "\n")
    result = result.replace("\n\n\n", "\n")
    result = result.replace("\n\n", "\n")
    result = result.replace("1 п/гр.", "<b><i>1 подгруппа</i></b>")
    result = result.replace("2 п/гр.", "<b><i>2 подгруппа\n</i></b>")
    result = result.replace("0730 - 0850", "\n1️⃣     <b>7:30 - 8:50</b>\n")
    result = result.replace("0855 - 1015", "\n2️⃣     <b>8:55 - 10:15</b>\n\n")
    result = result.replace("1040 - 1200", "\n3️⃣     <b>10:40 - 12:00</b>\n\n")
    result = result.replace("1210 - 1330", "\n4️⃣     <b>12:10 - 13:30</b>\n\n")
    result = result.replace("1340 - 1500", "\n5️⃣     <b>13:40 - 15:00</b>\n\n")
    result = result.replace("1520 - 1640", "\n6️⃣     <b>15:20 - 16:40</b>\n\n")
    result = result.replace("1645 - 1805", "\n7️⃣     <b>16:45 - 18:05</b>\n\n")
    result = result.replace("1810 - 1925", "\n8️⃣     <b>18:10 - 19:25</b>\n\n")
    result = result.replace("0730 - 0840", "\n1️     <b>7:30 - 8:40</b>\n")
    result = result.replace("0845 - 0955", "\n2️⃣     <b>8:45 - 9:55</b>\n")
    result = result.replace("1000 - 1110", "\n3️⃣     <b>10:00 - 11:10</b>\n")
    result = result.replace("1210 - 1330", "\n4️⃣     <b>12:10 - 13:30</b>\n")
    result = result.replace("1340 - 1500", "\n5️⃣     <b>13:40 - 15:00</b>\n")
    result = result.replace("ауд.", "<b>Аудитория</b>: ")
    result = result.replace("преп.", "<b>Преподаватель</b>: ")
    if "Расписание занятий групп" in result:
        result = result.split("года")[1]
    if "большая перемена 25 минут" in result:
        result = result.replace("большая перемена 25 минут", "")
    if "большая перемена 20 минут" in result:
        result = result.replace("большая перемена 20 минут", "")
    if "пара" in result:
        result = result.replace("I пара", "")
        result = result.replace("II пара", "")
        result = result.replace("III пара", "")
        result = result.replace("IV пара", "")
        result = result.replace("V пара", "")
        result = result.replace("VI пара", "")
        result = result.replace("V", "")
        result = result.replace("I", "")
    result = result.replace("\n\n\n\n\n\n", "\n")
    result = result.replace("\n\n\n\n", "\n")
    result = result.replace("\n\n\n", "\n")
    result = result.replace("\n\n", "\n")
    return result


@bot.message_handler(text=['Изменить группу📎'])
async def request_group(message):
    await bot.set_state(message.from_user.id, UserState.group, message.chat.id)
    await bot.send_message(message.chat.id, 'Введите группу (без лишних букв и дефисов, например ис211, экс202:')


@bot.message_handler(state=UserState.group)
async def update_group(message):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['group'] = message.text
        GROUP = data['group'].upper()
    if GROUP not in GROUP_ID:
        await bot.reply_to(message, f"Группа введена неверно, введите "
                                    f"группу в правильном формате!\nВы ввели: {GROUP}")
        await bot.set_state(message.from_user.id, UserState.group, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите группу (без лишних букв и символов, например ис211, экс202):')
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['group'] = message.text.upper()
        return
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        button1 = types.KeyboardButton("Расписание на сегодня 🗓")
        button2 = types.KeyboardButton("Расписание на завтра 🗓")
        button3 = types.KeyboardButton("Расписание на сегодня 📱")
        button4 = types.KeyboardButton("Расписание на завтра 📱")
        button5 = types.KeyboardButton("Изменить группу📎")
        button6 = types.KeyboardButton("Расписание на понедельник📅")
        button7 = types.KeyboardButton("Профиль📌")
        button8 = types.KeyboardButton("Помощь❓")

        markup.add(button1, button2)
        markup.add(button3, button4)
        markup.add(button5, button6)
        markup.add(button7, button8)

        await bot.reply_to(message, f"Ваша группа: {GROUP}", reply_markup=markup)

        async def update_group_val(user_group: str):
            us_id = message.from_user.id
            sqlite_update_query = 'UPDATE test SET user_group = ? WHERE user_id = ?'
            column_values = (user_group, us_id)
            cursor.execute(sqlite_update_query, column_values)
            conn.commit()

        MY_GROUP = GROUP_ID[GROUP]
        await update_group_val(user_group=MY_GROUP)
        await bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(text=['Расписание на сегодня 🗓'])
async def get_text_today(message):
    need_seconds = 5
    current_time = datetime.datetime.now()
    last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
    if not last_datetime:
        CHAT_BY_DATETIME[message.chat.id] = current_time
    else:
        delta_seconds = (current_time - last_datetime).total_seconds()
        seconds_left = int(need_seconds - delta_seconds)

        if seconds_left > 0:
            await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
        else:
            CHAT_BY_DATETIME[message.chat.id] = current_time

            async def get_result_today(user_id: int):
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()

                if group:
                    my_group = group[0]

                    today = pendulum.today('Europe/Moscow').format('YYYY-MM-DD')
                    response_today = requests.get(f"https://almetpt.ru/2020/site/schedule/group/{my_group}/{today}")
                    soup = BeautifulSoup(response_today.text, "lxml")
                    schedule = soup.find("div", class_="container")

                    if 'года не опубликовано' in schedule.text:
                        return "Расписания на сегодня нет."
                    else:
                        for item in schedule:
                            if item == "":
                                item.replace("", "1")

                        result = f'{schedule.text}'
                        return await format_result(result)

            await bot.reply_to(message, await get_result_today(message.from_user.id))


@bot.message_handler(text=['Расписание на завтра 🗓'])
async def get_text_tomorrow(message):
    need_seconds = 5
    current_time = datetime.datetime.now()
    last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
    if not last_datetime:
        CHAT_BY_DATETIME[message.chat.id] = current_time
    else:
        delta_seconds = (current_time - last_datetime).total_seconds()
        seconds_left = int(need_seconds - delta_seconds)

        if seconds_left > 0:
            await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
        else:
            CHAT_BY_DATETIME[message.chat.id] = current_time

            async def get_result_tomorrow(user_id: int):
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()

                if group:
                    my_group = group[0]

                    tomorrow = pendulum.tomorrow('Europe/Moscow').format('YYYY-MM-DD')
                    response_check_tomorrow = requests.get(
                        f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{tomorrow}')
                    soup = BeautifulSoup(response_check_tomorrow.text, 'lxml')
                    schedule = soup.find("div", class_="container")

                    if 'года не опубликовано' in schedule.text:
                        return "Расписание на завтра еще не вышло!"
                    else:
                        for item in schedule:
                            if item == "":
                                item.replace("", "1")
                        result = f'{schedule.text}'
                        return await format_result(result)

            await bot.reply_to(message, await get_result_tomorrow(message.from_user.id))


@bot.message_handler(text=['Расписание на сегодня 📱'])
async def get_screen_today(message):
    need_seconds = 8
    current_time = datetime.datetime.now()
    last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
    if not last_datetime:
        CHAT_BY_DATETIME[message.chat.id] = current_time
    else:
        delta_seconds = (current_time - last_datetime).total_seconds()
        seconds_left = int(need_seconds - delta_seconds)

        if seconds_left > 0:
            await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
        else:
            CHAT_BY_DATETIME[message.chat.id] = current_time

            async def get_screenshot_today(user_id: int):
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()

                if group:
                    my_group = group[0]

                if not last_datetime:
                    CHAT_BY_DATETIME[message.chat.id] = current_time
                else:
                    delta_seconds = (current_time - last_datetime).total_seconds()
                    seconds_left = int(need_seconds - delta_seconds)

                    if seconds_left > 0:
                        await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
                    else:
                        CHAT_BY_DATETIME[message.chat.id] = current_time
                        today = pendulum.today('Europe/Moscow').format('YYYY-MM-DD')
                        response_today = requests.get(f"https://almetpt.ru/2020/site/schedule/group/{my_group}/{today}")
                        soup = BeautifulSoup(response_today.text, "lxml")
                        schedule = soup.find("div", class_="container")

                        if 'года не опубликовано' in schedule.text:
                            return "Расписания на сегодня нет."
                        else:
                            browser = await launch()
                            page = await browser.newPage()
                            await page.setViewport({'width': 850, 'height': 1050})
                            await page.goto(f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{today}')
                            screen_id = message.from_user.id
                            await page.screenshot({'path': f"screenshots/{screen_id}_today.png"})
                            await browser.close()
                            return f"screenshots/{screen_id}_today.png"

            screen = await get_screenshot_today(message.from_user.id)
            if screen == "Расписания на сегодня нет.":
                await bot.reply_to(message, "Расписания на сегодня нет.")
            else:
                await bot.send_photo(message.chat.id, open(screen, 'rb'))


@bot.message_handler(text=['Расписание на завтра 📱'])
async def get_screen_tomorrow(message):
    need_seconds = 8
    current_time = datetime.datetime.now()
    last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
    if not last_datetime:
        CHAT_BY_DATETIME[message.chat.id] = current_time
    else:
        delta_seconds = (current_time - last_datetime).total_seconds()
        seconds_left = int(need_seconds - delta_seconds)

        if seconds_left > 0:
            await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
        else:
            CHAT_BY_DATETIME[message.chat.id] = current_time

            async def get_screenshot_tomorrow(user_id: int):
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()

                if group:
                    my_group = group[0]

                    tomorrow = pendulum.tomorrow('Europe/Moscow').format('YYYY-MM-DD')
                    response_check_tomorrow = requests.get(
                        f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{tomorrow}')
                    soup = BeautifulSoup(response_check_tomorrow.text, 'lxml')
                    schedule = soup.find("div", class_="container")

                    if 'года не опубликовано' in schedule.text:
                        return "Расписание на завтра еще не вышло!"
                    else:
                        browser = await launch()
                        page = await browser.newPage()
                        await page.setViewport({'width': 850, 'height': 1050})
                        await page.goto(f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{tomorrow}')
                        screen_id = message.from_user.id
                        await page.screenshot({'path': f"screenshots/{screen_id}_tomorrow.png"})
                        await browser.close()
                        return f"screenshots/{screen_id}_tomorrow.png"

            screen = await get_screenshot_tomorrow(message.from_user.id)
            if screen == "Расписание на завтра еще не вышло!":
                await bot.reply_to(message, "Расписание на завтра еще не вышло!")
            else:
                await bot.send_photo(message.chat.id, open(screen, 'rb'))


@bot.message_handler(text=['Расписание на понедельник📅'])
async def monday(message):
    async def check_monday(user_id: int):
        need_seconds = 5
        current_time = datetime.datetime.now()
        last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
        if not last_datetime:
            CHAT_BY_DATETIME[message.chat.id] = current_time
        else:
            delta_seconds = (current_time - last_datetime).total_seconds()
            seconds_left = int(need_seconds - delta_seconds)

            if seconds_left > 0:
                await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
            else:
                CHAT_BY_DATETIME[message.chat.id] = current_time
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()

                if group:
                    my_group = group[0]

                today = datetime.date.today()
                if calendar.day_name[today.weekday()] == 'Saturday':
                    monday = today + datetime.timedelta(days=2)
                    response_check_tomorrow = requests.get(
                        f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{monday}')
                    soup = BeautifulSoup(response_check_tomorrow.text, 'lxml')
                    schedule = soup.find("div", class_="container")

                    if 'года не опубликовано' in schedule.text:
                        return "Расписание на понедельник еще не вышло!"
                    else:
                        browser = await launch()
                        page = await browser.newPage()
                        await page.setViewport({'width': 850, 'height': 1050})
                        await page.goto(f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{monday}')
                        screen_id = message.from_user.id
                        await page.screenshot({'path': f"screenshots/{screen_id}_monday.png"})
                        await browser.close()
                        return f"screenshots/{screen_id}_monday.png"

                elif calendar.day_name[today.weekday()] == 'Sunday':
                    monday = today + datetime.timedelta(days=1)
                    response_check_tomorrow = requests.get(
                        f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{monday}')
                    soup = BeautifulSoup(response_check_tomorrow.text, 'lxml')
                    schedule = soup.find("div", class_="container")

                    if 'года не опубликовано' in schedule.text:
                        return "Расписание на понедельник еще не вышло!"
                    else:
                        browser = await launch()
                        page = await browser.newPage()
                        await page.setViewport({'width': 850, 'height': 1050})
                        await page.goto(f'https://almetpt.ru/2020/site/schedule/group/{my_group}/{monday}')
                        screen_id = message.from_user.id
                        await page.screenshot({'path': f"screenshots/{screen_id}_monday.png"})
                        await browser.close()
                        return f"screenshots/{screen_id}_monday.png"
                else:
                    await bot.reply_to(message, "Эта кнопка работает только в субботу и воскресенье.")

    screen = await check_monday(message.from_user.id)
    if screen == "Расписание на понедельник еще не вышло!":
        await bot.reply_to(message, "Расписание на понедельник еще не вышло!")
    else:
        await bot.send_photo(message.chat.id, open(screen, 'rb'))


@bot.message_handler(text=['Профиль📌'])
async def profile(message):
    async def show_profile(user_id: int):
        need_seconds = 5
        current_time = datetime.datetime.now()
        last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
        if not last_datetime:
            CHAT_BY_DATETIME[message.chat.id] = current_time
        else:
            delta_seconds = (current_time - last_datetime).total_seconds()
            seconds_left = int(need_seconds - delta_seconds)

            if seconds_left > 0:
                return f'Подождите {seconds_left} секунд перед выполнение этой команды'
            else:
                CHAT_BY_DATETIME[message.chat.id] = current_time
                cursor.execute("SELECT user_group FROM test WHERE user_id = ?", (user_id,))
                group = cursor.fetchone()
                cursor.execute("SELECT nickname FROM test WHERE user_id = ?", (user_id,))
                nickname = cursor.fetchone()

                if nickname:
                    result = nickname[0]

                if group:
                    my_group = group[0]
                    switch_group_name = {v: k for k, v in GROUP_ID.items()}
                    group_name = switch_group_name[my_group]

                    return f"Ваш ник: <b><i>{result}</i></b>\n➖➖➖➖➖➖➖\nВаша группа: <b><i>{group_name}</i></b>\n➖➖➖➖➖➖➖\nВаш id: <b><i>{message.from_user.id}</i></b>\n➖➖➖➖➖➖➖\nСменить <b>группу</b> вы можете нажав - Изменить группу📎"

    await bot.reply_to(message, await show_profile(message.from_user.id))


@bot.message_handler(text=['Помощь❓'])
async def get_help(message):
    need_seconds = 5
    current_time = datetime.datetime.now()
    last_datetime = CHAT_BY_DATETIME.get(message.chat.id)
    if not last_datetime:
        CHAT_BY_DATETIME[message.chat.id] = current_time
    else:
        delta_seconds = (current_time - last_datetime).total_seconds()
        seconds_left = int(need_seconds - delta_seconds)

        if seconds_left > 0:
            await bot.reply_to(message, f'Подождите {seconds_left} секунд перед выполнение этой команды')
        else:
            CHAT_BY_DATETIME[message.chat.id] = current_time
            await bot.reply_to(message, HELP_TEXT)


@bot.message_handler(chat_id=[702999620], commands=['admin_check'])
async def admin_rep(message):
    await bot.send_message(message.chat.id, "Вам разрешено использовать эту команду.")

    cursor.execute("SELECT user_id, user_group FROM test")
    matches = cursor.fetchall()
    d = dict(matches)

    for key, value in list(d.items()):
        if value is None:
            del d[key]

    for k, v in d.items():
        tomorrow = pendulum.tomorrow('Europe/Moscow').format('YYYY-MM-DD')

        async def send_new():
            browser = await launch()
            page = await browser.newPage()
            await page.setViewport({'width': 850, 'height': 1050})
            await page.goto(f'https://almetpt.ru/2020/site/schedule/group/{v}/{tomorrow}')
            await page.screenshot({'path': f"screenshots/{k}_tomorrow.png"})
            await browser.close()
            return f"screenshots/{k}_tomorrow.png"

    url = f'https://almetpt.ru/2020/site/schedule/group/{v}/{tomorrow}'
    response_check_tomorrow = requests.get(url=url)
    soup = BeautifulSoup(response_check_tomorrow.text, 'lxml')
    schedule = soup.find("div", class_="container")

    if 'года не опубликовано' in schedule.text:
        await bot.send_message(702999620, "Расписание на завтра еще не вышло!")
        await bot.send_message(702999620, f'❗Рассылка отменена')
    else:
        amount_message = 0
        amount_bad = 0
        start_time = time.time()
        for k, v in d.items():
            try:
                screen = await send_new()
                await bot.send_message(k, "Вышло расписание на завтра!")
                await bot.send_photo(k, open(screen, 'rb'))
                amount_message += 1
            except:
                amount_bad += 1
                pass

        sending_time = time.time() - start_time
        await bot.send_message(702999620,
                               f'✅Рассылка окончена\n'
                               f'❗Отправлено: {amount_message}\n'
                               f'❗Не отправлено: {amount_bad}\n'
                               f'🕐Время выполнения рассылки - {sending_time} секунд'
                               )


@bot.message_handler(chat_id=[702999620], commands=['show_users'])
async def admin_show(message):
    await bot.send_message(message.chat.id, "Вам разрешено использовать эту команду.")
    cursor.execute("SELECT user_id FROM test")
    matches = cursor.fetchall()
    users = list(matches)
    count_users = 0

    for user in users:
        if user:
            count_users += 1

    await bot.send_message(702999620, f'✅ Количество пользователей в боте: <b>{count_users}</b >')


@bot.message_handler(commands=['admin_check', 'show_users'])
async def not_admin(message):
    await bot.send_message(message.chat.id, "Вам не разрешено использовать эту команду.")




if __name__ == "__main__":
    while True:
        try:
            asyncio.run(bot.polling(skip_pending=True))
        except Exception as e:
            telebot.logger.error(e)
            time.sleep(15)
