import asyncio
import discord
from discord.ext import commands
from .utilities import Utils


async def is_admin(ctx):
	if not(ctx.guild.id==610931193516392472):
		return False
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		await ctx.send("You do not have permission to do this. This incident will be reported.")
		return False
	except Exception as e:
		print(e)
		return False

def isTarget(msg):
	global target
	if msg.author==target:
		return True
	return False

def adminRxn(rxn, user):
	if user.permissions_in(rxn.message.channel).administrator and not user.bot:
		if str(rxn.emoji) in [u"\U0001F5D1","🔨","🚫"]:
			return True
		return False
	else:
		return False
class Administration(commands.Cog):
	def __init__(self,bot):
		self.bot=bot
		global target
		target=None

	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def purge(self,ctx,*,msgs:int=10):
		"""ADMIN ONLY! removes the last x messages from the channel. Haruka will ask for confirmation. leave blank for default 10. ex. '$purge 200'"""
		rxnMsg=await ctx.send("Are you sure you want to delete the last {0} messages on the server? react {1} to confirm or {2} to cancel.".format(str(msgs),u"\U0001F5D1", "🚫" ))
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🚫")
		async with ctx.message.channel.typing():
			try:
				rxn, user=await self.bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
				if str(rxn.emoji)==u"\U0001F5D1":
					await ctx.message.channel.purge(limit = msgs)
					await ctx.send("purge complete")
				else:
					await ctx.send("cancelling the purge")
			except asyncio.TimeoutError:
				await rxnMsg.delete()

		return
	
	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def blacklist(self,ctx,*,user):
		person=self.bot.get_user(int(user))
		if person is None:
			person=await self.bot.fetch_user(int(user))
		print (person)
		for guild in self.bot.guilds:
			try:
				await guild.ban(person, reason="This user was banned by {0} through haruka's blacklist function from Nijicord; this means you let haruka have ban permissions in your server.".format(str(ctx.message.author)), delete_message_days=0)
				print("banned {0} from {1}".format(person.name,guild.name))
			except Exception as e:
				print("can't ban from {0} because of {1}".format(guild.name, e))

	@commands.command(hidden=True)
	@commands.check(is_admin)
	async def ban(self,ctx,*,person: discord.Member):
		"""ADMIN ONLY! Bans a user that is mentioned. Haruka will ask for confirmation. Either @ing them or getting their user ID works. ex. '$ban 613501680469803045'"""
		global target
		while target!=None:
			time.sleep(10)
		rxnMsg=await ctx.send("React {1} to purge {0}'s messages and ban then, react 🔨 to only ban them and react 🚫 to cancel".format(str(person),u"\U0001F5D1"))
		async with ctx.message.channel.typing():
			await rxnMsg.add_reaction(u"\U0001F5D1")
			await rxnMsg.add_reaction("🔨")
			await rxnMsg.add_reaction("🚫")
			try:
				rxn, user=await self.bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
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
		"""ADMIN ONLY! Removes all messages by a given user"""
		global target
		while target!=None:
			time.sleep(10)
		rxnMsg=await ctx.send("Are you sure you want to delete all messages in the past 2 weeks by {0}? React {1} to confirm or 🚫 to cancel.".format(str(person),u"\U0001F5D1"))
		async with ctx.message.channel.typing():
			await rxnMsg.add_reaction(u"\U0001F5D1")
			await rxnMsg.add_reaction("🚫")
			try:
				rxn, user=await self.bot.wait_for('reaction_add', check=adminRxn, timeout=60.0)
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
			

def setup(bot):
	bot.add_cog(Administration(bot))
