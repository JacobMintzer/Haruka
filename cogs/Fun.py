import asyncio
import discord
import requests
import pprint
import pandas as pd
import os
from saucenao import SauceNao
from discord.ext import commands
from .utilities import MessageHandler, Utils, Checks


class Fun(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.cooldown = []

	@commands.group()
	async def re(self, ctx, emote="", msg=""):
		"""Searches for a random emote by search term. ex. '$re yay' will return a random 'yay' emote."""
		if ctx.message.author.permissions_in(ctx.message.channel).administrator or ctx.message.guild is None:
			if emote.lower() == "disable":
				await self.disable(ctx, msg)
				return
			elif emote.lower() == "enable":
				await self.enable(ctx, msg)
				return
			elif emote.lower() == "slowmode":
				await self.slowmode(ctx, msg)
				return
		userHash = (str(ctx.message.guild.id) + str(ctx.message.author.id))
		if ctx.message.channel.id in self.bot.config["reDisabled"]:
			await ctx.message.add_reaction("❌")
			return
		emoji = Utils.getRandEmoji(ctx.bot.emojis, emote)
		if ctx.message.guild.id in self.bot.config["reSlow"]:
			if userHash in self.cooldown:
				await ctx.send("Please wait a little while before using this command again")
				return
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.loop.create_task(self.reCool(userHash))

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
		Utils.saveConfig(ctx)

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
		Utils.saveConfig(ctx)

	@re.command()
	async def slowmode(self, ctx, mode=""):
		"""ADMIN ONLY!! Adds cooldown per user of 15 seconds please say '$re slowmode' to toggle $re cooldown, or '$re slowmode on' or '$re slowmode off' to turn it on or off respectively."""
		if mode is "":
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
			else:
				self.bot.config["reSlow"].append(ctx.message.guild.id)
		elif mode.lower() is "on":
			if not(ctx.message.guild.id in self.bot.config["reSlow"]):
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
		elif mode.lower() is "off":
			if ctx.message.guild.id in self.bot.config["reSlow"]:
				self.bot.config["reSlow"].remove(ctx.message.guild.id)
		else:
			await ctx.send("please say '$re slowmode' to toggle $re cooldown, or '$re slowmode on' or '$re slowmode off' to turn it on or off respectively.")
		Utils.saveConfig(ctx)

	@commands.command()
	async def e(self, ctx, emote=""):
		"""Gets an emote from the server name. ex. $e aRinaPat."""
		emoji = discord.utils.find(
			lambda emoji: emoji.name.lower() == emote.lower(), self.bot.emojis)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))

	@commands.group()
	@Checks.isScoreEnabled()
	async def rank(self, ctx, *, idx="1"):
		"""Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
		print(str(idx))
		if str(idx).isdigit():
			idx = int(idx)
			await ctx.send(await self.bot.messageHandler.getPB(ctx.message.author, ctx.message.guild, idx))
		elif idx.lower() == 'ignore':
			print("ignoring")
			await self.ignore(ctx)
		elif idx.lower() == 'best' or idx.lower() == 'best girl':
			await self.best(ctx)

	@rank.command

	@rank.command()
	@Checks.hasBest()
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

	@commands.group()
	@Checks.is_admin()
	async def score(self, ctx):
		"""Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings"""
		if ctx.invoked_subcommand is None:
			await ctx.send("Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings")

	@score.command()
	@Checks.isScoreEnabled()
	async def ignore(self, ctx, ch: discord.channel = None):
		"""Use `$score ignore` to have Haruka ignore a channel"""
		if ch is None:
			ch = ctx.message.channel
		try:
			await ctx.send("ignoring {ch.mention}")
		except:
			pass
		self.bot.config["scoreIgnore"].append(ch.id)
		Utils.saveConfig(ctx)

	@score.command()
	@Checks.isScoreEnabled()
	async def unignore(self, ctx, ch: discord.channel = None):
		if ch is None:
			ch = ctx.message.channel
		await ctx.send("No longer ignoring {ch.mention}")
		try:
			self.bot.config["scoreIgnore"].remove(ch.id)
			Utils.saveConfig(ctx)
		except:
			print("could not remove channel from scoreIgnore")

	@score.command(name="enable")
	@Checks.is_admin()
	async def scoreEnable(self,ctx):
		if ctx.message.guild.id in self.bot.config["scoreEnabled"]:
			await ctx.send("scoring is already enabled")
		await self.bot.messageHandler.addGuildToDB(ctx.message.guild)
		self.bot.config["scoreEnabled"].append(ctx.message.guild.id)
		Utils.saveConfig(ctx)

	@commands.command()
	async def llasID(self, ctx, id: int, lb="0"):
		"""Search for a LLAS card by ID. Optionally give limit break level (defaults to 0). ex. '$llasID 146 2'"""
		async with ctx.typing():
			if lb.lower() == "mlb":
				lb = 5
			elif len(str(lb)) > 1:
				lb = int(str(lb)[-1])
			else:
				lb = int(lb)
			response = requests.get(
				"http://all-stars-api.uc.r.appspot.com/cards/id/{0}".format(str(id)))
			data = (response.json())
			embd = self.embedCard(data, lb)
			await ctx.send(embed=embd)

	@commands.command()
	async def llas(self, ctx, *, query):
		"""Search for a LLAS card. ex. $llas Bowling Eli"""
		async with ctx.typing():
			lb = 0
			if query[-3:].lower() == "mlb":
				lb = 5
				query = query[:-3]
			if query[-3:-1].lower() == "lb":
				lb = int(query[-1])
				query = query[:-3]
			query = query.strip()
			response = requests.get(
				"http://all-stars-api.uc.r.appspot.com/cards/search?query={0}".format(str(query)))
			data = (response.json())
			if len(data) > 15:
				await ctx.send("Too many potential cards, please send a more specific query.")
				return
			if len(data) > 1:
				await ctx.send(self.listCards(data))
				return
			if len(data) < 1:
				await ctx.send("No card found with given query.")
				return
			data = data[0]
			embd = self.embedCard(data, lb)
			await ctx.send(embed=embd)

	def embedCard(self, data, lb=0):
		embd = discord.Embed(title=data["idolizedTitle"], description=data["title"], colour=discord.Colour(
			int(data["idol"]["color"].replace("#", "0x"), 16)))
		embd.set_image(
			url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconI.jpg".format(data["id"]))
		embd.set_thumbnail(
			url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconN.jpg".format(data["id"]))
		rarity = discord.utils.find(lambda emoji: emoji.name.lower() == "LLAS{0}ICON".format(
			data["rarity"]["abbreviation"]).lower(), self.bot.emojis)
		embd.set_author(name=data["idol"]["firstName"] +
                  " " + data["idol"]["lastName"], icon_url=rarity.url)
		if lb < 0 or lb > 5:
			lb = 0
		embd.add_field(name="Appeal (LB{0})".format(
			str(lb)), value=data["appeal"]["lb{0}".format(lb)])
		embd.add_field(name="Stamina (LB{0})".format(
			str(lb)), value=data["stamina"]["lb{0}".format(lb)])
		embd.add_field(name="Technique (LB{0})".format(
			str(lb)), value=data["technique"]["lb{0}".format(lb)])
		embd.add_field(
			name="Skill", value=data["primaryActiveAbilityText"], inline=False)
		embd.add_field(name="Passive Ability",
                 value=data["passiveAbility"]["abilityText"], inline=False)
		embd.add_field(name="Active Ability",
                 value=data["secondaryActiveAbilityText"], inline=False)
		embd.set_footer(text="{0}: ID: {1}".format(data["title"], data["id"]))
		return embd

	def listCards(self, data):
		cardList = "Multiple cards found, please pick the card you want with `$llasID <id>` with <id> replaced with the ID you want.```\nID  Rarity    Idol   Title      Idolized Title\n"
		for card in data:
			cardList += "{0}.  {1} {2} {3}: {4} / {5}\n".format(
				card["id"], card["rarity"]["abbreviation"], card["idol"]["firstName"], card["idol"]["lastName"], card["title"], card["idolizedTitle"])
		return cardList + "```"


		
	@commands.command(hidden=True)
	async def source(self, ctx, url: str = ""):
		"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
		await self.sauce(ctx, url)


	@commands.command()
	async def sauce(self, ctx, url: str = ""):
		"""Uses SauceNao to attempt to find the source of an image. Either a direct link to the image, or uploading the image through discord works"""
		async with ctx.typing():
			try:
				if (len(ctx.message.attachments) > 0):
					url = ctx.message.attachments[0].url
				file = "image." + url.split('.')[-1]
				if (os.path.exists(file)):
					os.remove(file)
				request = requests.get(url, allow_redirects=True)
				print(file)
				open(file, 'wb').write(request.content)
			except Exception:
				await ctx.send("error downloading file")
				if (os.path.exists(file)):
					os.remove(file)
				return
			foundSauce = ""
			output = SauceNao(directory='./', api_key=self.bot.config["sauce"])
			result = output.check_file(file_name=file)
			if (os.path.exists(file)):
				os.remove(file)
			
			if (len(result) < 1):
				await ctx.send("no source found")
				return
			for source in result:
				if (float(source["header"]["similarity"]) < 90):
					break
				if "Pixiv ID" in source["data"]["content"][0]:
					await ctx.send("I believe the source is:\nhttps://www.pixiv.net/en/artworks/" + source["data"]["content"][0].split("Pixiv ID: ")[1].split("\n")[0])
					return
				elif "Source: Pixiv" in source["data"]["content"][0]:
					stuff = source["data"]["content"][0].split("\n")[0]
					id = stuff.split("Source: Pixiv #")[1]
					await ctx.send("I believe the source is:\nhttps://www.pixiv.net/en/artworks/" + id)
					return
				elif "dA ID" in source["data"]["content"][0]:
					foundSauce = ("I believe the source is:\nhttps://deviantart.com/view/" +
					              source["data"]["content"][0].split("dA ID: ")[1].split("\n")[0])
				elif "Seiga ID:" in source["data"]["content"][0]:
					foundSauce = ("I believe the source is:\nhttps://seiga.nicovideo.jp/seiga/im" +
					              source["data"]["content"][0].split("Seiga ID: ")[1].split("\n")[0])
			if (foundSauce != ""):
				await ctx.send(foundSauce)
				return
			if len(result[0]["data"]["ext_urls"]) > 0:
				await ctx.send("I couldn't find the exact link, but this might help you find it:\n" + "\n".join(result[0]["data"]["ext_urls"]))
				return
			await ctx.send("sorry, I'm not sure what the source for this is.")


def setup(bot):
	bot.add_cog(Fun(bot))
