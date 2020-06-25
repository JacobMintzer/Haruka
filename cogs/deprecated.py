import asyncio
import discord
import json
from discord.ext import commands
from .utilities import Utils, Checks
import aiosqlite
import re

class Deprecated(commands.Cog):
	"""This class is for commands that either were designed for a single use for setting things up, or are no longer used, and are here for future use"""
	def __init__(self, bot):
		self.bot = bot
	@commands.command()
	@Checks.is_me()
	async def ps(self, ctx):
		self.niji = discord.utils.get(
			self.bot.guilds, id=self.bot.config["nijiCord"])


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
		async with aiosqlite.connect("memberScores.db") as conn:
			for member in self.niji.members:
				print(str(member))
				if roles["sr"] in member.roles:
					score = self.bot.config["threshold"]["sr"]
				elif roles["jr"] in member.roles:
					score = self.bot.config["threshold"]["jr"]
				elif roles["new"] in member.roles:
					score = self.bot.config["threshold"]["new"]
				else:
					print("{0} has no roles".format(str(member)))
					score = 0
				if score > 0:
					try:
						cursor = await conn.execute('INSERT INTO "guild{0}" (ID,Name,Score) VALUES (?,?,?)'.format(str(self.niji.id)), (member.id, str(member)[:-5], score))
					except:
						pass
			await conn.commit()


		async with aiosqlite.connect("memberScores.db") as conn:
			with open("scores.txt") as file:
				line = file.readline()
				line = line.strip()
				while len(line) > 0:
					data = line.rpartition(" ")
					print(data)
					score = int(data[2].strip())
					user = data[0].strip()
					print(user)
					await self.addtodb(user, score, conn)
					line = file.readline()
					line = line.strip()
			await conn.commit()

	async def addtodb(self, userName, score, conn):
		user = discord.utils.find(lambda x: x.name == userName, self.niji.members)
		if user is None:
			return "{0} has score {1}".format(userName, score)
		cursor = await conn.execute('SELECT Score,Name FROM "guild{0}" WHERE Name=?'.format(str(self.niji.id)), (user.name,))
		newScore = await cursor.fetchone()
		await cursor.close()
		if newScore == None:
			cursor = await conn.execute('INSERT INTO "guild{0}" (ID,Name,Score) VALUES (?,?,?)'.format(str(self.niji.id)), (user.id, str(user)[:-5], score))
		else:
			print("{0} {3} {1} {2}".format(
				newScore[0], score, newScore[0] < score, type(newScore[0])))
			if newScore[0] < score:
				cursor = await conn.execute('UPDATE "guild{0}" SET Score=?,Name=? WHERE ID=?'.format(str(self.niji.id)), (score, str(user)[:-5], user.id))

		return

	async def pdpIfy(self,message):
		"""April fools day replacements"""
		self.girls = self.bot.config["best"][str(message.guild.id)]
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

def setup(bot):
	bot.add_cog(Deprecated(bot))
