import discord
from discord.ext import commands
import music

cogs = [music]
client = commands.Bot(command_prefix='.', intents = discord.Intents.all(), case_insensitive = True, help_command=None)

for i in range(len(cogs)):
  cogs[i].setup(client)


client.run('ODk1NDI5NzIyNzA2Njc3ODAx.YV4b6g.n9D8aUDey_9eiMhMrMWQIbk0_Ik')
