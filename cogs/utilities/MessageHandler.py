import discord
import re
import os
import time
import aiosqlite
import asyncio
import json
import pandas as pd
from cogs.utilities import Utils
import threading

cache = 3
spamCacheSize = 3
maxPoints = 25


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
		self.badWords = [x.strip() for x in content]

	def disconnect(self):
		self.isEnabled = False
		self.antispamLoop.cancel()

	async def initRoles(self, bot):
		self.isEnabled = True
		self.niji = discord.utils.get(bot.guilds, id=self.config["nijiCord"])
		self.anataYay = discord.utils.get(self.niji.emojis, name="AnataYay")
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
		self.antispamLoop = self.bot.loop.create_task(self.antiSpamSrv())

	async def getPB(self, user, guild, idx=1):
		if not self.isEnabled:
			return "Sorry, I can't do that at the moment, can you try again in a few seconds?"
		async with aiosqlite.connect("memberScores.db") as conn:
			cursor = await conn.execute('SELECT ID, Name, Score FROM "guild{0}" ORDER BY Score DESC'.format((str(guild.id))))
			response = await cursor.fetchall()
			result = pd.DataFrame(response)
			result.index += 1
			result.columns = ["Id", "User", "Score"]
			indexedResults = pd.Index(result["Id"])
			rank = indexedResults.get_loc(user.id)
			if idx < 1:
				idx = 1
			result = result.head(idx * 10)
			result = result.tail(10)
			result = result.drop(columns=["Id"])
			return ("```fortran\nShowing results for page {}:\nRank".format(idx) + result.to_string()[4:] + "\nCurrent rank for {0}: {1} (page {2})```".format(user.name, rank + 1, (rank // 10) + 1))

	async def addGuildToDB(self, guild):
		async with aiosqlite.connect("memberScores.db") as conn:
			cursor = await conn.execute('CREATE TABLE "guild{0}" (ID integer PRIMARY KEY, Score integer DEFAULT 0, Name text)'.format(str(guild.id)))
			await conn.commit()

	async def handleMessage(self, message, bot):
		if not((message.guild is None) or (message.guild.id in bot.config["enabled"])):
			return
		if message.content == "<@!{0}>".format(self.bot.user.id):
			await message.channel.send("Hello! My name is Haruka! My Commands can be accessed with the `$` prefix. If you want help setting up the server, try `$setup`. For general help try `$help`. I hope we can become great friends ❤️")
		if (message.guild is not None) and (message.guild.id == self.bot.config["nijiCord"]):
			if not (self.cooldown or message.author.bot):
				await self.meme(message)
			if (("gilfa" in message.content.lower()) or ("pregario" in message.content.lower()) or ("pregigi" in message.content.lower())) and message.channel.id != 611375108056940555:
				await message.channel.send("No")
				await message.delete()
		if not (message.author.bot):
			if not self.isEnabled and message.content.startswith("$"):
				await message.channel.send("Sorry, I can't do that at the moment, can you try again in a few seconds?")
				return
			await bot.process_commands(message)
		try:
			if message.guild is None or not (message.guild.id in bot.config["scoreEnabled"]):
				return
		except Exception as e:
			print(e)
			return
		if not (message.channel.id in bot.config["scoreIgnore"]):
			score = await self.score(message.author, message.content.startswith('$'), message.guild)
			if str(message.guild.id) in bot.config["antispam"].keys():
				await self.antiSpam(message, score)
			if not (score is None) and str(message.guild.id) in self.config["roleRanks"].keys():
				if message.guild.id == bot.config["nijiCord"]:
					await self.checkNijiRanks(message, score)
				elif not(message.author.bot):
					await self.checkRanks(message, score)

	async def checkRanks(self, message, score):
		roles = self.config["roleRanks"][str(message.guild.id)]
		for role in roles:
			if score > role["score"]:
				foundRole=message.guild.get_role(role["role"])
				if not(foundRole in message.author.roles):
					await message.author.add_roles(foundRole)
					await message.channel.send("{0} has been promoted to the role {1}".format(str(message.author), str(foundRole)))
			else:
				break
		
		


	async def checkNijiRanks(self, message, score):
		thresh = self.config["threshold"]
		givenRole = ""
		if score == 69 or score == 6969:
			await message.channel.send("nice")
		if score > thresh["exec"]:
			if not(self.roles["exec"] in message.author.roles):
				givenRole = "exec"
				old = self.roles["sr"]
		elif score > thresh["sr"]:
			if not(self.roles["sr"] in message.author.roles):
				givenRole = "sr"
				old = self.roles["jr"]
		elif score > thresh["jr"]:
			if not(self.roles["jr"] in message.author.roles):
				givenRole = "jr"
				old = self.roles["new"]
		elif score > thresh["new"]:
			if not(self.roles["new"] in message.author.roles):
				givenRole = "new"
				old = self.roles["app"]
		if givenRole == "":
			return
		rankUpMsg = self.config["msgs"][givenRole]
		newRole = self.roles[givenRole]
		hug = Utils.getRandEmoji(self.bot.emojis, "suteki")
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
				await self.mute(message.author, "banned word:\n {0}\n in {1}".format(message.content, message.channel))
				return False
		if score is None or score < 10:
			modifier = 4
		elif score < 100:
			modifier = 2
		else:
			modifier = 1
		points = 1
		if '@everyone' in message.content:
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

	async def test(self, guild, auth):
		rankUpMsg = self.config["msgs"]["sr"]
		hug = self.anataYay
		return rankUpMsg.format(auth.mention, str(hug))

	async def meme(self, message):
		cdTime = 90
		if message.channel.id == 696402682168082453:
			return
		content = re.sub(r'<[^>]+>', '', message.content).lower()
		if "kasukasu" in content or ("kasu kasu" in content and not("nakasu kasumi" in content or "nakasukasumi")):
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
			await message.channel.send("Hey, April Fools Day is over, they're Nijigasaki!")
		else:
			return
		self.bot.loop.create_task(self.memeCooldown(cdTime))

	async def memeCooldown(self, cdTime=90):
		await asyncio.sleep(cdTime)
		self.cooldown = False

	async def score(self, author, isCommand, guild):
		async with aiosqlite.connect("memberScores.db") as conn:
			score = -1
			if not author.id in self.MRU:
				cursor = await conn.execute('SELECT Score,Name FROM "guild{0}" WHERE ID=?'.format(str(guild.id)), (author.id,))
				newScore = await cursor.fetchone()
				await cursor.close()
				if newScore == None:
					cursor = await conn.execute('INSERT INTO "guild{0}" (ID,Name,Score) VALUES (?,?,1)'.format(str(guild.id)), (author.id, str(author)[:-5]))
				else:
					if isCommand:
						return newScore[0]
					cursor = await conn.execute('UPDATE "guild{0}" SET Score=?,Name=? WHERE ID=?'.format(str(guild.id)), (newScore[0] + 1, str(author)[:-5], author.id))
					score = newScore[0] + 1
				self.MRU.insert(0, author.id)
				if len(self.MRU) > cache:
					self.MRU.pop()
			await conn.commit()
			if score < 0:
				return None
			return score

	# april fools day replacement
	""" async def pdpIfy(self,message):
		if(message.author.bot):
			return False
		if (message.content[0]=='|'):
			return False
		if (message.content[0]=="$"):
			return False
		content=message.content
		content=re.sub(r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>','',content)
		testContent=content.lower().replace("again","")
		testContent=testContent.replace("wait","")
		testContent=testContent.replace("senpai","")
		if bool([ele for ele in self.girls if(ele in testContent)]): #"niji" in content.lower() or "ayumu" in content.lower() or "karin" in content.lower():
			msg=content
			regex=re.compile(re.escape('nijigasaki'),re.IGNORECASE)
			msg=regex.sub('PDP',msg)
			regex=re.compile(re.escape('nijigaku'),re.IGNORECASE)
			msg=regex.sub('The PDP School',msg)
			regex=re.compile(re.escape('niji'),re.IGNORECASE)
			msg=regex.sub('PDP',msg)
			regex=re.compile(re.escape('ayumu'),re.IGNORECASE)
			msg=regex.sub('Honoka 3',msg)
			regex=re.compile(re.escape('karin'),re.IGNORECASE)
			msg=regex.sub('Kanan with tiddy moles',msg)
			regex=re.compile(re.escape('kasumin'),re.IGNORECASE)
			msg=regex.sub('KasuKasu',msg)
			regex=re.compile(re.escape('kasumi'),re.IGNORECASE)
			msg=regex.sub('KasuKasu',msg)
			regex=re.compile(re.escape('setsuna'),re.IGNORECASE)
			msg=regex.sub('The self-insert weeb idol',msg)
			regex=re.compile(re.escape('shizuku'),re.IGNORECASE)
			msg=regex.sub('Volleyball target practice',msg)
			regex=re.compile(re.escape('kanata'),re.IGNORECASE)
			msg=regex.sub('zzzzzzzzzzzzzzz',msg)
			regex=re.compile(re.escape('emma'),re.IGNORECASE)
			msg=regex.sub('Emma, consumer of smaller idols',msg)
			regex=re.compile(re.escape('rina'),re.IGNORECASE)
			msg=regex.sub('Overlord Board-sama and her loyal flesh-slave',msg)
			regex=re.compile(re.escape('ai'),re.IGNORECASE)
			msg=regex.sub('The safest gyaru design of all time',msg)
			regex=re.compile(re.escape('haruka'),re.IGNORECASE)
			msg=regex.sub('Boneless Ruby',msg)
			regex=re.compile(re.escape('anata'),re.IGNORECASE)
			msg=regex.sub('Me, but if i were cuter and always talking to other cute girls',msg)
			await message.channel.send('{1} You mean `{0}`'.format(msg,message.author.mention))
			return True
		else:
			return False
	 """
