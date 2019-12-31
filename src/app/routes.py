from flask import render_template, jsonify
from app import app
# from main import Analysis

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")





