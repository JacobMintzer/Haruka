import asyncio
import os
import re
import threading
import time

import aiosqlite
import discord
import pandas as pd

from cogs.utilities import utils

cache = 3
spamCacheSize = 3
maxPoints = 60

async def scheduleDelete(message):
	await asyncio.sleep(10)
	await message.delete()

class MessageHandler():
	def __init__(self, config, bot):
		self.isEnabled = False
		self.bot = bot
		self.config = config
		self.MRU = []
		self.antiSpamCache = {}
		self.antiSpamScores = {}
		self.cooldown = False
		with open("bad-words.txt") as f:
			content = f.readlines()
		self.badWords = [x.strip() for x in content if x.strip()]
		self.tempRegex = re.compile(r"""(-?)(\d{1,3})(C|F|c|f)(?![^\s.,;?!`':>"])""")

	def disconnect(self):
		self.isEnabled = False
		self.antispamLoop.cancel()

	async def initRoles(self, bot):
		self.roles = {}
		self.isEnabled = True
		self.antispamLoop = self.bot.loop.create_task(self.antiSpamSrv())
		self.niji = discord.utils.get(bot.guilds, id=self.config["nijiCord"])
		# this prevents failure when not in nijicord, such as my test environment
		if self.niji in bot.guilds:
			roles = {}
			roles["new"] = discord.utils.get(
				self.niji.roles, name="New Club Member")
			roles["jr"] = discord.utils.get(
				self.niji.roles, name="Junior Club Member")
			roles["sr"] = discord.utils.get(
				self.niji.roles, name="Senior Club Member")
			roles["exec"] = discord.utils.get(
				self.niji.roles, name="Executive Club Member")
			roles["app"] = discord.utils.get(
				self.niji.roles, name="Idol Club Applicant")
			self.roles = roles

	async def getPB(self, user, guild, idx=1):
		async with aiosqlite.connect("memberScores.db") as conn:
			cursor = await conn.execute('SELECT ID, Name, Score FROM "guild{0}" ORDER BY Score DESC'.format((str(guild.id))))
			response = await cursor.fetchall()
			result = pd.DataFrame(response)
			result.index += 1
			result.columns = ["Id", "User", "Score"]
			try:
				indexedResults = pd.Index(result["Id"])
			except KeyError:
				cursor = await conn.execute('INSERT INTO "guild{0}" (ID,Name,Score) VALUES (?,?,1)'.format(str(guild.id)), (user.id, str(user)[:-5]))
			rank = indexedResults.get_loc(user.id)
			if idx < 1:
				idx = 1
			result = result.head(idx * 10)
			result = result.tail(10)
			result = result.drop(columns=["Id"])
			return ("```fortran\nShowing results for page {}:\nRank".format(idx) + result.to_string()[4:] + "\nCurrent rank for {0}: {1} (page {2})```".format(user.name, rank + 1, (rank // 10) + 1))

	async def addGuildToDB(self, guild):
		async with aiosqlite.connect("memberScores.db") as conn:
			await conn.execute('CREATE TABLE "guild{0}" (ID integer PRIMARY KEY, Score integer DEFAULT 0, Name text)'.format(str(guild.id)))
			await conn.commit()
	
	async def wipeGuildScore(self, guild):
		async with aiosqlite.connect("memberScores.db") as conn:
			await conn.execute('DELETE FROM "guild{0}"'.format(str(guild.id)))
			await conn.commit()


	async def handleMessage(self, message, bot):
		if message.guild and message.guild.id in bot.config["roleChannel"].keys() and message.channel.id == bot.config["roleChannel"][message.guild.id]["channel"]:
			if not(message.content.startswith("$") or message.author.id == bot.user.id):
				await message.delete()
				return
			elif message.author.id == bot.user.id and (message.id not in bot.config["roleChannel"][message.guild.id]["message"]):
				bot.loop.create_task(scheduleDelete(message))
				return
		if message.guild and message.guild.id in self.bot.config["nitroSpamMute"]:
			await self.checkForNitroSpam(message,self.bot.config["nitroSpamMute"][message.guild.id])
		if message.content == "<@!{0}>".format(self.bot.user.id):
			await message.channel.send("Hello! My name is Haruka! My Commands can be accessed with the `$` prefix. If you want help setting up the server, try `$setup`. For general help try `$help`, or DM `Junior Mints#2525`. I hope we can become great friends ❤️")
		if (message.guild is not None) and (message.guild.id == self.bot.config["nijiCord"]):
			try:
				await self.log(message)
			except Exception as e:
				print(f"error logging nijiMsg {e}")
			if not (self.cooldown or message.author.bot):
				await self.meme(message)
			if not (message.author.bot):
				if (tempMatch:=self.tempRegex.search(message.content)) and not(message.content.lower().startswith("$temp")):
					temperature = tempMatch.group(0)
					unit = temperature[-1]
					if temperature[0] == '-':
						magnitude = 0-(int(temperature[1:-1]))
					else:
						magnitude = int(temperature[:-1])
					if unit.lower() == 'c':
						res = "{0}​C is {1:.1f}​F".format(magnitude,magnitude*9/5+32)
					else:
						res = "{0}​F is {1:.1f}​C".format(magnitude,(magnitude-32)*5/9)
					await message.channel.send(res)
				elif instaURL:=re.search("(?P<url>https?://[^\s]+instagram\.com[^\s]+)", message.content, re.IGNORECASE):
					if  len(message.attachments)>0:
						try:
							embd = utils.getInstaEmbed(bot.config["instagramAccessToken"], instaURL.group(0))
							await message.channel.send(embed=embd)
						except Exception as e:
							print(f"error while parsing insta embed:\n {str(e)}")
							pass
					else:
						print("didn't post embed because there's an attachment")

		if not (message.author.bot):
			if message.guild and message.guild.id in bot.config["roleChannel"].keys() and message.channel.id==bot.config["roleChannel"][message.guild.id]["channel"]:
				bot.loop.create_task(scheduleDelete(message))
			await bot.process_commands(message)
		try:
			if message.guild is None or not (message.guild.id in bot.config["scoreEnabled"]):
				return
		except Exception as e:
			print(e)
			return
		if not (message.channel.id in bot.config["scoreIgnore"]):
			if (message.guild.id == bot.config["nijiCord"] or not(message.author.bot)):
				score = await self.score(message.author, message.content.startswith('$'), message.guild, message)
				if str(message.guild.id) in bot.config["antispam"].keys():
					await self.antiSpam(message, score)

				if not (score is None) and message.guild.id == bot.config["nijiCord"]:
					if not self.isEnabled:
						return
					await self.checkNijiRanks(message, score)
				elif not (score is None) and str(message.guild.id) in self.config["roleRanks"].keys() and not(message.author.bot):
					await self.checkRanks(message, score)

	async def checkRanks(self, message, score):
		roles = self.config["roleRanks"][str(message.guild.id)]
		for role in roles:
			if score >= role["score"]:
				foundRole = message.guild.get_role(role["role"])
				if not foundRole:
					print(f"Rank {role['role']} acheived at score {role['score']}doesn't exist in {message.guild.name}")
					break
				if not(foundRole in message.author.roles):
					await message.author.add_roles(foundRole)
					await message.channel.send("{0} has been promoted to the role {1}".format(str(message.author), str(foundRole)))
			else:
				break

	async def checkNijiRanks(self, message, score):
		thresh = self.config["threshold"]
		givenRole = ""
		if score >= thresh["exec"]:
			if not(self.roles["exec"] in message.author.roles):
				givenRole = "exec"
				old = self.roles["sr"]
		elif score >= thresh["sr"]:
			if not(self.roles["sr"] in message.author.roles):
				givenRole = "sr"
				old = self.roles["jr"]
		elif score >= thresh["jr"]:
			if not(self.roles["jr"] in message.author.roles):
				givenRole = "jr"
				old = self.roles["new"]
		elif score >= thresh["new"]:
			if not(self.roles["new"] in message.author.roles):
				givenRole = "new"
				old = self.roles["app"]
		if givenRole == "":
			return
		rankUpMsg = self.config["msgs"][givenRole]
		newRole = self.roles[givenRole]
		hug = utils.getRandEmoji(self.bot.emojis, "suteki")
		await message.author.remove_roles(old)
		await message.author.add_roles(newRole)
		await message.channel.send(rankUpMsg.format(message.author.mention, str(hug)))

	async def antiSpamSrv(self):
		print("starting service")
		while True:
			keys = list(self.antiSpamScores)
			for user in keys:
				if self.antiSpamScores[user] <= 5:
					del self.antiSpamScores[user]
					del self.antiSpamCache[user]
				else:
					self.antiSpamScores[user] -= 5
			await asyncio.sleep(5)

	async def antiSpam(self, message, score):
		if score == -1:
			return True
		if not (str(message.guild.id) in self.bot.config["antispam"].keys()):
			return True
		if message.channel.id in self.bot.config["antispamIgnore"]:
			return True
		if message.author.bot:
			return True
		for badWord in self.badWords:
			if badWord in message.content.lower():
				await self.mute(message.author, "banned word in {0}; check the logs".format( message.channel))
				await message.delete()
				return False
		if score is None or score < 10:
			modifier = 8
		elif score < 200:
			modifier = 4
		elif score < 500:
			modifier = 1
		else:
			return True
		points = 1
		if '@everyone' in message.content:
			points += modifier
		if "nitro" in message.content.lower():
			points += modifier
		if len(message.content) > 100:
			points += modifier
		if len(message.mentions) > 0:
			points += (len(message.mentions) * modifier)
		points += modifier * len(message.attachments)
		if message.author.id in self.antiSpamCache.keys():
			if message.content.lower() == self.antiSpamCache[message.author.id].lower():
				points += modifier
			self.antiSpamCache[message.author.id] = message.content
			self.antiSpamScores[message.author.id] += points
			totalScore = self.antiSpamScores[message.author.id]
		else:
			self.antiSpamCache[message.author.id] = message.content
			self.antiSpamScores[message.author.id] = points
			totalScore = points
		if totalScore > maxPoints:
			await self.mute(message.author, "exceeded max points at {0} where max is {1}. last message gave them {2} points".format(totalScore, maxPoints, points))
			return False
		return True

	async def mute(self, member, reason):
		role = discord.utils.find(
			lambda x: x.name.lower() == "muted", member.guild.roles)
		await member.add_roles(role)
		antispamCh = self.bot.get_channel(
			self.bot.config["antispam"][str(member.guild.id)]["ch"])
		await antispamCh.send("{2}{0} was muted for {1}".format(member.mention, reason, self.bot.config["antispam"][str(member.guild.id)]["mention"]))
		await member.send("You have been muted by my auto-moderation; a mod is currently reviewing your case.")

	async def meme(self, message):
		cdTime = 90
		if message.channel.id == 696402682168082453:
			return
		content = re.sub(r'<[^>]+>', '', message.content).lower()
		if "Krak" in message.clean_content or "KRAK" in message.clean_content:
			rxn = discord.utils.get(self.bot.emojis, name="EmmaHelp")
			await message.add_reaction(rxn)
		if "kasukasu" in content or ("kasu kasu" in content and not("nakasu kasumi" in content or "nakasukasumi")):
			rxn = discord.utils.get(message.guild.emojis, name="RinaBonk")
			await message.add_reaction(rxn)
			self.cooldown = True
			await message.channel.send("KA! SU! MIN! DESU!!!")
		elif "pooper" in content and "scooper" in content:
			rxn = discord.utils.get(message.guild.emojis, name="RinaBonk")
			await message.add_reaction(rxn)
			self.cooldown = True
			await message.channel.send("KA! SU! MIN! DESU!!!")
		elif "yoshiko" in content:
			if message.content.startswith("$llas "):
				return
			self.cooldown = True
			await message.channel.send("Dakara Yohane Yo!!!")
		elif content == "chun":
			self.cooldown = True
			await message.channel.send("Chun(・8・)Chun~")
		elif "aquors" in content:
			self.cooldown = True
			rxn = discord.utils.get(message.guild.emojis, name="RinaBonk")
			await message.add_reaction(rxn)
			await message.channel.send("AQOURS")
		elif "pdp" in content:
			self.cooldown = True
			rxn = discord.utils.get(message.guild.emojis, name="RinaBonk")
			await message.add_reaction(rxn)
			await message.channel.send("Bruh, what is it, 2017? Get with the times, boomer.")
		else:
			return
		self.bot.loop.create_task(self.memeCooldown(cdTime))

	async def memeCooldown(self, cdTime=90):
		await asyncio.sleep(cdTime)
		self.cooldown = False

	async def score(self, author, isCommand, guild, message):
		async with aiosqlite.connect("memberScores.db") as conn:
			score = -1
			cursor = await conn.execute('SELECT Score,Name FROM "guild{0}" WHERE ID=?'.format(str(guild.id)), (author.id,))
			oldScore = await cursor.fetchone()
			await cursor.close()
			if not author.id in self.MRU:
				if oldScore == None:
					try:
						cursor = await conn.execute('INSERT INTO "guild{0}" (ID,Name,Score) VALUES (?,?,1)'.format(str(guild.id)), (author.id, str(author)[:-5]))
						await conn.commit()
					except Exception as e:
						print(f"Error adding user {author.id} to score database")
						print(e)
						raise
				else:
					if isCommand:
						return oldScore[0]
					cursor = await conn.execute('UPDATE "guild{0}" SET Score=?,Name=? WHERE ID=?'.format(str(guild.id)), (oldScore[0] + 1, str(author)[:-5], author.id))
					score = oldScore[0] + 1
					await conn.commit()
					if guild.id == self.bot.config["nijiCord"] and (score == 69 or score == 6969):
						await message.channel.send("nice")
				self.MRU.insert(0, author.id)
				if len(self.MRU) > cache:
					self.MRU.pop()
			else:
				score = oldScore[0] if oldScore else -1
			if score < 0:
				return None
			return score

	async def log(self, message):
		async with aiosqlite.connect("NijiMessages.db") as conn:
			await conn.execute('INSERT INTO "Messages" (user_id,content,clean_content,channel,datetime,attachments,jump,msg_id) VALUES (?,?,?,?,?,?,?,?)', (message.author.id, message.content, message.clean_content,message.channel.id,message.created_at.timestamp(),len(message.attachments),message.jump_url,message.id))
			await conn.commit()
	
	async def checkForNitroSpam(self, message, channel_id):
		fake_discord_names = ["diiscord", "dlscord", "discocd"]
		content = message.content.lower()
		points = 0
		if len(message.mentions) + len(message.role_mentions)>2:
			points += 1
		if '@everyone' in content:
			points += 1
		if any([x in content for x in fake_discord_names]):
			points += 1
		if 'nitro' in content and ("free" in content or "gift" in content):
			points += 1
		if points >= 2:
			role = discord.utils.find(lambda x: x.name.lower() == "muted", message.guild.roles)
			await message.author.add_roles(role)
			ch = message.guild.get_channel(channel_id)
			clean = message.clean_content.replace("@", "@​").replace("`","")
			message_ch = message.channel
			try:
				await message.delete()
				success="has been deleted."
			except Exception:
				success = "has not been deleted. Please check my permissions if you want me to automatically delete messages."

			await ch.send(f"user {str(message.author)} was muted for the following message in {message_ch.mention}, which { success }\nmessage content:")
			await ch.send(f"`{clean}`")


