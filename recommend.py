import sys
import json
from multiprocessing.pool import ThreadPool

class Recommender():
	def __init__(self, path, minimumSupport=0.3, minimumConfidence=0.5):
		self.ocurrences = {}
		self.packages = self.load(path)
		try:
			with open("ocurrences.json") as ocurrencesFile:
				self.ocurrences = json.load(ocurrencesFile)
		except Exception as e:
			self.initialize()
			with open("ocurrences.json", "w") as ocurrencesFile:
				ocurrencesFile.write(json.dumps(self.ocurrences))
		self.minimumSupport = minimumSupport
		self.minimumConfidence = minimumConfidence

	"""
	Deprecated
	"""
	def doIRecommend(self, givenDependencies, dependencies):
		for givenDependencie in givenDependencies:
			if givenDependencie not in dependencies:
				return False
		return True

	"""
	Deprecated
	"""
	def mergeVersions(package):
		dependencies = []
		split = package.split("@")
		packageName = split[0]
		for item in self.packages:
			itemName = item.split("@")[0]
			if itemName == packageName:
				dependencies.append(self.packages[item]["dependencies"])

	"""
	Deprecated
	"""
	def getVersions(package):
		versions = []
		split = package.split("@")
		packageName = split[0]
		for item in self.packages:
			itemName = item.split("@")[0]
			if itemName == packageName:
				versions.append(item)

	def removeGiven(self, givenDependencies, recommends):
		for givenDependencie in givenDependencies:
			try:
				recommends.remove(givenDependencie)
			except Exception as e:
				pass
		return recommends

	def getPackageNames(self, dependencies):
		packageNames = []
		for dependency in dependencies:
			packageNames.append(dependency.split("@")[0])
		return packageNames

	def getDistinct(self, recommends):
		recommends = set(recommends)
		recommends = list(recommends)
		return recommends

	def getOcurrences(self, package):
		if package in self.ocurrences.keys():
			return self.ocurrences[package]
		ocurrences = []
		expandedSearch = "@" not in package 
		for item in self.packages:
			dependencies = self.packages[item]["dependencies"]
			if expandedSearch:
				dependencies = self.getPackageNames(dependencies)
			if package in dependencies:
				ocurrences.append(item)
		self.ocurrences[package] = ocurrences
		return self.ocurrences[package]

	def getPackages(self, givenDependencies, initialSet=None):
		ocurrencesOfSet = self.getOcurrences(givenDependencies[0])
		if initialSet:
			ocurrencesOfSet = set(ocurrencesOfSet).intersection(initialSet)
		for i in range(1, len(givenDependencies)):
			ocurrences = self.getOcurrences(givenDependencies[i])
			ocurrencesOfSet = set(ocurrencesOfSet).intersection(ocurrences)
		ocurrencesOfSet = list(ocurrencesOfSet)
		return ocurrencesOfSet

	def isExpandedSearch(self, givenDependencies):
		for dependency in givenDependencies:
			if "@" in dependency:
				return False
		return True

	def filterThread(self, recommends, ocurrences):
		print("filtering thread")
		filteredRecommendations = []
		index = 1
		for recommend in recommends:
			recommendOcurrence = self.getPackages([recommend], ocurrences)
			confidence = len(recommendOcurrence) / len(ocurrences)
			if confidence >= self.minimumConfidence:
				print("[" + str(index) + "/" + str(len(recommends)) + "]", "accepted", recommend, confidence)
				filteredRecommendations.append({"package":recommend,"confidence":confidence})
			index += 1
		return filteredRecommendations
		

	def filter(self, recommends, ocurrences):
		filteredRecommendations = []
		portionSize = int(len(recommends)/4)
		pool = ThreadPool(processes=4)
		thread1 = pool.apply_async(self.filterThread, (recommends[:portionSize], ocurrences))
		thread2 = pool.apply_async(self.filterThread, (recommends[portionSize:2*portionSize], ocurrences))
		thread3 = pool.apply_async(self.filterThread, (recommends[2*portionSize:3*portionSize], ocurrences))
		thread4 = pool.apply_async(self.filterThread, (recommends[3*portionSize:], ocurrences))
		filteredRecommendations += thread1.get()
		filteredRecommendations += thread2.get()
		filteredRecommendations += thread3.get()
		filteredRecommendations += thread4.get()
		return filteredRecommendations

	def calculateRecommends(self, givenDependencies):
		print("calculating", givenDependencies)
		recommendations = {}
		recommendations["given"] = givenDependencies
		recommendations["recommends"] = []
		if len(givenDependencies) < 0:
			return recommendations
		ocurrences = self.getPackages(givenDependencies)
		support = len(ocurrences) / len(self.packages.keys())
		print("support", support)
		recommendations["support"] = support
		if support < self.minimumSupport:
			return recommendations
		recommends = []
		print("combining")
		for ocurrence in ocurrences:
			recommends += self.packages[ocurrence]["dependencies"]
		if self.isExpandedSearch(givenDependencies):
			recommends = self.getPackageNames(recommends)
		recommends = self.getDistinct(recommends)
		recommends = self.removeGiven(givenDependencies, recommends)
		recommendations["recommends"] = self.filter(recommends, ocurrences)
		return recommendations

	def load(self, path):
		packages = {}
		with open(path) as dependencyList:
			packages = json.load(dependencyList)
		return packages

	def initialize(self):
		for package in self.packages:
			for dependency in self.packages[package]["dependencies"]:
				dependencyName = dependency.split("@")[0]
				try:
					self.ocurrences[dependency]
				except Exception as e:
					self.ocurrences[dependency] = []
				finally:
					self.ocurrences[dependency].append(package)
				try:
					self.ocurrences[dependencyName]
				except Exception as e:
					self.ocurrences[dependencyName] = []
				finally:
					self.ocurrences[dependencyName].append(package)

	def add(self, package):
		try:
			self.packages[package[package]] = package
			for dependency in package["dependencies"]:
				try:
					self.ocurrences[dependency].append(package[package])
				except Exception as e:
					pass
				try:
					self.ocurrences[dependency.split("@")[0]].append(package[package])
				except Exception as e:
					pass
			return {"status":"ok"}
		except Exception as e:
				return {"status":"fail"}

	def remove(self, package):
		try:
			for dependency in self.packages[package]["dependencies"]:
				try:
					del self.ocurrences[dependency]
				except Exception as e:
					pass
				try:
					del self.ocurrences[dependency.split("@")[0]]
				except Exception as e:
					pass
			del self.packages[package[package]]
			return {"status":"ok"}
		except Exception as e:
			return {"status":"fail"}

	def update(self, package):
		status = self.remove(package)
		if status["status"] == "fail":
			return {"status":"fail"}
		status = self.add(package)
		if status["status"] == "fail":
			return {"status":"fail"}
		return {"status":"ok"}

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("Usage:", sys.argv[0], "<input>")
		sys.exit(1)
	recommender = Recommender(sys.argv[1])
	givenDependencies = ["igraph", "stats"]
	recommends = recommender.calculateRecommends(givenDependencies)
	print(recommends)