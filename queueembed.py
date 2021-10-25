import discord

def queue_list(x):
  listembed = discord.Embed(title = 'List', color=0x0000FF)
  listembed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  for i in range(len(x)):
    listembed.add_field(name=f'{i + 1}.{x[i]}', value = '\u200b', inline=False)
  return listembed 
