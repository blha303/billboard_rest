#!/usr/bin/env python3
# MIT license, by Steven Smith (blha303)

from billboard import ChartData
from flask import Flask, jsonify, make_response, redirect, url_for, request
from werkzeug import secure_filename
from json import loads, load, dump
from time import time
import os

app = Flask(__name__)
REDIR = None

def cache_get(chart, date):
    s_chart, s_date = secure_filename(chart), secure_filename(date)
    if not os.path.exists("cache/{}/".format(s_chart)):
        os.makedirs("cache/{}/".format(s_chart))
    try:
        with open("cache/{}/{}.json".format(s_chart, s_date)) as f:
            data = load(f)
    except FileNotFoundError:
        with open("cache/{}/{}.json".format(s_chart, s_date), "w") as f:
            data = loads(ChartData(chart, date).to_JSON())
            dump(data, f)
    return data

def cache_write(chart, date, data):
    s_chart, s_date = secure_filename(chart), secure_filename(date)
    try:
        with open("cache/{}/{}.json".format(s_chart, s_date), "w") as f:
            dump(data, f)
        return True
    except:
        return False

@app.route("/")
def index():
    """ Lists available endpoints """
    return jsonify({rule.rule: globals()[rule.endpoint].__doc__ for rule in app.url_map.iter_rules() if rule.endpoint != "static"})

@app.route("/chart/<chart>/")
def chart(chart):
    """ Redirects to /chart/<chart>/<latest date>/ """
    global REDIR
    if (REDIR and time()-REDIR[0] > 3600) or not REDIR:
        REDIR = [time(), ChartData(chart)]
    _ = cache_write(chart, REDIR[1].date, loads(REDIR[1].to_JSON()))
    return redirect(url_for("chart_date", chart=chart, date=REDIR[1].date))

@app.route("/chart/<chart>/<date>/")
def chart_date(chart, date):
    """ Returns json for given chart directly from billboard.py """
    data = cache_get(chart, date)
    if len(data["entries"]) == 0:
        return make_response(
               jsonify({"error": "Invalid chart name (try hot-100), or date missing (try /chart/<chart>/)"}), 404
               )
    return jsonify(data)

@app.route("/chart/<chart>/<date>/<id>/")
def chart_item(chart, date, id):
    """ Returns detailed information for given chart, date and rank """
    try:
        id = int(id)-1 if int(id) > 0 else 0
    except ValueError:
        return make_response(
               jsonify({"error": "Invalid ID"}), 400
               )
    data = cache_get(chart, date)
    if not len(data["entries"]) > id:
        return make_response(
               jsonify({"error": "Given ID not available in chart"}), 404
               )
    return jsonify(data["entries"][id])

@app.route("/chart/<chart>/<date>/<id>/listen")
def chart_listen(chart, date, id):
    """ Redirects to the Spotify listen url for the given track ID """
    try:
        id = int(id)-1 if int(id) > 0 else 0
    except ValueError:
        return make_response(
               jsonify({"error": "Invalid ID"}), 400
               )
    data = cache_get(chart, date)
    if not len(data["entries"]) > id:
        return make_response(
               jsonify({"error": "Given ID not available in chart"}), 404
               )
    return redirect(data["entries"][id]["spotifyLink"])

if __name__ == "__main__":
    app.run(debug=True, port=23718)
