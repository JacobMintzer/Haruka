import asyncio
import discord
from discord.ext import commands

def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		return False
	except Exception as e:
		print(e)
		return False
class Administration(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
	
	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def purge(self,ctx,*,msgs:int=10):
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

	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def ban(self,ctx,*,person: discord.Member):
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


	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def prune(self,ctx,*,person: discord.Member):
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

	#@commands.command(hidden=True)
	#@commands.check(is_admin)
	#async def blacklist(self,ctx,*,id):
	#	print(id)

def setup(bot):
	bot.add_cog(Administration(bot))
