import os
from aiogram import Bot, Dispatcher, executor, types
import sqlite3


path = 'resources/img/'
list_of_dirs = os.listdir(path)

con = sqlite3.connect('bot_db')
cursor = con.cursor()
try:
    cursor.execute("""CREATE TABLE users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        user_name VARCHAR (50))
        """)
except:
    pass

API_TOKEN = ''
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
manager_id = 1871799232
fl_question = False


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    user = (message.from_user.id, message.from_user.username)
    try:
        cursor.execute('INSERT INTO users (user_id, user_name) VALUES (?, ?)', user)
    except:
        pass
    con.commit()
    await message.answer('Привет! Меня зовут Каролина, и я занимаюсь пошивом на заказ нижнего белья, бра, корсетов '
                         'и прочих аксессуаров. Ниже Вы можете ознакомиться с моими работами или оставить свой вопрос, '
                         'чтобы я могла с Вами связаться лично.')
    await get_action(message)


@dp.message_handler()
async def reply_message(message: types.Message):
    global fl_question
    if fl_question:
        await bot.send_message(chat_id=1871799232, text=f'Пользователь @{message.from_user.username} '
                                                        f'оставил Вам сообщение: {message.text}')
        buttons = [
            types.InlineKeyboardButton(text='Да', callback_data='yes'),
            types.InlineKeyboardButton(text='Нет', callback_data='no')
        ]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*buttons)
        await bot.send_message(message.chat.id, text='Ваш вопрос отправлен мастеру, вскоре он вам ответит. '
                                                     'Желаете посмотреть работы или задать ещё один вопрос ?',
                               reply_markup=keyboard)
        fl_question = False
    else:
        await bot.send_message(chat_id=message.from_user.id, text='К сожалению, я вас не понимаю.')
        await get_action(message)


async def get_action(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='Просмотреть работы', callback_data='gallery'),
        types.InlineKeyboardButton(text='Задать вопрос', callback_data='question')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    await bot.send_message(message.chat.id, text='Вы можете ознакомиться с работами или задать вопрос.',
                           reply_markup=keyboard)


async def get_photos(message: types.Message, count, directory):
    list_of_photos = os.listdir(path + list_of_dirs[count])
    media_group = []
    try:
        for photo in list_of_photos:
            full_path = path + directory + '/' + photo
            media_group.append(types.InputMediaPhoto(open(full_path, 'rb')))
        await bot.send_message(message.chat.id, text='Комплект №' + f'{count + 1}')
    except:
        await bot.send_message(message.chat.id, text='Фотографии не были найдены.')
    return media_group


@dp.callback_query_handler()
@dp.message_handler()
async def callback(call: types.CallbackQuery):
    global fl_question
    match call.data:
        case 'order':
            await bot.send_message(chat_id=1871799232, text=f'Пользователь @{call.message.chat.username} '
                                                            f'оставил заказ!')
            await bot.send_message(chat_id=call.message.chat.id,
                                   text='Спасибо, что оставили заказ.')
            await get_action(call.message)
        case 'question':
            fl_question = True
            await bot.send_message(chat_id=call.message.chat.id,
                                   text='Пожалуйста, напишите свой вопрос в чат.')
        case 'gallery':
            for count, directory in enumerate(list_of_dirs):
                await bot.send_media_group(call.message.chat.id,
                                           media=await get_photos(call.message, int(count), directory))
            buttons = [
                types.InlineKeyboardButton(text='Оставить заказ', callback_data='order'),
                types.InlineKeyboardButton(text='Вернуться назад', callback_data='back')
            ]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(*buttons)
            await bot.send_message(call.message.chat.id,
                                   text='Если Вам что-то понравилось, можете оставить предварительный заказ, '
                                        'и с Вами вскоре свяжется мастер.',
                                   reply_markup=keyboard)
        case 'no':
            await bot.send_message(call.message.chat.id, text='Всего доброго!')
        case 'back' | 'yes':
            await get_action(call.message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
