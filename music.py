import discord
from discord.ext import commands
import yt_dlp

class music(commands.Cog):
  def __init__(self, client):
    self.client = client

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

  @commands.command()
  async def play(self,ctx,url):
    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()

    ctx.voice_client.stop()
    FFMPEG_OPTIONS = {'options': '-vn'}  
    YDL_OPTIONS = {'format':'bestaudio'}
    vc = ctx.voice_client

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
      vc.play(source)

  @commands.command()
  async def pause(self,ctx):
    await ctx.voice_client.pause()

  @commands.command()
  async def resume(self,ctx):
    await ctx.voice_client.resume()

def setup(client):
  client.add_cog(music(client))    