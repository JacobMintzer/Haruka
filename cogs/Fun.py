import asyncio
import discord
import requests
import pprint
from discord.ext import commands
from .utilities import MessageHandler, Utils, Checks

class Fun(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
		self.cooldowns=[]
	
	@commands.command()
	async def re(self,ctx,emote=""):
		"""Searches for a random emote by search term. ex. '$re yay' will return a random 'yay' emote."""
		emoji=Utils.getRandEmoji(ctx.bot.emojis, emote)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))
		
		
	@commands.command()
	async def e(self,ctx, emote=""):
		"""Gets an emote from the server name. ex. $e aRinaPat."""
		emoji=discord.utils.find(lambda emoji: emoji.name.lower() == emote.lower(),self.bot.emojis)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))


	@commands.command()
	@Checks.is_niji()
	async def rank(self,ctx,idx=1):
		"""Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
		await ctx.send(await self.bot.messageHandler.getPB(ctx.message.author,idx))

	@commands.command()
	async def llas(self,ctx,*,query):
		async with ctx.typing():
			response=requests.get("http://all-stars-api.uc.r.appspot.com/cards/search?query={0}".format(str(query)))
			data= (response.json()[0])
			await ctx.send(data["rarity"]["abbreviation"]+" "+data["idol"]["firstName"]+" "+data["idol"]["lastName"]+" "+data["idolizedTitle"])

def setup(bot):
	bot.add_cog(Fun(bot))
