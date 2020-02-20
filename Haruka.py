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
import Music
import MessageHandler
from saucenao import SauceNao

bot = commands.Bot(command_prefix=['$'], description='NijigasakiBot')
global deletedMessages
deletedMessages=[]
global target
target=None
global cooldown
cooldown=False
cdTime=127

cogList=['Music']
messageHandler=MessageHandler.MessageHandler()
with open('Resources.json', 'r') as file_object:
	config=json.load(file_object)
asar=config["asar"]

songList=os.listdir("../Haruka/music/")
songList.sort()
"""
if not discord.opus.is_loaded():
        # the 'opus' library here is opus.dll on windows
        # or libopus.so on linux in the current directory
        # you should replace this with the location the
        # opus library is located in and with the proper filename.
        # note that on windows this DLL is automatically provided for you
        discord.opus.load_opus('opus')
"""

def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		return False
	except Exception as e:
		print(e)
		return False
@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
	for cog in cogList:
		bot.load_extension(cog)
	await bot.change_presence(activity = discord.Game("Making lunch for Kanata", type=1))

@bot.event
async def on_member_join(member):
	#print(member)
	welcomeCh = bot.get_channel(config["welcomeCh"])
	rules = bot.get_channel(config["rulesCh"])
	guild = bot.get_guild(config["nijiCord"])
	await welcomeCh.send(config["welcome"].format(member.display_name, rules.mention))
	log=bot.get_channel(config["logCh"])
	baseRole=discord.utils.find(lambda x: x.name == "Idol Club Applicant", guild.roles)
	await member.add_roles(baseRole)
	await log.send(embed=genLog(member,"has joined the server."))

@bot.event
async def on_member_remove(member):
	log=bot.get_channel(config["logCh"])
	await log.send(embed=genLog(member,"has left the server."))

@bot.event
async def on_message_delete(message):
	log=bot.get_channel(config["logCh"])
	fileList=[discord.File(io.BytesIO(await x.read(use_cached=True)),filename=x.filename,spoiler=True) for x in message.attachments]
	await log.send("{0}'s message was deleted from {2}. The message:\n{1}".format(message.author.display_name, message.content, message.channel),files=fileList)

@bot.event
async def on_message(message):
	await messageHandler.handleMessage(message,bot)
	return


def inBotMod(msg):
	return msg.channel.id==config["ModBotCH"]

def genLog(member, what):
	embd=discord.Embed()
	embd.title=member.display_name
	embd.description=what
	embd=embd.set_thumbnail (url=member.avatar_url)
	embd.type="rich"
	embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
	embd=embd.add_field(name = 'Discord Username', value = str(member))
	embd=embd.add_field(name = 'id', value = member.id)
	embd=embd.add_field(name = 'Joined', value = member.joined_at)
	embd=embd.add_field(name = 'Roles', value = ', '.join(map(lambda x: x.name, member.roles)))
	embd=embd.add_field(name = 'AccountCreated', value = member.created_at)
	return embd

def isTarget(msg):
	global target
	if msg.author==target:
		return True
	return False

@bot.command(hidden=True)
@commands.check(is_admin)
async def export(ctx):
	await ctx.send(await messageHandler.getPB())

@bot.command(hidden=True)
@commands.check(is_admin)
async def purge(ctx,*,msgs:int=10):
	rxnMsg=await ctx.send("Are you sure you want to delete the last {0} messages on the server? react {1} to confirm or {2} to cancel.".format(str(msgs),u"\U0001F5D1", "🚫" ))
	await rxnMsg.add_reaction(u"\U0001F5D1")
	await rxnMsg.add_reaction("🚫")
	async with ctx.message.channel.typing():
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				await ctx.message.channel.purge(limit = msgs)
				await ctx.send("purge complete")
			else:
				await ctx.send("cancelling the purge")
		except asyncio.TimeoutError:
			await rxnMsg.delete()

	return

def adminRxn(rxn, user):
	print(rxn.emoji)
	if user.permissions_in(bot.get_channel(config["generalCh"])).administrator and not user.bot:
		if str(rxn.emoji) in [u"\U0001F5D1","🔨","🚫"]:
			return True
	return False

@bot.command(hidden=True)
@commands.check(is_admin)
async def ban(ctx,*,person: discord.Member):
	global target
	while target!=None:
		time.sleep(10)
	rxnMsg=await ctx.send("React {1} to purge {0} and ban then, react 🔨 to only ban them and react 🚫 to cancel".format(str(person),u"\U0001F5D1"))
	async with ctx.message.channel.typing():
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🔨")
		await rxnMsg.add_reaction("🚫")
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				target = person
				for ch in ctx.message.guild.text_channels:
					await ch.purge(check=isTarget)
				target=None
				await ctx.send("purge complete")
				await person.ban()
			elif str(rxn.emoji)=="🔨":
				await person.ban()
			else:
				await ctx.send("cancelling the ban")
		except asyncio.TimeoutError:
			await rxnMsg.delete()
		return


