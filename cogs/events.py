from datetime import datetime, timedelta, timezone

import discord
import yaml
from discord.ext import commands
from unidecode import unidecode

from .utilities import checks, utils


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.starboardQueue = self.bot.config["sbq"]
		self.file_regex  = r"(https?:\/\/)?(media\.|cdn\.)?(discordapp\.com\/attachments)\/[0-9]+\/[0-9]+\/[A-z]+.\.(jpg|mp4|png|gif)"

	async def shutdown(self, ctx):
		pass


	def genStarboardPost(self, message):
		embd = discord.Embed()
		embd = embd.set_thumbnail(url=message.author.display_avatar)
		embd.type = "rich"
		embd.timestamp = message.created_at
		embd = embd.add_field(name='Author', value=message.author.mention)
		embd = embd.add_field(name='Channel', value=message.channel.mention)
		if message.clean_content:
			# add zero width space to get rid of the @everyones
			content = message.clean_content.replace("@", "@​")
			if len(content) > 1023:
				content = (content[:1020] + "...")
			embd = embd.add_field(name='Message', value=content, inline=False)
		embd = embd.add_field(
			name='Jump Link', value="[Here](" + message.jump_url + ")")
		embd.color = discord.Color.gold()
		return embd

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		emoji = payload.emoji
		if not(payload.guild_id in self.bot.config["starboard"].keys()):
			return
		ch = payload.member.guild.get_channel_or_thread(payload.channel_id)
		if type(ch) is discord.Thread:
			channel_id = ch.parent_id
		else:
			channel_id = ch.id
		if payload.channel_id == self.bot.config["starboard"][payload.guild_id]["channel"]:
			return
		if channel_id in self.bot.config["starboard"][payload.guild_id]["ignore"]:
			return
		if ch.id in self.bot.config["starboard"][payload.guild_id]["ignore"]:
			return
		if str(emoji) == self.bot.config["starboard"][payload.guild_id]["emote"]:
			message = await ch.fetch_message(payload.message_id)
			if message.created_at + timedelta(days=10) < datetime.now(timezone.utc):
				return
			user = payload.member
			if user.id == message.author.id or user.bot:
				reaction = (list(filter(lambda x: str(
					x.emoji) == self.bot.config["starboard"][message.guild.id]["emote"], message.reactions)))[0]
				try:
					await reaction.remove(message.author)
				except Exception:
					pass
				return
			if message.id in self.starboardQueue:
				return
			reactions = (list(filter(lambda x: str(
				x.emoji) == self.bot.config["starboard"][message.guild.id]["emote"], message.reactions)))
			if len(reactions) < 1:
				return
			if reactions[0].count >= self.bot.config["starboard"][message.guild.id]["count"]:
				ch = message.guild.get_channel(
					self.bot.config["starboard"][message.guild.id]["channel"])
				embd = self.genStarboardPost(message)
				files = []
				overflow_files = []
				if message.guild.premium_tier < 2:
					max_size = 8000000
				elif message.guild.premium_tier == 2:
					max_size = 50000000
				else:
					max_size = 100000000
				size = 0
				if len(message.attachments) == 1 and message.attachments[0].content_type.startswith("image/"):
					embd.set_image(url=message.attachments[0].url)
				elif len(message.attachments)>0:
					for attachment in message.attachments:
						if attachment.size + size <= max_size:
							size += attachment.size
							files.append(await attachment.to_file())
						else:
							overflow_files.append(attachment)
				if overflow_files:
					for file in overflow_files:
						embd.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)
				await ch.send(embed=embd, files=files)
				self.starboardQueue.append(message.id)
				if len(self.starboardQueue) > 200:
					self.starboardQueue.pop(0)
				self.bot.config["sbq"] = self.starboardQueue
				with open('Resources.yaml', 'w') as outfile:
					yaml.dump(self.bot.config, outfile)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		try:
			if member.guild.id in self.bot.config["urlKick"]:
				cleaned_name = member.name.lower()
				if "twitter.com" in cleaned_name or "h0nde" in cleaned_name:
					await member.kick(reason=f"url found in name {member.name=}")
					return
		except Exception as e:
			print("error in urlkick ")
			print (e)
		try:
			if member.guild.id in self.bot.config["scamYeet"]:
				banned_names = self.bot.config["scamNames"]
				cleaned_name = unidecode(member.name).replace("0",'o').replace(" ","").lower()
				for name in banned_names:
					if name in cleaned_name:
						await member.kick(reason=f"suspricious name found: {member.name=}")
						return
		except Exception as e:
			print ("error in scamyeet")
			print (e)

		if member.guild.id == self.bot.config["nijiCord"]:
			welcomeCh = self.bot.get_channel(
				self.bot.config["welcomeCh"][str(member.guild.id)])
			rules = self.bot.get_channel(self.bot.config["rulesCh"])
			await welcomeCh.send(self.bot.config["welcome"].format(member.display_name, rules.mention))
		elif str(member.guild.id) in self.bot.config["welcomeCh"].keys():
			welcomeCh = self.bot.get_channel(
				self.bot.config["welcomeCh"][str(member.guild.id)])
			welcomeMsg = self.bot.config["welcomeMsg"][str(member.guild.id)]
			await welcomeCh.send(welcomeMsg.format(member.display_name, member.mention))
		if str(member.guild.id) in self.bot.config["autorole"].keys():
			try:
				autorole = member.guild.get_role(
					self.bot.config["autorole"][str(member.guild.id)])
				await member.add_roles(autorole)
			except Exception:
				print("error adding autorole in {0}".format(member.guild.name))
		for watchedName in self.bot.config["watchList"]:
			if watchedName.lower() in member.name.lower():
				ch = self.bot.get_channel(self.bot.config["modCh"])
				await ch.send("user {2} with `thinkpad` in their name joined {0} with id {1}.".format(member.guild.name, member.id, member.name))
		

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if str(member.guild.id) in self.bot.config["farewellCh"].keys():
			farewellCh = self.bot.get_channel(
				self.bot.config["farewellCh"][str(member.guild.id)])
			farewellMsg = self.bot.config["farewellMsg"][str(member.guild.id)]
			await farewellCh.send(farewellMsg.format(member.display_name))

def setup(bot):
	print("adding events cog")
	bot.add_cog(Events(bot))
