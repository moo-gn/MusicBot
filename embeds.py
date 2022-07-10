from discord import Embed
from typing import List

color_in = 0x8dffd3

def queue_list(song_list: List[str], page: int = 1):
  """
  Generates an embed that displays the current music queue
  :params: song_list - List[str]
  """
  embed = Embed(title = 'Song Queue:', color=color_in)
  embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  embed.set_footer(text = '{0}/{1}'.format(page, -(-len(song_list)//25)) )
  for i in range((page -1)*25,len(song_list)):
    embed.add_field(name=f'{i + 1}. {song_list[i][0]}', value = '\u200b', inline=False)
  return embed 

def help_list(command_list: List[str]):
  """
  Generates an embed that displays the current supported commands
  :params: command_list - List[str]
  """
  embed = Embed(title = 'Commands:', color=color_in)
  embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
  for i in range(len(command_list)):
    embed.add_field(name=command_list[i].split(':')[0], value = command_list[i].split(':')[1], inline=False)
  return embed   

def c_playing(song_name: str):
  """
  Generates an embed that displays the song that is currently playing
  :params: song_name - str
  """
  embed = Embed(color=color_in)
  embed.add_field(name = 'Currently Playing:', value = song_name, inline=False)
  return embed  

def song_playing(song_name: str):
  """
  Generates an embed in the form "Playing {song_name}"
  :params: song_name - str
  """
  return Embed(description =f'Playing {song_name}', color=color_in)

def add_song_playing(song_name: str):
  """
  Generates an embed in the form "Added {song_name} to the queue"
  :params: song_name - str
  """
  return Embed(description = f'Added {song_name} to the queue', color=color_in)

def removed_song(song_name: str):
  """
  Generates an embed in the form "Removed {song_name} from the queue"
  :params: song_name - str
  """
  return Embed(description = f'Removed {song_name} from the queue', color=color_in)

def send_msg(message: str):
  """
  Generates an embed that displays the message
  :params: message - str
  """
  return Embed(description = message, color=color_in)  