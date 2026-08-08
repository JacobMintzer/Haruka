import discord
from discord.ext import commands
import yaml

from .utilities import checks, messageHandler, utils
class Score(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = []


    async def shutdown(self, ctx):
        pass

    
    @commands.group()
    @checks.isScoreEnabled()
    async def rank(self, ctx, *, idx="1"):
        """Gets message activity leaderboard. Optional page number. ex. '$rank 7' gets page 7 (ranks 61-70)"""
        if str(idx).isdigit():
            if ctx.message.guild.id in self.bot.config["rankHide"]:
                await ctx.message.add_reaction("🚫")
                return
            idx = int(idx)
            await ctx.send(
                await self.bot.messageHandler.getPB(
                    ctx.message.author, ctx.message.guild, idx
                )
            )
        elif idx.lower() == "best" or idx.lower() == "best girl":
            await self.best(ctx)
        elif idx.lower() == "ignore":
            if ctx.message.channel.permissions_for(ctx.author).administrator:
                await self.ignore(ctx)
            else:
                await ctx.send("This command is only available to an Administrator.")
        elif idx.lower().startswith("add"):
            if ctx.message.channel.permissions_for(ctx.author).administrator:
                await self.rankAdd(ctx, idx)
            else:
                await ctx.send("This command is only available to an Administrator.")
        elif idx.lower().startswith("hide"):
            if ctx.message.channel.permissions_for(ctx.author).administrator:
                await self.rankHide(ctx)

    @rank.command(name="add")
    @checks.is_admin()
    async def rankAdd(self, ctx, idx):
        """Adds a role that will be assigned upon reaching certain ranks. You can change the role name later. ex: `$rank add 500 New Recruit`."""
        if idx.split(" ")[1].isdigit():
            score = int(idx.split(" ")[1])
            if len(idx.split(" ")) > 2:
                roleName = idx.split(" ", 2)[2]
            else:
                roleName = None
        else:
            await ctx.send(
                "Please give a score value for the rank role and optionally a name. ex. `$rank add 500 New Recruit`. You can change the role name later."
            )
            return
        if roleName is None:
            role = await ctx.guild.create_role()
            await ctx.send(
                "Created role {0} that will be assigned upon reaching a score of {1}.".format(
                    role.mention, score
                )
            )
        else:
            role = discord.utils.find(lambda x: x.name == roleName, ctx.guild.roles)
            if role is None:
                role = await ctx.guild.create_role(name=roleName)
                await ctx.send(
                    "Created role {0} that will be assigned upon reaching a score of {1}.".format(
                        role.mention, score
                    )
                )
            else:
                await ctx.send(
                    "Found role {0}; it will be assigned upon reaching a score of {1}.".format(
                        role.name, score
                    )
                )
        self.bot.config["roleRanks"][str(ctx.guild.id)].append(
            {"score": score, "role": role.id}
        )
        self.bot.config["roleRanks"][str(ctx.guild.id)] = sorted(
            self.bot.config["roleRanks"][str(ctx.guild.id)], key=lambda x: x["score"]
        )
        utils.saveConfig(ctx)

    @rank.command()
    @checks.hasBest()
    async def best(self, ctx):
        """Use this to show the rankings of what the most popular `best girl` role is"""
        roleList = []
        for roleName in ctx.bot.config["best"][str(ctx.message.guild.id)]:
            role = discord.utils.find(
                lambda x: x.name.lower() == roleName.lower(), ctx.message.guild.roles
            )
            roleList.append(
                (
                    role.name,
                    len(
                        list(
                            filter(lambda x: role in x.roles, ctx.message.guild.members)
                        )
                    ),
                )
            )
        roleList.sort(key=lambda x: x[1], reverse=True)
        series = pd.DataFrame(roleList)
        series.index += 1
        series.columns = ["Best", "Users"]
        await ctx.send("```fortran\n{0}```".format(series.to_string()))

    @rank.command(name="hide")
    @checks.is_admin()
    async def rankHide(self, ctx):
        """ADMIN ONLY! Use this command to toggle visibility of leaderboard in the current server."""
        if ctx.message.guild.id in self.bot.config["rankHide"]:
            self.bot.config["rankHide"].remove(ctx.message.guild.id)
            await ctx.send("Leaderboard no longer hidden.")
        else:
            self.bot.config["rankHide"].append(ctx.message.guild.id)
            await ctx.send("Leaderboard is now hidden.")
        utils.saveConfig(ctx)
        await utils.yay(ctx)

    @commands.group()
    @checks.is_admin()
    async def score(self, ctx):
        """Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Use `$score ignore` or `$score unignore` to add or remove a channel from the ignore list for Haruka's rankings"
            )

    @score.command()
    @checks.isScoreEnabled()
    async def ignore(self, ctx, ch: discord.TextChannel = None):
        """Use `$score ignore` to have Haruka ignore a channel"""
        if ch is None:
            ch = ctx.message.channel
        try:
            await ctx.send(f"ignoring {ch.mention}")
        except:
            await utils.yay(ctx)
            pass
        self.bot.config["scoreIgnore"].append(ch.id)
        utils.saveConfig(ctx)

    @score.command()
    @checks.isScoreEnabled()
    async def unignore(self, ctx, ch: discord.TextChannel = None):
        if ch is None:
            ch = ctx.message.channel
        try:
            await ctx.send("No longer ignoring {ch.mention}")
        except:
            await utils.yay(ctx)
            pass
        try:
            self.bot.config["scoreIgnore"].remove(ch.id)
            utils.saveConfig(ctx)
        except:
            print("could not remove channel from scoreIgnore")

    @score.command(name="enable")
    @checks.is_admin()
    async def scoreEnable(self, ctx):
        if not (str(ctx.guild.id) in self.bot.config["roleRanks"].keys()):
            self.bot.config["roleRanks"][str(ctx.guild.id)] = []
        if ctx.message.guild.id in self.bot.config["scoreEnabled"]:
            await ctx.send("scoring is already enabled")
        else:
            try:
                await self.bot.messageHandler.addGuildToDB(ctx.message.guild)
            except:
                pass
            self.bot.config["scoreEnabled"].append(ctx.message.guild.id)
            await utils.yay(ctx)
        utils.saveConfig(ctx)

    @score.command(name="wipe")
    @checks.is_admin()
    async def scoreWipe(self, ctx):
        """use `$score wipe` to wipe all scores from your server. Must be admin. Warning; this cannot be undone, use with care."""
        if not ctx.message.guild.id in self.bot.config["scoreEnabled"]:
            await ctx.send("scoring isn't enabled")
            return

        await self.bot.messageHandler.wipeGuildScore(ctx.message.guild)
        await utils.yay(ctx)
        utils.saveConfig(ctx)



async def setup(bot):
    await bot.add_cog(Score(bot))
