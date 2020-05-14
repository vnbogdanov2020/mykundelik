from setting import bot_token
from setting import cnx
from setting import restlink
from setting import chat_id_service
import telebot
import keyboards
import datetime
from telebot import types
from kunapipy.kundelik import kundelik
import requests
import json

login = ''
password = ''
user_token = ''
class_id = ''
user_id = ''
person_id = ''
school_id = ''

cursor = cnx.cursor()

bot = telebot.TeleBot(bot_token)

#Первый запуск
@bot.message_handler(commands=['start'])
def start_message(message):
    sql = ("SELECT * FROM user WHERE chat_id= %s")
    cursor.execute(sql, [(message.from_user.id)])
    user = cursor.fetchone()
    if not user:
        # Добавляем нового пользователя
        newdata = (message.from_user.id, datetime.datetime.now())
        cursor.executemany("INSERT INTO user (chat_id, ddate) VALUES (%s, %s)", (newdata,))
        cnx.commit()
        cursor.close()
        cnx.close()
        bot.send_message(message.chat.id, 'Добро пожаловать!', reply_markup=keyboards.keyboard1)
    else:
        bot.send_message(message.chat.id, 'С возвращением!', reply_markup=keyboards.keyboard1)

@bot.message_handler(commands=['week_grades', 'month_grades', 'day_grades'], content_types=['text'])
def week_grades(message):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id

    bad = False
    sat = False

    if message.text == '/week_grades':
        start_date = str(datetime.date.today() - datetime.timedelta(days=7))
    if message.text == '/month_grades':
        start_date = str(datetime.date.today() - datetime.timedelta(days=30))
    if message.text == '/day_grades':
        start_date = str(datetime.date.today() - datetime.timedelta(days=1))

    end_date = str(datetime.date.today())
    current_marks = show_marks_in_period(person_id=person_id, start_date=start_date,
                                         school_id=school_id, end_date=end_date, user_token=user_token)
    for mark in current_marks:
        url = 'https://api.kundelik.kz/v2.0/lessons/' + mark['lesson_str']
        subject = requests.get(url, headers={'Access-Token': user_token}).json()
        if str(mark['value']) == 'ПЛХ':
            bad = True
        if str(mark['value']) == 'УДВ':
            sat = True
        marks_answer = str(subject['subject']['name']) + ' - ' + str(mark['value'])
        bot.send_message(message.chat.id, marks_answer)

    if bad:
        bot.send_message(message.chat.id, 'Похоже на то, что у тебя есть двойки! Но не расстраивайся, '
                                          'все твои пятерки еще впереди, надо лишь приложить немного усилий!')

    if  not bad and not sat and current_marks:
        bot.send_message(message.chat.id, 'Похоже на то, что у тебя ни одной тройки и двойки! '
                                          'Машинка, что сказать. Так держать.')
    if not current_marks:
        bot.send_message(message.chat.id, 'Ты еще не успел получить ни одной оценки')


@bot.message_handler(commands=['week_attend', 'month_attend', 'day_attend'], content_types=['text'])
def attendance(message):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id
    if message.text == '/week_attend':
        start_date = str(datetime.date.today() - datetime.timedelta(days=7))
    if message.text == '/month_attend':
        start_date = str(datetime.date.today() - datetime.timedelta(days=30))
    if message.text == '/day_attend':
        start_date = str(datetime.date.today() - datetime.timedelta(days=1))

    end_date = str(datetime.date.today())
    current_attendance = show_attendance_in_period(person_id=person_id, start_date=start_date,
                                                   end_date=end_date, user_token=user_token)
    try:
        logEntries = current_attendance['logEntries']

    except Exception as e:
        bot.send_message(message.chat.id, 'Нет записей за этот период')
        return 0

    if not logEntries:
        bot.send_message(message.chat.id, 'Нет записей за этот период')
    else:
        for note in logEntries:
            status = note['status']
            subject = get_lesson_information(lesson_id=str(note['lesson']), user_token=user_token)['subject']['name']
            if status == 'Pass':
                bot.send_message(message.chat.id, 'прогулял урок: ' + subject)
            if status == 'Absent':
                bot.send_message(message.chat.id, 'пропустил урок: ' + subject)
            if status == 'NotSet':
                pass
            if status == 'Ill':
                bot.send_message(message.chat.id, 'не присутствовал по болезни: ' + subject)
            if status == 'Late':
                bot.send_message(message.chat.id, 'опоздал на урок: ' + subject)

