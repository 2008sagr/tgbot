import telebot
import ast
from pydub import AudioSegment
import speech_recognition as sr
import sqlite3
import io



bot = telebot.TeleBot("8043008496:AAHrcQbDuvKEQ8EbzexF3CoYGJipje23t6g")
 


@bot.message_handler(func=lambda message: True)
def echo_all(message):
	tg_api = ast.literal_eval(str(message))
	print(tg_api['from_user']['id'])
	bot.reply_to(message, message.text)
       

@bot.message_handler(content_types='voice')
def handle_docs_audio(message):
    try:
        # Получаем информацию о голосовом файле
        file_info = bot.get_file(message.voice.file_id)
        
        # Скачиваем файл в память
        downloaded_file = bot.download_file(file_info.file_path)
        
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
            bot.reply_to(message, text)
        except sr.UnknownValueError:
            bot.reply_to(message, "Не удалось распознать речь")
        except sr.RequestError as e:
            bot.reply_to(message, f"Ошибка сервиса распознавания: {e}")
            
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка обработки аудио: {str(e)}")
        
bot.infinity_polling()