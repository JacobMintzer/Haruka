import asyncio
import discord
import requests
import pprint
from discord.ext import commands
from .utilities import MessageHandler, Utils, Checks

class Fun(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
		self.cooldown=[]
	
	@commands.group()
	async def re(self,ctx,emote="",msg=""):
		"""Searches for a random emote by search term. ex. '$re yay' will return a random 'yay' emote."""
		if ctx.message.author.permissions_in(ctx.message.channel).administrator or ctx.message.guild is None:
			if emote.lower() == "disable":
				await self.disable(ctx,msg)
				return
			elif emote.lower() == "enable":
				await self.enable(ctx,msg)
				return
			elif emote.lower() == "slowmode":
				await self.slowmode(ctx,msg)
				return
		userHash=(str(ctx.message.guild.id)+str(ctx.message.author.id))
		if ctx.message.channel.id in self.bot.config["reDisabled"]:
			await ctx.message.add_reaction("❌")
			return
		emoji=Utils.getRandEmoji(ctx.bot.emojis, emote)
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
	
	async def reCool(self,hash):
		self.cooldown.append(hash)
		await asyncio.sleep(15)
		self.cooldown.remove(hash)

	@re.command()
	async def disable(self,ctx,msg=""):
		"""ADMIN ONLY!! Disables the $re command in this channel. Use `$re disable all` to disable everywhere. To reenable use `$re enable`"""
		if msg.lower()=="all":
			for channel in ctx.message.guild.text_channels:
				if not(channel.id in self.bot.config["reDisabled"]):
					self.bot.config["reDisabled"].append(channel.id)
		else:
			if not(ctx.message.channel.id in self.bot.config["reDisabled"]):
				self.bot.config["reDisabled"].append(ctx.message.channel.id)
		Utils.saveConfig(ctx)

	@re.command()
	async def enable(self,ctx,msg=""):
		"""ADMIN ONLY!! Enables $re in this channel. To enable everywhere type $re enable all"""
		if msg.lower()=="all":
			for channel in ctx.message.guild.text_channels:
				if channel.id in self.bot.config["reDisabled"]:
					self.bot.config["reDisabled"].remove(channel.id)
		else:
			if (ctx.message.channel.id in self.bot.config["reDisabled"]):
				self.bot.config["reDisabled"].remove(ctx.message.channel.id)
		Utils.saveConfig(ctx)
		
	@re.command()
	async def slowmode(self,ctx,mode=""):
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
	async def e(self,ctx, emote=""):
		"""Gets an emote from the server name. ex. $e aRinaPat."""
		emoji=discord.utils.find(lambda emoji: emoji.name.lower() == emote.lower(),self.bot.emojis)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))


	@commands.group()
	@Checks.is_niji()
	async def rank(self,ctx,idx: int=1):
		"""Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
		await ctx.send(await self.bot.messageHandler.getPB(ctx.message.author,idx))

	@rank.command()
	async def ignore(self,ctx):
		await ctx.send("uwu")

	@commands.command()
	async def llasID(self,ctx,id:int,lb=0):
		"""Search for a LLAS card by ID. Optionally give limit break level (defaults to 0). ex. '$llasID 146 2'"""
		async with ctx.typing():
			if len(str(lb))>1:
				lb=int(lb[-1])
			response=requests.get("http://all-stars-api.uc.r.appspot.com/cards/id/{0}".format(str(id)))
			data = (response.json())
			embd = self.embedCard(data,lb)
			await ctx.send(embed=embd)

	@commands.command()
	async def llas(self,ctx,*,query):
		"""Search for a LLAS card. ex. $llas Bowling Eli"""
		async with ctx.typing():
			lb=0
			if query[-3:-1].lower()=="lb":
				lb=int(query[-1])
				query=query[:-3]
			query=query.strip()
			response=requests.get("http://all-stars-api.uc.r.appspot.com/cards/search?query={0}".format(str(query)))
			data= (response.json())
			if len(data)>15:
				await ctx.send("Too many potential cards, please send a more specific query.")
				return
			if len(data)>1:
				await ctx.send(self.listCards(data))
				return
			if len(data)<1:
				await ctx.send("No card found with given query.")
				return
			data=data[0]
			embd=self.embedCard(data,lb)
			await ctx.send(embed=embd)

	def embedCard(self,data,lb=0):
		embd=discord.Embed(title= data["idolizedTitle"], description=data["title"],colour=discord.Colour(int(data["idol"]["color"].replace("#","0x"),16)))
		embd.set_image(url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconI.jpg".format(data["id"]))
		embd.set_thumbnail(url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconN.jpg".format(data["id"]))
		rarity=discord.utils.find(lambda emoji: emoji.name.lower() == "LLAS{0}ICON".format(data["rarity"]["abbreviation"]).lower(),self.bot.emojis)
		embd.set_author(name = data["idol"]["firstName"] + " " + data["idol"]["lastName"], icon_url = rarity.url)
		if lb<0 or lb>5:
			lb = 0
		embd.add_field(name="Appeal (LB{0})".format(str(lb)), value=data["appeal"]["lb{0}".format(lb)])
		embd.add_field(name="Stamina (LB{0})".format(str(lb)), value=data["stamina"]["lb{0}".format(lb)])
		embd.add_field(name="Technique (LB{0})".format(str(lb)), value=data["technique"]["lb{0}".format(lb)])
		embd.add_field(name="Skill", value=data["primaryActiveAbilityText"], inline=False)
		embd.add_field(name="Passive Ability", value=data["passiveAbility"]["abilityText"], inline=False)
		embd.add_field(name="Active Ability", value=data["secondaryActiveAbilityText"], inline=False)
		embd.set_footer(text="{0}: ID: {1}".format(data["title"],data["id"]))
		return embd



	def listCards(self,data):
		cardList="Multiple cards found, please pick the card you want with `$llasID <id>` with <id> replaced with the ID you want.```\nID  Rarity    Idol   Title      Idolized Title\n"
		for card in data:
			cardList+="{0}.  {1} {2} {3}: {4} / {5}\n".format(card["id"],card["rarity"]["abbreviation"],card["idol"]["firstName"],card["idol"]["lastName"],card["title"],card["idolizedTitle"])
		return cardList+"```"
	
def setup(bot):
	bot.add_cog(Fun(bot))
