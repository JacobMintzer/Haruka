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

from .utilities import checks, messageHandler, utils
import cogs.utilities.constants as consts
from .models.idol_st.allstar_card import AllstarCard

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

	#@commands.command(hidden=True)
	async def ig(self, ctx, *, url):
		embd = utils.getInstaEmbed(ctx.bot.config["instagramAccessToken"], url)
		await ctx.send(embed=embd)

	@commands.command()
	async def masterpost(self, ctx):
		"""Gets the most recent version of the r/ll discord masterpost."""
		await ctx.send(ctx.bot.config["masterpost"])

	@commands.command(aliases=["isNijiS2Confirmed?"], hidden=True)
	async def isNijiS2Confirmed(self, ctx):
		await ctx.send("YES")

	@commands.command(aliases=["isNijiMovieConfirmed?","isNijiMovieConfirmed", "isNijiS3Confirmed?"], hidden=True)
	async def isNijiS3Confirmed(self, ctx):
		await ctx.send("Not yet")

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
			'text' : msg
		}]
		request = requests.post(url, headers=headers, json=body)
		response = request.json()
		await ctx.send(response[0]["translations"][0]["text"])
			
	@checks.is_me()
	@commands.command(hidden=True)
	async def yeetEmAll(self, ctx):
		usernames = ["Kagumi",
			"TvoyaWaifu",
			"J3ns3n",
			"nazagram",
			"DADIBRE",
			"heubiiii",
			"imbocsgo",
			"vDuty",
			"019275637391010102937",
			"Salaminas",
			"llamas",
			"abdulll",
			"Lix",
			"hitler",
			"KingSpartan117",
			"TripLowG",
			"Chema",
			"Cvsmic.Roses",
			"mjkiller7",
			"paltin",
			"Lands",
			"Nachorw",
			"killuaѪ灯",
			"Nacreous",
			"luffy34",
			"ytmegattv",
			"meThod_Man",
			"Linoxxx",
			"cult",
			"dedek pakistan",
			"~Nikola~",
			"haostwz",
			"KIT$",
			"zodiac00101",
			"jamel",
			"jxsu",
			"JorgeMV",
			"headbandkhardi",
			"renaa",
			"iiusiion",
			"litele-jacob89",
			"TheArtist2410",
			"키키",
			"NBA YOUNGBOY",
			"Gunserker",
			"55thdude",
			"matt5520",
			"Vision zlu",
			"Xnin (aliff)",
			"crazyaxe",
			"𝓖𝓪𝓶𝓮𝓻𝓽𝓸𝓹𝓼",
			"Stranger959785",
			"josefa",
			"its sum random",
			"elliot",
			"salchipapas29",
			"xJustFatmanx",
			"inofox",
			"kutooo",
			"Calsetin TactiCo😋😋",
			"Chastizedboy-a.k.a.-Karlos83",
			"Dedo",
			"Vl0ne_Stack$$$",
			"ac",
			"Lms   blont06x",
			"yougood1234",
			"Forgetfull_4kt",
			"Jude",
			"catt",
			"Meduzka",
			"sporting84004",
			"Nippster",
			"MajinRose",
			"CAPTAINS",
			"taz",
			"aka179",
			"david33610",
			"TrailBlazer",
			"mat-mat",
			"u-cruz",
			"ДруГ",
			"sZuzu",
			"mike335  🇩🇪",
			"RorBux",
			"ummshivam",
			"geT To The poinT - LDN, UK",
			"nad",
			"Yahali12f",
			"ERD",
			"LA HngryBttmDude",
			"OLIVERS2",
			"AnteGiaYpno",
			"CLONE",
			"YourLocalTank",
			"KingG",
			"davi343",
			"kun",
			"𝚖𝚒𝚕𝚔",
			"the Friend army member",
			"زاديرا ديفون",
			"derp",
			"ТвойСБУАгент",
			"rjsonly",
			"BLEEDOUT205",
			"LoganE195",
			"aposented",
			"1Sebastian5",
			"GTL  | KAIDO",
			"CihanK",
			"IamRamac",
			"nikopcas",
			"intoku",
			"Frdic",
			"VMIZ19",
			"Jarjarfranc",
			"goodtymes1993",
			"adidas",
			"AkshaYYYYY",
			"been hacked",
			"alezx51",
			"スANTEX ʕoᴥoʔ",
			"Mert",
			"klaerwerktaucher8i",
			"Hacks1212",
			"GoDoRWhaTT",
			"marcsamuel",
			"itsayaboi84123",
			"comp_anxiety",
			"Crazymessi21",
			"mike89",
			"V1C3N1T00",
			"menoska",
			"AngelSickos",
			"Pikochu",
			"BrittonEzAqt",
			"bigbodybenz",
			"seeker2.0",
			"TheHakeem",
			"hanss",
			"🍩Kyojuro Rengoku🔥",
			"rleqqx",
			"8285799149",
			"Josueee $",
			"Hornymale1231",
			"schniazz",
			"MonkeyMan",
			"aar",
			"caioct123",
			"Milly",
			"der Boss",
			"prayingtothesky",
			"StorminFr",
			"skoulfex",
			"claxzy1",
			"Deichzocker",
			"tianheile",
			"S.G64",
			"nxkxnfdn",
			"Owejs",
			"Karan pawar",
			"ZELDOTH",
			"NEO",
			"Raunchdog",
			"Leos",
			"o-YHATZEE-o",
			"7.arbona",
			"malaka-tutu",
			"Tuki",
			"Mr.★S𝒊𝒍𝒆𝒏𝒕ܔ𝒌𝒊𝒍𝒍𝒆𝒓࿐",
			"masson98",
			"xanz",
			"शिकारी",
			"brajn",
			"MrSweetBlood",
			"dood",
			"dudeeeeee40",
			"꧁ᴾᴿᴼ ᭄ ᴮᴼˢˢ✞༒꧂",
			"family_friendly_name",
			"Josh.SG",
			"ra1n0x",
			"Nightwalker",
			"BossElLoco",
			"tannant89",
			"master bater",
			"Spooderman",
			"Kingallsus",
			"abhipanchal09",
			"lcock",
			"Hillary",
			"stonerrick27",
			"Ahegao",
			"crazybear",
			"redseth1989",
			"gotiti04",
			"Danc246",
			"Ash Vito",
			"Lost",
			"michaelbf109",
			"𝘼𝙣𝙜𝙚𝙡𝙖",
			"kelechi",
			"lionbolanz",
			"onoe",
			"plugger",
			"Mats",
			"Nicoolidonni",
			"jayant1222",
			"best renekton",
			"E.J.",
			"fckhun8",
			"fendtpro",
			"Dan Istrate",
			"mk182",
			"𝐖 𝖗 𝖆 𝖙 𝖍",
			"jjjjjjj",
			"GigaKashi",
			"nickgur123",
			"Maurik1ng ☠",
			"OWA OWA",
			"Kaalia",
			"andre ismael",
			"InTracks",
			"OogaBooga",
			"Ahmet43",
			"Edward Newgate",
			"Sledg",
			"Bruno Bender",
			"vonn0body",
			"N0name inc",
			"Kequ",
			"cal_central",
			"THE SLUMP GOD",
			"Mar.-",
			"Duque",
			"GhoulツRobber",
			"elPato",
			"R9",
			"Birulee",
			"Luan.",
			"twdophin",
			"Retro",
			"Grizzy",
			"DRAM4X",
			"jjd_jamdagni",
			"ShaqScratchedHisCrack",
			"gagagaga",
			"helkpdoo",
			"Benja",
			"WoAiNi_J",
			"Tony Mahowney",
			"nazi bro",
			"el chiquito suiiiiiiiiiiiiiiiiii",
			"Bhinava",
			"mario ištvanić",
			"idodididi",
			"iamtp",
			"ghjjkktt",
			"Mushrambo",
			"djalil2810",
			"RunningMantheCoin",
			"artii",
			"tase",
			"BaranMnstr01",
			"cnsrewind",
			"le_benj",
			"chepa",
			"chicharrón",
			"Beastmode928",
			"YEAHBOY",
			"Ali baba 123",
			"ninjagase",
			"noRAGrets",
			"AKdrillxxx",
			"noik15",
			"Levi001",
			"tree",
			"𝐠𝐨𝐧𝐜𝐡𝐨",
			"T0Ny",
			"Romano(Pille)",
			"kitty cheshire",
			"AbowrdhS2",
			"Stingybee",
			"Hahaha",
			"ismas….07",
			"Scriiibe",
			"Miroo",
			"onoe",
			"Opaidus",
			"akash",
			"Jam4r",
			"Dimitrios",
			"danielp.",
			"Slugish",
			"kmarkbenjamin",
			"✷∆~𝙰𝚛𝚝𝙸𝚗𝚃𝚑𝚎𝙷𝚊𝚛𝚍~∆✷",
			"NERO",
			"I AM XIPICU",
			"GH0U53",
			"Fistcrunch",
			"MangoChina",
			"malyo_24",
			"Jaba.daba.du",
			"pickledpepper",
			"ElMarquito",
			"Ducky_Enough",
			"hatem",
			"steveschmidt11",
			"tibe",
			"no braincells",
			"DextheKiller",
			"TheAnimeKid",
			"Jxxz_30",
			"Jayp",
			"blake51",
			"tempra",
			"the mashkiv",
			"shanX",
			"salsik",
			"ＰＣＲ_ＪＯＮＫＩＥ〆503",
			"P00Shiesty",
			"lilcapa",
			"jsnsisns",
			"ruined yup",
			"ZĘŒ",
			"Ricsroofit",
			"yarin",
			"makis",
			"tom.henx",
			"rookydragoon",
			"just me",
			"ssm112",
			"JeFfJeFrSoN",
			"nicescheiß",
			"Admin123",
			"Teachy77",
			"Chaz0n",
			"Ciastek_12_v2",
			"OPPA_Gaza",
			"Simba",
			"MrVinnyC",
			"antriana❤",
			"ALEYou",
			"KapitänzurSee",
			"Zz",
			"jefe",
			"sgtboos821",
			"DonnieDarko",
			"maddy",
			"Vlăduț",
			"!san.k",
			"Flaxen",
			"camelo",
			"OTG XEN",
			"Am Saleh | LOCO",
			"YesIamtheone",
			"lol07",
			"Hunter07",
			"Jhani",
			"sam123123",
			"LOGJess!!!",
			"LehriBaba",
			"iashdb2uuwwi",
			"Fredi Rost",
			"∆º",
			"me, Juan",
			"я абемка",
			"Mr.Mile",
			"cybersholt",
			"A  C  H  E  E",
			"xvryzs",
			"yVicToR so2",
			"Jyims06",
			"DigitalExpandables",
			"Breezyy",
			"activesuun",
			"ash35",
			"elaldora",
			"Simoonbob",
			"impostor",
			"YT_juggernaut247",
			"Randomgirlie",
			"Mez",
			"draco",
			".vxrtex",
			"IdoShmuel43",
			"Zaham",
			"franta",
			"jimjim",
			"LawDaddy4Lyfe",
			"Herokovidz",
			"Dilan G",
			"manny",
			"santa1738999",
			"hidgbxdg",
			"EL MOY",
			"𝙐𝙋𝙊𝙎́",
			"RealBoca",
			"WavedHasLigma",
			"Carlirr",
			"☦RussianGopnik🪆",
			"lilboy",
			"edvin",
			"bayuanggara",
			"kurama",
			"The Reinster",
			"Osakabe",
			"mitoofn_",
			"HEARINGLEMON",
			"paris",
			"Dogman3009",
			"pedersenr",
			"PETATIXD",
			"pbj",
			"rubidib",
			"khesraw",
			"EpicPlayz",
			"nobodyhere",
			"Soofru",
			"i_play_to_much69",
			"Maciek Soszyński",
			"Henrik",
			"rj444",
			"cano",
			"ImGCR",
			"GOD |•shadow",
			"ballstein30",
			"Alone...",
			"Morendi_Oops",
			"PoXxii",
			"Texas Infidel",
			"BigSteppa",
			"unkown223",
			"user169270",
			"N.Nikolaides",
			"!    ☇ DHOM",
			"elknito",
			"MN9OORI",
			"faiz.shaikh6",
			"wes",
			"Jorg3",
			"951NakedBarber",
			"Goblin",
			"LividHem",
			"BMWMERCEdES racing",
			"LowKaneki",
			"Sal",
			"trix"]
		for username in usernames:
			try:
				member = discord.utils.get(ctx.guild.members, name=username)
				await member.kick()
				print(f"Kicked {member.name}#{member.discriminator}")
			except Exception as e:
				print("Error kicking ")
				print(e)

	@commands.command()
	@checks.is_me()
	async def uwu(self,ctx):
		member = discord.utils.get(ctx.guild.members, name="BMWMERCEdES racing")
		await ctx.send(f"found user {member.name}#{member.discriminator}")

def setup(bot):
	bot.add_cog(Fun(bot))
