import discord
from discord.ext import commands
import yt_dlp
import embeds as qb
from search_yt import search
import asyncio

class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.queue = []
    self.play_status = False
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    self.cmnds = ['join, j : joins the voice channel', 'leave : leaves the voice channel', 'play, p , add : plays song or appends it to queue', 'pause, stop, hold : pauses the song', 'resume, continue : resume playing','list, queue, l, q : displays the first 25 songs on the queue' , 'skip : skips song', 'clear, clr : clears the queue', 'remove, r : removes a song from queue based on its index']


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

  def play_next(self, ctx):
    if len(self.queue) > 0:
      fetch = self.queue.pop(0) 
      source = discord.FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS)
      ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
      
      
  @commands.command(aliases=['add', 'p'])
  async def play(self,ctx,*,message):
    YDL_OPTIONS = {'format':'bestaudio', 'playlistrandom': True, 'quiet' : True}
    await asyncio.sleep(0.01)

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    #if youtube playlist add each vid to the queue and play the first if its not playing
    if message.startswith('https://www.youtube.com/playlist?list='):
      msg = await ctx.send(embed=qb.send_msg('adding playlist ...'))
      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(message, download=False)
      for entry in info['entries']:
        self.queue.append([entry['title'], entry['url']])
        
      if not ctx.voice_client.is_playing():
        fetch = self.queue.pop(0)
        source = discord.FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        await ctx.send(embed=qb.first_song_playing(fetch[0]))
      await msg.edit(embed=qb.queue_list(self.queue))

    else:
      fetch = search(message)
      print(fetch[1])

      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(fetch[0], download=False)
          url2 = info['formats'][0]['url']

      if ctx.voice_client.is_playing():
        self.queue.append([fetch[1],url2])
        await ctx.send(embed=qb.add_song_playing(fetch[1]))
      else:  
        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))
        self.play_status = True 
        await ctx.send(embed=qb.first_song_playing(fetch[1]))


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
      await ctx.send(embed=qb.queue_list(self.queue)) 
    else:
      await ctx.send(embed=qb.send_msg('There is no current queue'))  

  @commands.command(aliases=['r'])
  async def remove(self,ctx,*,message):
    try:
      fetch = self.queue.pop(int(message)-1)
      await ctx.send(embed=qb.removed_song(fetch[1]))
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

  @commands.command()
  async def help(self, ctx):
    await ctx.send(embed=qb.help_list(self.cmnds))  

def setup(client):
  client.add_cog(music(client))   
