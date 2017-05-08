from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging

import openimages


from pymongo import MongoClient
client = MongoClient()
db = client.telegram
user_database = db.users


TOKEN = '302383997:AAFRArU5lOXML-GfaJBVEenDjXNd11lL0Uo'
updater = Updater(token=TOKEN)

dispatcher = updater.dispatcher
serving_keyboard = {'keyboard':[["1", "2", "3", "4"], ["5", "6", "7", "8"]]}
user_states = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def get_status_string(username, name):
	return "wololo"


def register(bot, update):
	# global user_database
	username = update.message.from_user.username
	name = update.message.from_user.first_name
	if user_database.find({"username": username}).count() != 0:
		reply_string = "Oops! You're already registered with us, " + name
	else:
		reply_string = "Thanks for registering with us, " + name + " !"
		user_database.insert_one({"username": username})
	bot.sendMessage(chat_id=update.message.chat_id, text=reply_string)


def status(bot, update):
	username = update.message.from_user.username
	name = update.message.from_user.first_name
	if user_database.find({"username": username}).count() == 0:
		bot.sendMessage(chat_id=update.message.chat_id, text="You need to register first via /register")
	else:
	bot.sendMessage(chat_id=update.message.chat_id, text=get_status_string(username, name))


def echo(bot, update):
	global user_database
	username = update.message.from_user.username
	if username in user_states:
		del user_states[username]
		quantity = int(update.message.text)
		bot.sendMessage(chat_id=update.message.chat_id, text="Got it!", reply_markup={'hide_keyboard': True})
	else:
		if user_database.find_one({"username": username}).count() == 0:
			bot.sendMessage(chat_id=update.message.chat_id, text="You need to register first via /register")
		else:
			bot.sendMessage(chat_id=update.message.chat_id, text="Send me a click of what you're eating first?")


def identify_image(bot, update):
	username = update.message.from_user.username
	name = update.message.from_user.first_name
	file_id = update.message.photo[-1].file_id
	file = bot.getFile(file_id)
	extension = file.file_path.split('.')[-1]
	file.download('temp')
	result = openimages.predict_on_image('temp')
	if result is None:
		bot.sendMessage(chat_id=update.message.chat_id, text="Oops! That's probably not an edible item (or at least that's what I think :P ). Click another pic, if it is?")	
	else:
		food_guessed = "apple"
		bot.sendMessage(chat_id=update.message.chat_id, text = "How many servings of " + food_guessed +  " did you have?", reply_markup=serving_keyboard)
		user_states[username] = 1
	# bot.sendMessage(chat_id=update.message.chat_id, text=str(result))


start_handler = CommandHandler('register', register)
dispatcher.add_handler(start_handler)

start_handler = CommandHandler('status', status)
dispatcher.add_handler(start_handler)

# echo_handler = MessageHandler(Filters.text, echo)
# dispatcher.add_handler(echo_handler)

image_handler = MessageHandler(Filters.photo, identify_image)
dispatcher.add_handler(image_handler)


if __name__ == "__main__":
	updater.start_polling()
