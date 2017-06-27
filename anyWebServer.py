from flask import Flask, request, render_template
import requests

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def home():
	dependencies = None
	recommends = None
	if request.method == "POST":
		dependencies = request.form['dependency']
		recommends = requests.get('http://localhost:5000/recommend/' + dependencies).content
	return render_template("index.html", dependencies=dependencies, recommends=recommends)

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True, port=5001)