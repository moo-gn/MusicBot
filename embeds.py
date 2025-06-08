from discord import Embed
from typing import List

color_in = 0x8dffd3

def queue_list(song_list: List[str], page: int = 1, title = "Song Queue:"):
  """
  Generates an embed that displays the current music queue
  :params: song_list - List[str]
  """
  embed = Embed(title=title, color=color_in)
  embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
    
  total_pages = -(-len(song_list) // 25)  # ceil division
  embed.set_footer(text=f'{page}/{total_pages}')
    
  start = (page - 1) * 25
  end = min(start + 25, len(song_list))  # limit to 25 entries
    
  for i in range(start, end):
      embed.add_field(name=f'{i + 1}. {song_list[i][0]}', value='\u200b', inline=False)

  return embed

def lyric_embed(chunks: List[str],page: int = 1, title: str = "Lyrics"):
  """
  Generates an embed that displays the lyrics of passed song
  :params: lyric chunks 4000 char max - List[str]
  """
  embed = Embed(title=title, description=chunks[page - 1], color=color_in)
  embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/901624454688440430/901664414963499079/musicStops.png')
    
  total_pages = len(chunks)
  embed.set_footer(text=f'{page}/{total_pages}')

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

def play_next(song_name: str):
  """
  Generates an embed in the form "Playing {song_name} next"
  :params: song_name - str
  """
  return Embed(description =f'Playing {song_name} next', color=color_in)

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