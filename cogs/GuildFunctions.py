import asyncio
import discord
import time
import datetime
import pytz
import json
from discord.ext import commands
from .utilities import MessageHandler,Utils,Checks

class GuildFunctions(commands.Cog):
	def __init__(self,bot):
		self.bot=bot


	@commands.command()
	async def info(self,ctx, member: discord.Member = None):
		"""$info for information on yourself"""
		if member == None:
			embd=Utils.genLog(ctx.message.author, "Info on {0}".format(ctx.message.author.display_name))
			embd.color=discord.Color.gold()
			await ctx.send(embed=embd)
		else:
			embd=Utils.genLog(member, "Info on {0}".format(member.display_name))
			embd.color=discord.Color.gold()
			await ctx.send(embed=embd)

	@commands.command()
	@Checks.is_admin()
	async def welcome(self,ctx,*,msg=""):
		"""ADMIN ONLY! Use this command in your welcome channel to enable welcome messages. For your message, use {0} to say the user's name, and {1} to ping the user. To disable logging type $welcome stop"""
		async with ctx.message.channel.typing():
			if msg.lower()=="stop":
				if str(ctx.message.guild.id) in self.bot.config["welcomeCh"].keys():
					del self.bot.config["welcomeCh"][str(ctx.message.guild.id)]
					del self.bot.config["welcomeMsg"][str(ctx.message.guild.id)]
			elif not msg:
				await ctx.send("You cannot have an empty welcome message. For your message, use `{0}` to say the user's name, and `{1}` to ping the user.")
			else:
				self.bot.config["welcomeCh"][str(ctx.message.guild.id)]=ctx.message.channel.id
				self.bot.config["welcomeMsg"][str(ctx.message.guild.id)]=msg
			with open('Resources.json', 'w') as outfile:
				json.dump(self.bot.config, outfile)
			emoji=Utils.getRandEmoji(ctx.guild.emojis,"yay")
			if emoji is None:
				emoji = Utils.getRandEmoji(self.bot.emojis,"yay")
			await ctx.message.add_reaction(emoji)
		

	@commands.command()
	async def sinfo(self,ctx):
		"""$sinfo if you want me to tell you information about this server"""
		embd=discord.Embed()
		embd.title=ctx.guild.name
		embd.description="Information on "+ctx.guild.name
		embd=embd.set_thumbnail (url=ctx.guild.icon_url)
		embd.type="rich"
		embd.timestamp=datetime.datetime.now(pytz.timezone('US/Eastern'))
		dt = ctx.guild.created_at
		embd=embd.add_field(name = 'Date Created', value = str(dt.date())+" at "+str(dt.time().isoformat('minutes')))
		embd=embd.add_field(name = 'ID', value = ctx.guild.id)
		embd=embd.add_field(name = 'Owner', value = str(ctx.guild.owner))
		embd=embd.add_field(name = 'Total Boosters', value = ctx.guild.premium_subscription_count)
		embd=embd.add_field(name = 'Total Channels', value = len(ctx.guild.channels))
		embd=embd.add_field(name = 'Total Members', value = ctx.guild.member_count)
		await ctx.send(embed=embd)

	@commands.command()
	async def invite(self,ctx):
		"""Generate an link to invite Haruka to your server"""
		await ctx.send("To invite Haruka to your sever, please click this link https://discord.com/api/oauth2/authorize?client_id=613501680469803045&permissions=268774468&scope=bot")

	@commands.command(name="iam")
	async def Iam(self,ctx,*, arole=''):
		"""Use this command to give a self-assignable role.(usage: $iam groupwatch) For a list of assignable roles, type $asar."""
		if not (str(ctx.message.guild.id) in self.bot.config["asar"].keys()):
			await ctx.send("This server has no self-assignable roles. Please have an admin use `$asar add rolename` to make roles self-assignable.")
		guild=ctx.message.guild
		if arole.lower() in self.bot.config["asar"][str(ctx.message.guild.id)]:
			role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), ctx.guild.roles)
			if role is None:
				await ctx.send("Hmmm, it looks  like the role you requested has been deleted. I will remove it from self assignable.")
				self.bot.config["asar"][str(ctx.message.guild.id)].remove(arole.lower())
				Utils.saveConfig(ctx)
			await ctx.message.author.add_roles(role)
			rxn=Utils.getRandEmoji(guild.emojis,"hug")
			if rxn is None:
				rxn = Utils.getRandEmoji(ctx.bot.emojis,"harukahug")
			await ctx.message.add_reaction(rxn)
		else:
			await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(self.bot.asar)))

	@commands.command(name="iamn")
	async def Iamn(self,ctx,*, arole=''):
		"""Use this command to remove a self-assignable role.(usage: $iamn groupwatch) For a list of assignable roles, type $asar."""
		guild=ctx.message.guild
		if arole.lower() in self.bot.config["asar"][str(ctx.message.guild.id)]:
			role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), ctx.guild.roles)
			await ctx.message.author.remove_roles(role)
			rxn=Utils.getRandEmoji(guild.emojis,"hug")
			if rxn is None:
				rxn = Utils.getRandEmoji(ctx.bot.emojis,"harukahug")
			await ctx.message.add_reaction(rxn) 
		else:
			await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(self.bot.asar)))

	@commands.group()
	async def asar(self,ctx):
		"""Use this command to list all self-assignable roles. Admins can add and remove roles from asar with '$asar add rolename' and '$asar remove rolename'"""
		if ctx.invoked_subcommand is None:
			roleMessage = "`, `".join(self.bot.config["asar"][str(ctx.message.guild.id)])
			await ctx.send("Self assignable roles here are: \n`{0}`.".format(roleMessage))

	@asar.command()
	@Checks.is_admin()
	async def add(self,ctx,*,role=""):
		"""ADMIN ONLY! Use this command to add roles to self-assignable with '$iam'. If a role with given name is not found, one will be created. Make sure the role is lower than haruka's highest role. ex. '$asar add roleName'"""
		if role == "":
			await ctx.send("Please enter a role")
			return
		if not str(ctx.message.guild.id) in self.bot.config["asar"].keys():
			self.bot.config["asar"][str(ctx.message.guild.id)]=[]
		requestedRole=discord.utils.find(lambda x: x.name.lower()==role.lower(),ctx.message.guild.roles)
		if requestedRole is None:
			try:
				await ctx.message.guild.create_role(name=role)
				self.bot.config["asar"][str(ctx.message.guild.id)].append(role.lower())
				await ctx.send("Role `{0}` was not found, so I created it, and it was added to the self-assignable roles.".format(role))
				Utils.saveConfig(ctx)
			except:
				await ctx.send("Role `{0}` not found, and I was unable to create the role. Please modify my permissions to manage roles so I can assign roles.".format(role))
		else:
			self.bot.config["asar"][str(ctx.message.guild.id)].append(role.lower())
			Utils.saveConfig(ctx)
			await ctx.send("Role {0} added to self-assignable roles.".format(requestedRole.name))

	@asar.command()
	@Checks.is_admin()
	async def remove(self,ctx,*,role=""):
		"""ADMIN ONLY! Use this command to remove roles from self-assignable with '$iam'. ex. '$asar remove roleName'"""
		if role == "":
			await ctx.send("Please enter a role")
			return
		if role.lower() in self.bot.config["asar"][str(ctx.message.guild.id)]:
			self.bot.config["asar"][str(ctx.message.guild.id)].remove(role.lower())
			Utils.saveConfig(ctx)
		else:
			await ctx.send("Role `{0}` not found in self assignable list.".format(role))

	@commands.command(name="pronoun")
	async def Pronoun(self,ctx, action='', pronoun=''):
		"""Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod."""
		member=ctx.message.author
		theyRole = discord.utils.find(lambda x: x.name == "p:they/them", ctx.guild.roles)
		if theyRole is None:
			return
		if action=="" or pronoun=="":
			await ctx.send("Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
			return
		if pronoun.lower().strip() == 'they':
			role = theyRole
		elif pronoun.lower().strip() == 'she':
			role = discord.utils.find(lambda x: x.name == "p:she/her", ctx.guild.roles)
		elif pronoun.lower().strip() == 'he':
			role = discord.utils.find(lambda x: x.name == "p:he/him", ctx.guild.roles)
		else:
			await ctx.send("please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
			return

		if action.strip().lower() == "add":
			await member.add_roles(role)
		elif action.strip().lower() == "remove":
			await member.remove_roles(role)
		else:
			await ctx.send("please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
		rxn=Utils.getRandEmoji(ctx.guild.emojis,"hug")
		if rxn is None:
			rxn = "👍"
		await ctx.message.add_reaction(rxn)


	@commands.command(name="best")
	async def best(self,ctx, *, role):
		"""Show your support for your best girl! Ex. '$best Kanata' will give you the kanata role. '$best clear' will clear your role."""
		if not( str(ctx.message.guild.id) in ctx.bot.config["girls"].keys()):
			return
		roleNames=self.bot.config["girls"][str(ctx.message.guild.id)]
		if role.lower()=="clear":
			role="clear"
		elif role.title() not in roleNames:
			await ctx.send("Not a valid role.")
			return
		await self.setRole(ctx,roleNames,role,role.lower()+"yay")
		return

	@commands.command()
	@Checks.is_niji()
	async def seiyuu(self,ctx,*,role):
		"""Show your support for your favorite seiyuu! Ex. '$seiyuu Miyu' will give you the Miyu role. '$seiyuu clear' will clear your role."""
		roleNames=self.bot.config["seiyuu"]
		if role.lower()=="clear":
			role="clear"
		elif role.title() not in roleNames:
			await ctx.send("Not a valid role.")
			return
		await self.setRole(ctx,roleNames,role)
		return

	@commands.command()
	@Checks.is_niji()
	async def sub(self,ctx,*,role):
		"""Show your support for your favorite subunit! Ex. '$sub QU4RTZ' will give you the QU4RTZ role. '$sub clear' will clear your role."""
		roleNames=self.bot.config["sub"]
		if role.lower() == "diverdiva" or role.lower() == "diver diva":
			roleName="DiverDiva"
		elif role.lower()=="azuna" or role.lower()=="a・zu・na":
			roleName="A・ZU・NA"
		elif role.lower()=="qu4rtz" or role.lower()=="quartz":
			roleName="QU4RTZ"
		elif role.lower()=="clear":
			roleName="clear"
		else:
			await ctx.send("Not a valid subunit")
		await self.setRole(ctx,roleNames,roleName)

	async def setRole(self,ctx,allRoles,role,rxnChoice=None):
		async with ctx.typing():
			member=ctx.message.author
			roles=list(filter(lambda x: x.name in allRoles, ctx.message.guild.roles))
			requestedRole=discord.utils.find(lambda x: x.name.lower()==role.lower(), roles)
			await member.remove_roles(*roles, atomic=True)
			if not(role=="clear"):
				await member.add_roles(requestedRole)
			if rxnChoice is None:
				emoji=Utils.getRandEmoji(ctx.guild.emojis,"yay")
				if emoji is None:
					emoji=Utils.getRandEmoji(self.bot.emojis,"yay")
			else:
				if rxnChoice.lower() == "setsunayay":
					rxnChoice=rxnChoice.replace("etsuna","etsu")
				emoji=Utils.getRandEmoji(self.bot.emojis,rxnChoice)
				if emoji == "No Emoji Found" or emoji is None:
					emoji=Utils.getRandEmoji(self.bot.emojis,"harukayay")
			await ctx.message.add_reaction(emoji) #"👍")
		return

def setup(bot):
	bot.add_cog(GuildFunctions(bot))
