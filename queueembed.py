import discord

def queue(list):
  listembed = discord.Embed(title = 'List', color=0x0000FF)
  listembed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  for i in range(list):
    listembed.add_field(name=f'{i}.{list[i][1]}', value = '', inline=True)
  return listembed 
