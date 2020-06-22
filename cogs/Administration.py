import asyncio
import discord
from discord.ext import commands
from .utilities import Utils, Checks
import os
import io
import pytz
import datetime
import json


async def is_admin(ctx):
	try:
		if ctx.author.permissions_in(ctx.message.channel).administrator:
			return True
		return False
	except Exception as e:
		print(e)
		return False

# used for purging, since we want to selectively check if messages are by the user currently being targetted. TODO find better way to implement this


def isTarget(msg):
	global target
	if msg.author.id in target:
		return True
	return False


def adminRxn(rxn, user):
	global target
	if not rxn.message.author.id == 613501680469803045:
		return False
	if user.permissions_in(rxn.message.channel).administrator and not user.bot and user.id in target:
		if str(rxn.emoji) in [u"\U0001F5D1", "🔨", "🚫"]:
			return True
		return False
	else:
		return False


def saveConfig(ctx):
	print("saving")
	with open('Resources.json', 'w') as outfile:
		json.dump(ctx.bot.config, outfile)


class Administration(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		global target
		target = []

	@commands.command(hidden=True)
	@Checks.is_me()
	async def uwu(self, ctx, *, msg=" "):
		"""test command please ignore"""
		print(ctx.message.content)
		await ctx.send(msg)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not(member.guild.id in self.bot.config["logEnabled"]):
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(member.guild.id)])
		embd = Utils.genLog(member, "has joined the server.")
		embd.color = discord.Color.teal()
		await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if not(member.guild.id in self.bot.config["logEnabled"]):
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(member.guild.id)])
		embd = Utils.genLog(member, "has left the server.")
		embd.color = discord.Color.dark_red()
		await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.guild is None:
			return
		if message.author.bot:
			return
		if not(message.guild.id in self.bot.config["logEnabled"]):
			return
		att = None
		try:
			fileList = [discord.File(io.BytesIO(await x.read(use_cached=True)), filename=x.filename, spoiler=True) for x in message.attachments]
		except discord.errors.NotFound as e:
			print("error downloading file: {0}".format(e))
			att = [x.proxy_url for x in message.attachments]
		log = self.bot.get_channel(
			self.bot.config["log"][str(message.guild.id)])

		embd = discord.Embed()
		embd.title = message.author.display_name
		embd.description = "{0}'s Message was deleted from {1}".format(
			message.author, message.channel)
		embd = embd.set_thumbnail(url=message.author.avatar_url)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd = embd.add_field(name='Discord Username',
                        value=str(message.author))
		embd = embd.add_field(name='id', value=message.author.id)
		embd = embd.add_field(name='Joined', value=message.author.joined_at)
		embd.color = discord.Color.red()
		embd = embd.add_field(name='Channel', value=message.channel.name)
		if message.clean_content:
			embd = embd.add_field(name='Message Content',
                         value=message.clean_content, inline=False)
		else:
			embd = embd.add_field(
				name='Message Content', value="`contents of message was empty`", inline=False)
		if att is not None:
			embd = embd.add_field(name='Attachments',
                         value="\n".join(att), inline=False)
			await log.send(embed=embd)
		elif fileList is None or len(fileList) < 1:
			await log.send(embed=embd, files=fileList)
		else:
			await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_message_edit(self, original, message):
		if message.guild is None:
			return
		if message.author.bot:
			return
		if not(message.guild.id in self.bot.config["logEnabled"]):
			return
		if original.clean_content == message.clean_content:
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(message.guild.id)])
		embd = discord.Embed()
		embd.title = message.author.display_name
		embd.description = "{0}'s message was edited in {1}".format(
			message.author, message.channel)
		embd = embd.set_thumbnail(url=message.author.avatar_url)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd.colour = discord.Color.gold()
		embd = embd.add_field(
			name='Jump Link', value="[Here](" + message.jump_url + ")")
		embd = embd.add_field(name='Original Content',
                        value=original.clean_content)
		embd = embd.add_field(name='Changed Content',
                        value=message.clean_content)
		await log.send(embed=embd)

	@commands.command()
	@commands.check(is_admin)
	async def log(self, ctx, msg=""):
		"""ADMIN ONLY! Use this command in your logs channel to enable logging. To disable logging type $log disable"""
		async with ctx.message.channel.typing():
			if msg.lower() == "disable":
				if ctx.message.guild.id in self.bot.config["logEnabled"]:
					self.bot.config["logEnabled"].remove(ctx.message.guild.id)
					del self.bot.config["log"][str(ctx.message.guild.id)]
			else:
				if not (ctx.message.guild.id in self.bot.config["logEnabled"]):
					self.bot.config["logEnabled"].append(ctx.message.guild.id)
				self.bot.config["log"][str(
					ctx.message.guild.id)] = ctx.message.channel.id
			emoji = Utils.getRandEmoji(ctx.guild.emojis, "yay")
			if emoji is None:
				emoji = Utils.getRandEmoji(self.bot.emojis, "yay")
			await ctx.message.add_reaction(emoji)
			saveConfig(ctx)

	@commands.command()
	@commands.check(is_admin)
	async def autorole(self, ctx, *, role):
		"""ADMIN ONLY! Use this command to set up an autorole for the server. ex. '$autorole member'. To clear type '$autorole clear'. Make sure the role is lower than Haruka's role."""
		if role.lower() == "clear":
			if str(ctx.message.guild.id) in self.bot.config["autorole"].keys():
				del self.bot.config["autorole"][str(ctx.message.guild.id)]
		else:
			autorole = discord.utils.find(
				lambda x: x.name.lower() == role.lower(), ctx.guild.roles)
			if autorole is None:
				await ctx.send("Role not found, please create the role, and make sure it is below my highest role so I can add it to users")
			else:
				self.bot.config["autorole"][str(
					ctx.message.guild.id)] = autorole.id
				await ctx.send("Autorole set to {0}. To remove this autorole, type `$autorole clear`".format(str(autorole)))
		saveConfig(ctx)

	@commands.command()
	@commands.check(is_admin)
	async def purge(self, ctx, *, msgs: int = 10):
		"""ADMIN ONLY! removes the last x messages from the channel. Haruka will ask for confirmation. leave blank for default 10. ex. '$purge 200'"""
		global target
		rxnMsg = await ctx.send("Are you sure you want to delete the last {0} messages on the server? react {1} to confirm or {2} to cancel.".format(str(msgs), u"\U0001F5D1", "🚫"))
		await rxnMsg.add_reaction(u"\U0001F5D1")
		await rxnMsg.add_reaction("🚫")
		async with ctx.message.channel.typing():
			try:
				target.append(ctx.message.author.id)
				rxn, user = await self.bot.wait_for('reaction_add', check=adminRxn, timeout=20.0)
				target.remove(ctx.message.author.id)
				if str(rxn.emoji) == u"\U0001F5D1":
					await ctx.message.channel.purge(limit=msgs)
					await ctx.send("purge complete")
				else:
					await ctx.send("cancelling the purge")
			except asyncio.TimeoutError:
				await rxnMsg.delete()
				target.remove(ctx.message.author.id)

		return

	@commands.command()
	@Checks.is_niji()
	@commands.check(is_admin)
	async def blacklistprop(self, ctx, *users):
		"""NIJICORD ADMIN ONLY! This blacklists a user from all the servers Haruka is on. This is only used in exceedingly rare situations like gore-spammers."""
		bans = ""
		people = ""
		async with ctx.message.channel.typing():
			for guild in self.bot.guilds:

				bans += "\n**{0}**:\n".format(guild.name)
				if guild.id in self.bot.config["ignoreBL"]:
					bans += "Guild does not take part in blacklist"
					continue
				for user in users:
					person = self.bot.get_user(int(user))
					if person is None:
						person = await self.bot.fetch_user(int(user))

					try:
						await guild.ban(person, reason="""This user was banned by {0} through haruka's blacklist function from Nijicord;
						this means you let haruka have ban permissions in your server.""".format(str(ctx.message.author)), delete_message_days=0)
						bans += ("*{0}* was banned".format(person.display_name) + "\n")
						if ctx.message.guild.id in self.bot.config["logEnabled"]:
							log = self.bot.get_channel(
								self.bot.config["log"][str(guild.id)])
							await log.send("{0} was banned through Haruka's auto-blacklist by {1} on Nijicord".format(str(person), str(ctx.message.author)))
					except Exception as e:
						bans += ("{2} not banned from {0} because of {1}".format(guild.name,
                                                               e, person.display_name) + "\n")
		try:
			await ctx.send(bans)
		except:
			await ctx.send("message too long, check my console/my log channels individually")
			print("{0} were {1}".format(people, bans))

	@commands.command()
	@Checks.is_admin()
	async def blacklist(self, ctx, *users):
		"""This blacklists a user joining this server even if they aren't in the server currently."""
		log = None
		if ctx.message.guild.id in self.bot.config["logEnabled"]:
			log = self.bot.get_channel(
				self.bot.config["log"][str(ctx.message.guild.id)])
		for user in users:
			person = self.bot.get_user(int(user))
			if person is None:
				person = await self.bot.fetch_user(int(user))
			print(person)
			try:
				await ctx.message.guild.ban(person)
				if log is not None:
					await log.send("{0} was blacklisted by Haruka on this server.".format(str(person)))
			except:
				await ctx.send("Could not ban user, please check to make sure I have the `ban user` permission.")

	@commands.group()
	@Checks.is_me()
	@commands.check(is_admin)
	async def antispam(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("""For enabling antispam be sure to make a role named 'Muted', and run `$antispam enable 
			@mention` for me to mention you, a role, or everyone in a channel when someone is muted. To disable 
			the antispam, run `$antispam disable`. To set Haruka to ignore a channel, run `$antispam ignore` 
			in that channel.""")

	@antispam.command()
	async def enable(self, ctx, mention=""):
		"""enables antispam, and sets reporting channel to be the channel it is posted in"""
		msg = ""
		if mention.lower() == "everyone":
			msg = "@everyone"
		elif len(ctx.message.mentions) > 0:
			for member in ctx.message.mentions:
				msg += member.mention
		elif len(ctx.message.role_mentions) > 0:
			for role in ctx.message.role_mentions:
				print("role {0}".format(role.mention))
				msg += role.mention
		if len(msg) > 1:
			msg += "\n"
		obj = {"ch": ctx.message.channel.id, "mention": msg}
		self.bot.config["antispam"][str(ctx.message.guild.id)] = obj
		saveConfig(ctx)

	@antispam.command()
	async def ignore(self, ctx):
		if not(ctx.message.channel.id in self.bot.config["antispamIgnore"]):
			self.bot.config["antispamIgnore"].append(ctx.message.channel.id)
			print("added")
			saveConfig(ctx)

	@commands.command()
	@commands.check(is_admin)
	async def ban(self, ctx, *, person: discord.Member):
		"""ADMIN ONLY! Bans a user that is mentioned. Haruka will ask for confirmation. Either @ing them or getting their user ID works. 
		ex. '$ban 613501680469803045'"""
		global target
		rxnMsg = await ctx.send("React {1} to purge {0}'s messages and ban then, react 🔨 to only ban them and react 🚫 to cancel".format(str(person), u"\U0001F5D1"))
		async with ctx.message.channel.typing():
			await rxnMsg.add_reaction(u"\U0001F5D1")
			await rxnMsg.add_reaction("🔨")
			await rxnMsg.add_reaction("🚫")
			try:
				target.append(ctx.message.author.id)
				rxn, user = await self.bot.wait_for('reaction_add', check=adminRxn, timeout=20.0)
				target.remove(ctx.message.author.id)
				if str(rxn.emoji) == u"\U0001F5D1":
					# target = person
					# for ch in ctx.message.guild.text_channels:
					#	await ch.purge(check=isTarget)
					# target=None
					await ctx.send("purge complete")
					await person.ban(delete_message_days=7)
				elif str(rxn.emoji) == "🔨":
					await person.ban()
				else:
					await ctx.send("cancelling the ban")
			except asyncio.TimeoutError:
				await rxnMsg.delete()
				target.remove(ctx.message.author.id)
			return

	@commands.command()
	@commands.check(is_admin)
	async def prune(self, ctx, *, person: discord.Member):
		"""ADMIN ONLY! Removes all messages by a given user"""
		global target
		while target != None:
			await asyncio.sleep(10)
		rxnMsg = await ctx.send("""Are you sure you want to delete all messages in the past 2 weeks by 
		{0}? React {1} to confirm or 🚫 to cancel.""".format(str(person), u"\U0001F5D1"))
		async with ctx.message.channel.typing():
			await rxnMsg.add_reaction(u"\U0001F5D1")
			await rxnMsg.add_reaction("🚫")
			try:
				target.append(ctx.message.author.id)
				rxn, user = await self.bot.wait_for('reaction_add', check=adminRxn, timeout=20.0)
				target.remove(ctx.message.author.id)
				if str(rxn.emoji) == u"\U0001F5D1":
					target = person
					for ch in ctx.message.guild.text_channels:
						await ch.purge(check=isTarget)
					target = None
				elif str(rxn.emoji) == "🚫":
					await ctx.send("cancelling prune")
			except asyncio.TimeoutError:
				await rxnMsg.delete()
				target.remove(ctx.message.author.id)
			return


def setup(bot):
	bot.add_cog(Administration(bot))
