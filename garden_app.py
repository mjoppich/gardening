import json
import os
from flask import Flask, request, jsonify, render_template, redirect, send_from_directory
import logging

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import time, calendar
from datetime import timedelta, datetime

from string import Template

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)

auth = HTTPBasicAuth()

users = {
        "markus": generate_password_hash("markus")
}


@auth.verify_password
def verify_password(username, password):
    if username in ["markus"]:
        if check_password_hash(users.get(username), password):
            return username
    else:
        logging.warn("unknown username: {}".format(username))
    return False


app = Flask(__name__)

def get_current_data_path():
    return os.path.dirname(__file__) + "/current_data.json"

@app.route("/add-alarm", methods=["POST"])
@auth.login_required
def addalarm():
    hours = int(request.form['hours'])
    minutes = int(request.form["minutes"])

    cdata = get_current_data()

    cdata["alarm_times_utc"].append([hours, minutes])
    with open(get_current_data_path(), "w") as fout:
        json.dump(cdata, fout)

    return redirect("/", 302)


@app.route("/delete-alarm/<int:hours>/<int:minutes>")
@auth.login_required
def delalarm(hours, minutes):
    cdata = get_current_data()

    calarms = cdata["alarm_times_utc"]
    nalarms = []

    for x in calarms:
        if x[0] == hours and x[1] == minutes:
            continue
        nalarms.append(x)

    cdata["alarm_times_utc"] = nalarms

    with open(get_current_data_path(), "w") as fout:
            json.dump(cdata, fout)

    return redirect("/", 302)


@app.route("/sleepMin", methods=["GET"])
def sleepMin():
    cdata = get_current_data()
    return str(cdata.get("sleep_min", 15))

@app.route("/waterMin", methods=["GET"])
def waterMin():
    cdata = get_current_data()
    return str(cdata.get("water_min", 15))


@app.route("/set-sleepMin", methods=["POST"])
@auth.login_required
def setSleepMin():
    minutes = int(request.form["minutes"])

    cdata = get_current_data()

    cdata["sleep_min"] = minutes
    with open(get_current_data_path(), "w") as fout:
        json.dump(cdata, fout)

    return redirect("/", 302)

@app.route("/set-waterMin", methods=["POST"])
@auth.login_required
def setWaterMin():
    minutes = int(request.form["minutes"])

    cdata = get_current_data()

    cdata["water_min"] = minutes
    with open(get_current_data_path(), "w") as fout:
        json.dump(cdata, fout)

    return redirect("/", 302)


@app.route("/water_times", methods=["GET"])
def water_times():

    cdata = get_current_data()
    return jsonify(tuple(cdata["alarm_times_utc"]))        

def get_utc_seconds():
    return int(calendar.timegm(time.gmtime()))

@app.route("/start_watering", methods=["GET"])
def start_watering():

    try:
        inData = get_current_data()
        shouldWater = False


        for timer in inData["alarm_times_utc"]:

            #if last_timer < alarm_time and alarm_time < now: start

            seconds_to_lasttimer = get_seconds_to_alarm(timer, inData["last_timer"])
            seconds_to_now = get_seconds_to_alarm(timer, get_utc_seconds())

            logging.warning("last timer: " + str(inData["last_timer"]))
            logging.warning("seconds to last: " + str(seconds_to_lasttimer))
            logging.warning("seconds to now: " + str(seconds_to_now))

            if seconds_to_lasttimer > 0 and seconds_to_now < 0:
                shouldWater = True

        if shouldWater:
            return "1"
            

    except Exception as e:
        logging.error("Error Calculating Watering Time")
        logging.error(str(e))

    return "0"

def get_seconds_to_alarm( timer, reftime=None ):
    secondsAlarm = timer[0] * 60*60 + timer[1] * 60

    curTime = time.gmtime(reftime)
    secondsCur = curTime.tm_hour * 60 * 60 + curTime.tm_min * 60
    secondsToAlarm = secondsAlarm - secondsCur

    return secondsToAlarm

def get_time_to_alarm( timer, reftime ) :

    seconds = get_seconds_to_alarm(timer, reftime)
    return strfdelta(timedelta(0, seconds), '%H:%M:%S')


@app.route("/send", methods=["POST"])
def send_data():

    if request.method == "POST":
        rdata = request.get_json()

        cdata = get_current_data()

        for x in rdata:
            cdata[x] = rdata[x]

        cdata["last_timer"] = int(calendar.timegm( time.gmtime() ))

        if "watering" in rdata and int(rdata["watering"]) == 1:
            cdata["last_watering"] = int(calendar.timegm( time.gmtime() ))

        for x in ["temperatures", "soilmoistures", "humidities", "airpressures"]:
            if not x in cdata:
                cdata[x] = []

        histLength = 500

        cdata["temperatures"].append( (get_utc_seconds(), float((cdata["temp"][:-1])) ) )
        if len(cdata["temperatures"]) > histLength:
            cdata["temperatures"] = cdata["temperatures"][-histLength:]

        cdata["soilmoistures"].append( (get_utc_seconds(), float((cdata["soilmoisture"])) ) )
        if len(cdata["soilmoistures"]) > histLength:
            cdata["soilmoistures"] = cdata["soilmoistures"][-histLength:]

        cdata["humidities"].append( (get_utc_seconds(), float((cdata["humidity"][:-1])) ) )
        if len(cdata["humidities"]) > histLength:
            cdata["humidities"] = cdata["humidities"][-histLength:]

        cdata["airpressures"].append( (get_utc_seconds(), float((cdata["airpressure"][:-3])) ) )
        if len(cdata["airpressures"]) > histLength:
            cdata["airpressures"] = cdata["airpressures"][-histLength:]


        with open(get_current_data_path(), "w") as fout:
            json.dump(cdata, fout)

            return "thanks"
        
        return "posting"

    return "bye"


def get_current_data():
    try:
        with open(get_current_data_path(), "r") as fin:
            inData = json.load(fin)
            return inData
    except:
        logging.error("could not load current_data")
        logging.error(get_current_data_path())
        return {}

def update_current_time():

    returnData = get_current_data()
    returnData["current_time_utc"] = get_utc_seconds()
    returnData["current_time_local"] = int(time.mktime( time.localtime() ))
    returnData["time_to_alarm"] = [ get_time_to_alarm(x, returnData["current_time_utc"]) for x in returnData["alarm_times_utc"] ]

    with open(get_current_data_path(), "w") as fout:
        json.dump(returnData, fout)

    return returnData

def render_time(intime):

    if isinstance(intime, time.struct_time):
        return time.strftime('%Y-%m-%dT%H:%M:%S', intime)
    elif isinstance(intime, (int, float)):
        time_event = datetime.fromtimestamp(intime)
        return time_event.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(intime, str):
        return intime
    else:
        return ":".join([str(x) for x in intime])

def render_times(intimes):

    alltimes = [render_time(x) for x in intimes]
    return ", ".join(alltimes)


@app.route('/favicon.ico')
@auth.login_required
def favicon():
    return send_from_directory("images", 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
@auth.login_required
def report_status():

    directory_path = os.getcwd()
    logging.warning("my current directory is : {}".format(directory_path))

    returnData = update_current_time()
    return render_template("main.html", data=returnData, render_time=render_time, render_times=render_times)




if __name__ == "__main__":
    app.run()
