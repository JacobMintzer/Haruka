import asyncio
import datetime
import io

import discord
import pytz
import yaml
from discord.ext import commands

from .utilities import checks, utils


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.starboardQueue = self.bot.config["sbq"]

	async def shutdown(self, ctx):
		pass

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		print("I joined the guild: {0}".format(str(guild)))

	def genStarboardPost(self, message):
		embd = discord.Embed()
		embd = embd.set_thumbnail(url=message.author.avatar_url)
		embd.type = "rich"
		embd.timestamp = message.created_at
		embd = embd.add_field(name='Author', value=message.author.mention)
		embd = embd.add_field(name='Channel', value=message.channel.mention)
		if message.clean_content:
			# add zero width space to get rid of the @everyones
			content = message.clean_content.replace("@", "@​")
			if len(content) > 1023:
				content = (content[:1020] + "...")
			embd = embd.add_field(name='Message', value=content, inline=False)
		embd = embd.add_field(
			name='Jump Link', value="[Here](" + message.jump_url + ")")
		embd.color = discord.Color.gold()
		return embd

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		emoji = payload.emoji
		if not(payload.guild_id in self.bot.config["starboard"].keys()):
			return
		if payload.channel_id == self.bot.config["starboard"][payload.guild_id]["channel"]:
			return
		if payload.channel_id in self.bot.config["starboard"][payload.guild_id]["ignore"]:
			return
		if str(emoji) == self.bot.config["starboard"][payload.guild_id]["emote"]:
			messageChannel = self.bot.get_channel(payload.channel_id)
			message = await messageChannel.fetch_message(payload.message_id)
			if message.created_at + datetime.timedelta(days=14) < datetime.datetime.now():
				return
			user = payload.member
			if user.id == message.author.id or user.bot:
				reaction = (list(filter(lambda x: str(
					x.emoji) == self.bot.config["starboard"][message.guild.id]["emote"], message.reactions)))[0]
				try:
					await reaction.remove(message.author)
				except Exception:
					pass
				return
			if message.id in self.starboardQueue:
				return
			reactions = (list(filter(lambda x: str(
				x.emoji) == self.bot.config["starboard"][message.guild.id]["emote"], message.reactions)))
			if len(reactions) < 1:
				return
			if reactions[0].count >= self.bot.config["starboard"][message.guild.id]["count"]:
				ch = message.guild.get_channel(
					self.bot.config["starboard"][message.guild.id]["channel"])
				embd = self.genStarboardPost(message)
				if len(message.attachments) > 0:
					embd.set_image(url=message.attachments[0].url)
				await ch.send(embed=embd)
				self.starboardQueue.append(message.id)
				if len(self.starboardQueue) > 100:
					self.starboardQueue.pop(0)
				self.bot.config["sbq"] = self.starboardQueue
				with open('Resources.yaml', 'w') as outfile:
					yaml.dump(self.bot.config, outfile)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if member.guild.id == self.bot.config["nijiCord"]:
			welcomeCh = self.bot.get_channel(
				self.bot.config["welcomeCh"][str(member.guild.id)])
			rules = self.bot.get_channel(self.bot.config["rulesCh"])
			await welcomeCh.send(self.bot.config["welcome"].format(member.display_name, rules.mention))
		elif str(member.guild.id) in self.bot.config["welcomeCh"].keys():
			welcomeCh = self.bot.get_channel(
				self.bot.config["welcomeCh"][str(member.guild.id)])
			welcomeMsg = self.bot.config["welcomeMsg"][str(member.guild.id)]
			await welcomeCh.send(welcomeMsg.format(member.display_name, member.mention))
		if str(member.guild.id) in self.bot.config["autorole"].keys():
			try:
				autorole = member.guild.get_role(
					self.bot.config["autorole"][str(member.guild.id)])
				await member.add_roles(autorole)
			except Exception:
				print("error adding autorole in {0}".format(member.guild.name))
		for watchedName in self.bot.config["watchList"]:
			if watchedName.lower() in member.name.lower():
				ch = self.bot.get_channel(self.bot.config["modCh"])
				await ch.send("user {2} with `thinkpad` in their name joined {0} with id {1}.".format(member.guild.name, member.id, member.name))
		


def setup(bot):
	bot.add_cog(Events(bot))
