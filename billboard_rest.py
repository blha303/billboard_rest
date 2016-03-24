#!/usr/bin/env python3
# MIT license, by Steven Smith (blha303)

from billboard import ChartData
from flask import Flask, jsonify, make_response, redirect, url_for, request
from json import dumps, loads

app = Flask(__name__)
REDIR = None

@app.route("/")
def index():
    """ Lists available endpoints """
    return jsonify({rule.rule: globals()[rule.endpoint].__doc__ for rule in app.url_map.iter_rules() if rule.endpoint != "static"})

@app.route("/chart/<chart>/")
def chart(chart):
    """ Redirects to /chart/<chart>/<latest date>/ """
    global REDIR
    REDIR = ChartData(chart)
    return redirect(url_for("chart_date", chart=chart, date=REDIR.date))

@app.route("/chart/<chart>/<date>/")
def chart_date(chart, date=None):
    """ Returns json for given chart directly from billboard.py """
    global REDIR
    if REDIR:
        data = REDIR
        REDIR = None
    else:
        data = ChartData(chart, date)
    if len(data) == 0:
        return make_response(
               jsonify({"error": "Invalid chart name (try hot-100)"}), 404
               )
    return jsonify(loads(data.to_JSON()))

@app.route("/chart/<chart>/<date>/<id>/")
def chart_item(chart, date, id):
    """ Returns detailed information for given chart, date and rank """
    try:
        id = int(id)-1 if int(id) > 0 else 0
    except ValueError:
        return make_response(
               jsonify({"error": "Invalid ID"}), 400
               )
    data = ChartData(chart, date)
    if not len(data) > id:
        return make_response(
               jsonify({"error": "Given ID not available in chart"}), 404
               )
    return jsonify(loads(data[id].to_JSON()))

@app.route("/chart/<chart>/<date>/<id>/listen")
def chart_listen(chart, date, id):
    """ Returns the Spotify listen link for the given song, with a redirect if ?redirect is specified """
    try:
        id = int(id)-1 if int(id) > 0 else 0
    except ValueError:
        return make_response(
               jsonify({"error": "Invalid ID"}), 400
               )
    data = ChartData(chart, date)
    if not len(data) > id:
        return make_response(
               jsonify({"error": "Given ID not available in chart"}), 404
               )
    if "redirect" in request.args:
        return redirect(loads(data[id].to_JSON())["spotifyLink"])
    else:
        return jsonify({"listen": loads(data[id].to_JSON())["spotifyLink"]})

if __name__ == "__main__":
    app.run(debug=True, port=23718)
