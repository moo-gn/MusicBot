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
    self.bangers = []
    self.loop = False
    self.play_status = False
    self.play_skip = False
    self.play_skip_int = 0
    #initiate genuis object to search lyrics of songs
    self.genius = lyricsgenius.Genius(genius_token, timeout=5, retries=2, excluded_terms=['spotify', 'top hits', 'Release Calendar'])
    self.currently_playing = ''
    self.json_file = "playlist.json"
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    self.cmnds = ['join, j : joins the voice channel', 
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
    'banger: add a banger to the queue']

  #Join the voice channel of the caller
  @commands.command(aliases=['j'])
  async def join(self,ctx):
    if ctx.author.voice is None:
      await ctx.send('Please join a voice channel!')
    vc = ctx.author.voice.channel
    if ctx.voice_client is None:
      await vc.connect()
    else:
      await ctx.voice_client.move_to(vc)      
  
  #Leave the current voice channel
  @commands.command()
  async def leave(self,ctx):
    await ctx.voice_client.disconnect()  
  
  #ADD COMMENT
  @commands.command()
  async def position(self,ctx):
    await ctx.send(embed=qb.send_msg(self.increment))
  
  #Print the song currently playing
  @commands.command(aliases=['c'])
  async def current(self,ctx):
    await ctx.send(embed=qb.send_msg(str(self.increment) + ' ' + self.currently_playing))

  #Maintain indexing in bounds
  def if_end(self, x):
    x %= len(self.queue)
    return x    
  
  #the function is called after the audio finishes playing, it plays the next song in queue and removes it if loop is off
  def play_next(self, ctx):
    if len(self.queue) > 0:
      
      self.increment += 1
      self.increment = self.if_end(self.increment)
      next = 0
      
      #Check flag for skipping to this song
      if self.play_skip:
        next = self.play_skip_int
        self.increment = next
        self.play_skip = False

      if self.loop:
        fetch = self.queue[self.increment]
        plcmnt = str(self.increment + 1) + '. '
      else:  
        fetch = self.queue.pop(next)
        plcmnt = ''
       
      #create ffmpegOpusAudio from link and play it and send a message 
      source = discord.FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS)
      ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
      self.currently_playing = fetch[0]
      #send the placement in the queue if its looping, and the name of song
      self.client.loop.create_task(ctx.send(embed=qb.first_song_playing(plcmnt + fetch[0])))

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
    



  #Play the requested song
  @commands.command(aliases=['add', 'p'])
  async def play(self,ctx,*,message):
    YDL_OPTIONS = {'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}
    await asyncio.sleep(0.01)

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()


    if len(self.queue) > 100:
        await ctx.send(embed=qb.send_msg('Queue limit reached!'))

    #if youtube playlist add each vid to the queue and play the first if its not playing
    elif message.startswith('https://www.youtube.com/playlist?list='):
      msg = await ctx.send(embed=qb.send_msg('adding playlist ...'))
      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(message, download=False)
        for entry in info['entries']:
          self.queue.append([entry['title'], entry['url']])
        
      if not ctx.voice_client.is_playing():
        fetch = self.queue.pop(0)
        source = await discord.FFmpegOpusAudio.from_probe(fetch[1], **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        self.currently_playing = fetch[0]
        self.play_status = True 
        await ctx.send(embed=qb.first_song_playing(fetch[0]))


      await msg.edit(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)
    # search youtube for message and get link from results
    else:
      fetch = search(message)
      print(fetch[1])

      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(fetch[0], download=False)
          #BEFORE PUSHING CHECK FOR URL
          for format in info['formats']:
              if 'url' in format:
                  s = format['url'].lstrip('https://')
                  if s[0] == 'r':
                      url2 = format['url']
                      break
      #play or add to list if already
      if ctx.voice_client.is_playing():
        self.queue.append([fetch[1],url2])
        await ctx.send(embed=qb.add_song_playing(fetch[1]))
      else: 
        #create ffmpegOpusAudio from link and play it and send a message, call play_next after the song ends
        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        self.currently_playing = fetch[1]
        self.play_status = True 
        await ctx.send(embed=qb.first_song_playing(fetch[1]))

  #if client voice is playing add this song to the top of the queue
  @commands.command(aliases=['pn'])
  async def playnext(self, ctx, *, message):
    if ctx.voice_client and ctx.voice_client.is_playing():
      YDL_OPTIONS = {'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}

      fetch = search(message)

      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(fetch[0], download=False)
          #BEFORE PUSHING CHECK FOR URL
          for format in info['formats']:
              if 'url' in format:
                  s = format['url'].lstrip('https://')
                  if s[0] == 'r':
                      url2 = format['url']
                      break

      self.queue.insert(self.increment + 1,[fetch[1],url2])
      await ctx.send(embed=qb.playnext_embed(fetch[1]))
    else:
      await ctx.send(content= 'nothing is playing')


  @commands.command()
  async def play_load(self,ctx,x):
    YDL_OPTIONS = {'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}
    await asyncio.sleep(0.01)

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    print(x)
    fetch = search(x)
    print(fetch[1])

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(fetch[0], download=False)
        url2 = info['formats'][0]['url']

    if ctx.voice_client.is_playing():
      self.queue.append([fetch[1],url2])
    else:  
      source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
      ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
      self.currently_playing = fetch[1]
      self.play_status = True 
  
  #Pause the music
  @commands.command(aliases=['stop', 'hold'])
  async def pause(self,ctx):
        self.play_status = False
        try:
          await ctx.voice_client.pause()
          await ctx.send(embed=qb.send_msg('Paused music!'))
        except (TypeError,AttributeError):
          return
  
  #Resume the music
  @commands.command(aliases=['continue'])
  async def resume(self,ctx):
    self.play_status = True 
    try:
      await ctx.voice_client.resume() 
      await ctx.send(embed=qb.send_msg('Resume playing'))
    except (TypeError,AttributeError):
      return        
  
  # #Add Banger to banger  list UNFINISHED
  # @commands.command(aliases=['bang'])
  # async def bang(self,ctx):
  #   pass   
  
  # #Play Banger from banger list UNFINISHED
  # @commands.command(aliases=['banger'])
  # async def banger(self,ctx):
  #   pass
  
  #SHOW AN EMBED FOR THE QUEUE
  @commands.command(aliases=['queue', 'q', 'l'])
  async def list(self,ctx):
    if self.queue:
      await ctx.send(embed=qb.c_playing(self.currently_playing))
      await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue) > 25 else None)
    else:
      await ctx.send(embed=qb.send_msg('There is no current queue'))  
  
  #Remove song by index
  @commands.command(aliases=['r', 'rm'])
  async def remove(self,ctx,*,message):
    try:
      fetch = self.queue.pop(int(message)-1)
      await ctx.send(embed=qb.removed_song(fetch[0]))
    except IndexError: 
      await ctx.send("Index error")
  
  #Clear queue
  @commands.command(aliases=['clr'])
  async def clear(self, ctx):
    self.queue.clear()
    await ctx.send(embed=qb.send_msg('Cleared the queue!'))
  
  #Skip current song
  @commands.command(aliases=['s'])
  async def skip(self, ctx):
    try:
      await ctx.send(embed=qb.send_msg('Skipped!'))
      await ctx.voice_client.stop()
      self.play_next(ctx)
    except (TypeError,AttributeError):
      return 
  
  #Display options
  @commands.command(aliases=['h'])
  async def help(self, ctx):
    await ctx.send(embed=qb.help_list(self.cmnds))  
  
  #Toggle looping the queue
  @commands.command()
  async def loop(self, ctx):
    self.loop = not self.loop
    bool = "on" if self.loop else "off"
    self.increment = -1 
    await ctx.send(embed=qb.send_msg('Queue loop turned {0}!'.format(bool)))
    
  #Shuffle the queue                 
  @commands.command()
  async def shuffle(self, ctx):
    await ctx.send(embed=qb.send_msg('Shuffled the queue!'))  
    random.shuffle(self.queue) 
    self.increment = -1 
  
  #PLAY SKIP TO INDEX IN QUEUE
  @commands.command(aliases=['ps'])
  async def playskip(self, ctx,*,message):
    if int(message)-1 > len(self.queue) - 1 or int(message)-1 < 1:
      await ctx.send(embed=qb.send_msg('Skip number not admissible'))
      return
    try:
      await ctx.send(embed=qb.send_msg(f"Skipped to {int(message)}!"))
      self.play_skip = True
      self.play_skip_int = int(message)-1
      await ctx.voice_client.stop()
      self.play_next(ctx)
    except (TypeError,AttributeError):
      return    
  
  #Save playlist
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
  
  #Load playlist
  @commands.command()
  async def load(self, ctx, *, message):
    with open(self.json_file) as json_in:
      playlist_list = (json.load(json_in))
      
    #If the playlist is found, load into queue
    if message in playlist_list['playlists']:
      await ctx.send(embed=qb.send_msg('Loading playlist...'))
      for song in playlist_list['playlists'][message]:
        print(song[0])
        await self.play_load(ctx, song[0])
      await self.list(ctx)  
    else:
     await ctx.send(embed=qb.send_msg('Playlist name not valid!'))

async def setup(client, genius_token):
  await client.add_cog(music(client, genius_token))   
