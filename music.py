from distutils.log import error
import discord
from discord.ext import commands
import yt_dlp
import embeds as qb
from search_yt import search
import asyncio
import random
from qbuttons import Qbuttons
import json
import lyricsgenius

class music(commands.Cog):
  def __init__(self, client, genius_token):
    self.client = client
    self.increment = -1
    self.queue = []
    self.loop = False
    self.play_status = False
    self.genius = lyricsgenius.Genius(genius_token, timeout=5, retries=2, excluded_terms=['spotify', 'top hits', 'Release Calendar', 'Best Songs', 'Genius Picks'])
    self.currently_playing = ''
    self.json_file = "playlist.json"
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    self.cmnds = [
    'join, j : joins the voice channel', 
    'leave : leaves the voice channel', 
    'play, p , add : plays song or appends it to queue', 
    'pause, stop, hold : pauses the song', 
    'resume, continue : resume playing',
    'list, queue, l, q : displays the queue' , 
    'skip : skips song', 'clear, clr : clears the queue', 
    'remove, r, rm : removes a song from queue based on its index', 
    'loop: turns on or off a loop of the queue', 
    'shuffle: shuffles the order of the current queue', 
    'playskip, ps: playskips to a selected song', 
    'playnext, pn: adds new song to the start of the queue',
    'lyrics, lyric, ly: sends lyrics of any song (default is current song)',
    'save: saves the current queue', 
    'load: loads a playlist to the queue', 
    'bang: add a banger to the banger list', 
    'banger: add a banger to the queue'
    ]

  """
  *************************
      Function: join
  *************************
  Description: Results in the musicbot joining the caller's voice channel.
  """
  @commands.command(aliases=['j'])
  async def join(self,ctx):
    if ctx.author.voice is None:
      await ctx.send('Please join a voice channel!')
    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()
    else:
      await ctx.voice_client.move_to(ctx.author.voice.channel)      
  
  """
  *************************
      Function: leave
  *************************
  Description: Results in the musicbot leaving the caller's voice channel.
  """
  @commands.command()
  async def leave(self,ctx):
    await ctx.voice_client.disconnect()  

  
  """
  *************************
      Function: song_info
      Parameters: str inquiry - (intended to be the inquiry of what is to be played)
      return: tuple fetch - (link, song name), str url2 (link of the audio of the youtube clip)
  *************************
  Description: Parses youtube for an inquiry and returns the name and audio link of the first result.
  """
  def song_info(self, inquiry):
      fetch = search(inquiry)
      info = yt_dlp.YoutubeDL({'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}).extract_info(fetch[0], download=False)
      for format in info['formats']:
                if 'url' in format:
                    s = format['url'].lstrip('https://')
                    if s[0] == 'r':
                        url2 = format['url']
                        break
      return fetch, url2

  """
  *************************
      Function: play
      Parameters: str message - (the message parsed from the function call)
      Helper functions: append_playlist
  *************************
  Description: Plays an audio version of a requested inquiry from youtube in the caller's voice channel.
  """
  # Appends the enrties in the playlist to the queue
  def append_playlist(self, message):
    info = yt_dlp.YoutubeDL({'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}).extract_info(message, download=False)
    for entry in info['entries']:
      self.queue.append([entry['title'], entry['url']])

  @commands.command(aliases=['add', 'p'])
  async def play(self,ctx,*,message):

      # Give a 0.01s wait between calling the fucntion.
      await asyncio.sleep(0.01)

      # Connect the bot to the caller's voice channel if the bot is not connected.
      if ctx.voice_client is None:
          await ctx.author.voice.channel.connect()

      # Limit of songs in the queue to maintain 
      if len(self.queue) > 100:
          await ctx.send(embed=qb.send_msg('Queue limit reached!'))

      # Else if play a youtube playlist request, add each vid to the queue and play the first if its not playing.
      elif message.startswith('https://www.youtube.com/playlist?list='):
          msg = await ctx.send(embed=qb.send_msg('Adding playlist, please wait as this might take some time.'))

          # Append songs from the playlist to the current queue
          self.append_playlist(message)

          # If audio is not playing start playing songs from the beginning of the queue
          if not ctx.voice_client.is_playing():
              fetch = self.queue.pop(0)
              ctx.voice_client.play(await discord.FFmpegOpusAudio.from_probe(fetch[1], **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
              self.currently_playing = fetch[0]
              self.play_status = True 
              await ctx.send(embed=qb.song_playing(fetch[0]))
              
          # Display the new queue
          await msg.edit(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

      # Finally, if not a playlist and not above current queue limit, Search youtube for an inquiry and play the audio clip or add it to queue
      else:

          # Get information
          fetch, audio_url = self.song_info(message)
          print(fetch[1])

          # Play or add to list if already playing
          if ctx.voice_client.is_playing():
              self.queue.append([fetch[1],audio_url])
              await ctx.send(embed=qb.add_song_playing(fetch[1]))

          # Create ffmpegOpusAudio from link and play it and send a message, call play_after after the song ends
          else: 
              ctx.voice_client.play(await discord.FFmpegOpusAudio.from_probe(audio_url, **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
              self.currently_playing = fetch[1]
              self.play_status = True 
              await ctx.send(embed=qb.song_playing(fetch[1]))

  """
  *************************
      Function: playnext
  *************************
  Description: If client voice is playing, load the information of a requested inquiry from youtube and add it to the top of the queue
  """
  # If client voice is playing add this song to the top of the queue
  @commands.command(aliases=['pn'])
  async def playnext(self, ctx, *, message):

      # Check that the client is playing
      if ctx.voice_client and ctx.voice_client.is_playing():

          # Gather information
          fetch, audio_url = self.song_info(message)

          # Insert to the top of the queue
          self.queue.insert(0, [fetch[1],audio_url])
          await ctx.send(embed=qb.playnext_embed(fetch[1]))

      # If the client is not playing send the following message
      else:
        await ctx.send(content= 'Nothing is playing')

  """
  *************************
      Function: play_load
  *************************
  Description: This function is called when a playlist is loaded from JSON or SQL and it loads the songs into the queue. 
  """
  @commands.command()
  async def play_load(self,ctx,x):

      # Give a moments wait between loading songs
      await asyncio.sleep(0.01)

      # Check if the bot is playing music, if not connect it to the voice channel
      if ctx.voice_client is None:
          await ctx.author.voice.channel.connect()

      # Gather information
      fetch, audio_url = self.song_info(x)

      # if playing add song to queue, if not play it now
      if ctx.voice_client.is_playing():
        self.queue.append([fetch[1],audio_url])
      else:  
        ctx.voice_client.play(await discord.FFmpegOpusAudio.from_probe(audio_url, **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
        self.currently_playing = fetch[1]
        self.play_status = True 

  """
  *************************
      Function: play_after
      Helper Functions: load_next
  *************************
  Description: This function is called after an audio finishes playing. If a queue exists, it will pop off the song at the beginning of the queue and play it. 
              If the shuffle condition is on, The function will not pop the song and it will keep it in the queue. It will use self.increment to determine the next song to play.
  """
  # Adhering to normal or loop mode
  def load_next(self):
      if self.loop:
          fetch = self.queue[self.increment]
          plcmnt = str(self.increment + 1) + '. '
      else:  
          fetch = self.queue.pop(0)
          plcmnt = ''
      return fetch, plcmnt
    
  def play_after(self, ctx):

      # If a queue exists do the following
      if len(self.queue) > 0:

          # Increment the position in the queue and Maintain the increment within bounds
          self.increment += 1
          self.increment %= len(self.queue)

          # Based on the play mode(normal or loop), determine the next song to be played and update the queue accordingly
          fetch, plcmnt = self.load_next()

          # Create ffmpegOpusAudio from link and play it
          ctx.voice_client.play(discord.FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))

          # Update the song that is currently playing
          self.currently_playing = fetch[0]

          # Send the placement in the queue if its looping, and the name of song
          self.client.loop.create_task(ctx.send(embed=qb.song_playing(plcmnt + fetch[0])))
  
  """
  *************************
      Function: position
  *************************
  Description: Prints the increment's current position in the queue.
  """
  @commands.command()
  async def position(self,ctx):
    await ctx.send(embed=qb.send_msg(self.increment))
  
  """
  *************************
      Function: position
  *************************
  Description: Prints song currently playing.
  """
  @commands.command(aliases=['c'])
  async def current(self,ctx):
    await ctx.send(embed=qb.send_msg(str(self.increment) + ' ' + self.currently_playing))

  """
  *************************
      Function: lyrics
      Parameters: str message - (The message is defaulted as the song currently playing)
  *************************
  Description: Prints the lyrics of the requested song.
  """
  @commands.command(aliases=['ly','lyric'])
  async def lyrics(self,ctx,*,message=None):

    # Search for song by given name (Default is currently playing song)
    if message:
      song = self.genius.search_song(message)
    else:
      if not self.currently_playing:
        await ctx.send('No song is currently playing')
        return
      song = self.genius.search_song(self.currently_playing.split('(', 1)[0].split('[', 1)[0])
      
    # If song is not found, relay error 
    if not song:
      await ctx.send(content="Could not find lyrics")
      return

    # Separating lyrics lines to lines
    LRC = song.lyrics.split("\n")
    first_line = LRC[0].split("Lyrics")

    # Song name without whitespace
    song_name = first_line[0][:-1]
    artist = song.artist
    LRC[0] = f"**{song_name} - {artist}**\n"

    # Re-add the first lyric line
    LRC.insert(1, (first_line[1]))

    # Clean last line from numbers in the end
    LRC[-1] = LRC[-1].replace("Embed","")
    while True:
      try:
        last_line = LRC[-1]
        if int(last_line[-1]) + 1: 
          LRC[-1] = last_line[:-1]
      except:
        break
    
    # Collect messages of length <2000 as fragments
    message_fragments = []
    while LRC:
      s = ""
      while LRC and (len(s) + len(LRC[0])) <= 2000:
        s += LRC.pop(0) + "\n"
      message_fragments.append(s)
    
    # Print each fragment as a separate message
    for fragment in message_fragments:
      await ctx.send(content=fragment)
    
  """
  *************************
      Function: ressume
  *************************
  Description: Resumes audio playing.
  """
  @commands.command(aliases=['continue'])
  async def resume(self,ctx):
    try:
      await ctx.voice_client.resume() 
      await ctx.send(embed=qb.send_msg('Resume playing'))
      self.play_status = True 
    except (TypeError,AttributeError):
      return        
  
  """
  *************************
      Function: list
  *************************
  Description: Shows the queue as an embed in discord.
  """
  @commands.command(aliases=['queue', 'q', 'l'])
  async def list(self,ctx):
    if self.queue:
      await ctx.send(embed=qb.c_playing(self.currently_playing))
      await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue) > 25 else None)
    else:
      await ctx.send(embed=qb.send_msg('There is no current queue'))  
  
  """
  *************************
      Function: remove
      Parameters: message
  *************************
  Description: Removes song from the queue by index.
  """
  @commands.command(aliases=['r', 'rm'])
  async def remove(self,ctx,*,message):
    try:
      fetch = self.queue.pop(int(message)-1)
      await ctx.send(embed=qb.removed_song(fetch[0]))
    except IndexError: 
      await ctx.send("Index error")
  
  """
  *************************
      Function: clear
  *************************
  Description: Clears the queue.
  """
  @commands.command(aliases=['clr'])
  async def clear(self, ctx):
    self.queue.clear()
    await ctx.send(embed=qb.send_msg('Cleared the queue!'))
  
  """
  *************************
      Function: skip
  *************************
  Description: Skips the current song.
  """
  @commands.command(aliases=['s'])
  async def skip(self, ctx):
    try:
      await ctx.send(embed=qb.send_msg('Skipped!'))
      await ctx.voice_client.stop()
      self.play_after(ctx)
    except (TypeError,AttributeError):
      return 
  
  """
  *************************
      Function: help
  *************************
  Description: Displays a help embed in discord that showcases commands.
  """
  @commands.command(aliases=['h'])
  async def help(self, ctx):
    await ctx.send(embed=qb.help_list(self.cmnds))  
  
  """
  *************************
      Function: loop
  *************************
  Description: Toggles loop mode.
  """
  @commands.command()
  async def loop(self, ctx):
    self.loop = not self.loop
    await ctx.send(embed=qb.send_msg("Queue loop turned {status}".format(status="on" if self.loop else "off")))
    
  """
  *************************
      Function: shuffle
  *************************
  Description: Shuffles the queue.
  """                
  @commands.command()
  async def shuffle(self, ctx):
    await ctx.send(embed=qb.send_msg('Shuffled the queue!'))  
    random.shuffle(self.queue) 
    self.increment = -1 
  
  """
  *************************
      Function: playskip
      Parameters: message
  *************************
  Description: Playskips to a specific song in the queue.
  """
  @commands.command(aliases=['ps'])
  async def playskip(self, ctx,*,message):
    try:
      fetch = self.queue.pop(int(message)-1)
      self.queue.insert(0, fetch)
      await ctx.voice_client.stop()
      self.play_after(ctx)
      await ctx.send(embed=qb.send_msg(f"Skipped to {int(message)}!"))
    except (TypeError, AttributeError, IndexError):
      return
  
  """
  *************************
      Function: save
  *************************
  Description: Saves current queue as a playlist in JSON.
  """
  @commands.command()
  async def save(self, ctx, *, message):
    if self.queue:

      #Open the playlist directory and overwrite the saved playlist with current queue
      with open(self.json_file) as json_in:
        playlist_list = (json.load(json_in))
      playlist_list['playlists'][message] = self.queue 
      
      #Save the new directory
      with open(self.json_file, 'w') as outfile:
        json.dump(playlist_list, outfile)
      await ctx.send(embed=qb.send_msg(f"Saved queue as {message}!"))

    else:
      await ctx.send(embed=qb.send_msg('No queue to save as a playlist!'))  
  
  """
  *************************
      Function: load
  *************************
  Description: Loads a playlist from JSON.
  """
  @commands.command()
  async def load(self, ctx, *, message):
    with open(self.json_file) as json_in:
      playlist_list = (json.load(json_in))
      
    # If the playlist is found, load into queue
    if message in playlist_list['playlists']:
      await ctx.send(embed=qb.send_msg('Loading playlist...'))
      for song in playlist_list['playlists'][message]:
        await self.play_load(ctx, song[0])
      await self.list(ctx)  
    else:
     await ctx.send(embed=qb.send_msg('Playlist name not valid!'))

  # #Add Banger to banger  list UNFINISHED
  # @commands.command(aliases=['bang'])
  # async def bang(self,ctx):
  #   pass   
  
  # #Play Banger from banger list UNFINISHED
  # @commands.command(aliases=['banger'])
  # async def banger(self,ctx):
  #   pass

async def setup(client, genius_token):
  await client.add_cog(music(client, genius_token))   