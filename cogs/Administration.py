import asyncio
import discord
from discord.ext import commands
from .utilities import Utils,Checks
import os
import io
import pytz
import datetime
import json

async def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		await ctx.send("You do not have permission to do this. This incident will be reported.")
		return False
	except Exception as e:
		print(e)
		return False

#used for purging, since we want to selectively check if messages are by the user currently being targetted. TODO find better way to implement this
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

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not(member.guild.id in self.bot.config["logEnabled"]):
			return
		log=self.bot.get_channel(self.bot.config["log"][str(member.guild.id)])
		embd=Utils.genLog(member,"has joined the server.")
		embd.color=discord.Color.teal()
		await log.send(embed=embd)


	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if not(member.guild.id in self.bot.config["logEnabled"]):
			return
		log=self.bot.get_channel(self.bot.config["log"][str(member.guild.id)])
		embd=Utils.genLog(member,"has left the server.")
		embd.color=discord.Color.dark_red()
		await log.send(embed=embd)

	
	@commands.Cog.listener()
	async def on_message_delete(self,message):
		if not(message.guild.id in self.bot.config["logEnabled"]):
			return
		att=None
		try:
			fileList=[discord.File(io.BytesIO(await x.read(use_cached=True)),filename=x.filename,spoiler=True) for x in message.attachments]
		except discord.errors.NotFound as e:
			print ("error downloading file: {0}".format(e))
			att=[x.proxy_url for x in message.attachments]
		log=self.bot.get_channel(self.bot.config["log"][str(message.guild.id)])
		
		embd=discord.Embed()
		embd.title=message.author.display_name
		embd.description="{0}'s Message was deleted from {1}".format(message.author,message.channel)
		embd=embd.set_thumbnail (url=message.author.avatar_url)
		embd.type="rich"
		embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd=embd.add_field(name = 'Discord Username', value = str(message.author))
		embd=embd.add_field(name = 'id', value = message.author.id)
		embd=embd.add_field(name = 'Joined', value = message.author.joined_at)
		embd.color=discord.Color.red()
		embd=embd.add_field(name = 'Channel', value = message.channel.name)
		if message.clean_content:
			embd=embd.add_field(name = 'Message Content', value = message.clean_content, inline=False)
		else:
			embd=embd.add_field(name = 'Message Content', value = "`contents of message was empty`", inline=False)
		if att is not None:
			embd=embd.add_field(name='Attachments', value="\n".join(att),inline=False)
			await log.send(embed=embd)
		elif fileList is None or len(fileList)<1:
			await log.send(embed=embd,files=fileList)
		else:
			await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_message_edit(self,original,message):
		if not( message.guild.id in self.bot.config["logEnabled"]):
			return
		if original.clean_content==message.clean_content:
			return
		log=self.bot.get_channel(self.bot.config["log"][str(message.guild.id)])
		embd=discord.Embed()
		embd.title=message.author.display_name
		embd.description="{0}'s message was edited in {1}".format(message.author,message.channel)
		embd=embd.set_thumbnail (url=message.author.avatar_url)
		embd.type="rich"
		embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd=embd.add_field(name = 'Discord Username', value = str(message.author))
		embd=embd.add_field(name = 'id', value = message.author.id)
		embd=embd.add_field(name = 'Joined', value = message.author.joined_at)
		embd.color=discord.Color.gold()
		embd=embd.add_field(name = 'Channel', value = message.channel.name)
		embd=embd.add_field(name = 'Jump Link', value=message.jump_url)
		embd=embd.add_field(name = 'Original Content', value = original.clean_content, inline=False)
		embd=embd.add_field(name= 'Changed Content', value = message.clean_content, inline=False)
		await log.send(embed=embd)


	@commands.command()
	@commands.check(is_admin)
	async def log(self,ctx,msg=""):
		"""ADMIN ONLY! Use this command in your logs channel to enable logging. To disable logging type $log stop"""
		async with ctx.message.channel.typing():
			if msg.lower()=="stop":
				if ctx.message.guild.id in self.bot.config["logEnabled"]:
					self.bot.config["logEnabled"].remove(ctx.message.guild.id)
					del self.bot.config["log"][str(ctx.message.guild.id)]
			else:
				if not (ctx.message.guild.id in self.bot.config["logEnabled"]):
					self.bot.config["logEnabled"].append(ctx.message.guild.id)
				self.bot.config["log"][str(ctx.message.guild.id)]=ctx.message.channel.id
			with open('Resources.json', 'w') as outfile:
				json.dump(self.bot.config, outfile)
			emoji=Utils.getRandEmoji(ctx.guild.emojis,"yay")
			await ctx.message.add_reaction(emoji)
		


	@commands.command()
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
	
	@commands.command()
	@Checks.is_niji()
	@commands.check(is_admin)
	async def blacklist(self,ctx,*,user):
		"""NIJICORD ADMIN ONLY! This blacklists a user from all the servers Haruka is on. This is only used in exceedingly rare situations like gore-spammers."""
		person=self.bot.get_user(int(user))
		if person is None:
			person=await self.bot.fetch_user(int(user))
		print (person)
		bans=""
		for guild in self.bot.guilds:
			try:
				await guild.ban(person, reason="This user was banned by {0} through haruka's blacklist function from Nijicord; this means you let haruka have ban permissions in your server.".format(str(ctx.message.author)), delete_message_days=0)
				bans+=("banned from {0}".format(guild.name)+"\n")
				if ctx.message.guild.id in self.bot.config["logEnabled"]:
					log=self.bot.get_channel(self.bot.config["log"][str(guild.id)])
					await log.send("{0} was banned through Haruka's auto-blacklist by {1} on Nijicord".format(str(person),str(ctx.message.author)))
			except Exception as e:
				bans+=("not banned from {0} because of {1}".format(guild.name, e)+"\n")
		await ctx.send("{0} was {1}".format(person.display_name,bans))


	@commands.command()
	@commands.check(is_admin)
	async def ban(self,ctx,*,person: discord.Member):
		"""ADMIN ONLY! Bans a user that is mentioned. Haruka will ask for confirmation. Either @ing them or getting their user ID works. ex. '$ban 613501680469803045'"""
		global target
		while target!=None:
			await asyncio.sleep(10)
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


	@commands.command()
	@commands.check(is_admin)
	async def prune(self,ctx,*,person: discord.Member):
		"""ADMIN ONLY! Removes all messages by a given user"""
		global target
		while target!=None:
			await asyncio.sleep(10)
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
