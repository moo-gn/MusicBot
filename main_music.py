import discord
from discord.ext import commands
import music

cogs = [music]
client = commands.Bot(command_prefix='.', intents = discord.Intents.all(), case_insensitive = True, help_command=None)

for i in range(len(cogs)):
  cogs[i].setup(client)

@client.event
async def on_voice_state_update(member, before, after):
  if before.channel and not after.channel and not member.bot:
    x = member.guild.voice_client
    for y in x.channel.members:
      if not y.bot:
        return
    await x.disconnect()

client.run('ODk1NDI5NzIyNzA2Njc3ODAx.YV4b6g.n9D8aUDey_9eiMhMrMWQIbk0_Ik')
#client.run('OTI1MDk4ODA5MDgyNjU4ODI2.YcoLZw.tAZa08XOdeZTLAT1is9VpysOPnE')
