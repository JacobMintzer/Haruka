import asyncio
import discord
from discord.ext import commands
from .utilities import Utils

class Fun(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
	
	
	@commands.command()
	async def randomEmoji(self, ctx, emote=""):
		"""Gets a random emote from the server. Optionally add a search term. ex.'$randomEmoji yay'. '$re yay' for short."""
		emoji=Utils.getRandEmoji(ctx.message.guild, emote)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))
	@commands.command()
	async def re(self,ctx,emote=""):
		thisCog=self.bot.get_cog("Fun")
		await thisCog.randomEmoji(ctx,emote)
		
		
	@commands.command(hidden=True)
	async def e(self,ctx, emote=""):
		"""Gets emoji by name; sorthand for getEmoji"""
		thisCog=self.bot.get_cog("Fun")
		await thisCog.getEmoji(ctx, emote)

	@commands.command()
	async def getEmoji(self,ctx, emote=""):
		"""Gets an emote from the server by search term. ex. $getEmoji aRinaPat. $e aRinaPat for short."""
		emoji=discord.utils.find(lambda emoji: emoji.name.lower() == emote.lower(),self.bot.emojis)
		if emoji is None:
			await ctx.send("emoji not found")
		else:
			await ctx.send(str(emoji))

	@commands.command()
	async def rank(self,ctx,idx=1):
		"""Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
		await ctx.send(await self.bot.messageHandler.getPB(ctx.message.author,idx))




def setup(bot):
	bot.add_cog(Fun(bot))
