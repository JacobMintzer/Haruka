import asyncio
import datetime
import io
import os

import discord
import pytz
import requests
from discord.ext import commands

from .utilities import checks, utils


async def score_enabled(ctx):
	try:
		if ctx.guild.id in ctx.bot.config["scoreEnabled"]:
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


def isPruneTarget(msg):
	global pruneTarget
	if msg.author.id in pruneTarget:
		return True
	return False


def adminRxn(rxn, user):
	global target
	if not rxn.message.author.id == 613501680469803045:
		return False
	if rxn.message.channel.permissions_for(user).administrator and not user.bot and user.id in target:
		if str(rxn.emoji) in [u"\U0001F5D1", "🔨", "🚫"]:
			return True
		return False
	else:
		return False


class Administration(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		global target
		global pruneTarget
		target = []
		pruneTarget = []

	async def shutdown(self, ctx):
		pass

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not(str(member.guild.id) in self.bot.config["log"].keys()):
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(member.guild.id)])
		embd = utils.genLog(member, "has joined the server.")
		embd.color = discord.Color.teal()
		await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if not(str(member.guild.id) in self.bot.config["log"].keys()):
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(member.guild.id)])
		embd = utils.genLog(member, "has left the server.")
		embd.color = discord.Color.dark_red()
		await log.send(embed=embd)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.guild is None:
			return
		if message.author.bot:
			return
		if not(str(message.author.guild.id) in self.bot.config["log"].keys()):
			return
		if message.guild.id in self.bot.config["roleChannel"].keys() and message.channel.id == self.bot.config["roleChannel"][message.guild.id]["channel"]:
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
		embd = embd.set_thumbnail(url=message.author.display_avatar)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd = embd.add_field(name='Discord Username',
                        value=str(message.author))
		embd = embd.add_field(name='id', value=message.author.id)
		embd = embd.add_field(name='Joined', value=message.author.joined_at)
		embd.color = discord.Color.red()
		embd = embd.add_field(name='Channel', value=message.channel.name)
		if message.clean_content:
			if len(message.clean_content)>1022:
				embd = embd.add_field(name='Message Content (1)',
		                        value=(message.clean_content[:1020]+"..."))
				embd = embd.add_field(name='Message Content (2)',
		                        value=("..."+message.clean_content[1020:]))
			else:
				embd = embd.add_field(name='Message Content',
		                        value=message.clean_content)
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
		if not(str(message.guild.id) in self.bot.config["log"].keys()):
			return
		if original.clean_content == message.clean_content:
			return
		log = self.bot.get_channel(
			self.bot.config["log"][str(message.guild.id)])
		embd = discord.Embed()
		embd.title = message.author.display_name
		embd.description = "{0}'s message was edited in {1}".format(
			message.author, message.channel)
		embd = embd.set_thumbnail(url=message.author.display_avatar)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		embd.colour = discord.Color.gold()
		embd = embd.add_field(
			name='Jump Link', value="[Here](" + message.jump_url + ")")
		if len(original.clean_content)>1022:
			embd = embd.add_field(name='Original Content (1)',
	                        value=(original.clean_content[:1020]+"..."))
			embd = embd.add_field(name='Original Content (2)',
	                        value=("..."+original.clean_content[1020:]))
		else:
			embd = embd.add_field(name='Original Content',
	                        value=original.clean_content)
		if len(message.clean_content)>1022:
			embd = embd.add_field(name='Changed Content (1)',
	                        value=(message.clean_content[:1020]+"..."))
			embd = embd.add_field(name='Changed Content (2)',
	                        value=("..."+message.clean_content[1020:]))
		else:
			embd = embd.add_field(name='Changed Content',
	                        value=message.clean_content)
		await log.send(embed=embd)

	@commands.command()
	@checks.is_admin()
	async def log(self, ctx, msg=""):
		"""ADMIN ONLY! Use this command in your logs channel to enable logging. To disable logging type $log disable"""
		async with ctx.message.channel.typing():
			if msg.lower() == "disable":
				if str(ctx.message.author.guild.id) in self.bot.config["log"].keys():
					del self.bot.config["log"][str(ctx.message.guild.id)]
			else:
				self.bot.config["log"][str(
					ctx.message.guild.id)] = ctx.message.channel.id
			await utils.yay(ctx)
			utils.saveConfig(ctx)

	@commands.command()
	@checks.is_admin()
	async def autorole(self, ctx, *, role):
		"""ADMIN ONLY! Use this command to set up an autorole for the server. ex. '$autorole member'. To clear type '$autorole clear'. Make sure the role is lower than Haruka's role."""
		if role.lower() == "clear":
			if str(ctx.message.guild.id) in self.bot.config["autorole"].keys():
				del self.bot.config["autorole"][str(ctx.message.guild.id)]
			await utils.yay(ctx)
		else:
			autorole = discord.utils.find(
				lambda x: x.name.lower() == role.lower(), ctx.guild.roles)
			if autorole is None:
				await ctx.send("Role not found, please create the role, and make sure it is below my highest role so I can add it to users")
			else:
				self.bot.config["autorole"][str(
					ctx.message.guild.id)] = autorole.id
				await ctx.send("Autorole set to {0}. To remove this autorole, type `$autorole clear`".format(str(autorole)))
		utils.saveConfig(ctx)

	@commands.command()
	@checks.is_admin()
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

	@commands.command()
	@checks.is_me()
	async def banEmote(self, ctx, *, emote: int):
		foundEmote = discord.utils.find(
			lambda emoji: (emoji.id == emote), self.bot.emojis)
		if foundEmote:
			self.bot.config["emoteBanned"].append(foundEmote.guild.id)
			await ctx.send(f"server is {foundEmote.guild}", embed = self.genGuildEmbed(foundEmote.guild))
			utils.saveConfig(ctx)

	@commands.command()
	@checks.is_me()
	async def exportEmotes(self, ctx):
		for emote in ctx.message.guild.emojis:
			if emote.animated:
				try:
					request = requests.get(emote.url, allow_redirects=True)
					file = "./rina/{0}.gif".format(emote.name)
					open(file, 'wb').write(request.content)
				except:
					print("can't do {0}".format(str(emote)))

	@commands.command()
	@checks.is_me()
	async def dumpEmotes(self, ctx):
		out = ""
		for emote in self.bot.emojis:
			if (len(str(emote)) + len(out)) >= 2000:
				await ctx.send(out)
				out = str(emote)
			else:
				out += str(emote)
		await ctx.send(out)

	@commands.command()
	@checks.is_me()
	async def stk(self, ctx, *, id=None):
		if id:
			guild = self.bot.get_guild(int(id))
			embd = self.genGuildEmbed(guild)
			msgs=[""]
			for emote in guild.emojis:
				if len(msgs[-1])>1800:
					msgs+=[""]
				msgs[-1] += f"{str(emote)} "
			if msgs[0]:
				await ctx.send(embed=embd, content=msgs[0])
				for msg in msgs[1:]:
					await ctx.send(msg)
			else:
				await ctx.send(embed=embd)
			return

		for guild in self.bot.guilds:

			embd = self.genGuildEmbed(guild)
			msgs=[""]
			for emote in guild.emojis:
				if len(msgs[-1])>1800:
					msgs+=[""]
				msgs[-1] += f"{str(emote)} "
			if msgs[0]:
				await ctx.send(embed=embd, content=msgs[0])
				for msg in msgs[1:]:
					await ctx.send(msg)
			else:
				await ctx.send(embed=embd)
			await asyncio.sleep(1)

	def genGuildEmbed(self, guild):
		embd = discord.Embed()
		embd.title = guild.name
		embd.description = "Information on " + guild.name
		embd = embd.set_thumbnail(url=guild.icon_url)
		embd.type = "rich"
		embd.timestamp = datetime.datetime.now(pytz.timezone('US/Eastern'))
		dt = guild.created_at
		embd = embd.add_field(name='Date Created', value=str(
			dt.date()) + " at " + str(dt.time().isoformat('minutes')))
		embd = embd.add_field(name='ID', value=guild.id)
		embd = embd.add_field(name='Owner', value=str(guild.owner))
		embd = embd.add_field(name='Total Boosters',
		                      value=guild.premium_subscription_count)
		embd = embd.add_field(name='Total Channels', value=len(guild.channels))
		embd = embd.add_field(name='Total Members', value=guild.member_count)
		return embd

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		ch = self.bot.get_channel(self.bot.config["harukaLogs"])
		await ch.send("I joined the guild: {0}".format(str(guild)))
		embd = self.genGuildEmbed(guild)
		msgs=[""]
		for emote in guild.emojis:
			if len(msgs[-1])>1800:
				msgs+=[""]
			msgs[-1] += f"{str(emote)} "
		if msgs[0]:
			await ch.send(embed=embd, content=msgs[0])
			for msg in msgs[1:]:
				await ch.send(msg)
		else:
			await ch.send(embed=embd)
		return

	@commands.command()
	@checks.is_me()
	async def reall(self, ctx, *, query=""):
		banned = ctx.bot.config["emoteBanned"].copy()
		if ctx.message.guild:
			if ctx.message.guild.id in banned:
				banned.remove(ctx.message.guild.id)
		emojis = list(filter(lambda x: not(x.guild.id in banned) and x.available, self.bot.emojis))
		choices = [str(emoji) for emoji in emojis if query.lower() in emoji.name.lower()]
		if len(choices)==0:
			await ctx.send("none")
			return
		try:
			await ctx.send(" ".join(choices))
		except Exception as e:
			await ctx.send(f"Failed because {e}")


	@commands.command()
	@checks.is_niji()
	@checks.is_admin()
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
						if str(guild.id) in self.bot.config["log"].keys():
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
		emoji = utils.getRandEmoji(ctx.guild.emojis, "yay")
		if emoji is None:
			emoji = utils.getRandEmoji(self.bot.emojis, "yay")
		await ctx.message.add_reaction(emoji)

	@commands.command()
	@checks.is_admin()
	async def blacklist(self, ctx, *users):
		"""This blacklists a user joining this server even if they aren't in the server currently."""
		log = None
		if str(ctx.message.author.guild.id) in self.bot.config["log"].keys():
			log = self.bot.get_channel(
				self.bot.config["log"][str(ctx.message.guild.id)])
		for user in users:
			person = self.bot.get_user(int(user))
			if person is None:
				person = await self.bot.fetch_user(int(user))
			print(person)
			try:
				await ctx.message.guild.ban(person, reason="Blacklisted by {0} on this server.".format(str(ctx.message.author)))
				if log is not None:
					await log.send("{0} was blacklisted by Haruka on this server.".format(str(person)))
			except:
				await ctx.send("Could not ban user, please check to make sure I have the `ban user` permission.")
		await utils.yay(ctx)

	@commands.group()
	@checks.is_me()
	@checks.is_admin()
	@commands.check(score_enabled)
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
		elif len(mention) > 5:
			try:
				role = ctx.guild.get_role(int(mention))
				msg += role.mention
			except Exception:
				user = ctx.guild.get_user(int(mention))
				msg += user.mention
		if len(msg) > 1:
			msg += "\n"
		obj = {"ch": ctx.message.channel.id, "mention": msg}
		self.bot.config["antispam"][str(ctx.message.guild.id)] = obj
		await utils.yay(ctx)
		utils.saveConfig(ctx)

	@antispam.command()
	async def ignore(self, ctx):
		if not(ctx.message.channel.id in self.bot.config["antispamIgnore"]):
			self.bot.config["antispamIgnore"].append(ctx.message.channel.id)
			await utils.yay(ctx)
			utils.saveConfig(ctx)

	@commands.command()
	@checks.is_admin()
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
					await utils.yay(ctx)
				else:
					await ctx.send("cancelling the ban")
			except asyncio.TimeoutError:
				await rxnMsg.delete()
				target.remove(ctx.message.author.id)
			return

	@commands.command()
	@checks.is_admin()
	async def prune(self, ctx, *, person: discord.Member):
		"""ADMIN ONLY! Removes all messages by a given user"""
		global target
		global pruneTarget
		rxnMsg = await ctx.send("""Are you sure you want to delete all messages in the past 2 weeks by {0}? React {1} to confirm or 🚫 to cancel.""".format(str(person), u"\U0001F5D1"))
		async with ctx.message.channel.typing():
			await rxnMsg.add_reaction(u"\U0001F5D1")
			await rxnMsg.add_reaction("🚫")
			try:
				target.append(ctx.message.author.id)
				rxn, user = await self.bot.wait_for('reaction_add', check=adminRxn, timeout=20.0)
				target.remove(ctx.message.author.id)
				if str(rxn.emoji) == u"\U0001F5D1":
					pruneTarget.append(person)
					for ch in ctx.message.guild.text_channels:
						await ch.purge(check=isPruneTarget)
					pruneTarget.remove(person)
					try:
						await ctx.send("prune complete")
					except:
						await utils.yay(ctx)
				elif str(rxn.emoji) == "🚫":
					await ctx.send("cancelling prune")
			except asyncio.TimeoutError:
				await rxnMsg.delete()
				target.remove(ctx.message.author.id)
			return

	@commands.command()
	@checks.is_admin()
	async def urlBan(self, ctx, *, status="on"):
		if status.lower() == "on":
			if ctx.message.guild.id not in ctx.bot.config["urlKick"]:
				self.bot.config["urlKick"].append(ctx.message.guild.id)
				utils.saveConfig(ctx)
				await utils.yay(ctx)
		elif status.lower() == "off":
			if ctx.message.guild.id in ctx.bot.config["urlKick"]:
				self.bot.config["urlKick"].remove(ctx.message.guild.id)
				utils.saveConfig(ctx)
				await utils.yay(ctx)
		else:
			await ctx.send("Please send either `$urlBan on` or `$urlBan off`")




def setup(bot):
	bot.add_cog(Administration(bot))
