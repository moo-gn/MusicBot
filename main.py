import discord
from discord.ext import commands
import music

cogs = [music]
client = commands.Bot(command_prefix='>', intents = discord.Intents.all())

for i in range(len(cogs)):
  cogs[i].setup(client)


client.run('ODk1NDI5NzIyNzA2Njc3ODAx.YV4b6g.LIpXWRsMByq4Z260NeELu-bE5AE')
