
import discord
from discord.ext import commands


def is_niji():
	async def predicate(ctx):
		if ctx.message.guild is None:
			return False
		if ctx.message.guild.id == ctx.bot.config["nijiCord"]:
			return True
		else:
			await ctx.message.channel.send("Sorry, this command is not available to all servers at the moment. If are interested in getting this to work here, please message Junior Mints#2525.")
			return False
	return commands.check(predicate)


def is_admin():
	async def predicate(ctx):
		try:
			if ctx.author.permissions_in(ctx.message.channel).administrator:
				return True
			else:
				await ctx.message.channel.send("This command is only available to an Administrator.")
				return False
		except Exception as e:
			print(e)
			return False
	return commands.check(predicate)


def isScoreEnabled():
	async def predicate(ctx):
		try:
			if ctx.message.guild is None:
				return False
			if ctx.message.guild.id in ctx.bot.config["scoreEnabled"]:
				return True
			else:
				await ctx.message.channel.send("You must enable scoring on this server to use this command. An admin can enable it by using `$score enable`.")
				return False
		except Exception as e:
			print(e)
			return False
	return commands.check(predicate)


def is_me():
	def predicate(ctx):
		return ctx.message.author.id == ctx.bot.config["owner"]
	return commands.check(predicate)


def hasBest():
	def predicate(ctx):
		try:
			if ctx.message.guild is None:
				return False
			return str(ctx.message.guild.id) in ctx.bot.config["best"]
		except Exception as e:
			print(e)
			return False
	return commands.check(predicate)
