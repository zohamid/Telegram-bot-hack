import sys
from fatsecret import Fatsecret
import time

from pymongo import MongoClient
client = MongoClient()
db = client.food
user_database = db.lookup

def get_food_info(item, name, fs):
	try:
		foods = fs.food_get(item)
		print foods
		exit()
	except Exception, e:
		print e


def populate(fs, filename):
	f = open(filename, 'r')
	dictio = {}
	for x in f:
		name, ide = x.rstrip().split(':')
		dictio[ide] = name
	f.close()
	for x in dictio.keys():
		time.sleep(1.1)
		get_food_info(x, dictio[x], fs)
		print dictio[x]


if __name__ == "__main__":
	fs = Fatsecret(sys.argv[1], sys.argv[2])
	z = populate(fs, sys.argv[3])
