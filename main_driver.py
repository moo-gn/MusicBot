import discord
from discord.ext import commands
from music import Music 
import asyncio

cogs = [Music]
bot = commands.Bot(command_prefix='.',
                      intents = discord.Intents.all(),
                      case_insensitive = True,
                      help_command=None,
                      description='Gamer Nation music discord bot',
)

import sys
sys.path.append("..")
import credentials

#Put your bot token here 
TOKEN = credentials.Rhythm
GENIUS_TOKEN = credentials.Genius

async def main():
    async with bot:
      await bot.add_cog(Music(bot))
      await bot.start(TOKEN)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_voice_state_update(member, before, after):
  if before.channel and not after.channel and not member.bot:
    x = member.guild.voice_client
    if x is None:
      return
    for y in x.channel.members:
      if not y.bot:
        return
    await x.disconnect()


asyncio.run(main())
