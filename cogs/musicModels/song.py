

class Song:

	name=""
	fullPath=""
	source=None

	def __init__(self, name, source="local"):
		raise NotImplementedError



	def __str__(self):
		raise NotImplementedError

	def __eq__(self, obj):
		return self.source == obj.source

	def __ne__(self, obj):
		return not (obj.fullPath == self.fullPath)

	def getPlaying(self):
		return self.name, self.fullPath

	def getQueueInfo(self):
		return self.name, self.fullPath

	def getInfo(self):
		raise NotImplementedError
