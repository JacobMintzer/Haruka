import importlib
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import yaml

from .models.idol_st.allstar_card import AllstarCard
from .models.ui.translation_view import DropdownView, DropdownPersistentView
from .services import translation_service
from .models.ui import translation_select, translation_view, translation_modal, translation_button_view, translation_config_modal

from .utilities import checks, utils
import aiohttp

class IdolContent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        with open("secrets.yaml", "r") as file:
            secrets = yaml.full_load(file)
        self.tlUrl = secrets["tlurl"]
        self.tlKey = secrets["tlkey"]
        self.base_uri = "https://idol.st/api/allstars/cards"
        self.bot.translation_service = translation_service.TranslationClient()


    async def cog_load(self):
        self.bot.add_view(DropdownPersistentView())
        self.bot.translation_service=None
        importlib.reload(translation_service)
        self.bot.translation_service = translation_service.TranslationClient()
        try:
            importlib.reload(translation_select)
            importlib.reload(translation_view)
            importlib.reload(translation_modal)
            importlib.reload(translation_button_view)
            importlib.reload(translation_config_modal)
        except Exception as e:
            print(e)

    async def shutdown(self, ctx):
        pass


    
    @commands.command(aliases=["tl"])
    async def translate(self, ctx, *, msg):
        from_language = "ja"
        url = f"{self.tlUrl}/translate?api-version=3.0&from={from_language}&to=en"
        location = "eastus"
        headers = {
            "Ocp-Apim-Subscription-Key": self.tlKey,
            "Ocp-Apim-Subscription-Region": location,
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }
        body = [{"text": msg.replace("@", "@" + "\u200b")}]
        request = requests.post(url, headers=headers, json=body)
        response = request.json()
        await ctx.send(response[0]["translations"][0]["text"])

    @commands.command()
    async def llasID(self, ctx, id: int):
        response = requests.get(self.base_uri, params={"id": id})
        data = response.json()["results"]
        card = AllstarCard(**data[0])
        await ctx.send(embed=card.get_embed())

    @commands.command()
    async def llas(self, ctx, *, query):
        async with ctx.typing():
            tokens = query.lower().split(" ")
            version = None
            params = {}
            for token in tokens:
                if token.title() in consts.idols:
                    params["idol"] = token
                elif token.upper() in consts.rarities:
                    params["rarity"] = token
                elif token.lower() in consts.attributes:
                    params["attribute"] = token
                elif token == "new":
                    version = 0
                elif token.isdigit():
                    version = -1 * int(token)
            response = requests.get(self.base_uri, params=params)
            data = response.json()["results"]
            if version != None:
                card = AllstarCard(**data[version])
                await ctx.send(embed=card.get_embed())
            elif len(data) == 1:
                card = AllstarCard(**data[0])
                await ctx.send(embed=card.get_embed())
            elif len(data) == 0:
                await ctx.send("No card found with given query.")
            else:
                await ctx.send(self.listCards(data))

    def listCards(self, data):
        cards = [AllstarCard(**x) for x in data]
        cardList = "Multiple cards found, please pick the card you want with `$llasID <id>` with <id> replaced with the ID you want.```\nID  Rarity    Idol   Title      Idolized Title\n"
        for card in cards:
            cardList += "{0}.  {1} {2}: {3} / {4}\n".format(
                card.id, card.rarity, card.idol_name, card.name, card.name_idolized
            )
        return cardList + "```"


    @commands.command()
    @checks.is_me()
    async def bluebirdTweets(self, ctx):
        if ctx.message.guild.id in self.bot.config["bluebirdSubscribers"]:
            del self.bot.config["bluebirdSubscribers"][ctx.message.guild.id]
            await ctx.send("unsubscribed from bluebird tweets")
        else:
            self.bot.config["bluebirdSubscribers"][ctx.message.guild.id]=ctx.message.channel.id
            await ctx.send("subscribed to bluebird tweets")
        utils.saveConfig(ctx)
        await utils.yay(ctx)

    @commands.command()
    @checks.is_me()
    async def bbTweetWH(self, ctx):
        if ctx.message.guild.id in self.bot.config["af_wh"]:
            ch = ctx.message.channel
            try:
                webhook = await ch.create_webhook(name="harukaWebhookaf2")
                self.bot.config["af_wh"][ctx.message.guild.id].append(webhook.id)
                await ctx.send("subscribed to bluebird tweets through a webhook")
            except Exception as e:
                await ctx.send("Error creating webhook check my permissions")
                return
        else:
            ch = ctx.message.channel
            try:
                webhook = await ch.create_webhook(name="harukaWebhookaf")
                self.bot.config["af_wh"][ctx.message.guild.id]=[webhook.id]
                await ctx.send("subscribed to bluebird tweets through a webhook")
            except Exception as e:
                await ctx.send("Error creating webhook check my permissions")
                return
        utils.saveConfig(ctx)
        await utils.yay(ctx)


    @commands.command(aliases=["gt"])
    @checks.is_me()
    async def gettweet(self, ctx, char="polka"):
        
        channel = self.bot.get_channel(1371868585705603183)
        thread = channel.get_thread(self.bot.config["bbThreads"][char.lower()])
        msg = await thread.fetch_message(thread.last_message_id)
        (embed,view,_) = await self.bot.translation_service.generate_tweet_embed(msg,True)
        msg = await ctx.send("", view=view)
        try:
            await msg.publish()
        except Exception as e:
            print("failed to publish message")
            print(e)
        #await ctx.send("", embed=embed,view=view)

        
    @commands.command(aliases=["gtwh"])
    @checks.is_me()
    async def gettweetwh(self, ctx, char="polka"):
        
        channel = self.bot.get_channel(1371868585705603183)
        thread = channel.get_thread(self.bot.config["bbThreads"][char.lower()])
        msg = await thread.fetch_message(thread.last_message_id)
        (embed,view,character) = await self.bot.translation_service.generate_tweet_embed(msg,True)
        wh_id = self.bot.config["bluebirdSubscribersWH"][ctx.message.guild.id]
        wh = await self.bot.fetch_webhook(wh_id)
        username = self.bot.translation_service.full_names[character]
        msg = await wh.send("", view=view, username=username, avatar_url=embed.thumbnail.url)
        #msg = await wh.send("",embed=embed,view=dropdown_view,username=char,avatar_url=embed.thumbnail.url)
        try:
            await msg.publish()
        except Exception as e:
            print("failed to publish message")
            print(e)
        #await ctx.send("", embed=embed,view=dropdown_view)

    #@app_commands.command(name="bb_tweets", description="subscribe to bluebird tweets")
    #@app_commands.guilds(280954773346320386)
    async def bbTweets(self, interaction: discord.Interaction):
        """set up bluebird tweet subscription"""
        await interaction.response.send_modal(translation_config_modal.TweetConfigModal(interaction.guild_id, self.bot))

    

    @commands.command()
    @checks.is_me()
    async def sync_tweets(self, ctx, ts=None):
        if ts is None:
            ts = await self.bot.translation_service.get_most_recent_tweet()[0]
        dt = datetime.fromtimestamp(int(ts))
        for channel in self.bot.config["bbChannels"].values():
            tweet_ch = self.bot.get_channel(channel)
            print("going through channels")
            async for message in tweet_ch.history(limit=100, after=dt):
                print(f"message to be sent: {message.clean_content}")
                for subbed_channel in self.bot.config["bluebirdSubscribers"].values():
                    try:
                        ch = self.bot.get_channel(subbed_channel)
                        pass
                        (_,button_view,_) = await self.bot.translation_service.generate_tweet_embed(message, True)
                        msg = await ch.send("",view=dropdown_view)
                        await msg.publish()
                    except Exception as e:
                        print(f"Error posting BB tweet for channel in guild: {ch.guild.name} ", e)
                    
                for wh_id in self.bot.config["bluebirdSubscribersWH"].values():
                    try:
                        wh = await self.bot.fetch_webhook(wh_id)
                        (embed,dropdown_view,character) = await self.bot.translation_service.generate_tweet_embed(message, True)
                        username = self.bot.translation_service.full_names[character.lower()]
                        msg = await wh.send("",view=dropdown_view, username=username, avatar_url=embed.thumbnail.url)
                        await msg.publish()
                    except Exception as e:
                        print(f"Error posting BB tweet for channel in guild: {ch.guild.name} ", e)
        

async def setup(bot):
    await bot.add_cog(IdolContent(bot))
