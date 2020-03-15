import discord
import re
import os
import time
import sqlite3
import asyncio
import json
import pandas as pd
from paste_bin import PasteBinApi

cache=3

class MessageHandler():
	def __init__(self,config):
		self.config=config
		self.MRU=[]
		self.conn=sqlite3.connect("Nijicord.db")
		self.db=self.conn.cursor()
		self.cooldown=False
		data=json.load(open('pastebin.json'))
		self.api=PasteBinApi(dev_key=data['key'])
		self.user_key=self.api.user_key(username=data['username'],password=data['password'])
	async def initRoles(self,bot):
		nijicord = discord.utils.get(bot.guilds, id = self.config["nijiCord"])
		roles={}
		roles["new"] = discord.utils.get(nijicord.roles, name="New Club Member")
		roles["jr"] = discord.utils.get(nijicord.roles, name="Junior Club Member")
		roles["sr"] = discord.utils.get(nijicord.roles, name="Senior Club Member")
		roles["exec"] = discord.utils.get(nijicord.roles, name="Executive Club Member")
		roles["app"] = discord.utils.get(nijicord.roles, name="Idol Club Applicant")
		self.roles=roles
	async def getPB(self,user,idx=1):
		self.db.execute("SELECT ID,Name,Score FROM memberScores ORDER BY Score DESC")
		response=self.db.fetchall()
		result=pd.DataFrame(response)
		result.index+=1
		result.columns=["Id","User","Score"]
		indexedResults=pd.Index(result["Id"])
		rank=indexedResults.get_loc(user.id)
		if idx<1:
			idx=1
		result=result.head(idx*10)
		result=result.tail(10)
		result=result.drop(columns=["Id"])
		#link=self.api.paste(self.user_key,title='activity',raw_code=result,private=1,expire_date=None)
		return ("```fortran\nShowing results for page {}:\nRank".format(idx)+result.to_string()[4:]+"\nCurrent rank for {0}: {1} (page {2})```".format(user.name,rank+1,(rank//10)+1))
	async def handleMessage(self,message,bot):
		content=message.content
		if not self.cooldown:
			await self.meme(message)
		if (("gilfa" in message.content.lower()) or ("pregario" in message.content.lower()) or ("pregigi" in message.content.lower())) and message.channel.id!=611375108056940555:
			await message.channel.send("No")
			await message.delete()
		await bot.process_commands(message)
		try:
			if (message.channel.category_id==610934583730634752 or message.channel.category_id==610934583730634752) or message.channel.id==613535108846321665:
				return
		except:
			return
		score=await self.score(message.author)
		result=None
		if not(score is None):
			if score<505 and score>=500:
				result=await self.rankUp(message.author,score)
			elif score<2505 and score>=2500:
				result=await self.rankUp(message.author,score)
			elif score%10000<=5:
				result=await self.rankUp(message.author,score)
			if not(result is None):
				rankUpMsg=self.config["msgs"][result]
				hug=discord.utils.get(message.guild.emojis,name="HarukaHug")
				await message.channel.send(rankUpMsg.format(message.author.mention,"<:HarukaHug:{0}>".format(hug.id)))

	async def meme(self,message):
		cdTime=90
		if "kasukasu" in message.content.lower() or ("kasu kasu" in message.content.lower() and not("nakasu kasumi" in message.content.lower())):
			rxn=discord.utils.get(message.guild.emojis,name="RinaBonk")
			await message.add_reaction(rxn)
			self.cooldown=True
			await message.channel.send("KA! SU! MIN! DESU!!!")
		elif "yoshiko" in message.content.lower():
			self.cooldown=True
			await message.channel.send("Dakara Yohane Yo!!!")
		elif message.content.lower()=="chun":
			self.cooldown=True
			await message.channel.send("Chun(・8・)Chun~")
		elif "aquors" in message.content.lower():
			self.cooldown=True
			await message.channel.send("AQOURS")
		else:
			return
		await asyncio.sleep(cdTime)
		self.cooldown=False
	async def score(self,author):
		score=-1
		if not author.id in self.MRU:
			self.db.execute("SELECT Score,Name FROM memberScores WHERE ID=?",(author.id,))
			newScore=self.db.fetchone()
			if newScore==None:
				self.db.execute("INSERT INTO memberScores (ID,Name) VALUES (?,?)",(author.id,str(author)[:-5]))
			else:
				self.db.execute("UPDATE memberScores SET Score=?,Name=? WHERE ID=?",(newScore[0]+1,str(author)[:-5], author.id))
				score=newScore[0]+1
			self.MRU.insert(0,author.id)
			if len(self.MRU)>cache:
				self.MRU.pop()
		self.conn.commit()
		if score<0:
			return None
		return score

	async def rankUp(self,member,score):
		announce=None
		thresh=self.config["threshold"]
		if score<thresh["new"]:
			givenRole=self.roles["app"]
		elif score<thresh["jr"]:
			if self.roles["app"] in member.roles:
				announce="new"
			givenRole=self.roles["new"]
		elif score<thresh["sr"]:
			if self.roles["new"] in member.roles:
				announce="jr"
			givenRole=self.roles["jr"]
		elif score<thresh["exec"]:
			if self.roles["jr"] in member.roles:
				announce="sr"
			givenRole=self.roles["sr"]
		else:
			if self.roles["sr"] in member.roles:
				announce="exec"
			givenRole=self.roles["exec"]
		if givenRole in member.roles:
			return None
		else:
			for role in self.roles.values():
				await member.remove_roles(role)
			await member.add_roles(givenRole)
			return announce
