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
	def __init__(self):
		self.MRU=[]
		self.MRU2=[]
		self.conn=sqlite3.connect("Nijicord.db")
		self.db=self.conn.cursor()
		self.cooldown=False
		data=json.load(open('pastebin.json'))
		self.api=PasteBinApi(dev_key=data['key'])
		self.user_key=self.api.user_key(username=data['username'],password=data['password'])
	async def getPB(self):
		self.db.execute("SELECT Name,Score FROM memberScores ORDER BY Score DESC")
		response=self.db.fetchall()
		result=(pd.DataFrame(response).to_string())+"\n\n"
		self.db.execute("Select Name,Score FROM memberScores2 ORDER BY Score Desc")
		response=self.db.fetchall()
		result=result+(pd.DataFrame(response).to_string())
		link=self.api.paste(self.user_key,title='activity',raw_code=result,private=1,expire_date=None)
		return link
	async def handleMessage(self,message,bot):
		content=message.content
		if not self.cooldown:
			await self.meme(message)
		if (("gilfa" in message.content.lower()) or ("pregario" in message.content.lower()) or ("pregigi" in message.content.lower())) and message.channel.id!=611375108056940555:
			await message.channel.send("No")
			await message.delete()
		await bot.process_commands(message)
		await self.score(message.author)
	async def meme(self,message):
		cdTime=90
		if "kasukasu" in message.content.lower() or ("kasu kasu" in message.content.lower() and not("nakasu kasumi" in message.content.lower())):
			kasuGun=discord.utils.get(message.guild.emojis,name="KasuGun")
			await message.add_reaction(kasuGun)
			self.cooldown=True
			await message.channel.send("KA! SU! MIN! DESU!!!")
			await asyncio.sleep(cdTime)
		elif "yoshiko" in message.content.lower():
			self.cooldown=True
			await message.channel.send("Dakara Yohane Yo!!!")
			await asyncio.sleep(cdTime)
		elif message.content.lower()=="chun":
			self.cooldown=True
			await message.channel.send("Chun(・8・)Chun~")
			await asyncio.sleep(cdTime)
		else:
			return
		self.cooldown=False
	async def score(self,author):
		if not author.id in self.MRU:
			self.db.execute("SELECT Score,Name FROM memberScores WHERE ID=?",(author.id,))
			newScore=self.db.fetchone()
			if newScore==None:
				self.db.execute("INSERT INTO memberScores (ID,Name) VALUES (?,?)",(author.id,str(author)))
			else:
				self.db.execute("UPDATE memberScores SET Score=?,Name=? WHERE ID=?",(newScore[0]+1,str(author), author.id))
			self.MRU.insert(0,author.id)
			if len(self.MRU)>cache:
				self.MRU.pop()
		if not author.id in self.MRU2:
			self.db.execute("SELECT Score,Name FROM memberScores2 WHERE ID=?",(author.id,))
			newScore=self.db.fetchone()
			if newScore==None:
				self.db.execute("INSERT INTO memberScores2 (ID,Name) VALUES (?,?)",(author.id,str(author)))
			else:
				self.db.execute("UPDATE memberScores2 SET Score=?,Name=? WHERE ID=?",(newScore[0]+1,str(author), author.id))
			self.MRU2.insert(0,author.id)
			if len(self.MRU2)>2:
				self.MRU2.pop()
		self.conn.commit()
		return False
