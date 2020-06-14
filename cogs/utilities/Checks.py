
import discord
from discord.ext import commands

def is_niji():
	def predicate(ctx):
		if ctx.message.guild is None:
			return False
		return ctx.message.guild.id == ctx.bot.config["nijiCord"]
	return commands.check(predicate)
	
def is_admin():
	def predicate(ctx):
		try:
			if ctx.author.permissions_in(ctx.message.channel).administrator:
				return True
			return False
		except Exception as e:
			print(e)
			return False
	return commands.check(predicate)	

def isScoreEnabled():
	def predicate(ctx):
		try:
			if ctx.message.guild is None:
				return False
			return ctx.message.guild.id in ctx.bot.config["scoreEnabled"]
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