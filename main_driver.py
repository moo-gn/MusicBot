import discord
from discord.ext import commands
import music

cogs = [music]
client = commands.Bot(command_prefix='_', intents = discord.Intents.all(), case_insensitive = True, help_command=None)

import sys
sys.path.append("..")
import credentials

#Put your bot token here 
TOKEN = credentials.Music_Test
GENIUS_TOKEN = credentials.Genius

@client.event
async def on_ready():
  print(f'signed in as {client.user}')
  for i in range(len(cogs)):
    await cogs[i].setup(client, GENIUS_TOKEN)

@client.event
async def on_voice_state_update(member, before, after):
  if before.channel and not after.channel and not member.bot:
    x = member.guild.voice_client
    for y in x.channel.members:
      if not y.bot:
        return
    await x.disconnect()

client.run(TOKEN)
