import discord
from discord.ext import commands
import yt_dlp
import embeds as qb
from search_yt import search
import asyncio
import random
from qbuttons import Qbuttons
import json

class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.queue = []
    self.increment = -1
    self.loop = False
    self.play_status = False
    self.play_skip = False
    self.play_skip_int = 0
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
    'save: saves the current queue', 
    'load: loads a playlist to the queue']


  @commands.command(aliases=['j'])
  async def join(self,ctx):
    if ctx.author.voice is None:
      await ctx.send('Please join a voice channel!')
    vc = ctx.author.voice.channel
    if ctx.voice_client is None:
      await vc.connect()
    else:
      await ctx.voice_client.move_to(vc)      

  @commands.command()
  async def leave(self,ctx):
    await ctx.voice_client.disconnect()  

  @commands.command()
  async def position(self,ctx):
    await ctx.send(embed=qb.send_msg(self.increment))

  @commands.command()
  async def current(self,ctx):
    await ctx.send(embed=qb.send_msg(str(self.increment) + ' ' + self.currently_playing))

  def if_end(self, x):
    if x >= len(self.queue):
      x = 0
    return x    

  def play_next(self, ctx):
    if len(self.queue) > 0:
      #questionable
      self.increment += 1
      self.increment = self.if_end(self.increment)
      next = 0

      if self.play_skip:
        next = self.play_skip_int
        self.increment = next
        self.play_skip = False

      if self.loop:
        fetch = self.queue[self.increment]
      else:  
        fetch = self.queue.pop(next)

      source = discord.FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS)
      ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
      self.currently_playing = fetch[0]
      
      
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
        source = discord.FFmpegOpusAudio.from_probe(fetch[1], **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        self.currently_playing = fetch[0]
        await ctx.send(embed=qb.first_song_playing(fetch[0]))
      await msg.edit(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

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

      if ctx.voice_client.is_playing():
        self.queue.append([fetch[1],url2])
        await ctx.send(embed=qb.add_song_playing(fetch[1]))
      else:  
        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        self.currently_playing = fetch[1]
        self.play_status = True 
        await ctx.send(embed=qb.first_song_playing(fetch[1]))

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

  @commands.command(aliases=['stop', 'hold'])
  async def pause(self,ctx):
        self.play_status = False
        try:
          await ctx.voice_client.pause()
          await ctx.send(embed=qb.send_msg('Paused music!'))
        except (TypeError,AttributeError):
          return

  @commands.command(aliases=['continue'])
  async def resume(self,ctx):
    self.play_status = True 
    try:
      await ctx.voice_client.resume() 
      await ctx.send(embed=qb.send_msg('Resume playing'))
    except (TypeError,AttributeError):
      return        

  @commands.command(aliases=['queue', 'q', 'l'])
  async def list(self,ctx):
    if len(self.queue):
      await ctx.send(embed=qb.c_playing(self.currently_playing))
      await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue) > 25 else None)
    else:
      await ctx.send(embed=qb.send_msg('There is no current queue'))  

  @commands.command(aliases=['r', 'rm'])
  async def remove(self,ctx,*,message):
    try:
      fetch = self.queue.pop(int(message)-1)
      await ctx.send(embed=qb.removed_song(fetch[0]))
    except IndexError: 
      await ctx.send("Index error")

  @commands.command(aliases=['clr'])
  async def clear(self, ctx):
    self.queue.clear()
    await ctx.send(embed=qb.send_msg('Cleared the queue!'))

  @commands.command(aliases=['s'])
  async def skip(self, ctx):
    try:
      await ctx.send(embed=qb.send_msg('Skipped!'))
      await ctx.voice_client.stop()
      self.play_next(ctx)
    except (TypeError,AttributeError):
      return 

  @commands.command(aliases=['h'])
  async def help(self, ctx):
    await ctx.send(embed=qb.help_list(self.cmnds))  

  @commands.command()
  async def loop(self, ctx):
    if self.loop:
      self.loop = False
      await ctx.send(embed=qb.send_msg('Queue loop turned off!'))
    else:
      self.loop = True
      await ctx.send(embed=qb.send_msg('Queue loop turned on!')) 

  @commands.command()
  async def shuffle(self, ctx):
    await ctx.send(embed=qb.send_msg('Shuffled the queue!'))  
    random.shuffle(self.queue) 
    self.increment = -1 

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

  @commands.command()
  async def save(self, ctx, *, message):
    if len(self.queue):
      with open(self.json_file) as json_in:
        playlist_list = (json.load(json_in))
      playlist_list['playlists'][message] = self.queue 

      with open(self.json_file, 'w') as outfile:
        json.dump(playlist_list, outfile)

      await ctx.send(embed=qb.send_msg(f"Saved queue as {message}!"))
    else:
      await ctx.send(embed=qb.send_msg('No queue to save as a playlist!'))  

  @commands.command()
  async def load(self, ctx, *, message):
    with open(self.json_file) as json_in:
      playlist_list = (json.load(json_in))

    if message in playlist_list['playlists']:
      await ctx.send(embed=qb.send_msg('Loading playlist...'))
      for song in playlist_list['playlists'][message]:
        print(song[0])
        await self.play_load(ctx, song[0])
      await self.list(ctx)  
    else:
     await ctx.send(embed=qb.send_msg('Playlist name not valid!'))

def setup(client):
  client.add_cog(music(client))   