@bot.command(hidden=True)
@commands.check(is_admin)
async def prune(ctx,*,person: discord.Member):
	global target
	while target!=None:
		time.sleep(10)
	rxnMsg=await ctx.send("Are you sure you want to delete all messages in the past 2 weeks by {0}? React {1} to confirm or 🚫 to cancel.".format(str(person),u"\U0001F5D1"))
	async with ctx.message.channel.typing():
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🚫")
		try:
			rxn, user=await bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
			if str(rxn.emoji)==u"\U0001F5D1":
				target = person
				for ch in ctx.message.guild.text_channels:
					await ch.purge(check=isTarget)
				target=None
			elif str(rxn.emoji)=="🚫":
				await ctx.send("cancelling prune")
		except asyncio.TimeoutError:
			await rxnMsg.delete()
		return

@bot.command(hidden=True)
@commands.check(is_admin)
async def blacklist(ctx,*,id):
	print(id)
#@bot.command()
async def uwu(ctx):
	msg=genLog(ctx.message.author,"has left the guild.")
	await ctx.send(embed=msg)


@bot.command()
async def sauce(ctx, url: str=""):
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
	output=SauceNao(directory='./', api_key=config["sauce"])
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

@bot.command()
async def info(ctx, member: discord.Member = None):
	"""$info for information on yourself"""
	if member == None:
		await ctx.send(embed=genLog(ctx.message.author, "Info on {0}".format(ctx.message.author.display_name)))
	else:
		await ctx.send(embed=genLog(member, "info on {0}".format(member.display_name)))

@bot.command()
async def sinfo(ctx):
        """$sinfo if you want me to tell you information about this server"""
        embd=discord.Embed()
        embd.title=ctx.guild.name
        embd.description="information on "+ctx.guild.name
        embd=embd.set_thumbnail (url=ctx.guild.icon_url)
        embd.type="rich"
        embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
        dt = ctx.guild.created_at
        embd=embd.add_field(name = 'Date Created', value = str(dt.date())+" at "+str(dt.time().isoformat('minutes')))
        embd=embd.add_field(name = 'ID', value = ctx.guild.id)
        embd=embd.add_field(name = 'Owner', value = str(ctx.guild.owner))
        embd=embd.add_field(name = 'Total Boosters', value = ctx.guild.premium_subscription_count)
        embd=embd.add_field(name = 'Total Channels', value = len(ctx.guild.channels))
        embd=embd.add_field(name = 'Total Members', value = ctx.guild.member_count)
        await ctx.send(embed=embd)

@bot.command(name="best")
async def best(ctx, *, role):
	"""Show your support for your best girl! Ex. '$best Kanata' will give you the kanata role."""
	roleNames=config["girls"]
	if role.lower()=="girl":
		role="haruka"
	if role.title() not in roleNames:
		await ctx.send("Not a valid role.")
		return
	member = ctx.message.author
	requestedRole = discord.utils.find(lambda x: x.name.lower() == role.lower(), ctx.guild.roles)
	roles = list(filter(lambda x: x.name.title() in roleNames, ctx.guild.roles))
	await member.remove_roles(*roles, atomic=True)
	await member.add_roles(requestedRole)
	if role.lower()=="haruka":
		await ctx.message.add_reaction("❤")
	else:
		await ctx.message.add_reaction("👍")

@bot.command(name="iam")
async def Iam(ctx, arole=''):
	"""Use this command to give a self-assignable role.(usage: $iam groupwatch) For a list of assignable roles, type $asar."""
	if arole.lower() in asar:
		role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), ctx.guild.roles)
		await ctx.message.author.add_roles(role)
		await ctx.message.add_reaction(discord.utils.get(ctx.message.guild.emojis, name="HarukaHug"))
	else:
		await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(asar)))

@bot.command(name="iamn")
async def Iamn(ctx, arole=''):
	"""Use this command to remove a self-assignable role.(usage: $iamn groupwatch) For a list of assignable roles, type $asar."""
	if arole.lower() in asar:
		role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), ctx.guild.roles)
		await ctx.message.author.remove_roles(role)
		await ctx.message.add_reaction(discord.utils.get(ctx.message.guild.emojis, name="HarukaHug"))
	else:
		await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(asar)))

@bot.command(name="asar")
async def Asar(ctx):
	"""Use this command to list all self-assignable roles. Roles can be assigned with the $iam command, and removed using the $iamn command"""
	await ctx.send(str(asar))

@bot.command(name="pronoun")
async def Pronoun(ctx, action='', pronoun=''):
	"""Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod."""
	member=ctx.message.author
	if action=="" or pronoun=="":
		await ctx.send("Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
		return

	if pronoun.lower().strip() == 'they':
		role = discord.utils.find(lambda x: x.name == "p:they/them", ctx.guild.roles)
	elif pronoun.lower().strip() == 'she':
		role = discord.utils.find(lambda x: x.name == "p:she/her", ctx.guild.roles)
	elif pronoun.lower().strip() == 'he':
		role = discord.utils.find(lambda x: x.name == "p:he/him", ctx.guild.roles)
	else:
		await ctx.send("please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
		return

	if action.strip().lower() == "add":
		await member.add_roles(role)
	elif action.strip().lower() == "remove":
		await member.remove_roles(role)
	else:
		await ctx.send("please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")

with open("token.txt","r") as file_object:
	bot.run(file_object.read().strip())
