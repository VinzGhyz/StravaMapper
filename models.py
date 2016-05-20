from peewee import *

db = SqliteDatabase('athletes.db')

class Athlete(Model):
	user_id = PrimaryKeyField()
	access_token = CharField()

	class Meta:
		database = db

