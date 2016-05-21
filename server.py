#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import Flask, session, render_template, request, redirect, jsonify
import json, os, requests

from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from models import db, Athlete

app = Flask(__name__)
app.debug = True
app.secret_key = os.environ['SECRET_KEY']

strava_client_id = "11680"
strava_client_secret = "e4ee4894886dbf9de1d4622d9a247294bc5dc3fc"
strava_access_token = "f1de10689f30b7460244bf601c3f623b042d0615"

strava_auth_url = ("https://www.strava.com/oauth/authorize?"
					"client_id="+ strava_client_id +
  					"&response_type=code"
					"&redirect_uri="+ os.environ['STRAVA_CALLBACK_URL'] +"/token_exchange"
					"&scope=view_private")

strava_exchange_url = "https://www.strava.com/oauth/token"

@app.route("/")
def hello():
	if len(Athlete.select()) > 0:
		return render_template('index.html')
	else:
		return render_template('strava_auth.html', strava_auth_url=strava_auth_url)

@app.route("/auth")
def authenticate():
	return render_template('strava_auth.html', strava_auth_url=strava_auth_url)

@app.route("/token_exchange")
def token_exchange():
	code = request.args.get('code')

	r = requests.post(strava_exchange_url, {
			'client_id': strava_client_id,
			'client_secret': strava_client_secret,
			'code': code
		})

	if r.status_code != 200:
		return r.text

	athlete = Athlete.create(user_id=r.json()['athlete']['id'], access_token=r.json()['access_token'])

	return redirect('/')

'''
	Activity loading logic
'''
activity_counter = 0
club_activities = None

@app.route("/next")
def next():
	global activity_counter, club_activities

	if not club_activities:
		access_token = Athlete.select()[0].access_token
		club_activities = requests.get('https://www.strava.com/api/v3/clubs/198580/activities?access_token='+ access_token).json()

	current_activity = club_activities[activity_counter]
	# if current_activity['type'] != "Run" and current_activity['type'] != "Ride":
	# 	app.logger.debug('Stumbled upon an activity of type: %s, moving on to the next!' % current_activity['type'])
	# 	activity_counter += 1
	# 	if activity_counter == len(club_activities): activity_counter = 0
	# 	next()

	#access_token = Athlete.get(Athlete.user_id == 14511295).access_token
	#r = requests.get('https://www.strava.com/api/v3/activities/%s/streams/latlng,time?access_token=%s' % ('580277459', access_token))
	access_token = Athlete.get(Athlete.user_id == current_activity['athlete']['id']).access_token
	r = requests.get('https://www.strava.com/api/v3/activities/%s/streams/latlng,time?access_token=%s' % (current_activity['id'], access_token))

	activity_counter += 1
	if activity_counter == len(club_activities): activity_counter = 0

	app.logger.debug('Activity counter: %s' % activity_counter)

	data = current_activity
	data['streams'] = r.json()

	return json.dumps(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
