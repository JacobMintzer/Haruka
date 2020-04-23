import asyncio
import discord
from discord.ext import commands
from .utilities import Utils

class GuildFunctions(commands.Cog):
	def __init__(self,bot):
		self.bot=bot


	@commands.command()
	async def info(self,ctx, member: discord.User = None):
		"""$info for information on yourself"""
		if member == None:
			embd=genLog(ctx.message.author, "Info on {0}".format(ctx.message.author.display_name))
			embd.color=discord.Color.gold()
			await ctx.send(embed=embd)
		else:
			embd=genLog(member, "Info on {0}".format(member.display_name))
			embd.color=discord.Color.gold()
			await ctx.send(embed=embd)

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



	@commands.command(name="iam")
	async def Iam(self,ctx,*, arole=''):
		"""Use this command to give a self-assignable role.(usage: $iam groupwatch) For a list of assignable roles, type $asar."""
		guild=ctx.message.guild
		if arole.lower() in self.bot.asar:
			role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), self.bot.allRoles)
			await ctx.message.author.add_roles(role)
			await ctx.message.add_reaction(Utils.getRandEmoji(guild,"hug")) 
		else:
			await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(self.bot.asar)))

	@commands.command(name="iamn")
	async def Iamn(self,ctx,*, arole=''):
		"""Use this command to remove a self-assignable role.(usage: $iamn groupwatch) For a list of assignable roles, type $asar."""
		guild=ctx.message.guild
		if arole.lower() in self.bot.asar:
			role=discord.utils.find(lambda x: x.name.lower()==arole.lower(), ctx.guild.roles)
			await ctx.message.author.remove_roles(role)
			await ctx.message.add_reaction(Utils.getRandEmoji(guild,"hug")) 
		else:
			await ctx.send("Please enter a valid assignable role. Assignable roles at the moment are {0}".format(str(self.bot.asar)))

	@commands.command(name="asar")
	async def Asar(self,ctx):
		"""Use this command to list all self-assignable roles. Roles can be assigned with the $iam command, and removed using the $iamn command"""
		await ctx.send(str(self.bot.asar))

	@commands.command(name="pronoun")
	async def Pronoun(self,ctx, action='', pronoun=''):
		"""Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod."""
		member=ctx.message.author
		if action=="" or pronoun=="":
			await ctx.send("Please say '$pronoun add ' or '$pronoun remove ' followed by 'he', 'she', or 'they'. If you want a different pronoun added, feel free to contact a mod.")
			return

		if pronoun.lower().strip() == 'they':
			role = discord.utils.find(lambda x: x.name == "p:they/them", ctx.guild.roles)
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
		await ctx.message.add_reaction(Utils.getRandEmoji(guild,"hug"))


	@commands.command(name="best")
	async def best(self,ctx, *, role):
		"""Show your support for your best girl! Ex. '$best Kanata' will give you the kanata role. '$best clear' will clear your role."""
		roleNames=self.bot.config["girls"]
		if role.lower()=="girl":
			role="haruka"
		elif role.lower()=="clear":
			role="clear"
		elif role.title() not in roleNames:
			await ctx.send("Not a valid role.")
			return
		member = ctx.message.author
		global allRoles
		await self.setRole(ctx,roleNames,role)
		return
		with ctx.typing():
			requestedRole = discord.utils.find(lambda x: x.name.lower() == role.lower(), allRoles)
			if (requestedRole is None) and (role!="clear"):
				print ("role {0} not found".format(requestedRole))
				await ctx.send("Sorry, there seems to be some trouble with the API, please ping Junior or another officer for assistance.")
				all=""
				for rol in all:
					all=all+(", "+str(rol))
				print(all)
			roles = list(filter(lambda x: x.name.title() in roleNames, allRoles))
			await member.remove_roles(*roles, atomic=True)
			#print('4')
			if not(role=="clear"):
				try:
					start=time.time()
					await ctx.message.author.add_roles(requestedRole)
					end=time.time()
					print("adding roles took {0}".format(end-start))
				except Exception as e:
					console.log(e)
					await ctx.send("Sorry, there seems to be some trouble with the API, please ping Junior or another officer for assistance.")
					print(str(role))
			#print('5')
			if role.lower()=="haruka":
				await ctx.message.add_reaction("❤")
			else:
				await ctx.message.add_reaction("👍")
			#print ('6')
		return

	@commands.command()
	async def seiyuu(self,ctx,*,role):
		"""Show your support for your favorite seiyuu! Ex. '$seiyuu Miyu' will give you the Miyu role. '$seiyuu clear' will clear your role."""
		roleNames=self.bot.config["seiyuu"]
		if role.lower()=="clear":
			role="clear"
		elif role.title() not in roleNames:
			await ctx.send("Not a valid role.")
			return
		member = ctx.message.author
		await self.setRole(ctx,roleNames,role)
		return
		async with ctx.typing():
			requestedRole = discord.utils.find(lambda x: x.name.lower() == role.lower(), allRoles)
			roles=list(filter(lambda x: x.name in roleNames, ctx.message.guild.roles))
			await member.remove_roles(*roles, atomic=True)
			if not(role=="clear"):
				await member.add_roles(requestedRole)
			await ctx.message.add_reaction("👍")
		return

	@commands.command()
	async def sub(self,ctx,*,role):
		"""Show your support for your favorite subunit! Ex. '$sub QU4RTZ' will give you the QU4RTZ role. '$sub clear' will clear your role."""
		member=ctx.message.author
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

	async def setRole(self,ctx,allRoles,role):
		async with ctx.typing():
			member=ctx.message.author
			roles=list(filter(lambda x: x.name in allRoles, ctx.message.guild.roles))
			requestedRole=discord.utils.find(lambda x: x.name.lower()==role.lower(), roles)
			await member.remove_roles(*roles, atomic=True)
			if not(role=="clear"):
				await member.add_roles(requestedRole)
			emoji=Utils.getRandEmoji(ctx.guild,"yay")
			await ctx.message.add_reaction(emoji) #"👍")
		return

def setup(bot):
	bot.add_cog(GuildFunctions(bot))
