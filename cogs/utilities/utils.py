import asyncio
import datetime
import random
import time

import discord
import pytz
import requests
import yaml
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from discord.ext import commands


def getRandEmoji(emojis, query="", ctx=None):
	if ctx:
		banned = ctx.bot.config["emoteBanned"].copy()
		if ctx.message.guild:
			if ctx.message.guild.id in banned:
				banned.remove(ctx.message.guild.id)
		emojis = list(filter(lambda x: not(x.guild.id in banned), emojis))
	if query == "":
		return random.choice(emojis)
	choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
	if len(choices) < 1:
		return None
	choice = random.choice(choices)
	return choice


async def yay(ctx):
	emoji = getRandEmoji(ctx.message.guild.emojis, "yay")
	if emoji is None:
		emoji = getRandEmoji(ctx.bot.emojis, "yay")
	await ctx.message.add_reaction(emoji)


def genLog(member, what):
	embd = discord.Embed()
	embd.title = member.display_name
	embd.description = what
	embd = embd.set_thumbnail(url=member.avatar_url)
	embd.type = "rich"
	embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
	embd = embd.add_field(name='Discord Username', value=str(member))
	embd = embd.add_field(name='id', value=member.id)
	embd = embd.add_field(name='Joined', value=member.joined_at)
	embd = embd.add_field(name='Roles', value=', '.join(
		map(lambda x: x.name, member.roles)))
	embd = embd.add_field(name='Account Created', value=member.created_at)
	embd = embd.add_field(name='Profile Picture', value=member.avatar_url)
	return embd


def saveConfig(ctx):
	print("saving")
	with open('Resources.yaml', 'w') as outfile:
		yaml.dump(ctx.bot.config, outfile)

def getInstaEmbed(token,url):
	baseHtmlEmbed=requests.get(f"https://graph.facebook.com/v8.0/instagram_oembed?url={url}&access_token={token}").json()
	authorUserName=baseHtmlEmbed["author_name"]
	imgUrl=baseHtmlEmbed["thumbnail_url"]
	soup=BeautifulSoup(baseHtmlEmbed["html"], features="html.parser")
	comment=soup.p.a.contents[0]
	authorName=(soup.find_all("p")[1]).contents[1].contents[0].strip()
	time=(soup.find_all("p")[1]).contents[3].contents[0]
	timestamp = search_dates(time, settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True})[0]
	profileUrl=f"https://www.instagram.com/{authorUserName}/"
	profileInfo=requests.get(f"{profileUrl}?__a=1").json()
	profilePicUrl=profileInfo["graphql"]["user"]["profile_pic_url"]
	embd = discord.Embed()
	embd.type = "rich"
	embd.color = discord.Color.purple()
	embd.title = f"Instagram Post by {authorName}"
	print(profilePicUrl)
	embd = embd.set_author(name = f"{authorName} ({authorUserName})", url=profileUrl, icon_url=profilePicUrl)
	embd = embd.set_image(url=imgUrl)
	embd.url = url
	embd.description = comment
	embd.timestamp = timestamp[1]
	return embd

