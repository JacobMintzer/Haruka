import datetime
import random
import time
import re

import discord
import pytz
import yaml
from discord.ext import commands


def getReSlash(emojis,bot, query=""):
	banned = bot.config["emoteBanned"].copy()
	emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, emojis))
	if query == "":
		return random.choice(emojis)
	choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
	return random.choice(choices)

def getRandEmoji(emojis, query="", ctx=None):
	if ctx:
		banned = ctx.bot.config["emoteBanned"].copy()
		if ctx.message.guild:
			if ctx.message.guild.id in banned:
				banned.remove(ctx.message.guild.id)
		emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, emojis))
	if query == "":
		return random.choice(emojis)
	choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
	if len(choices) < 1:
		if ctx:
			emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, ctx.bot.emojis))
			choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
			if len(choices) < 1:
				return None
		else:
			return None
	choice = random.choice(choices)
	return choice


async def yay(ctx):
	if ctx.message.guild is None or ctx.message.guild.emojis is None:
		emoji = getRandEmoji(ctx.bot.emojis, "yay")
	else:
		emoji = getRandEmoji(ctx.message.guild.emojis, "yay")
	if emoji is None:
		emoji = getRandEmoji(ctx.bot.emojis, "yay")	
	await ctx.message.add_reaction(emoji)


def genLog(member, what):
	embd = discord.Embed()
	embd.title = member.display_name
	embd.description = what
	embd = embd.set_thumbnail(url=member.display_avatar)
	embd.type = "rich"
	embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
	embd = embd.add_field(name='Discord Username', value=str(member))
	embd = embd.add_field(name='id', value=member.id)
	embd = embd.add_field(name='Joined', value=member.joined_at)
	embd = embd.add_field(name='Roles', value=', '.join(
		map(lambda x: x.name, member.roles)))
	embd = embd.add_field(name='Account Created', value=member.created_at)
	embd = embd.add_field(name='Profile Picture', value=member.display_avatar)
	return embd


def saveConfig(ctx):
	print("creating backup")
	with open('Resources.yaml', "r") as file:
		backup = yaml.full_load(file)
	print("saving")
	try:
		with open('Resources.yaml', 'w') as outfile:
			yaml.dump(ctx.bot.config, outfile)
	except:
		with open('Resources.yaml', 'w') as outfile:
			yaml.dump(backup, outfile)
		raise


def suppress_links(msg):
	"""Given a message, will find links using regex and surround them with <>"""
	linkRegex = re.compile(r'((http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/\S*)?)+')
	return re.sub(linkRegex, r'<\1>', msg)
