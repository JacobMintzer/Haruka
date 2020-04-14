import discord
from discord.ext import commands
import asyncio
import random

def getRandEmoji(guild,query=""):
	if query is "":
		return random.choice(guild.emojis)
	choices=[emoji for emoji in guild.emojis if query.lower() in emoji.name.lower()]
	return random.choice(choices)
