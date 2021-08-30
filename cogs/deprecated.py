import asyncio
import discord
import json
from discord.ext import commands
from .utilities import utils, checks
import aiosqlite
import re
from datetime import datetime

class Deprecated(commands.Cog):
	"""This class is for commands that either were designed for a single use for setting things up, or are no longer used, and are here for future use"""
	def __init__(self, bot):
		self.bot = bot
		with open('greetings.yaml', "r") as file:
			self.greetings = yaml.full_load(file)
		with open('xmas.yaml', "r") as file:
			self.xmas = yaml.full_load(file)


	@commands.command()
	@checks.is_me()
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
		if bool([ele for ele in self.girls if(ele in testContent.split(" "))]): #"niji" in content.lower() or "ayumu" in content.lower() or "karin" in content.lower():
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

	@checks.is_niji()
	@checks.is_admin()
	@commands.command()
	async def fixXmas(self,ctx,*,person: discord.Member):
		id=person.id
		self.xmas[id]["last_present"] = 0
		self.save_xmas

	@checks.is_niji()
	@commands.command()
	async def present(self, ctx):
		if ctx.message.channel.id != 790292236524716052:
			await ctx.send("Wrong channel!")
			return
		if ctx.author.id in self.xmas.keys():
			if datetime.now() < datetime.fromtimestamp(self.xmas[ctx.author.id]["last_present"]) + timedelta(hours=12):
				elapsed_time = datetime.fromtimestamp(
					self.xmas[ctx.author.id]["last_present"]) + timedelta(hours=12) - datetime.now()
				await ctx.send(f"You already received your present for the day! Try again in {elapsed_time.seconds//3600} hours {(elapsed_time.seconds//60)%60} minutes.")
				return
		else:
			self.xmas[ctx.author.id] = {
				"last_present": 0, "girls": [], "gifts": []}
			self.save_xmas()
		embd = discord.Embed()
		embd.color = discord.Color.red()
		embd.type = "rich"
		embd.set_image(url="https://kachagain.com/images/llsif/boxes/box_05.png")
		embd.description = "Click the reaction to open your present"
		embd.title = f"{ctx.message.author.display_name} has received a present!"
		present = await ctx.send(embed=embd)

		def presentCheck(reaction, user):
			return user == ctx.message.author and reaction.emoji.name == "harukaPresent"

		emoji = discord.utils.find(
			lambda emoji: emoji.name == "harukaPresent", self.bot.emojis)
		await present.add_reaction(emoji)
		try:
			_, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=presentCheck)
		except asyncio.TimeoutError:
			await present.delete()
			return
		else:
			if isChristmas and self.find_best(ctx.message.author) and (self.find_best(ctx.message.author) not in self.xmas[ctx.message.author.id]["girls"]):
				girl = self.find_best(ctx.message.author)
			elif (len(self.greetings["Image"].keys())==len(self.xmas[ctx.message.author.id]["girls"])):
				girl = random.choice(self.greetings["Image"])
			else:
				girl = random.choice([x for x in self.greetings["Image"].keys(
				) if x not in self.xmas[ctx.message.author.id]["girls"]])
			embd = self.gen_present(ctx, girl)
			if girl == self.find_best(ctx.message.author):
				embd.add_field(
					name=f"{girl}:", value=f"Hey, {ctx.message.author.mention}, can you meet me behind the school later? I have something I want to say in private (check your DMs)", inline=True)
				await present.edit(embed=embd)
				await asyncio.sleep(5)
				embd = self.gen_present(ctx, girl)
				greeting = self.greetings["Message"][girl]
				embd.add_field(name=f"{girl}:", value=greeting, inline=True)
				await ctx.message.author.send(embed=embd)
				self.xmas[ctx.message.author.id]["girls"].append(girl)
				self.xmas[ctx.message.author.id]["last_present"] = datetime.now().timestamp()
				self.save_xmas()
				return
			embd = self.gen_present(ctx, girl)
			gift = random.choice([x for x in self.greetings["Gifts"] if x not in self.xmas[ctx.message.author.id]["girls"]])
			greeting = f"I got you {gift} for Christmas!"
			embd.add_field(name=f"{girl}:", value=greeting, inline=True)
			self.xmas[ctx.message.author.id]["girls"].append(girl)
			self.xmas[ctx.message.author.id]["last_present"] = datetime.now().timestamp()
			self.xmas[ctx.message.author.id]["gifts"] .append(gift)
			self.save_xmas()
			await present.edit(embed=embd)

	def gen_present(self, ctx, girl):
		embd = discord.Embed()
		embd.color = discord.Color.green()
		embd.type = "rich"
		image = self.greetings["Image"][girl]
		if girl == "Haruka":
			embd.set_author(name="Link to original image", url="https://www.pixiv.net/en/artworks/85591672")
		elif girl == "Yu":
			embd.set_author(name="Link to Sei's tweet", url="https://twitter.com/seion_alter/status/1341419302939975680")
		embd.set_image(url=image)
		embd.title = f"{ctx.message.author.display_name} received a gift from {girl}!"
		return embd

	def save_xmas(self):
		with open('xmas.yaml', 'w') as outfile:
			yaml.dump(self.xmas, outfile)

	def find_best(self, member):
		bestRoles = self.bot.config["best"]['610931193516392472']
		for role in member.roles:
			if role.name in bestRoles:
				return role.name
		return None








