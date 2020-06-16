import sys
import logging
import requests
import time
import discord
from discord.ext import commands
import importlib
import asyncio
import re
import random
import os
import io
import json
import datetime
import pytz
from cogs.utilities import MessageHandler, Utils, Checks
import atexit

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
	filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
	'%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix=[
                   '$'], description="I may just be a bot, but I really do love my big sister Kanata! For questions about Haruka please visit 'https://discord​​.gg/qp7nuPC' or DM `Junior Mints#2525`", case_insensitive=True)

cogList = ['cogs.Music', 'cogs.Administration', 'cogs.Fun',
           'cogs.GuildFunctions', 'cogs.events', 'cogs.setup']
with open('Resources.json', 'r') as file_object:
	bot.config = json.load(file_object)
bot.messageHandler = MessageHandler.MessageHandler(bot.config, bot)


async def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		print("You do not have permission to do this. This incident will be reported.")
		return False
	except Exception as e:
		print(e)
		return False


def is_me():
	def predicate(ctx):
		return ctx.message.author.id == ctx.bot.config["owner"]
	return commands.check(predicate)


def is_admin_enabled():
	def predicate(ctx):
		return ctx.message.guild.id in ctx.bot.config["modEnabled"]
	return commands.check(predicate)


@bot.check
def check_enabled(ctx):
	if ctx.message.guild is None:
		return True
	if ctx.message.guild.id in bot.config["enabled"]:
		return True
	return False


@bot.event
async def on_ready():
	for cog in cogList:
		bot.load_extension(cog)
	await bot.change_presence(activity=discord.Game("Making lunch for Kanata!", type=1))
	await bot.messageHandler.initRoles(bot)
	guild = bot.get_guild(bot.config["nijiCord"])
	bot.allRoles = guild.roles
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	guildList = ""
	totalUsers = 0
	for guild in bot.guilds:
		guildList = guildList + guild.name + ", "
		totalUsers += guild.member_count
	print("Currently in the current guilds: {0} with a total userbase of {1}".format(
		guildList, totalUsers))


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, KeyboardInterrupt):
		print("is keyboard interrupt")
		await shutdown()
	ignored = (commands.CommandNotFound, commands.UserInputError)
	if hasattr(ctx.command, 'on_error'):
		print(error)
		return
	if isinstance(error, ignored):
		return
	print("error in {0}".format(str(ctx.guild)))
	try:
		logger.error("Error in {0} with message {1}".format(
			str(ctx.guild), str(ctx.message.clean_content)))
	except:
		logger.error(
			"Message that caused error either doesn't exist or can't be found")
	raise (error)


async def shutdown():
	print("shutting down messagehandler")
	bot.messageHandler.disconnect()
	print("shutting down music cog")
	music = bot.get_cog("Music")
	await music.kill()
	print("killed music cog")
	for cog in cogList:
		print("shutting down {0}".format(cog))
		bot.unload_extension(cog)
		print("shut down {0}".format(cog))
	print("shutdown complete")
	x = bot.logout()
	print("logging out")
	await x


@Checks.is_me()
@bot.command(hidden=True)
async def softReset(ctx, *, selectedCogs=None):
	await bot.change_presence(activity=discord.Game("Quickly doing a soft-reset for a minor update, will be back up soon!", type=1))
	if selectedCogs is None:
		msg = True
		cogs = cogList
		selectedCogs = ""
	elif "messageHandler" in selectedCogs:
		cogs = selectedCogs.split(" ")
		cogs.remove("messageHandler")
		msg = True
	else:
		cogs = selectedCogs.split(" ")
		msg = False
	if msg:
		bot.messageHandler.disconnect()
	music = bot.get_cog("cogs.Music")
	if "cogs.Music" in selectedCogs or "Music" in selectedCogs:
		try:
			await music.kill()
		except:
			print("no music service active")
	print("about to unload cogs")
	for cog in cogs:
		try:
			bot.unload_extension("cogs." + cog.replace("cogs.", ""))
		except Exception as e:
			print("cannot unload cog {0}".format(cog))
	print("cogs unloaded, reloading everything now")

	with open('Resources.json', 'r') as file_object:
		bot.config = json.load(file_object)
	if msg:
		importlib.reload(MessageHandler)
		bot.messageHandler = MessageHandler.MessageHandler(bot.config, bot)

	for cog in cogs:
		try:
			bot.load_extension("cogs." + cog.replace("cogs.", ""))
		except Exception as e:
			await ctx.send("WARNING: cog {0} was not successfully reloaded for reason:\n`{1}`".format(cog, str(e)))
	if msg:
		try:
			await bot.messageHandler.initRoles(bot)
		except Exception as e:
			await ctx.send("WARNING: MessageHandler was not successfully reloaded for reason {0}".format(str(e)))
	guild = bot.get_guild(bot.config["nijiCord"])
	bot.allRoles = guild.roles
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	guildList = ""
	totalUsers = 0
	for guild in bot.guilds:
		guildList = guildList + guild.name + ", "
		totalUsers += guild.member_count
	print("Currently in the current guilds: {0} with a total userbase of {1}".format(
		guildList, totalUsers))
	await bot.change_presence(activity=discord.Game("Making lunch for Kanata!", type=1))
	rxn = Utils.getRandEmoji(bot.emojis, "hug")
	await ctx.message.add_reaction(rxn)


@Checks.is_me()
@bot.command(hidden=True)
async def kill(ctx):
	print("shutting down messagehandler")
	bot.messageHandler.disconnect()
	print("shutting down music cog")
	music = bot.get_cog("Music")
	await music.kill()
	print("killed music cog")
	for cog in cogList:
		print("shutting down {0}".format(cog))
		bot.unload_extension(cog)
		print("shut down {0}".format(cog))
	print("shutdown complete")
	x = bot.logout()
	print("logging out")
	await x


@bot.event
async def on_message(message):
	await bot.messageHandler.handleMessage(message, bot)
	return


@bot.command(hidden=True)
@commands.check(is_admin)
async def s(ctx, *, msg=""):
	fileList = [discord.File(io.BytesIO(await x.read(use_cached=True)), filename=x.filename) for x in ctx.message.attachments]
	await ctx.send(msg, files=fileList)
	await ctx.message.delete()


@bot.command()
async def git(ctx):
	"""Link to Haruka's source code, and information related to the development"""
	await ctx.send("Haruka was developed by Junior Mints#2525 and you can deliver any questions or comments to him. You can find the source code at https://github.com/JacobMintzer/Haruka \nIf you have any questions about it, feel free to message Junior Mints, or submit a pull request if you have any improvements you can make.")


with open("token.txt", "r") as file_object:
	bot.run(file_object.read().strip())
