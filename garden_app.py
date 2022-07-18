import json
import os
from flask import Flask, request, jsonify, render_template, redirect
import logging
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

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


@app.route("/timezone", methods=["GET"])
def timezone():
    return "2"


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

@app.route("/send", methods=["POST"])
def send_data():

    if request.method == "POST":
        rdata = request.get_json()

        cdata = get_current_data()

        for x in rdata:
            cdata[x] = rdata[x]

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


@app.route("/")
@auth.login_required
def report_status():

    directory_path = os.getcwd()
    logging.warning("my current directory is : {}".format(directory_path))

    returnData = get_current_data()

    return render_template("main.html", data=returnData)




if __name__ == "__main__":
    app.run()
