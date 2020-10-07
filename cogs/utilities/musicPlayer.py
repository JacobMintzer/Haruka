import discord
from discord.ext import commands

import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
import mutagen
from random import shuffle
import os


class MusicPlayer:
	def __init__(self, ctx):
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
			if len(self.vc.channel.voice_states)<2:
				self.destroy(self._guild)
			
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
			self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
			# self.np = await self._channel.send(f'**Now Playing:** `{song.title}` requested by `{source.requester}`')
			await self.next.wait()

			# Make sure the FFmpeg process is cleaned up.
			source.cleanup()
			self.history.append(self.current)
			if len(self.history)>10:
				self.history.pop(0)
			self.current = None
			"""
			try:
				# We are no longer playing this song...
				await self.np.delete()
			except discord.HTTPException:
				pass"""

	def destroy(self, guild):
		"""Disconnect and cleanup the player."""
		return self.bot.loop.create_task(self._cog.cleanup(guild))


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

	def getPlaying(self):
		songInfo = self.getInfo()
		if "title-jp" in songInfo.keys():
			title = "EN:{0}\n\t\tJP:{1}".format(
				self.name, songInfo["title-jp"])
		else:
			title = self.name
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
			artist = "JP: {0}\n\t\tEN:{1}".format(en, jp)
		return title, artist

	def getQueueInfo(self):
		info = self.getInfo()
		if "title-en" in info.keys():
			title = info["title-en"]
		else:
			title = info["title"]
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
			songInfo["title-en"] = str(data["TXXX:title_en"])
		if "TXXX:title_jp" in data.keys():
			songInfo["title-jp"] = str(data["TXXX:title_jp"])
		if "TPE1" in data.keys():
			songInfo["artist"] = str(data["TPE1"])
		if "TXXX:artist_en" in data.keys():
			songInfo["artist-en"] = str(data["TXXX:artist_en"])
		if "TXXX:artist_jp" in data.keys():
			songInfo["artist-jp"] = str(data["TXXX:artist_jp"])
		return songInfo
