from flask import Flask, request, jsonify
from recommend import *
import json

RECOMMENDER = None

HELP = {
	"recommend_query":"http://localhost:5000/recommend?q={package1@version11+package2@version2}",
	"recommend_rest":"http://localhost:5000/recommend/{package1@version11+package2@version2}",
	"remove_package":"http://localhost:5000/delete/{package1@version11}",
	"update_package":{"method":"post","url":"http://localhost:5000/update/"},
	"add_package":{"method":"post","url":"http://localhost:5000/create/"}
}

app = Flask(__name__)

@app.route('/')
def home():
	return jsonify(HELP)

@app.route('/recommend/<query>')
@app.route('/recommend', methods=["GET"])
def recommend(query=None):
	if query:
		givenDependencies = query.split("+")
		response = RECOMMENDER.calculateRecommends(givenDependencies)
		return jsonify(response)
	return str(query)

@app.route('/delete/<package>')
def delete(package=None):
	if package:
		response = RECOMMENDER.remove(package)
		return jsonify(response)
	return str(package)

@app.route('/update', methods=["POST"])
def update():
	response = RECOMMENDER.update(package)
	return jsonify(response)

@app.route('/create', methods=["POST"])
def create():
	response = RECOMMENDER.create(package)
	return jsonify(response)

if __name__ == "__main__":
	RECOMMENDER = Recommender("../npm/data/normalizedVersionDependencyList.json", 0.1, 0.01)
	app.run(host='0.0.0.0', debug=True)