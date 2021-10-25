import discord

color_in = 0xADD8E6

def queue_list(x):
  listembed = discord.Embed(title = 'Song Queue:', color=color_in)
  listembed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  for i in range(len(x)):
    listembed.add_field(name=f'{i + 1}.{x[i][1]}', value = '\u200b', inline=False)
  return listembed 

def first_song_playing(x):
  embed = discord.Embed(description =f'Playing {x}', color=color_in)
  return embed

def add_song_playing(x):
  embed = discord.Embed(description = f'Added {x} to the queue', color=color_in)
  return embed

def removed_song(x):
  embed = discord.Embed(description = f'Removed {x} from the queue', color=color_in)
  return embed

def send_msg(x):
  embed = discord.Embed(description = x, color=color_in)
  return embed   