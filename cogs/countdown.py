import asyncio

import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import SlashCommandGroup

from datetime import datetime
from dateutil import relativedelta

from core import checks
from core.time import UserFriendlyTime
from core.checks import PermissionLevel
from core.base_cog import BaseCog

from PIL import Image, ImageFont, ImageDraw

import traceback

class Countdown(BaseCog):
    _id = "countdown"
    
    kusanaliDrop = 1664002800

    default_cache = {
        "countdowns": { 
            
        },
    }
    
    _cd = SlashCommandGroup("countdown", "Manages countdown channels.")
    
    def __init__(self, bot) -> None:
        super().__init__(bot)
    
    async def load_cache(self):
        await super().load_cache()

    async def after_load(self):
        for k, v in list(self.cache["countdowns"].items()):
            self.bot.loop.create_task(self.start_countdown(k))
    

    async def start_countdown(self, channelId):
        channel = self.bot.get_channel(int(channelId))
        if not channel:
            self.cache["countdowns"].pop(str(channelId))
            await self.update_db()
            return

        while True:
            if not await self.update(self.cache["countdowns"][str(channelId)]['name'], self.cache["countdowns"][str(channelId)]['date'], channel):
                return

    async def update(self, name, date, channel):
        diff = relativedelta.relativedelta(date, datetime.utcnow())

        if date < datetime.utcnow():
            await channel.edit(name=name)
            self.cache["countdowns"].pop(str(channel.id))
            return False

        years = diff.years
        months = diff.months
        days = diff.days
        hours = diff.hours
        minutes = diff.minutes
        seconds = diff.seconds

        if years > 1:
            if months >= 6:
                years += 1

            await channel.edit(name=f"{name}: {years} years")
            await asyncio.sleep(31556952)

        elif months > 1:
            if days > 15:
                months += 1

            await channel.edit(name=f"{name}: {months} months")
            await asyncio.sleep(2629800)

        elif days > 1:
            if hours >= 12:
                days += 1

            await channel.edit(name=f"{name}: {days} days")
            await asyncio.sleep(86400)

        elif hours > 1:
            if minutes >= 30:
                hours += 1

            await channel.edit(name=f"{name}: {hours} hours")
            await asyncio.sleep(3600)

        elif minutes > 1:
            if seconds >= 30:
                minutes += 1
            await channel.edit(name=f"{name}: {minutes} minutes")
            await asyncio.sleep(300)

        elif seconds:
            await channel.edit(name=f"{name}: A few seconds")
            await asyncio.sleep(seconds)
        
        else:
            await channel.edit(name=name)
            return False
        return True

    @_cd.command(name="create", description="Create a countdown")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def create(self, ctx: ApplicationContext, name: discord.Option(str, description="Message you would like to count down"), time: discord.Option(str, description="How long the countdown is")):
        after = UserFriendlyTime()
        await after.convert(time)
        
        if after.dt <= datetime.utcnow():
            embed = discord.Embed(title="Error", description="Invalid time provided")
            await ctx.respond(embed=embed)
            return
        vc = None

        try:
            vc = await ctx.guild.create_voice_channel(name=name, category=ctx.channel.category)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="Bot does not have permissions")
            await ctx.respond(embed=embed)
            return

        self.cache["countdowns"][str(vc.id)] = {"name": name, "date": after.dt}
        await self.update_db()
        
        self.bot.loop.create_task(self.start_countdown(str(vc.id)))
        
        embed = discord.Embed(title="Success", description="Countdown created.")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="cd", description="Gets duration until Kusanali Drop") 
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def cd(self, ctx: ApplicationContext):
        diff = round((datetime.fromtimestamp(Countdown.kusanaliDrop) - datetime.now()).total_seconds())

        m, r = divmod(diff, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        font = ImageFont.truetype("./fonts/blue-yellow.ttf", 120)
        cd_image = Image.open("./assets/countdown_template.png")

        draw = ImageDraw.Draw(cd_image)

        # coordinates found via pixspy.com
        width, height = draw.textsize(f"{d}", font=font)
        draw.text(((253-width)/2, (499-height)/2), f"{d}", font=font)

        width, height = draw.textsize(f"{h}", font=font)
        draw.text(((767-width)/2, (499-height)/2), f"{h}", font=font)

        width, height = draw.textsize(f"{m}", font=font)
        draw.text(((1249-width)/2, (499-height)/2), f"{m}", font=font)

        cd_image.save("./assets/countdown.png")

        await ctx.respond(file=discord.File('./assets/countdown.png'))

def setup(bot):
    bot.add_cog(Countdown(bot))
