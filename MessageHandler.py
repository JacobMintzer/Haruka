import discord
import re
import os
import time
import sqlite3
import asyncio
import json
import pandas as pd
import Utils
#from paste_bin import PasteBinApi

cache=3

class MessageHandler():
	def __init__(self,config):
		self.config=config
		self.girls=[girl.lower() for girl in config["girls"]]
		self.girls.append("niji")
		self.girls.append("anata")
		self.MRU=[]
		self.conn=sqlite3.connect("Nijicord.db")
		self.db=self.conn.cursor()
		self.cooldown=False
		#data=json.load(open('pastebin.json'))
		#self.api=PasteBinApi(dev_key=data['key'])
		#self.user_key=self.api.user_key(username=data['username'],password=data['password'])
	async def initRoles(self,bot):
		nijicord = discord.utils.get(bot.guilds, id = self.config["nijiCord"])
		self.niji=nijicord
		self.anataYay = discord.utils.get(nijicord.emojis, name = "AnataYay")
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
	async def pdpIfy(self,message):
		if(message.author.bot):
			return False
		if (message.content[0]=='|'):
			return False
		content=message.content
		content=re.sub(r'<[^>]+>','',content)
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
	async def handleMessage(self,message,bot):
		if not (self.cooldown or message.author.bot):
			await self.meme(message)
		if (("gilfa" in message.content.lower()) or ("pregario" in message.content.lower()) or ("pregigi" in message.content.lower())) and message.channel.id!=611375108056940555:
			await message.channel.send("No")
			await message.delete()
		await bot.process_commands(message)
		try:
			if (message.channel.category_id==610934583730634752 or message.channel.category_id==610934583730634752) or message.content.startswith('$'):
				return
		except Exception as e:
			print (e)
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
				hug = Utils.getRandEmoji(message.guild,"suteki")
				await message.channel.send(rankUpMsg.format(message.author.mention,str(hug)))
	async def test(self,guild,auth):
		rankUpMsg=self.config["msgs"]["sr"]
		hug=self.anataYay
		return rankUpMsg.format(auth.mention,str(hug))
	async def meme(self,message):
		cdTime=120
		#if "kasukasu" in message.content.lower() or ("kasu kasu" in message.content.lower() and not("nakasu kasumi" in message.content.lower())):
		#	rxn=discord.utils.get(message.guild.emojis,name="RinaBonk")
		#	await message.add_reaction(rxn)
		#	self.cooldown=True
		#	await message.channel.send("KA! SU! MIN! DESU!!!")
		if(await self.pdpIfy(message)):
			self.cooldown=True
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
