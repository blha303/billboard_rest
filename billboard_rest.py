#!/usr/bin/env python2
# MIT license, by Steven Smith (blha303)

from billboard import ChartData
from flask import Flask, jsonify, make_response, redirect, url_for, request, current_app, render_template
from werkzeug import secure_filename
from json import loads, load, dump
from time import time
import os
from datetime import timedelta
from functools import update_wrapper

app = Flask(__name__)
REDIR = None


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


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
@crossdomain(origin='*')
def index():
    """ Lists available endpoints """
    return jsonify({
        "endpoints": {
            rule.rule: {
                "docs": globals()[rule.endpoint].__doc__,
                "example": rule.rule.replace("<chart>", "hot-100").replace("<date>", "2016-04-02").replace("<id>", "1")
            } for rule in app.url_map.iter_rules() if rule.endpoint != "static"
        },
        "source": "https://github.com/blha303/billboard_rest",
        "license": "MIT"
    })

@app.route("/chart/<chart>/")
@crossdomain(origin='*')
def chart(chart):
    """ Redirects to /chart/<chart>/<latest date>/ """
    global REDIR
    if (REDIR and time()-REDIR[0] > 3600) or not REDIR:
        REDIR = [time(), ChartData(chart)]
    _ = cache_write(chart, REDIR[1].date, loads(REDIR[1].to_JSON()))
    return redirect(url_for("chart_date", chart=chart, date=REDIR[1].date))

@app.route("/chart/<chart>/date/<date>/")
@crossdomain(origin='*')
def chart_date(chart, date):
    """ Returns json for given chart directly from billboard.py """
    data = cache_get(chart, date)
    if len(data["entries"]) == 0:
        return make_response(
               jsonify({"error": "Invalid chart name (try hot-100), or date missing (try /chart/<chart>/)"}), 404
               )
    return jsonify(data)

#@app.route("/chart/<chart>/date/<date>/iframe")
#def chart_iframe(chart, date):
#    """ Returns a html list of iframes for all spotify links in the chart """
#    data = cache_get(chart, date)
#    return render_template("iframes.html", entries=data["entries"])

@app.route("/chart/<chart>/date/<date>/id/<id>/")
@crossdomain(origin='*')
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

@app.route("/chart/<chart>/date/<date>/id/<id>/listen")
@crossdomain(origin='*')
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
