import asyncio
from fastapi import FastAPI
from telebot.async_telebot import AsyncTeleBot  # Асинхронная версия бота
import io
from pydub import AudioSegment
import speech_recognition as sr
import sqlite3
from telebot import types
import json



# Настройки
BOT_TOKEN = ("")

# Инициализация FastAPI
app = FastAPI()

# Инициализация асинхронного бота
bot = AsyncTeleBot(BOT_TOKEN)

# Эндпоинт FastAPI
@app.get("/")
async def home():
    return {"status": "Bot is running"}


# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["Еда", "Алкоголь"]
    markup.add(*buttons)
    return markup


#Меню голосования за алкоголь
def alcohol_menu():
    #Тут читаем из базы список алкоголя
    try:
        cursor.execute("""SELECT name FROM alcohol """)
        #Генерируем из него словорь и делаем новое меню
        alcohol = [row[0] for row in cursor.fetchall()]
    
    except Exception as e:
        print(f'Ошибка при формировании меню алкоголя: {str(e)}')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*alcohol)
    return markup



#Тут мы получаем команду на показ меню
@bot.message_handler(commands=['menu'])
async def echo_all(message):
    await bot.send_message(
        message.chat.id,
        "Главное меню",
        reply_markup=main_menu()
    )


#Тут обрабатываем кнопку 'Еда'
@bot.message_handler(func=lambda m: m.text == 'Еда')
async def show_catalog(message):
    await bot.send_message(
        message.chat.id,
        "Тут голосуем за еду",
        #reply_markup=catalog_menu()
    )


#Тут обрабатываем кнопку 'Алкоголь'
@bot.message_handler(func=lambda m: m.text == 'Алкоголь')
async def show_catalog(message):
    await bot.send_message(
        message.chat.id,
        "Тут голосуем за алкоголь",
        reply_markup=alcohol_menu()
    )


#Тут обрабатываем кнопку 'Пиво'
@bot.message_handler(func=lambda m: m.text == 'Пиво')
async def show_catalog(message):
    try:
        cursor.execute("""SELECT votes FROM users WHERE id = ?""", (message.from_user.id,))
        result = cursor.fetchone()
        votes = {}
        if result and result[0]:  # Проверяем, что результат не None и не пустой
            try:
                votes = json.loads(result[0])
            except json.JSONDecodeError:
                votes = {}  # Если не удалось распарсить JSON, начинаем с чистого словаря
    
    except Exception as e:
        await bot.send_message(
            message.chat.id,
            f'Ошибка: {e}'
        )

    votes['Пиво'] = 1
    try:
        cursor.execute("""UPDATE users SET votes = ? WHERE id = ?""",(json.dumps(votes, ensure_ascii= False), message.from_user.id))
        conn.commit()
        await bot.send_message(
            message.chat.id,
            f"{message.from_user.first_name} проголосовал за пиво"
        )
 
    except Exception as e:
        await bot.send_message(
            message.chat.id,
            f'Ошибка: {e}'
        )
    

# Команда для бота
@bot.message_handler(commands=['add'])
async def send_welcome(message):
    try:
        # Проверяем существование пользователя
        cursor.execute('SELECT 1 FROM users WHERE id = ?', (message.from_user.id,))
        if cursor.fetchone():
            await bot.reply_to(message, "Ты уже в базе!")
            return

        # Добавляем нового пользователя
        cursor.execute('''
            INSERT INTO users (id, name) 
            VALUES (?, ?)
        ''', (message.from_user.id, message.from_user.first_name))
        conn.commit()

        await bot.reply_to(message, "Я тебя записал")
        
    except Exception as e:
        await bot.reply_to(message, f"❌ Ошибка при регистрации: {str(e)}")
        conn.rollback()


#Получаем голосовое сообщение и преобразовываем его в текст
@bot.message_handler(content_types='voice')
async def handle_docs_audio(message):
    try:
        # Получаем информацию о голосовом файле
        file_info = await bot.get_file(message.voice.file_id)
        
        # Скачиваем файл в память
        downloaded_file =await bot.download_file(file_info.file_path)
        
        # Создаем файлоподобный объект в памяти для OGG данных
        ogg_audio = io.BytesIO(downloaded_file)
        ogg_audio.name = 'voice.ogg'  # Указываем расширение для pydub
        
        # Конвертируем OGG в WAV в памяти
        audio = AudioSegment.from_ogg(ogg_audio)
        wav_audio = io.BytesIO()
        audio.export(wav_audio, format="wav")
        wav_audio.seek(0)  # Перематываем на начало для чтения
        
        # Распознаем речь
        r = sr.Recognizer()
        with sr.AudioFile(wav_audio) as source:
            audio_data = r.record(source)
        
        try:
            # Пытаемся распознать русскую речь
            text = r.recognize_google(audio_data, language="ru-RU")
            await bot.reply_to(message, text)
        except sr.UnknownValueError:
            await bot.reply_to(message, "Не удалось распознать речь")
        except sr.RequestError as e:
            await bot.reply_to(message, f"Ошибка сервиса распознавания: {e}")
            
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка обработки аудио: {str(e)}")


# Запуск бота и FastAPI
async def telebot_run():    
    # Запускаем поллинг (опрос сервера Telegram)
    await bot.infinity_polling()


if __name__ == "__main__":
    import uvicorn

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    #Создаем таблицу если ее нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            votes TEXT 
        )
    """)
    conn.commit()
    #alcohol_init()
    
    # Запускаем FastAPI и бота в одном событийном цикле
    loop = asyncio.get_event_loop()
    
    # Запуск FastAPI на порту 8000
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop=loop)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    
    # Запуск бота и сервера параллельно
    loop.run_until_complete(asyncio.gather(
        uvicorn_server.serve(),
        telebot_run()
    ))