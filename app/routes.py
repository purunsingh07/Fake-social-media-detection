from flask import render_template,jsonify, request
import requests
from . import app
from flask import send_from_directory


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/reports')
def reports():
    return render_template('reports.html')


@app.route('/<path:username>/<path:profile_name>/<path:filename>')
def serve_json(username, profile_name, filename):
    directory = f'../{username}/{profile_name}'
    try:
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        abort(404)

@app.route('/cyber')
def cyber():
    return render_template('cyber.html')


@app.route('/cyberreport')
def cyberreport():
    return render_template('cyberreport.html')

@app.route('/cyberhistory')
def cyberhistory():
    return render_template('cyberhistory.html')




# @app.route('/multipledata', methods=['POST'])
# def multiple_data():
#     data = request.form.to_dict()  # Access form data
#     print("Received Data:", data)
#     return render_template('multipledata.html')




