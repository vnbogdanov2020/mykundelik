import telebot
from telebot import types

keyboard1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=1)
keyboard1.row('Мои ученики')

keyboard2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=1)
keyboard2.row('Расписание','Предметы')


#keyboard1.row('Привет', 'Пока','Я тебя люблю')
#keyboard1.row('Запрос')

NewStudent = telebot.types.ReplyKeyboardMarkup(resize_keyboard=1)
key_b = types.KeyboardButton(text='Новый ученик',request_contact=True)
NewStudent.add(key_b)