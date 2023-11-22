import asyncio
import yaml

import discord
import io
from discord.ext import commands

from .utilities import checks, utils


class Setup(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	async def shutdown(self, ctx):
		pass

	@commands.command()
	async def setup(self, ctx):
		"""Gives information on helpful commands to get you started with Haruka"""
		msg = """Important commands for setting haruka up in the server. Note that these can only be performed by someone with the Admin permission
`$welcome <msg>`
Use this command in your welcome channel to enable welcome messages. For your message, use {0} to say the user's name, and {1} to ping the user. To disable logging type `$welcome stop`. Note that if you mention a channel in your message, it will show up  in the welcome message
ex. `$welcome Welcome {0} to Haruka's official fan discord!`

`$autorole <role>`
Use this command to set up an autorole for the server (automatically adding a role when someone joins). Haruka will confirm the name on successfully adding it. ex. `$autorole server member`. To clear type `$autorole clear`. Make sure the role is lower than Haruka's role.

`$log <msg>`
Use this command in your logs channel to enable logging. To disable logging type `$log disable`. An example of the logging can be seen in the #logs channel in Harukacord

`$asar add <rolename>`
Use this command to add a self assignable role. If it find a role with the same name, it'll use that, otherwise it will create a role.

`$asar remove <rolename>`
Removes a role from the self assignable list.
If you have any more questions please feel free to message `Junior Mints#2525`"""
		await ctx.send(msg)

	@commands.command()
	async def subscribe(self, ctx):
		"""Subscribe to updates about Haruka. You will get occasional messages about new or changed features. You can unsubscribe with '$unsubscribe' at any time. Haruka will message you directly"""
		author = ctx.message.author.id
		if author in self.bot.config["subs"]:
			await ctx.send("You are already subscribed to my updates. To unsubscribe send '$unsubscribe'.")
		else:
			self.bot.config["subs"].append(author)
			utils.saveConfig(ctx)
			await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "harukahug"))

	@commands.command()
	async def unsubscribe(self, ctx):
		"""Unsubscribe from updates about Haruka. You can resubscribe with '$subscribe'."""
		author = ctx.message.author.id
		if author in self.bot.config["subs"]:
			self.bot.config["subs"].remove(author)
			utils.saveConfig(ctx)
		await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "pensive"))

	@checks.is_admin()
	@commands.command()
	async def ignoreBlacklist(self, ctx):
		"""This command will have Haruka ignore this server for its propogated blacklisting. Note that propogated blacklisting is only used for malicious spammers."""
		if not (ctx.message.guild.id in self.bot.config["ignoreBL"]):
			self.bot.config["ignoreBL"].append(ctx.message.guild.id)
			utils.saveConfig(ctx)
			await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "harukahug"))

	@checks.is_me()
	@commands.command()
	async def addConfig(self, ctx, key: str, value: str = "str"):
		value = value.lower().strip()
		if value == "str" or value =="string":
			self.bot.config[key]=""
		elif value == "list":
			self.bot.config[key]=[]
		elif value == "dict":
			self.bot.config[key]={}
		else:
			await ctx.send("do a better data type")
			return
		utils.saveConfig(ctx)
		await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "harukahug"))



	@checks.is_admin()
	@commands.command()
	async def unIgnoreBlacklist(self, ctx):
		"""This command will have Haruka ban users for its propogated blacklisting. Note that propogated blacklisting is only used for malicious spammers."""
		if (ctx.message.guild.id in self.bot.config["ignoreBL"]):
			self.bot.config["ignoreBL"].remove(ctx.message.guild.id)
			utils.saveConfig(ctx)
			await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "harukahug"))

	@checks.is_me()
	@commands.command(hidden=True)
	async def announce(self, ctx, *, message):
		base = "Hello, this is a Haruka update. Remember you can unsubscribe at any time with $unsubscribe.\n{0}\nFor more information or questions feel free to dm `Junior Mints#2525` or ask in <https://discord.gg/qp7nuPC>."
		userList = self.bot.config["subs"]
		for sub in userList:
			try:
				user = self.bot.get_user(sub)
				await user.send(base.format(message))
			except Exception as e:
				print("could not send message to user {0} because of {1}".format(
					str(user), str(e)))
		await ctx.send(message)
		await ctx.message.delete()

	@checks.is_me()
	@commands.command(hidden=True)
	async def reload(self,ctx):
		with open('Resources.yaml', "r") as file:
			self.bot.config = yaml.full_load(file)


		
	@checks.is_me()
	@commands.command(hidden=True)
	async def umu(self,ctx):
		pass

async def setup(bot):
	await bot.add_cog(Setup(bot))