@bot.message_handler(commands=['class_average_mark'], content_types=['text'])
def class_average_mark(message):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id

    bot.send_message(message.chat.id, 'Будет показан средний балл класса с начала года то сегодняшнего дня')
    url = 'https://api.kundelik.kz/v2.0/edu-groups/' + class_id + '/avg-marks/2020-04-01/2020-05-01'
    average_mark = requests.get(url, headers={'Access-Token': user_token}).json()
    all_marks = []
    print(average_mark)
    print(user_token)
    for student in average_mark:
        for subject in student['per-subject-averages']:
            all_marks.append(float(subject['avg-mark-value'].replace(',', '.',)))
    answer = sum(all_marks) / len(all_marks)
    url = 'https://api.kundelik.kz/v2.0/edu-groups/1565042653527550944'
    class_name = (requests.get(url, headers={'Access-Token': user_token}).json())['name']
    bot.send_message(message.chat.id, 'Средний балл класса ' + str(class_name) + ' равен ' + str(answer))

@bot.message_handler(content_types=['text'])
def send_text(message):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id

    if message.text.lower() == 'мои ученики':
        markup = types.InlineKeyboardMarkup()
        sql = ("SELECT name, id FROM students WHERE chat_id= %s")
        cursor.execute(sql, [(message.from_user.id)])
        students = cursor.fetchall()
        for row in students:
            switch_button = types.InlineKeyboardButton(text=row[0], callback_data='sel_student'+str(row[1]))
            markup.add(switch_button)
        #switch_button = types.InlineKeyboardButton(text="Добавить ...", callback_data="add_student")
        #markup.add(switch_button)
        bot.send_message(message.chat.id, "Список учеников", reply_markup=markup)
    if message.text.lower() == 'расписание':
        start_date = str(datetime.date.today() + datetime.timedelta(days=1))
        end_date = str(datetime.date.today() + datetime.timedelta(days=2))
        print(person_id)
        print(class_id)
        url = 'https://api.kundelik.kz/v2.0/persons/' + person_id + '/groups/' + class_id + '/schedules/' \
         '?startDate=' + start_date + '&endDate=' + end_date
        outtext = 'Уроки на завтра ('+start_date+')'+'\n'+'\n'
        print(url)
        schedule = requests.get(url, headers={'Access-Token': user_token}).json()['days'][0]['lessons']
        for lesson in schedule:
            outtext = outtext+(
                               #str(lesson['number']) + ') ' +
                               str(lesson['hours']) + ' ' +
                             get_lesson_information(user_token=user_token, lesson_id=lesson['id'])['subject']['name'])
            outtext = outtext +'\n'
        bot.send_message(message.chat.id,outtext)
        #bot.send_message(message.chat.id, str(lesson['number']) + ') ' + str(lesson['hours']) + ' - ' +
            #                 get_lesson_information(user_token=user_token, lesson_id=lesson['id'])['subject']['name'])
    if message.text.lower() == 'предметы':
        subjects = get_subject_name(class_id=class_id, user_token=user_token)
        markup = types.InlineKeyboardMarkup()
        for subject in subjects:
            switch_button = types.InlineKeyboardButton(text=subject['name'], callback_data='sel_subject_' + subject['name'])
            markup.add(switch_button)
        bot.send_message(message.chat.id, 'Предметы ученика', reply_markup=markup)


def get_user_information(user_token, user_id):
    url = 'https://api.kundelik.kz/v2.0/users/' + str(user_id) + '/context'
    res = requests.get(url, headers={'Access-Token': user_token})

    return json.loads(res.text)