# AF 2021


	@checks.is_niji()
	@checks.is_admin()
	@commands.command()
	async def rate(self, ctx, *, rates=None):
		if rates is None:
			await ctx.send(reference=ctx.message.to_reference(),content=f"Currents rates are {self.rates*100}% or {self.bot.config['rates']} ")
			return
		rate=rates.split("/")
		if rate[0] >= rate[1]: 
			await ctx.send(reference=ctx.message.to_reference(),content="no")
			return
		self.rates = float(rate[0]) / float(rate[1])
		self.bot.config['rates'] = rates
		utils.saveConfig(ctx)
		await ctx.message.add_reaction(utils.getRandEmoji(self.bot.emojis, "harukahug"))
	
	#@commands.Cog.listener()
	async def on_typing(self, channel, user, when):
		if not channel.guild.id == self.bot.config['nijiCord']:
			return
		if channel.id in self.ignoreCH:
			return
		if random.random() < self.rates:
			files = os.listdir("../Haruka/af2021/")
			file = discord.File(open("../Haruka/af2021/{0}".format(random.choice(files)), 'rb'))
			await channel.send(file=file)


	async def pdpIfy(self, message):
		"""April fools day replacements"""
		if len(message.content)<1:
			return False
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


		if bool([ele for ele in self.girls if(ele.lower() in testContent.split())]): #"niji" in content.lower() or "ayumu" in content.lower() or "karin" in content.lower():
			msg=content
			regex=re.compile(re.escape('nijigasaki'),re.IGNORECASE)
			msg=regex.sub(random.choice(['practice Liella', 'PDP']),msg)
			regex=re.compile(re.escape('nijigaku'),re.IGNORECASE)
			msg=regex.sub(random.choice(['The Liella Warmup School', 'The PDP School']),msg)
			regex=re.compile(re.escape('niji'),re.IGNORECASE)
			msg=regex.sub(random.choice(['practice Liella', 'PDP']),msg)
			regex=re.compile(re.escape('setsuna'),re.IGNORECASE)
			msg=regex.sub(random.choice(['The self-insert weeb idol', 'My secret student council president can\'t possibly be a pyromaniac?!']),msg)
			regex=re.compile(re.escape('ayumu'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Setsuna\'s Girlfriend\'s Childhood Friend','Walking attachment issues','Honoka 3']),msg)
			regex=re.compile(re.escape('karin'),re.IGNORECASE)
			msg=regex.sub(random.choice(['The girl who got lost in a straight hallway','Kanan with tiddy moles']),msg)
			regex=re.compile(re.escape('kasumin'),re.IGNORECASE)
			msg=regex.sub(random.choice(['bababooey','Nijigasaki\'s pet rat', 'kasukasu']),msg)
			regex=re.compile(re.escape('kasumi'),re.IGNORECASE)
			msg=regex.sub(random.choice(['bababooey','Nijigasaki\'s pet rat', 'kasukasu']),msg)
			regex=re.compile(re.escape('shizuku'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Kasumin\'s bread dispenser','Volleyball target practice']),msg)
			regex=re.compile(re.escape('kanata'),re.IGNORECASE)
			msg=regex.sub(random.choice(['fucking piece of shit that doesn\'t sleep and now i need to learn to cook','zzzzzzzzzzzzzz']),msg)
			regex=re.compile(re.escape('emma'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Emma, blocker of canals', 'Emma, consumer of smaller idols']),msg)
			regex=re.compile(re.escape('rina'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Overlord Board-sama and her loyal flesh-slave', 'idol that says poggers irl']),msg)
			if 'ai' in testContent.split():
				aiRepl = random.choice(['The safest gyaru design of all time','Sasuke\'s food', 'Rina\'s babysitter'])
				deconMSG=msg.split()
				newMSG=[]
				for token in deconMSG:
					if token.lower() == 'ai':
						newMSG.append(aiRepl)
					else:
						newMSG.append(token)
				msg=" ".join(newMSG)
			regex=re.compile(re.escape('haruka'),re.IGNORECASE)
			msg=regex.sub(random.choice(['benevolent goddess and all knowing mind reader', 'boneless Ruby']),msg)
			regex=re.compile(re.escape('yu'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Me, but if i were cuter and always talking to other cute girls', 'queen of the hump and dump']),msg)
			regex=re.compile(re.escape('shioriko'),re.IGNORECASE)
			msg=regex.sub(random.choice(['A sentient fang with a girl attached', 'the girl you\'re into just because you like vampires']),msg)
			regex=re.compile(re.escape('shio'),re.IGNORECASE)
			msg=regex.sub(random.choice(['A sentient fang with a girl attached', 'the girl you\'re into just because you like vampires']),msg)
			regex=re.compile(re.escape('lanzhu'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Commie Dommy Mommy']),msg)
			regex=re.compile(re.escape('mia'),re.IGNORECASE)
			msg=regex.sub(random.choice(['Taylor Swift']),msg)
			await message.channel.send(reference=message.to_reference(), content='You mean `{0}`'.format(msg))
			return True
		else:
			return False



	# old llas commands for bock's database

	@commands.command()
	async def llas(self, ctx, *, query):
		"""Search for a LLAS card. ex. $llas Bowling Eli"""
		await ctx.send("I am currently in the process of migrating to a new cards database, so my card lookup feature is currently disabled. Thank you for waiting patiently, and keep an eye on my status for when it launches!")
		return
		async with ctx.typing():
			lb = 0
			if query[-3:].lower() == "mlb":
				lb = 5
				query = query[:-3]
			if query[-3:-1].lower() == "lb":
				lb = int(query[-1])
				query = query[:-3]
			query = query.strip()
			response = requests.get(
				"http://all-stars-api.uc.r.appspot.com/cards/search?query={0}".format(str(query)))
			data = (response.json())
			if len(data) > 15:
				await ctx.send("Too many potential cards, please send a more specific query.")
				return
			if len(data) > 1:
				await ctx.send(self.listCards(data))
				return
			if len(data) < 1:
				await ctx.send("No card found with given query.")
				return
			data = data[0]
			embd = self.embedCard(data, lb)
			await ctx.send(embed=embd)


	@commands.command()
	async def llasID(self, ctx, id: int, lb="0"):
		"""Search for a LLAS card by ID. Optionally give limit break level (defaults to 0). ex. '$llasID 146 2'"""
		await ctx.send("I am currently in the process of migrating to a new cards database, so my card lookup feature is currently disabled. Thank you for waiting patiently, and keep an eye on my status for when it launches!")
		return
		async with ctx.typing():
			if lb.lower() == "mlb":
				lb = 5
			elif len(str(lb)) > 1:
				lb = int(str(lb)[-1])
			else:
				lb = int(lb)
			response = requests.get(
				"http://all-stars-api.uc.r.appspot.com/cards/id/{0}".format(str(id)))
			data = (response.json())
			embd = self.embedCard(data, lb)
			await ctx.send(embed=embd)

def embedCard(self, data, lb=0):
		embd = discord.Embed(title=data["idolizedTitle"], description=data["title"], colour=discord.Colour(
			int(data["idol"]["color"].replace("#", "0x"), 16)))
		embd.set_image(
			url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconI.jpg".format(data["id"]))
		embd.set_thumbnail(
			url="https://all-stars-api.uc.r.appspot.com/img/cards/{0}/iconN.jpg".format(data["id"]))
		rarity = discord.utils.find(lambda emoji: emoji.name.lower() == "LLAS{0}ICON".format(
			data["rarity"]["abbreviation"]).lower(), self.bot.emojis)
		embd.set_author(name=data["idol"]["firstName"] +
                  " " + data["idol"]["lastName"], icon_url=rarity.url)
		if lb < 0 or lb > 5:
			lb = 0
		embd.add_field(name="Appeal (LB{0})".format(
			str(lb)), value=data["appeal"]["lb{0}".format(lb)])
		embd.add_field(name="Stamina (LB{0})".format(
			str(lb)), value=data["stamina"]["lb{0}".format(lb)])
		embd.add_field(name="Technique (LB{0})".format(
			str(lb)), value=data["technique"]["lb{0}".format(lb)])
		embd.add_field(
			name="Skill", value=f'**Effect**: {data["primarySkill"]["effect"]}\n**Applies To**: {data["primarySkill"]["appliesTo"]}', inline=False)
		embd.add_field(
			name="Passive Ability",
                				value=f'**Effect**: {data["passiveAbility"]["effect"]}\n**Applies To**: {data["passiveAbility"]["appliesTo"]}', inline=False)
		embd.add_field(
			name="Active Ability",
                				value=f'**Effect**: {data["activeAbility"]["effect"]}\n**Applies To**: {data["activeAbility"]["appliesTo"]}', inline=False)
		embd.set_footer(text="{0}: ID: {1}".format(data["title"], data["id"]))
		return embd
