import asyncio
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yaml
import pytz
from discord.ext import commands
from dateparser.search import search_dates
from datetime import datetime as dt, timezone, timedelta
import re
from .utilities import messageHandler, utils, checks

gracePeriod = 600


class Scheduler(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.scheduler = AsyncIOScheduler(timezone=pytz.utc)
		with open('Reminders.yaml', "r") as file:
			self.events = yaml.full_load(file)
			if self.events is None:
				self.events = []
		for event in self.events:
			if (event["time"] + timedelta(seconds=gracePeriod)) >= dt.now(timezone.utc):
				job = self.scheduler.add_job(
					self.reminder, args=[event], trigger="date", run_date=event["time"], misfire_grace_time=gracePeriod)
				event["id"] = job.id
			else:
				print("Event {0} has expired".format(event))
				self.events.remove(event)
		self.saveEvents()
		self.scheduler.start()

	async def shutdown(self, ctx):
		pass

	async def reminder(self, event):
		user = self.bot.get_user(event["user"])
		await user.send("You asked me to remind you {0}".format(str(event["message"]).strip()))
		self.events.remove(event)
		self.saveEvents()

	def saveEvents(self):
		with open('Reminders.yaml', 'w') as outfile:
			yaml.dump(self.events, outfile)

	def scheduleEvent(self, event):
		job = self.scheduler.add_job(
			self.reminder, args=[event], trigger="date", run_date=event["time"], misfire_grace_time=600)
		event["id"] = job.id
		self.events.append(event)

	@commands.command(alias="remindme")
	async def remind(self, ctx, *, content):
		"""Have Haruka remind you about something in relative or absolute time. Defaults to UTC, but you can specify a timezone. Remember that DST changes the timezone name (EST->EDT). Cancel with $cancelReminder."""
		if content.lower().startswith("me"):
			content = content[2:].strip()
		cleanContent = content
		if cleanContent.lower().startswith("on"):
			cleanContent = cleanContent[2:].strip()
		if cleanContent.lower().startswith("at"):
			cleanContent = cleanContent[2:].strip()
		cleanContent = re.sub(r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>','',cleanContent)
		timeContent, time = (search_dates(
			cleanContent, settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True})[0])
		message = content.replace(timeContent, "")
		utcNow = dt.now(timezone.utc)
		if time< utcNow:
			if time.month == utcNow.month and time.day == utcNow.day:
				time = time + timedelta(hours=24)
			else:
				time = time.replace(time.year + 1)
			if time < utcNow:
				await ctx.send("You cannot specify a time in the past.")
				return
		await ctx.send("will remind you at `{0} UTC` {1}".format(time.strftime("%b %d, %Y at %H:%M"), message.strip()))
		event = {
			'user': ctx.message.author.id,
			'time': time,
			'message': message
		}
		self.scheduleEvent(event)
		self.saveEvents()
		rxn = utils.getRandEmoji(ctx.message.guild.emojis, "hug")
		if rxn is None:
			rxn = utils.getRandEmoji(ctx.bot.emojis, "harukahug")
		await ctx.message.add_reaction(rxn)

	@commands.command()
	async def cancelReminder(self, ctx, *, reminder: int = -1):
		"""Cancel an event. Not passing a number as an argument will list all the events in chronological order from when they will occur. Ex. `$cancelReminder 2`"""
		events = filter(lambda x: x['user'] == ctx.author.id, self.events)
		events = sorted(events, key=lambda event: event["time"])
		if reminder <= 0:
			if len(events) > 0:
				message = "```fortran\nPick an event to cancel. based on the ID below\n"
				for x in range(len(events)):
					message += f"{x+1}.\t{events[x]['time'].strftime('%b %d, %Y at %H:%M')}\t{events[x]['message']}\n"
				message += "```"
			else:
				message = "You have no reminders scheduled!"
			await ctx.send(message)
		else:
			reminder = reminder - 1
			self.scheduler.remove_job(events[reminder]["id"])
			self.events.remove(events[reminder])
			self.saveEvents()


def setup(bot):
	bot.add_cog(Scheduler(bot))