@bot.callback_query_handler(func=lambda c:True)
def inline(callback):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id

    print(callback.data)
    indate = callback.data
    if indate.find('add_student') != -1:
        bot.send_message(callback.message.chat.id, 'Новый ученик', reply_markup=keyboards.NewStudent)

    if indate.find('sel_student') != -1:
        get_connect(callback.message.chat.id, indate[11:len(indate)])
        bot.send_message(callback.message.chat.id, 'Меню ученика', reply_markup=keyboards.keyboard2)

    if indate.find('sel_subject_') != -1:
        subject_name = indate[12:len(indate)]
        url = 'https://api.kundelik.kz/v2.0/edu-group/' + class_id + '/person/' + person_id + '/criteria-marks'
        res = requests.get(url, headers={'Access-Token': user_token}).json()
        if not get_subject_id(subject_name=subject_name, user_token=user_token, class_id=class_id):
            bot.send_message(callback.message.chat.id, 'Не найден предмет.')
            return 0

        for subject in res:
            if subject['subject'] == get_subject_id(subject_name=subject_name, user_token=user_token,
                                                    class_id=class_id):
                if subject['personmarks']:
                    str_marks = subject_name + '\n'
                    for mark in subject['personmarks'][0]['criteriamarks']:
                        str_marks += str(mark['date'])[:10] + ' Балл: ' + str(mark['value']) + '\n'
                    bot.send_message(callback.message.chat.id, str_marks)
                else:
                    bot.send_message(callback.message.chat.id, 'За этот предмет нет оценок')

def get_connect(in_user_id, sel_student):
    global login, password, user_token, random_answers, \
        person_id, user_id, class_id, school_id

    sql = ("SELECT login, password FROM students WHERE id= %s and chat_id=%s")
    data = (sel_student, in_user_id)
    cursor.execute(sql, data)
    students = cursor.fetchall()
    for row in students:
        login = row[0]
        password = row[1]
        dn = kundelik.KunAPI(login=login, password=password)
        user_token = dn.get_token(login=login, password=password)
        user_id = str(dn.get_info()['id'])
        person_id = str(dn.get_info()['personId'])
        data = get_user_information(user_token=user_token, user_id=user_id)
        school_id = str(data['schools'][0]['id'])
        class_id = data['eduGroups'][0]['id_str']
        #bot.send_message(in_user_id, 'Меню ученика', reply_markup=keyboards.keyboard2)

        # Обновим текущего ученика для пользователя
        sql = ("UPDATE user SET sel_student = %s WHERE chat_id= %s")
        data = (sel_student, in_user_id)
        cursor.execute(sql, data)


def get_lesson_information(lesson_id, user_token):
    url = 'https://api.kundelik.kz/v2.0/lessons/' + str(lesson_id)
    res = requests.get(url, headers={'Access-Token': user_token}).json()

    return res


def get_user_information(user_token, user_id):
    url = 'https://api.kundelik.kz/v2.0/users/' + str(user_id) + '/context'
    res = requests.get(url, headers={'Access-Token': user_token})

    return json.loads(res.text)


def show_marks_in_period(person_id, school_id, start_date, end_date, user_token):
    url_mark = 'https://api.kundelik.kz/v2.0/persons/' + person_id + '/schools' \
                                                                '/' + school_id + '/marks/' + start_date + '/' \
                                                                + end_date
    res = requests.get(url_mark, headers={'Access-Token': user_token}).json()

    return res


def show_attendance_in_period(person_id, start_date, end_date, user_token):
    url = 'https://api.kundelik.kz/v2.0/persons/' + person_id + '/lesson-log-entries?startDate=' \
           + start_date + '&endDate=' + end_date
    res = requests.get(url, headers={'Access-Token': user_token}).json()

    return res


def get_subject_name(class_id, user_token, subject_id=0):
    url = 'https://api.kundelik.kz/v2.0/edu-groups/' + class_id + '/subjects'
    res = requests.get(url, headers={'Access-Token': user_token}).json()
    if subject_id == 0:
        return res
    for subject in res:
        if subject['id'] == subject_id:
            return subject['name']

    return None


def get_subject_id(subject_name, user_token, class_id):
    url = 'https://api.kundelik.kz/v2.0/edu-groups/' + class_id + '/subjects'
    res = requests.get(url, headers={'Access-Token': user_token}).json()
    for subject in res:
        if subject['name'] == subject_name:
            return subject['id']

    return False
bot.polling()