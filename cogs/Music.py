import asyncio
import discord
from discord.ext import commands
import re
import random
import os
import time
import datetime
from random import shuffle
import sys
import mutagen
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sqlite3
import json
import pandas as pd
from .utilities import Utils

class Music(commands.Cog):

	def __init__(self,bot):
		self.bot=bot
		self.mode="../Haruka/music/"
		self.artist="none"
		self.songList=os.listdir(self.mode)
		self.songList=sorted(self.songList, key=str.casefold)
		self.songs=['```']
		for song in self.songList:
			if len(self.songs[-1])>1800:
				self.songs[-1]+='```'
				self.songs.append('```')
			if '.mp3' in song:
				self.songs[-1]+=song.replace('.mp3','')
				self.songs[-1]+='\n'
		self.songs[-1]+='```'
		self.current="nothing"
		self.message=0
		self.requests=[]
		self.config=json.load(open('Resources.json'))

	@commands.command(hidden=True)
	async def update(self,ctx):
		"""Sometimes I forget when I learn new songs~"""
		self.songList=os.listdir(self.mode)
		self.songList.sort()
		self.songs=['```']
		for song in self.songList:
			if len(self.songs[-1])>1800:
				self.songs[-1]+='```'
				self.songs.append('```')
			if '.mp3' in song:
				self.songs[-1]+=song.replace('.mp3','')
				self.songs[-1]+='\n'
		self.songs[-1]+='```'


	async def status(self,ctx):
		data=mutagen.File(self.mode+self.current)
		title=self.current
		if "TPE1" in data.keys():
	                artist=str(data["TPE1"])
		elif "TXXX:artist_en" in data.keys():
			artist=str(data["TXXX:artist_en"])
		elif "TXXX:artist_jp" in data.keys():
			artist=str(data["TXXX:artist_jp"])
		else:
			artist="artist unknown, pm junior mints to add one"
		await ctx.bot.change_presence(activity = discord.Game(title.replace(".mp3", "" )+" by "+artist,type=1))


	def get_vc(self,ctx,channel):
		for ch in ctx.guild.voice_channels:
			if ch.id==channel:
				return ch

	async def play(self,ctx):
		bot=ctx.bot
		await bot.wait_until_ready()
		ch=self.get_vc(ctx,int(self.config["musicCh"]))
		self.voice = await ch.connect()
		songs=self.shuff()
		if len(self.requests)>0:
			self.current=self.requests.pop(0)
		else:
			self.current=songs.pop(0)
		player=self.voice.play(discord.FFmpegPCMAudio(self.mode+self.current,options="-q:a 7"))
		await self.status(ctx)
		#player.start()
		while True:
			if self.message==-1: #stop command
				await bot.change_presence(activity = discord.Game("Making lunch for Kanata!",type=1))
				await self.voice.disconnect()
				break
			elif self.message==5: #skip song
				self.message=1
				self.voice.stop()
				if len(songs)<1:
					songs=self.shuff()
				if len(self.requests)>0:
					self.current=self.requests.pop(0)
				else:
					self.current=songs.pop(0)
					if ".mp3" not in self.current:
						self.current=songs.pop(0)
				await self.status(ctx)
				self.voice.play(discord.FFmpegPCMAudio(self.mode+self.current,options="-q:a 7"))
			elif self.voice.is_playing():
				#print("is playing")
				await asyncio.sleep(4)
			else:
				if len(songs)<1:
					songs=self.shuff()
				if len(self.requests)>0:
					self.current=self.requests.pop(0)
				else:
					self.current=songs.pop(0)
					if ".mp3" not in self.current:
						self.current=songs.pop(0)
				await self.status(ctx)
				self.voice.play(discord.FFmpegPCMAudio(self.mode+self.current,options="-q:a 7"))



	def shuff(self):
		if self.artist=="M":
			with open ("playlist/muse.txt") as f:
				songList=f.readlines()
			songList=[x.strip() for x in songList]
		elif self.artist=="A":
			with open ("playlist/Aqours.txt") as f:
				songList=f.readlines()
			songList=[x.strip() for x in songList]
		else:
			songList=os.listdir(self.mode)
			self.artist="none"
		shuffle(songList)
		return songList

	@commands.command(no_pm=True)
	async def skip(self,ctx):
		"""If you want me to play another song"""
		self.message=5


	@commands.command(no_pm=True)
	async def stop(self,ctx):
		"""stops music"""
		self.message=-1

	@commands.command(no_pm=True)
	async def music(self,ctx):
		"""Let's start the music!"""
		msg=ctx.message.content.replace("!music ","")
		if msg.lower()=="muse" or msg.lower()=="u\'s" or "μ" in msg.lower():
			self.artist="M"
		elif msg.lower()=="aqours":
			self.artist="A"
		else:
			self.artist="none"
		if msg.lower()=="aquors":
			await ctx.send("never heard of them")
		if self.message!=2:
			self.message=1
			self.bot.loop.create_task(self.play(ctx))


	@commands.command()
	async def playing(self,ctx):
		"""I tell you the song I am singing"""
		data=mutagen.File(self.mode+self.current)
		title="\n[Title]: "
		if "TIT2" in data.keys():
			title+=str(data["TIT2"])
			title+="\n"
		if "TXXX:title_en" in data.keys():
			title+="\tEN: "
			title+=str(data["TXXX:title_en"])
			title+="\n"
		if "TXXX:title_jp" in data.keys():
			title+="\tJP: "
			title+=str(data["TXXX:title_jp"])
			title+="\n"
		artist="[Artist]: "
		if "TPE1" in data.keys():
			artist+=str(data["TPE1"])
			artist+=" \n"
		if "TXXX:artist_en" in data.keys():
			artist+="\tEN: "
			artist+=str(data["TXXX:artist_en"])
			artist+="\n"
		if "TXXX:artist_jp" in data.keys():
			artist+="\tJP: "
			artist+=str(data["TXXX:artist_jp"])
			artist+="\n"
		if not("TPE1" in data.keys() or "TXXX:artist_en" in data.keys() or "TXXX:artist_jp" in data.keys()):
			artist="\nArtist unknown, pm junior mints to add one"
		await ctx.send("```css\n[File]: "+self.current+title+artist+"```")


	@commands.command()
	async def queue(self,ctx):
		"""See what songs will play next."""
		requestList="```"
		if len(self.requests)==0:
			requestList=requestList+"Queue is empty"
		else:
			for request in self.requests:
				requestList=requestList+request
				requestList=requestList+"\n"
		requestList=requestList+"```"
		await ctx.send(requestList)


	@commands.command(no_pm=True,pass_context=True)
	async def request(self,ctx,*,msg):
		"""Request Haruka to play a song! If you only know some of the name that's fine, I can figure out what you're looking for!"""
		potential=[]
		#bot.send_typing(ctx.message.channel)
		if msg.lower()=="gay":
			#ctx.send('adding every love live song ever')
			await ctx.message.add_reaction(Utils.getRandEmoji(ctx.guild, "yay"))
			#await ctx.message.add_reaction(discord.utils.get(ctx.message.guild.emojis, name="mariSuperSmug"))
			for song in self.songList:
				if fuzz.ratio('Garasu no Hanazono'.lower()+'.mp3',song.lower())>95:
					self.requests.append(song)
					return 0
		elif "lesbian" in msg.lower():
			await ctx.message.add_reaction(Utils.getRandEmoji(ctx.guild, "yay"))
			for song in self.songList:
				if fuzz.ratio('Zurui yo Magnetic today.mp3'.lower(),song.lower())>95:
					self.requests.append(song)
					return 0
		else:
			for song in self.songList:
				if fuzz.ratio(msg.lower()+'.mp3',song.lower())>95:
					self.requests.append(song)
					#yield from bot.say("added")
					await ctx.message.add_reaction(Utils.getRandEmoji(ctx.guild, "yay"))
					return 0
				elif fuzz.partial_ratio(msg.lower(),song.lower())>85:
					potential.append(song)
			if len(potential)==0:
				await ctx.send("Song not found, check your spelling or dm junior mints to add the song.")
			elif len(potential)==1:
				#yield from bot.say("added")
				await ctx.message.add_reaction(Utils.getRandEmoji(ctx.guild, "yay"))
				self.requests.append(potential[0])
			else:
				response="```These are potential matches, try being more specific with the name."
				x=0
				for song in potential:
					response+='\n'
					response+=song
				response+='```'
				await ctx.send(response)

	@commands.command(pass_context=True)
	async def list(self,ctx):
		"""I can message you all the songs I know."""
		for songName in self.songs:
			await ctx.message.author.send(songName)
		await ctx.message.author.send("If there are any songs that should be here, please DM Junior Mints#2525")

def setup(bot):
	bot.add_cog(Music(bot))
