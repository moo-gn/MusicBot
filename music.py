import discord
from discord.ext import commands
import yt_dlp


from search_yt import search

class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.queue = []

  @commands.command()
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
      source = self.queue.pop(0)  
      ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))

  @commands.command()
  async def play(self,ctx,*,message):

    # Convert query text into url
    fetch = search(message)
    
    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format':'bestaudio'}

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(fetch[0], download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)

      if ctx.voice_client.is_playing():
        self.queue.append(source)
      else:  
        ctx.voice_client.play(source, after= lambda x : self.play_next(ctx))

  @commands.command()
  async def pause(self,ctx):
    await ctx.voice_client.pause()

  @commands.command()
  async def list(self,ctx):
    await ctx.send(self.queue) 

  @commands.command()
  async def resume(self,ctx):
    await ctx.voice_client.resume()  

  @commands.command()
  async def remove(self,ctx,*,message):
    try:
      self.queue.pop(int(message)-1)
    except IndexError: 
      await ctx.send("Index error")

def setup(client):
  client.add_cog(music(client))    