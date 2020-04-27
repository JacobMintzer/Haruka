import sys
import logging
import requests
import time
import discord
from discord.ext import commands
import asyncio
import re
import random
import os
import io
import json
import datetime
import pytz
from cogs.utilities import MessageHandler,Utils
from saucenao import SauceNao


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix=['$'], description='I may just be a bot, but I really do love my big sister Kanata!')

cogList=['cogs.Music','cogs.Administration', 'cogs.Fun','cogs.GuildFunctions']
with open('Resources.json', 'r') as file_object:
	bot.config=json.load(file_object)
bot.messageHandler=MessageHandler.MessageHandler(bot.config,bot)
bot.asar=bot.config["asar"]

async def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		await ctx.send("You do not have permission to do this. This incident will be reported.")
		return False
	except Exception as e:
		print(e)
		return False
@bot.event
async def on_ready():
	for cog in cogList:
		bot.load_extension(cog)
	await bot.change_presence(activity = discord.Game("Making lunch for Kanata!", type=1))
	await bot.messageHandler.initRoles(bot)
	guild = bot.get_guild(bot.config["nijiCord"])
	bot.allRoles = guild.roles
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	guildList=""
	totalUsers=0
	for guild in bot.guilds:
		guildList=guildList+guild.name+", "
		totalUsers+=guild.member_count
	print("Currently in the current guilds: {0} with a total userbase of {1}".format(guildList,totalUsers))


@bot.event
async def on_member_join(member):
	if member.guild.id!=bot.config["nijiCord"]:
		return
	welcomeCh = bot.get_channel(bot.config["welcomeCh"])
	rules = bot.get_channel(bot.config["rulesCh"])
	await welcomeCh.send(bot.config["welcome"].format(member.display_name, rules.mention))


@bot.event
async def on_message(message):
	await bot.messageHandler.handleMessage(message,bot)
	return

def inBotMod(msg):
	return msg.channel.id==bot.config["ModBotCH"]

@bot.command(hidden=True)
@commands.check(is_admin)
async def uwu(ctx):
	await ctx.message.add_reac
	
@bot.command(hidden=True)
@commands.check(is_admin)
async def s(ctx,*,msg=""):
	fileList=[discord.File(io.BytesIO(await x.read(use_cached=True)),filename=x.filename) for x in ctx.message.attachments]
	await ctx.send(msg,files=fileList)
	await ctx.message.delete()



@bot.command()
async def git(ctx):
	"""Link to Haruka's source code, and information related to the development"""
	await ctx.send("Haruka was developed by Junior Mints#2525 and you can deliver any questions or comments to him. You can find the source code at https://github.com/JacobMintzer/Haruka \nIf you have any questions about it, feel free to message Junior Mints, or submit a pull request if you have any improvements you can make.")

@bot.command()
async def source(ctx, url: str=""):
	"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
	await sauce(ctx,url)

@bot.command()
async def sauce(ctx, url: str=""):
	"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
	async with ctx.typing():
		try:
			if (len(ctx.message.attachments)>0):
				url=ctx.message.attachments[0].url
			file="image."+url.split('.')[-1]
			if (os.path.exists(file)):
				os.remove(file)
			request=requests.get(url,allow_redirects=True)
			print (file)
			open(file,'wb').write(request.content)
		except:
			await ctx.send("error downloading file")
			return
		#print ("uwu")
		foundSauce=""
		output=SauceNao(directory='./', api_key=bot.config["sauce"])
		result=output.check_file(file_name=file)
		#print (result)
		if (len(result)<1):
			await ctx.send("no source found")
			return
		for source in result:
			if (float(source["header"]["similarity"])<90):
				break
			if "Pixiv ID" in source["data"]["content"][0]:
				await ctx.send("I believe the source is:\nhttps://www.pixiv.net/en/artworks/"+source["data"]["content"][0].split("Pixiv ID: ")[1].split("\n")[0])
				return
			elif "Source: Pixiv" in source["data"]["content"][0]:
				stuff=source["data"]["content"][0].split("\n")[0]
				#print (stuff)
				id=stuff.split("Source: Pixiv #")[1]
				await ctx.send("I believe the source is:\nhttps://www.pixiv.net/en/artworks/"+id)
				return
			elif "dA ID" in source["data"]["content"][0]:
				foundSauce=("I believe the source is:\nhttps://deviantart.com/view/"+source["data"]["content"][0].split("dA ID: ")[1].split("\n")[0])
			elif "Seiga ID:" in source["data"]["content"][0]:
				foundSauce=("I believe the source is:\nhttps://seiga.nicovideo.jp/seiga/im"+source["data"]["content"][0].split("Seiga ID: ")[1].split("\n")[0])
		if (foundSauce!=""):
			await ctx.send(foundSauce)
			return
		if len(result[0]["data"]["ext_urls"])>0:
			#print(result[0]["data"]["content"][0])
			await ctx.send("I couldn't find the exact link, but this might help you find it:\n"+"\n".join(result[0]["data"]["ext_urls"]))
			return
		await ctx.send("sorry, I'm not sure what the source for this is.")



with open("token.txt","r") as file_object:
	bot.run(file_object.read().strip())

