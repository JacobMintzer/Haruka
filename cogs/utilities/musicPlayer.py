import asyncio
import itertools
import os
import sys
import traceback
from functools import partial
from random import shuffle
import datetime

import discord
import mutagen
from async_timeout import timeout
from discord.ext import commands


class MusicPlayer:
	def __init__(self, ctx):
		self.ctx = ctx
		self.bot = ctx.bot
		self._guild = ctx.guild
		self._channel = ctx.channel
		self._cog = ctx.cog
		self.vc = ctx.voice_client
		self.queue = []
		self.randQueue = list(map(lambda x: Song(x), os.listdir("./music/")))
		shuffle(self.randQueue)
		self.next = asyncio.Event()
		self.history = []
		self.np = None  # Now playing message
		self.volume = .5
		self.current = None

		ctx.bot.loop.create_task(self.player_loop())

	async def player_loop(self):
		"""Our main player loop."""

		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			if len(self.vc.channel.voice_states) < 2:
				self.destroy()
			self.next.clear()
			if len(self.queue) > 0:
				song = self.queue.pop(0)
			else:
				song = self.randQueue.pop(0)
				if len(self.randQueue) < 1:
					self.randQueue = list(map(lambda x: Song(x), os.listdir("./music/")))
					shuffle(self.randQueue)

			song.volume = self.volume
			self.current = song
			source = await discord.FFmpegOpusAudio.from_probe(song.fullPath, options="-b:a 96k")
			if self._guild.voice_client:
				self._guild.voice_client.play(
					source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
			else:
				return
			if self.np:
				if (self.np.created_at + datetime.timedelta(hours=2)) > datetime.datetime.now(datetime.timezone.utc):
					await self.np.edit(content=self.getPlaying())
				else:
					self.np = None

			await self.next.wait()

			# Make sure the FFmpeg process is cleaned up.
			source.cleanup()
			self.history.append(self.current)
			if len(self.history) > 10:
				self.history.pop(0)
			self.current = None
			"""
			try:
				# We are no longer playing this song...
				await self.np.delete()
			except discord.HTTPException:
				pass"""

	def destroy(self):
		"""Disconnect and cleanup the player."""
		return self.bot.loop.create_task(self._cog.cleanup(self._guild, self.ctx))

	def update(self):
		self.randQueue = list(map(lambda x: Song(x), os.listdir("./music/")))
		shuffle(self.randQueue)
	
	def getPlaying(self):
		title, artist = self.current.getPlaying()
		current = "[Current]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
			title, artist)
		if len(self.history) > 0:
			title, artist = self.history[-1].getPlaying()
			previous = "[Previous]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
				title, artist)
		else:
			previous = ""
		if len(self.queue) > 0:
			song = self.queue[0]
		else:
			song = self.randQueue[0]
		title, artist = song.getPlaying()
		upcoming = "[Next]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
			title, artist)
		return("```css\n{0}{1}{2}```".format(current, previous, upcoming))

	def remove_dupes(self):
		newQ=[]
		[newQ.append(x) for x in self.queue if x not in newQ]
		self.queue = newQ

class Song:
	def __init__(self, name, source="local"):
		if source == "local":
			self.source = source
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
		return obj.fullPath == self.fullPath

	def __ne__(self, obj):
		return not (obj.fullPath == self.fullPath)

	def getPlaying(self):
		songInfo = self.getInfo()
		artist = ""
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
		artist = ""
		if "artist-en" in info.keys():
			artist = info["artist-en"]
		elif "artist" in info:
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
