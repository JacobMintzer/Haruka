import asyncio
import datetime
import os
import random
import re
import sys
import time
from random import shuffle

import discord
import mutagen
from discord.ext import commands
from rapidfuzz import fuzz, process

from .utilities import checks, utils
from .utilities.musicPlayer import MusicPlayer, Song


class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.players = {}
		self.dir = "../Haruka/music/"
		self.songList = sorted(os.listdir(self.dir), key=str.casefold)
		self.songs = ['```']
		for song in self.songList:
			if len(self.songs[-1]) > 1800:
				self.songs[-1] += '```'
				self.songs.append('```')
			if '.mp3' in song:
				self.songs[-1] += song.replace('.mp3', '')
				self.songs[-1] += '\n'
		self.songs[-1] += '```'

	async def shutdown(self, ctx):
		self.kill()

	def kill(self):
		for guild, player in self.players:
			player.destroy()

	def get_player(self, ctx):
		"""Retrieve the guild player, or generate one."""
		try:
			player = self.players[ctx.guild.id]
		except KeyError:
			player = MusicPlayer(ctx)
			self.players[ctx.guild.id] = player
		return player

	@commands.command(hidden=True)
	@checks.is_me()
	async def update(self, ctx):
		"""Sometimes I forget when I learn new songs~"""
		self.songList = os.listdir(self.dir)
		self.songList.sort()
		self.songs = ['```']
		for song in self.songList:
			if len(self.songs[-1]) > 1800:
				self.songs[-1] += '```'
				self.songs.append('```')
			if '.mp3' in song:
				self.songs[-1] += song.replace('.mp3', '')
				self.songs[-1] += '\n'
		self.songs[-1] += '```'
		for _,player in self.players:
			player.update()

	@commands.command(no_pm=True)
	@checks.isMusicEnabled()
	async def music(self, ctx, *, channel: discord.VoiceChannel = None):
		"""I'll join your channel and start playing music!"""
		if channel is None:
			try:
				channel = ctx.message.author.voice.channel
			except Exception:
				await ctx.send("You must either be in a voice channel I can join, or supply a voice channel.")
				return
		vc = ctx.voice_client
		if vc:
			if vc.channel.id == channel.id:
				return
			try:
				await vc.move_to(channel)
			except asyncio.TimeoutError:
				await ctx.send("Unable to switch to channel: timed out.")
		else:
			try:
				await channel.connect()
			except asyncio.TimeoutError:
				await ctx.send("Unable to join channel: timed out.")
		self.get_player(ctx)

	@commands.command(no_pm=True)
	@checks.isMusicEnabled()
	async def skip(self, ctx):
		"""If you want me to play another song"""
		vc = ctx.voice_client
		if vc.is_paused():
			pass
		elif not vc.is_playing():
			return

		vc.stop()

	@commands.command(no_pm=True)
	@checks.isMusicEnabled()
	async def stop(self, ctx):
		"""stops music"""
		vc = ctx.voice_client
		await self.cleanup(ctx.guild, ctx)

	@commands.command(no_pm=True)
	@checks.isMusicEnabled()
	async def removeDupes(self, ctx):
		player = self.get_player(ctx)
		player.remove_dupes()
		await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay"))

	async def cleanup(self, guild, ctx):
		try:
			await guild.voice_client.disconnect()
		except AttributeError:
			pass
		try:
			del self.players[guild.id]
		except KeyError:
			return await ctx.send('I am not currently playing anything!', delete_after=20)

	@commands.command()
	@checks.isMusicEnabled()
	async def queue(self, ctx):
		"""See what songs will play next."""
		player = self.get_player(ctx)
		msg = ""
		i = 1
		for song in player.queue:
			title, artist = song.getQueueInfo()
			msg = msg + "{0}.\t{1} by {2}\n".format(i, title, artist)
			i += 1
		if i < 10:
			msg = msg + "These songs selected randomly:\n"
			for song in player.randQueue[:11 - i]:
				title, artist = song.getQueueInfo()
				msg = msg + "{0}.\t{1} by {2}\n".format(i, title, artist)
				i += 1
		await ctx.send("```css\n{0}```".format(msg.strip()))

	def getSong(self, player):
		title, artist = player.current.getPlaying()
		current = "[Current]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
			title, artist)
		if len(player.history) > 0:
			title, artist = player.history[-1].getPlaying()
			previous = "[Previous]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
				title, artist)
		else:
			previous = ""
		if len(player.queue) > 0:
			song = player.queue[0]
		else:
			song = player.randQueue[0]
		title, artist = song.getPlaying()
		upcoming = "[Next]:\n\t[Title]:\n\t\t{0}\n\t[Artist]:\n\t\t{1}\n\n".format(
			title, artist)
		return("```css\n{0}{1}{2}```".format(current, previous, upcoming))

	@commands.command()
	@checks.isMusicEnabled()
	async def playing(self, ctx):
		"""Check which song is playing"""
		player = self.get_player(ctx)
		np = await ctx.send(self.getSong(player))
		player.np=np

	@commands.command(aliases=["req"])
	@checks.isMusicEnabled()
	async def request(self, ctx, *, msg):
		"""Request Haruka to play a song! If you only know some of the name that's fine, I can figure out what you're looking for!"""
		player = self.get_player(ctx)
		potential = []
		if msg.lower() == "gay":
			player.queue.append(Song("Garasu no Hanazono.mp3"))
			await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay"))
			return
		elif "lesbian" in msg.lower():
			player.queue.append(Song("Zurui yo Magnetic today.mp3"))
			await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay"))
			return
		elif "fireworks by katy perry" in msg.lower():
			player.queue.append(Song("Tiny Stars.mp3"))
			await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay"))
			return
		else:
			potential = list(filter(lambda song: fuzz.ratio(
				msg.lower(), song.replace(".mp3", "").lower()) > 95, self.songList))
			if len(potential) == 1:
				player.queue.append(Song(potential[0]))
				await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay", ctx))
				return
			if len(potential) < 1:
				potential = list(filter(lambda song: fuzz.partial_ratio(
                                    msg.lower(), song.replace(".mp3", "").lower()) >= 95, self.songList))
				if len(potential) == 1:
					player.queue.append(Song(potential[0]))
					await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay", ctx))
					return
			if len(potential) < 1:
				potential = list(filter(lambda song: fuzz.partial_ratio(
                                    msg.lower(), song.replace(".mp3", "").lower()) >= 85, self.songList))
				if len(potential) == 1:
					player.queue.append(Song(potential[0]))
					await ctx.message.add_reaction(utils.getRandEmoji(ctx.guild.emojis, "yay", ctx))
					return
			if len(potential) == 0:
				await ctx.send("Song not found, check your spelling or dm junior mints to add the song.")
				return
			if len(potential) > 1:
				response = "```These are potential matches, try being more specific with the name."
				for song in potential:
					response += '\n'
					response += song
				response += '```'
				await ctx.send(response)

	@commands.command(pass_context=True)
	async def list(self, ctx):
		"""I can message you all the songs I know."""
		for songName in self.songs:
			await ctx.message.author.send(songName)
		await ctx.message.author.send("If there are any songs that should be here, please DM Junior Mints#2525")

	@commands.command(hidden=True)
	@checks.is_me()
	async def vcstatus(self,ctx):
		await ctx.send(f"currently active in the following {len(self.players.items())} guilds:")
		msg = ""
		for guild_id, musicplayer in self.players.items():
			msg += f"{guild_id} {musicplayer._guild.name}\n"
		if msg:
			await ctx.send (msg)



def setup(bot):
	bot.add_cog(Music(bot))
