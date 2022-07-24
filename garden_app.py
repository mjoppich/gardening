import json
import os
from flask import Flask, request, jsonify, render_template, redirect
import logging

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import time, calendar
from datetime import timedelta

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


@app.route("/add-alarm", methods=["POST"])
@auth.login_required
def addalarm():
    hours = int(request.form['hours'])
    minutes = int(request.form["minutes"])

    cdata = get_current_data()

    cdata["alarm_times_utc"].append([hours, minutes])
    with open("current_data.json", "w") as fout:
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

    with open("current_data.json", "w") as fout:
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
    with open("current_data.json", "w") as fout:
        json.dump(cdata, fout)

    return redirect("/", 302)

@app.route("/set-waterMin", methods=["POST"])
@auth.login_required
def setWaterMin():
    minutes = int(request.form["minutes"])

    cdata = get_current_data()

    cdata["water_min"] = minutes
    with open("current_data.json", "w") as fout:
        json.dump(cdata, fout)

    return redirect("/", 302)


@app.route("/water_times", methods=["GET"])
def water_times():

    with open("current_data.json", "r") as fin:
        inData = json.load(fin)
        return jsonify(tuple(inData["alarm_times_utc"]))

    return jsonify(tuple([]))

def get_utc_seconds():
    return int(calendar.timegm(time.gmtime()))

@app.route("/start_watering", methods=["GET"])
def start_watering():

    try:
        with open("current_data.json", "r") as fin:
            inData = json.load(fin)

            shouldWater = True

            for timer in inData["alarm_times_utc"]:

                #if last_timer < alarm_time and alarm_time < now: start

                seconds_to_lasttimer = get_seconds_to_alarm(timer, inData["last_timer"])
                seconds_to_now = get_seconds_to_alarm(timer, get_utc_seconds())

                if seconds_to_lasttimer > 0 and seconds_to_now < 0:
                    shouldWater = True

            if shouldWater:
                return "1"
            

    except:
        pass

    return "0"

def get_seconds_to_alarm( timer, reftime=None ):
    secondsAlarm = timer[0] * 60*60 + time[1] * 60

    curTime = time.gmtime(reftime)
    secondsCur = curTime.tm_hour * 60 * 60 + curTime.tm_min * 60
    secondsToAlarm = secondsAlarm - secondsCur

    return secondsToAlarm

def get_time_to_alarm( timer, reftime ) :

    seconds = get_seconds_to_alarm(timer, reftime)
    return timedelta(seconds)


@app.route("/send", methods=["POST"])
def send_data():

    if request.method == "POST":
        rdata = request.get_json()

        cdata = get_current_data()

        for x in rdata:
            cdata[x] = rdata[x]

        cdata["last_timer"] = int(calendar.timegm( time.gmtime() ))

        if int(rdata["watering"]) == 1:
            cdata["last_watering"] = int(calendar.timegm( time.gmtime() ))


        cdata["temperatures"].append( (get_utc_seconds(), float((cdata["temp"][:-1])) ) )
        if len(cdata["temperatures"]) > 1000:
            cdata["temperatures"] = cdata["temperatures"][-1000:]

        with open("current_data.json", "w") as fout:
            json.dump(cdata, fout)

            return "thanks"
        
        return "posting"

    return "bye"


def get_current_data():
    try:
        with open("current_data.json", "r") as fin:
            inData = json.load(fin)
            return inData
    except:
        return []

def update_current_time():

    returnData = get_current_data()
    returnData["current_time_utc"] = get_utc_seconds()
    returnData["current_time_local"] = int(time.mktime( time.localtime() ))
    returnData["time_to_alarm"] = [ get_time_to_alarm(x, returnData["current_time_utc"]) for x in returnData["alarm_times_utc"] ]

    with open("current_data.json", "w") as fout:
        json.dump(returnData, fout)

    return returnData

def render_time(x):

    if isinstance(x, time.struct_time):
        return time.asctime( time.localtime(time.time()) )

    else:
        return ":".join(x)

def render_times(intimes):

    alltimes = [render_time(x) for x in intimes]
    return ", ".join(alltimes)


@app.route("/")
@auth.login_required
def report_status():

    directory_path = os.getcwd()
    logging.warning("my current directory is : {}".format(directory_path))

    returnData = update_current_time()
    return render_template("main.html", data=returnData, render_time=render_time, render_times=render_times)




if __name__ == "__main__":
    app.run()
