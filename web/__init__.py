from flask import Flask, render_template
from threading import Thread
from waitress import serve

# ============ Flask functions ============
""" Init a web application, can be used to keep your bot alive with uptime services """

appFlask = Flask(__name__)

@appFlask.route('/')
def home():
    return render_template('index.html')

def run():
    serve(appFlask, port=10000)

def keep_alive():
    thread = Thread(target=run)
    print('Start Flask seperated from the bot')
    thread.start()
