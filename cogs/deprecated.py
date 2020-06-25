import asyncio
import discord
import json
from discord.ext import commands
from .utilities import Utils, Checks
import aiosqlite

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
def setup(bot):
	bot.add_cog(Deprecated(bot))
