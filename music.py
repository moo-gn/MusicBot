import discord
from discord.ext import commands
import yt_dlp
import queueembed as qb
from search_yt import search
import asyncio

class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.queue = []
    self.play_status = False
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

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
      ctx.voice_client.play(fetch[0], after= lambda x : self.play_next(ctx)) 
      

  @commands.command(aliases=['add', 'p'])
  async def play(self,ctx,*,message):
    await asyncio.sleep(1)
    fetch = search(message)
    print(fetch[1])

    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()
 
    YDL_OPTIONS = {'format':'bestaudio'}

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(fetch[0], download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)

      if ctx.voice_client.is_playing():
        self.queue.append([source, fetch[1]])
        await ctx.send(embed=qb.add_song_playing(fetch[1]))
      else:  
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

  @commands.command()
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

  @commands.command()
  async def skip(self, ctx):
    try:
      await ctx.send(embed=qb.send_msg('Skipped!'))
      await ctx.voice_client.stop()
      self.play_next(ctx)
    except (TypeError,AttributeError):
      return 

def setup(client):
  client.add_cog(music(client))    