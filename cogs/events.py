import asyncio
import discord
from discord.ext import commands
from .utilities import utils, checks


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def shutdown(self,ctx):
		pass
	
	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		print("I joined the guild: {0}".format(str(guild)))
		

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
			except:
				print("error adding autorole in {0}".format(member.guild.name))


def setup(bot):
	bot.add_cog(Events(bot))
