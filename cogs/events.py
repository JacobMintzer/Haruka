import asyncio
import discord
import datetime
import io
import pytz
from discord.ext import commands
from .utilities import utils, checks


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.starboardQueue = []

	async def shutdown(self, ctx):
		pass

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		print("I joined the guild: {0}".format(str(guild)))

	def genStarboardPost(self, message):
		embd = discord.Embed()
		embd = embd.set_thumbnail(url=message.author.avatar_url)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd = embd.add_field(name='Author', value=message.author.mention)
		embd = embd.add_field(name='Channel', value=message.channel.mention)
		if message.clean_content:
			# add zero width space to get rid of the @everyones
			content = message.clean_content.replace("@", "@​")
			embd = embd.add_field(name='Message', value=content, inline=False)
		embd = embd.add_field(
			name='Jump Link', value="[Here](" + message.jump_url + ")")
		embd.color = discord.Color.gold()
		return embd

	@commands.Cog.listener()
	async def on_reaction_add(self, reaction, user):
		if not(reaction.message.guild.id in self.bot.config["starboard"].keys()):
			return
		if reaction.message.channel.id == self.bot.config["starboard"][reaction.message.guild.id]["channel"]:
			return
		if reaction.message.channel.id in self.bot.config["starboard"][reaction.message.guild.id]["ignore"]:
			return
		if str(reaction.emoji) == self.bot.config["starboard"][reaction.message.guild.id]["emote"]:
			if user.id == reaction.message.author.id or user.bot:
				try:
					await reaction.remove(reaction.message.author)
				except Exception:
					pass
				return
			if reaction.message.id in self.starboardQueue:
				return
			reactions = (list(filter(lambda x: str(
				x.emoji) == self.bot.config["starboard"][reaction.message.guild.id]["emote"], reaction.message.reactions)))
			if len(reactions) < 1:
				return
			if reactions[0].count >= self.bot.config["starboard"][reaction.message.guild.id]["count"]:
				ch = reaction.message.guild.get_channel(
					self.bot.config["starboard"][reaction.message.guild.id]["channel"])
				self.starboardQueue.append(reaction.message.id)
				embd = self.genStarboardPost(reaction.message)
				if len(reaction.message.attachments) > 0:
					embd.set_image(url=reaction.message.attachments[0].url)
				await ch.send(embed=embd)
			else:
				print("not enough @ {0}".format((list(filter(lambda x: str(
                                    x.emoji) == self.bot.config["starboard"][reaction.message.guild.id]["emote"], reaction.message.reactions)))))

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


def setup(bot):
	bot.add_cog(Events(bot))
