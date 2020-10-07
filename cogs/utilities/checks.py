
import discord
from discord.ext import commands


def is_niji():
	async def predicate(ctx):
		if ctx.message.guild is None:
			return False
		if ctx.message.guild.id == ctx.bot.config["nijiCord"]:
			return True
		else:
			return False
	return commands.check(predicate)


def is_admin():
	async def predicate(ctx):
		try:
			if ctx.author.permissions_in(ctx.message.channel).administrator:
				return True
			else:
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
				return False
		except Exception as e:
			print(e)
			return False
	return commands.check(predicate)

def isMusicEnabled():
	async def predicate(ctx):
		try:
			if ctx.message.guild is None:
				return False
			if ctx.message.guild.id in ctx.bot.config["musicEnabled"]:
				return True
			else:
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
