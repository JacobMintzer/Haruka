import asyncio
from datetime import datetime, timedelta
import json
import yaml
import os
import pprint
import re
import random
import uuid

import discord
import pandas as pd
import pytz
import requests
import yaml
from discord.ext import commands
from discord import ActivityType, app_commands

from .utilities import checks, messageHandler, utils
import cogs.utilities.constants as consts
from .models.idol_st.allstar_card import AllstarCard



@app_commands.context_menu(name="sauce",)
async def sauce2(interaction: discord.Interaction, message:discord.Message):
	await message.add_reaction(utils.getRandEmoji(self.bot.emojis))

class Fun(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cooldown = []
		with open('secrets.yaml', "r") as file:
			secrets = yaml.full_load(file)
		self.SNKey = secrets["snkey"]
		self.tlUrl = secrets['tlurl']
		self.tlKey = secrets['tlkey']
		self.base_uri='https://idol.st/api/allstars/cards'

	async def shutdown(self, ctx):
		pass

	@app_commands.command(name="hello")
	async def hello(self,interaction: discord.Interaction):
		"""Says hello!"""
		await interaction.response.send_message(f'Hi, {interaction.user.mention}')

	@app_commands.command(name="re",description="random emote")
	@app_commands.describe(emote="emote you want to search for (optional)")
	async def sre(self, interaction: discord.Interaction, emote:str=None):

		def getReSlash(emojis,bot, query=None):
			banned = bot.config["emoteBanned"].copy()
			emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, emojis))
			if not query:
				return random.choice(emojis)
			choices = [emoji for emoji in emojis if query.lower() in emoji.name.lower()]
			return random.choice(choices)


		emoji = getReSlash(self.bot.emojis, self.bot, emote)
		if not (interaction.guild_id is None):
			userHash = (str(interaction.guild.id) + str(interaction.user.id))
			if interaction.channel.id in self.bot.config["reDisabled"]:
				await interaction.response.send_message("re is disabled in this channel",ephemeral=True)
				return
			if interaction.guild.id in self.bot.config["reSlow"]:
				if userHash in self.cooldown:
					await interaction.response.send_message("Please wait a little while before using this command again",ephemeral=True)
					return
		if emoji is None:
			await interaction.response.send_message("emoji not found")
		elif not(interaction.guild_id is None):
			await interaction.response.send_message(str(emoji))
			if interaction.guild_id in self.bot.config["reSlow"]:
				self.bot.loop.create_task(self.reCool(userHash))
		else:
			await interaction.response.send(str(emoji))


	
		

	@commands.group()
	async def re(self, ctx, emote="", msg=""):
		"""Searches for a random emote by search term. Servers with inappropriate emotes will be removed from the global emote pool. ex. '$re yay' will return a random 'yay' emote."""
		if ctx.message.channel.permissions_for(ctx.message.author).administrator or ctx.message.guild is None:
			if emote.lower() == "disable":
				await self.disable(ctx, msg)
				return
			elif emote.lower() == "enable":
				await self.enable(ctx, msg)
				return
			elif emote.lower() == "slowmode":
				await self.slowmode(ctx, msg)
				return
		emoji = utils.getRandEmoji(ctx.bot.emojis, emote, ctx=ctx)
		if not (ctx.message.guild is None):
			userHash = (str(ctx.message.guild.id) + str(ctx.message.author.id))
			if ctx.message.channel.id in self.bot.config["reDisabled"]:
				await ctx.message.add_reaction("❌")
				return
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				if userHash in self.cooldown:
					await ctx.send("Please wait a little while before using this command again")
					return
		if emoji is None:
			await ctx.send("emoji not found")
		elif not (ctx.message.guild is None):
			await ctx.send(str(emoji))
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.loop.create_task(self.reCool(userHash))
		else:
			await ctx.send(str(emoji))

	async def reCool(self, hash):
		self.cooldown.append(hash)
		await asyncio.sleep(15)
		self.cooldown.remove(hash)

	@re.command()
	async def disable(self, ctx, msg=""):
		"""ADMIN ONLY!! Disables the $re command in this channel. Use `$re disable all` to disable everywhere. To reenable use `$re enable`"""
		if msg.lower() == "all":
			for channel in ctx.message.guild.text_channels:
				if not(channel.id in self.bot.config["reDisabled"]):
					self.bot.config["reDisabled"].append(channel.id)
		else:
			if not(ctx.message.channel.id in self.bot.config["reDisabled"]):
				self.bot.config["reDisabled"].append(ctx.message.channel.id)
		utils.saveConfig(ctx)
		await utils.yay(ctx)

	@re.command()
	async def enable(self, ctx, msg=""):
		"""ADMIN ONLY!! Enables $re in this channel. To enable everywhere type $re enable all"""
		if msg.lower() == "all":
			for channel in ctx.message.guild.text_channels:
				if channel.id in self.bot.config["reDisabled"]:
					self.bot.config["reDisabled"].remove(channel.id)
		else:
			if (ctx.message.channel.id in self.bot.config["reDisabled"]):
				self.bot.config["reDisabled"].remove(ctx.message.channel.id)
		utils.saveConfig(ctx)
		await utils.yay(ctx)

	@re.command()
	async def slowmode(self, ctx, mode=""):
		"""ADMIN ONLY!! Adds cooldown per user of 15 seconds please say '$re slowmode' to toggle $re cooldown, or '$re slowmode on' or '$re slowmode off' to turn it on or off respectively."""
		if mode == "":
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
			else:
				self.bot.config["reSlow"].append(ctx.message.guild.id)
		elif mode.lower() == "on":
			if not(ctx.message.guild.id in self.bot.config["reSlow"]):
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
		elif mode.lower() == "off":
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
		else:
			await ctx.send("please say '$re slowmode' to toggle $re cooldown, or '$re slowmode on' or '$re slowmode off' to turn it on or off respectively.")
			return
		utils.saveConfig(ctx)
		await utils.yay(ctx)

	@checks.is_me()
	@commands.command(hidden=True)
	async def syncme(self, ctx):
		if not self.bot.tree:
			self.bot.tree = app_commands.CommandTree(self.bot)
		try:
			synced = await self.bot.tree.sync()
			await self.bot.tree.sync(guild=ctx.message.guild.id)
			await utils.yay(ctx)
		except Exception as e:
			await ctx.send(str(e))


	@commands.command()
	async def e(self, ctx, emote=""):
		"""Gets an emote from the server name. ex. $e aRinaPat."""
		banned = ctx.bot.config["emoteBanned"].copy()
		if ctx.message.guild:
			if ctx.message.guild.id in banned:
				banned.remove(ctx.message.guild.id)
		emoji = discord.utils.find(lambda emoji: ((emoji.name.lower(
		) == emote.lower()) and (not emoji.guild.id in banned)), self.bot.emojis)

		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))

	@commands.command(hidden=True, no_pm=True)
	async def rs(self, ctx, *, stickerName=""):
		"""Searches for a random sticker by search term. Only local server stickers work for now. ex. '$re yay' will return a random 'yay' sticker."""
		
		stickers = ctx.message.guild.stickers
		if stickerName == "":
			await ctx.send(stickers=[random.choice(stickers)])
			return
		choices = [sticker for sticker in stickers if stickerName.lower() in sticker.name.lower()]
		
		sticker = random.choice(choices)
		if not (ctx.message.guild is None):
			userHash = (str(ctx.message.guild.id) + str(ctx.message.author.id))
			if ctx.message.channel.id in self.bot.config["reDisabled"]:
				await ctx.message.add_reaction("❌")
				return
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				if userHash in self.cooldown:
					await ctx.send("Please wait a little while before using this command again")
					return
		if sticker is None:
			await ctx.send("sticker not found")
		await ctx.send(stickers=[sticker])
		if ctx.message.guild.id in self.bot.config["reSlow"]:
			self.bot.loop.create_task(self.reCool(userHash))

	@commands.group()
	@checks.isScoreEnabled()
	async def rank(self, ctx, *, idx="1"):
		"""Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
		if str(idx).isdigit():
			if ctx.message.guild.id in self.bot.config["rankHide"]:
				await ctx.message.add_reaction("🚫")
				return
			idx = int(idx)
			await ctx.send(await self.bot.messageHandler.getPB(ctx.message.author, ctx.message.guild, idx))
		elif idx.lower() == 'best' or idx.lower() == 'best girl':
			await self.best(ctx)
		elif idx.lower() == 'ignore':
			if(ctx.message.channel.permissions_for(ctx.author).administrator):
				await self.ignore(ctx)
			else:
				await ctx.send("This command is only available to an Administrator.")
		elif idx.lower().startswith("add"):
			if(ctx.message.channel.permissions_for(ctx.author).administrator):
				await self.rankAdd(ctx, idx)
			else:
				await ctx.send("This command is only available to an Administrator.")
		elif idx.lower().startswith("hide"):
			if(ctx.message.channel.permissions_for(ctx.author).administrator):
				await self.rankHide(ctx)


	@rank.command(name="add")
	@checks.is_admin()
	async def rankAdd(self, ctx, idx):
		"""Adds a role that will be assigned upon reaching certain ranks. You can change the role name later. ex: `$rank add 500 New Recruit`."""
		if (idx.split(" ")[1].isdigit()):
			score = int(idx.split(" ")[1])
			if len(idx.split(" ")) > 2:
				roleName = idx.split(" ", 2)[2]
			else:
				roleName = None
		else:
			await ctx.send("Please give a score value for the rank role and optionally a name. ex. `$rank add 500 New Recruit`. You can change the role name later.")
			return
		if roleName is None:
			role = await ctx.guild.create_role()
			await ctx.send("Created role {0} that will be assigned upon reaching a score of {1}.".format(role.mention, score))
		else:
			role = discord.utils.find(
				lambda x: x.name == roleName, ctx.guild.roles)
			if role is None:
				role = await ctx.guild.create_role(name=roleName)
				await ctx.send("Created role {0} that will be assigned upon reaching a score of {1}.".format(role.mention, score))
			else:
				await ctx.send("Found role {0}; it will be assigned upon reaching a score of {1}.".format(role.name, score))
		self.bot.config["roleRanks"][str(ctx.guild.id)].append(
			{"score": score, "role": role.id})
		self.bot.config["roleRanks"][str(ctx.guild.id)] = sorted(
			self.bot.config["roleRanks"][str(ctx.guild.id)], key=lambda x: x["score"])
		utils.saveConfig(ctx)

	@rank.command()
	@checks.hasBest()
	async def best(self, ctx):
		"""Use this to show the rankings of what the most popular `best girl` role is"""
		roleList = []
		for roleName in ctx.bot.config["best"][str(ctx.message.guild.id)]:
			role = discord.utils.find(lambda x: x.name.lower(
			) == roleName.lower(), ctx.message.guild.roles)
			roleList.append((role.name, len(
				list(filter(lambda x: role in x.roles, ctx.message.guild.members)))))
		roleList.sort(key=lambda x: x[1], reverse=True)
		series = pd.DataFrame(roleList)
		series.index += 1
		series.columns = ["Best", "Users"]
		await ctx.send("```fortran\n{0}```".format(series.to_string()))

	@rank.command(name="hide")
	@checks.is_admin()
	async def rankHide(self, ctx):
		"""ADMIN ONLY! Use this command to toggle visibility of leaderboard in the current server."""
		if ctx.message.guild.id in self.bot.config["rankHide"]:
			self.bot.config["rankHide"].remove(ctx.message.guild.id)
			await ctx.send("Leaderboard no longer hidden.")
		else:
			self.bot.config["rankHide"].append(ctx.message.guild.id)
			await ctx.send("Leaderboard is now hidden.")
		utils.saveConfig(ctx)
		await utils.yay(ctx)



	@commands.group()
	@checks.is_admin()
	async def score(self, ctx):
		"""Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings"""
		if ctx.invoked_subcommand is None:
			await ctx.send("Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings")

	@score.command()
	@checks.isScoreEnabled()
	async def ignore(self, ctx, ch: discord.TextChannel = None):
		"""Use `$score ignore` to have Haruka ignore a channel"""
		if ch is None:
			ch = ctx.message.channel
		try:
			await ctx.send(f"ignoring {ch.mention}")
		except:
			await utils.yay(ctx)
			pass
		self.bot.config["scoreIgnore"].append(ch.id)
		utils.saveConfig(ctx)

	@score.command()
	@checks.isScoreEnabled()
	async def unignore(self, ctx, ch: discord.TextChannel = None):
		if ch is None:
			ch = ctx.message.channel
		try:
			await ctx.send("No longer ignoring {ch.mention}")
		except:
			await utils.yay(ctx)
			pass
		try:
			self.bot.config["scoreIgnore"].remove(ch.id)
			utils.saveConfig(ctx)
		except:
			print("could not remove channel from scoreIgnore")

	@score.command(name="enable")
	@checks.is_admin()
	async def scoreEnable(self, ctx):
		if not(str(ctx.guild.id) in self.bot.config["roleRanks"].keys()):
			self.bot.config["roleRanks"][str(ctx.guild.id)] = []
		if ctx.message.guild.id in self.bot.config["scoreEnabled"]:
			await ctx.send("scoring is already enabled")
		else:
			try:
				await self.bot.messageHandler.addGuildToDB(ctx.message.guild)
			except:
				pass
			self.bot.config["scoreEnabled"].append(ctx.message.guild.id)
			await utils.yay(ctx)
		utils.saveConfig(ctx)

	
	@score.command(name="wipe")
	@checks.is_admin()
	async def scoreWipe(self, ctx):
		"""use `$score wipe` to wipe all scores from your server. Must be admin. Warning; this cannot be undone, use with care."""
		if not ctx.message.guild.id in self.bot.config["scoreEnabled"]:
			await ctx.send("scoring isn't enabled")
			return
		
		await self.bot.messageHandler.wipeGuildScore(ctx.message.guild)
		await utils.yay(ctx)
		utils.saveConfig(ctx)

	@commands.command()
	async def llasID(self, ctx, id: int):
		response = requests.get(self.base_uri, params = {"id":id})
		data = response.json()["results"]
		card = AllstarCard(**data[0])
		await ctx.send(embed=card.get_embed())


	@commands.command()
	async def llas(self, ctx, *, query):
		async with ctx.typing():
			tokens = query.lower().split(" ")
			version = None
			params = {}
			for token in tokens:
				if token.title() in consts.idols:
					params["idol"] = token
				elif token.upper() in consts.rarities:
					params["rarity"] = token
				elif token.lower() in consts.attributes:
					params["attribute"] = token
				elif token == "new":
					version = 0
				elif token.isdigit():
					version = -1 * int(token) 
			response = requests.get(self.base_uri, params = params)
			data = response.json()["results"]
			if version != None:
				card = AllstarCard(**data[version])
				await ctx.send(embed=card.get_embed())
			elif len(data)==1:
				card = AllstarCard(**data[0])
				await ctx.send(embed=card.get_embed())
			elif len(data)==0:
				await ctx.send("No card found with given query.")
			else:
				await ctx.send(self.listCards(data))

	def listCards(self, data):
		cards = [AllstarCard(**x) for x in data]
		cardList = "Multiple cards found, please pick the card you want with `$llasID <id>` with <id> replaced with the ID you want.```\nID  Rarity    Idol   Title      Idolized Title\n"
		for card in cards:
			cardList += "{0}.  {1} {2}: {3} / {4}\n".format(
				card.id, card.rarity, card.idol_name, card.name, card.name_idolized)
		return cardList + "```"

	@commands.command(hidden=True)
	async def source(self, ctx, url: str = ""):
		"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
		await self.sauce(ctx, url)

	@commands.command()
	async def sauce(self, ctx, url: str = ""):
		"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
		try:
			if (len(ctx.message.attachments) > 0):
				url = ctx.message.attachments[0].url
			request = requests.get(url, allow_redirects=True)
			file = "image." + url.split('.')[-1]
			open(file, 'wb').write(request.content)
		except Exception as e:
			print(e)
			await ctx.send("error downloading file")
			return
		endpoint = 'http://saucenao.com/search.php?output_type=2&api_key={0}&db=999&numres=10'.format(
			self.SNKey)
		files = {'file': ('image.png', open(file, 'rb'))}
		response = requests.post(endpoint, files=files)
		os.remove(file)
		if response.status_code != 200:
			print("status code is {0}".format(response.status_code))
		output = json.loads(response.content.decode("utf-8"))
		result = output["results"]

		if (len(result) < 1) or float(result[0]["header"]["similarity"]) < 80:
			await ctx.send("no source found")
		elif "source" in result[0]["data"].keys() and result[0]["data"]["source"] != "":
			await ctx.send("I believe the source is: {0}".format(result[0]["data"]["source"]))
		elif(len(result[0]["data"]["ext_urls"]) == 1):
			await ctx.send("I believe the source is: {0}".format(result[0]["data"]["ext_urls"][0]))
		elif len(result[0]["data"]["ext_urls"]) > 0:
			await ctx.send("I couldn't find the exact link, but this might help you find it:\n" + "\n".join(result[0]["data"]["ext_urls"]))
		

	@commands.command(aliases=["announcement"], hidden=True)
	async def announcements(self, ctx):
		await ctx.send("https://imgur.com/a/37W6U64")

	@commands.command(hidden=True)
	async def noinfo(self, ctx):
		await ctx.send("https://imgur.com/a/sGooJcB")

	@commands.command()
	async def masterpost(self, ctx):
		"""Gets the most recent version of the r/ll discord masterpost."""
		await ctx.send(ctx.bot.config["masterpost"])

	@commands.command(aliases=["isNijiS2Confirmed?"], hidden=True)
	async def isNijiS2Confirmed(self, ctx):
		await ctx.send("YES")

	@commands.command(aliases=["isNijiMovieConfirmed?","isNijiMovieConfirmed"], hidden=True)
	async def isNijiS3Confirmed(self, ctx):
		await ctx.send("bruh its already out")

	@commands.command(aliases=["temperature"])
	async def temp(self, ctx, *, msg):
		"""Convert temperatures between F and C. Remember to include your given unit as F or C. ex. `$temp 30C`"""
		tempRegex = re.compile(r"""(-?)(\d{1,3})(C|F|c|f)(?![^\s.,;?!`':>"])""")
		if tempMatch := tempRegex.search(msg):
			temperature = tempMatch.group(0)
			unit = temperature[-1]
			if temperature[0] == '-':
				magnitude = 0 - (int(temperature[1:-1]))
			else:
				magnitude = int(temperature[:-1])
			if unit.lower() == 'c':
				res = "{0}​C is {1:.1f}​F".format(magnitude, magnitude * 9 / 5 + 32)
			else:
				res = "{0}​F is {1:.1f}​C".format(magnitude, (magnitude - 32) * 5 / 9)
			await ctx.send(res)

	@commands.command(aliases=["distance","dist"])
	async def length(self, ctx, *, msg):
		"""Convert lengths between feet and inches and centimeters. Ex. `$length 110cm` `$dist 5'7"` `$distance 3 feet 7 inches`"""
		msg=msg.lower().replace('inches','\"').replace('in','\"').replace("feet","\'").replace("ft","\'").replace(" ","")
		distRegex = re.compile(
			r"^(?!$|.*\'[^\x22]+$)(?:([0-9]+)\')?(?:([0-9]+)\x22?)?$")
		if "cm" in msg.lower():
			cmDist = float(msg.replace("cm", "").strip())
			totalDist = 0.39370 * cmDist
			if totalDist > 12:
				inDist = totalDist % 12
				ftDist = int(totalDist/12)
				await ctx.send("{:.2f} cm is {:.0f} feet {:.2f} inches".format(cmDist,ftDist,inDist))
			else:
				await ctx.send(f"{cmDist} cm is {round(totalDist,2)} inches")
			return
		elif distMatch := distRegex.search(msg):
			feet = int(distMatch.group(1) if distMatch.group(1) else 0)
			inches = int(distMatch.group(2) if distMatch.group(2) else 0)
			totalInches = 12 * feet + inches
			totalCM = totalInches / 0.39370
			if feet>0:
				await ctx.send(f"{feet} feet {inches} inches is {round(totalCM,2)}cm")
			else:
				await ctx.send(f"{inches} inches is {round(totalCM,2)}cm")
		else:
			await ctx.send("please put your conversion in the format of `30cm` or `5'7\"`")


	@commands.command(aliases=["tl"])
	async def translate(self, ctx, *, msg):
		from_language = 'ja'
		url = f'{self.tlUrl}/translate?api-version=3.0&from={from_language}&to=en'
		location = 'eastus'
		headers = {
			'Ocp-Apim-Subscription-Key': self.tlKey,
			'Ocp-Apim-Subscription-Region': location,
			'Content-type': 'application/json',
			'X-ClientTraceId': str(uuid.uuid4())

		}
		body = [{
			'text' : msg.replace("@","@"+u"\u200B")
		}]
		request = requests.post(url, headers=headers, json=body)
		response = request.json()
		await ctx.send(response[0]["translations"][0]["text"])

	@commands.command()
	@checks.is_me()
	async def uwu(self,ctx,id):
		foundEmote = discord.utils.find(lambda emoji: (emoji.id == id), self.bot.emojis)
		await ctx.send(foundEmote)
		pass

	@commands.command()
	@checks.is_me()
	async def status(self,ctx,*,msg=""):
		if msg:
			await ctx.bot.change_presence(
				activity=discord.Activity(
					name=msg, 
					type=ActivityType.playing,
					platform="PS5",
					start=datetime(2019,9,26),
					end=datetime(2030,1,1),
					state="Gayming"
				),
				status=discord.Status.idle
			)
			self.bot.config["status"] = msg
			utils.saveConfig(ctx)
			await utils.yay(ctx)



async def setup(bot):
	await bot.add_cog(Fun(bot))
