from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging

import openimages

import requests
import datetime
import base64


from pymongo import MongoClient
client = MongoClient()
db = client.telegram
user_database = db.users
db2 = client.food
food_database = db2.lookup

WHENHUB_TOKEN = "H4s5piDr9jCiY9t4eaLgbDiUQsmzW2dLD4LzRiBBXJD8GgyaCcV2mEhCCsehKMCe"
WHENHUB_ID = "590c18af39694901903f5306"
TOKEN = '302383997:AAFRArU5lOXML-GfaJBVEenDjXNd11lL0Uo'
updater = Updater(token=TOKEN)

dispatcher = updater.dispatcher
serving_keyboard = {'keyboard':[["1", "2", "3", "4"], ["5", "6", "7", "8"]]}
user_states = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def create_schedule(name):
	send_data = {# "icon": "string",
  		"name": name + "'s nutrition timeline",
  		"description": "Tracking food consumption",
  		"scope": "public"}
	url = "https://api.whenhub.com/api/users/" + WHENHUB_ID + "/schedules?access_token=" + WHENHUB_TOKEN
	response = requests.request("POST", url, data=send_data)
	return response.json()['id']


def publish_event(schedule_id, calories, carbohydrate, protein, fat, food, quantity):
	intro_string = "Had " + str(quantity) + " of " + food
	info_string = "Calories: %f\n Carbohydrates: %f\n Protein: %f\n Fat:%f\n" % (calories, carbohydrate, protein, fat)
	send_data = {
  		"when": {
    		"period": "minute",
    		"startDate": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    		"startTimezone": "Asia/Kolkata"
  		},
  		"name": intro_string,
  		"description": info_string,
  		# "icon": "string",
  		"tags": [food]
	}
  	url = "https://api.whenhub.com/api/schedules/" + schedule_id + "/events?access_token=" + WHENHUB_TOKEN
	response = requests.request("POST", url, data=send_data)
	print response.json()
	event_id = response.json()['id']
	with open('temp', 'rb') as image_file:
		send_data = {
			"type": "image",
  			"content": base64.b64encode(image_file.read())
  		}
	url = "https://api.whenhub.com/api/events/ " + event_id + "/media?access_token=" + WHENHUB_TOKEN
	response = requests.request("POST", url, data=send_data)
	


def get_status_string(username, name):
	# db.collection.update_one({"_id":"key1"}, {"$set": {"id":"key1"}}, upsert=True)
	for z in user_database.find({"username": username}):
		calories = quantity * z['calories']
		carbohydrate = quantity * z['carbohydrate']
		protein = quantity * z['protein']
		schedule_id = z['schedule_id']
		fat = quantity * z['fat']
	return_string = "Hey, " + name + ". Your consumption for the day so far is: "
	return_string += "Calories: %f, Carbohydrates: %f, Protein:  %f, Fat: %f" % (calories, carbohydrate, protein, fat)
	whenhub_url = "https://studio.whenhub.com/schedules/" + schedule_id
	return_string += "You may track your nutrient intake here at : %s" % (whenhub_url)
	return return_string


def register(bot, update):
	# global user_database
	username = update.message.from_user.username
	name = update.message.from_user.first_name
	if user_database.find({"username": username}).count() != 0:
		reply_string = "Oops! You're already registered with us, " + name
	else:
		reply_string = "Thanks for registering with us, " + name + " !"
		user_database.insert_one({"username": username, "schedule_id": create_schedule(name)})
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
	global user_states
	print "Got message"
	username = update.message.from_user.username
	if username in user_states:
		quantity = int(update.message.text)
		calories = 100
		carbohydrate = 2
		protein =0.1
		fat = 2 
		# for z in food_database.find({"name": user_states[username]}):
		# 	calories = quantity * z['calories']
		# 	carbohydrate = quantity * z['carbohydrate']
		# 	protein = quantity * z['protein']
		# 	fat = quantity * z['fat']
		for z in user_database.find({"username": username}):
			schedule_id = z['schedule_id']
		publish_event(schedule_id, calories, carbohydrate, protein, fat, user_states[username], quantity)
		bot.sendMessage(chat_id=update.message.chat_id, text="Got it!", reply_markup={'hide_keyboard': True})
		del user_states[username]
	else:
		if user_database.find_one({"username": username}).count() == 0:
			bot.sendMessage(chat_id=update.message.chat_id, text="You need to register first via /register")
		else:
			bot.sendMessage(chat_id=update.message.chat_id, text="Send me a click of what you're eating first?")


def identify_image(bot, update):
	global user_states
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
		user_states[username] = food_guessed
		print "Set user state to ", food_guessed
	# bot.sendMessage(chat_id=update.message.chat_id, text=str(result))


start_handler = CommandHandler('register', register)
dispatcher.add_handler(start_handler)

start_handler = CommandHandler('status', status)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

image_handler = MessageHandler(Filters.photo, identify_image)
dispatcher.add_handler(image_handler)


if __name__ == "__main__":
	updater.start_polling()
