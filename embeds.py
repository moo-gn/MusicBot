import discord

color_in = 0x8dffd3

def queue_list(x, page = 1):
  listembed = discord.Embed(title = 'Song Queue:', color=color_in)
  listembed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  listembed.set_footer(text = '{0}/{1}'.format(page, -(-len(x)//25)) )
  for i in range((page -1)*25,len(x)):
    listembed.add_field(name=f'{i + 1}.{x[i][0]}', value = '\u200b', inline=False)
  return listembed 

def help_list(x):
  listembed = discord.Embed(title = 'Commands:', color=color_in)
  listembed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  for i in range(len(x)):
    listembed.add_field(name=x[i].split(':')[0], value = x[i].split(':')[1], inline=False)
  return listembed   

def c_playing(x):
  embed = discord.Embed(color=color_in)
  embed.add_field(name = 'Currently Playing:', value = x, inline=False)
  return embed  

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