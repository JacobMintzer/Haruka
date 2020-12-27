from .song import Song
import mutagen

class LocalSong(Song):
	def __init__(self, name):
		self.source = "local"
		self.fullPath = "./music/{0}".format(name)
		self.name = name.replace(".mp3", "")


	def __str__(self):
		songInfo = self.getInfo()
		if "title-jp" in songInfo.keys():
			title = "EN:{0}\n\tJP:{1}".format(
				self.name, songInfo["title-jp"])
		else:
			title = title.format(self.name)
		jp = None
		en = None
		if "artist-jp" in songInfo.keys():
			jp = songInfo["artist-jp"]
		if "artist-en" in songInfo.keys():
			en = songInfo["artist-en"]
		if jp is None:
			if "artist" in songInfo.keys():
				jp = songInfo["artist"]
		if en is None:
			if "artist" in songInfo.keys():
				en = songInfo["artist"]
		if jp == en:
			if jp == None:
				artist = songInfo["artist"]
			artist = jp
		elif jp != None and en != None:
			artist = "JP: {0}\n\tEN:{1}".format(en, jp)
		return "```css\nCurrent:\n[Title]: {0}\n[Artist]: {1}```".format(title, artist)

	def __eq__(self, obj):
		return super().__eq__(obj) and obj.fullPath == self.fullPath

	def __ne__(self, obj):
		return super().__ne__(obj) and not (obj.fullPath == self.fullPath)

	def getPlaying(self):
		songInfo = self.getInfo()
		if "title-jp" in songInfo.keys():
			title = "EN:{0}\n\t\tJP:{1}".format(
				self.name, songInfo["title-jp"])
		else:
			title = self.name
		jp = None
		en = None
		if "artist" in songInfo.keys():
			artist = songInfo["artist"]
		if "artist-jp" in songInfo.keys():
			jp = songInfo["artist-jp"]
		if "artist-en" in songInfo.keys():
			en = songInfo["artist-en"]
		if jp is None:
			if "artist" in songInfo.keys():
				jp = songInfo["artist"]
		if en is None:
			if "artist" in songInfo.keys():
				en = songInfo["artist"]
		if jp == en:
			if not(jp is None):
				artist = jp
		elif jp != None and en != None:
			artist = "JP: {0}\n\t\tEN:{1}".format(en, jp)
		return title, artist

	def getQueueInfo(self):
		title = self.name
		info = self.getInfo()
		if "artist-en" in info.keys():
			artist = info["artist-en"]
		else:
			artist = info["artist"]
		return title, artist

	def getInfo(self):
		data = mutagen.File(self.fullPath)
		songInfo = {}
		if "TIT2" in data.keys():
			songInfo["title"] = str(data["TIT2"])
		if "TXXX:title_en" in data.keys():
			songInfo["title-en"] = self.name
		if "TXXX:title_jp" in data.keys():
			songInfo["title-jp"] = str(data["TXXX:title_jp"])
		if "TPE1" in data.keys():
			songInfo["artist"] = str(data["TPE1"])
		if "TXXX:artist_en" in data.keys():
			songInfo["artist-en"] = str(data["TXXX:artist_en"])
		if "TXXX:artist_jp" in data.keys():
			songInfo["artist-jp"] = str(data["TXXX:artist_jp"])
		return songInfo
