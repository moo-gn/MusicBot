# This example requires the 'message_content' privileged intent to function.

import asyncio
import random
import discord
import yt_dlp as youtube_dl
from discord.ext import commands
from discord.ext.commands import Context, Cog
from dataBase import db_add_song, random_songs, artist_songs, blacklist, get_blacklist
import embeds as qb
from qbuttons import Qbuttons
from ytdlpSource import YTDLPSource
from search_yt import search
import sys
sys.path.append("..")
import credentials

# Suppress noise about console usage from errors
# youtube_dl.utils.bug_reports_message = lambda: ''


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.now_playing = []
        self.loop = False
        self.auto_play = False

    @commands.command(aliases=['j'])
    async def join(self, ctx : Context):
        """Joins a voice channel"""

        if ctx.voice_client is None and ctx.author.voice is None:
            return await ctx.send(embed=qb.send_msg('Please join a voice channel first!'))
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(ctx.author.voice.channel)

        await ctx.author.voice.channel.connect()

    @commands.command(aliases=["p"])
    async def play(self, ctx:Context, *, query):
        """Search yt and streams it"""

        async with ctx.typing():
            info = await search(query)
            loop_tag = " 🔁" if self.loop else ""
            
            if not ctx.voice_client.is_playing():
                player = await YTDLPSource.from_url(info[1], loop=self.bot.loop)
                await db_add_song(song=info[0], link=info[1])
                ctx.voice_client.play(player, after=lambda x: asyncio.run_coroutine_threadsafe(self.play_after(ctx),self.bot.loop))
                await ctx.send(embed=qb.send_msg(f'Now playing: **{info[0]}** {loop_tag}'))
                self.now_playing = [info[0],info[1]]

                if self.loop:
                    self.queue.append([info[0],info[1]])

            else:
                self.queue.append([info[0],info[1]])
                await ctx.send(embed=qb.send_msg(f'Added **{info[0]}** to queue {loop_tag}'))
            

    async def play_after(self, ctx:Context):
        async with ctx.typing():
            if self.queue:
                song = self.queue.pop(0)
                if self.loop:
                    self.queue.append(song)
                try:
                    player = await YTDLPSource.from_url(song[1], loop=self.bot.loop)
                except youtube_dl.utils.DownloadError:
                    await ctx.send(embed=qb.send_msg(f"'**{song[0]}**' is unavailable retrying with another song!"))
                    song = await random_songs(ctx, 1)
                    self.queue.extend(song)
                    if not ctx.voice_client.is_playing():
                        await self.play_after(ctx)
                
                await db_add_song(song=song[0], link=song[1])
                ctx.voice_client.play(player, after=lambda x: asyncio.run_coroutine_threadsafe(self.play_after(ctx),self.bot.loop))
                loop_tag = " 🔁" if self.loop else ""
                autoplay_tag = " 🤖" if self.auto_play else ""
                await ctx.send(embed=qb.send_msg(f'Now playing: **{song[0]}** {autoplay_tag}{loop_tag}'))
                self.now_playing = song

            elif self.auto_play:
                song = await random_songs(ctx, 1)
                self.queue.extend(song)
                await self.play_after(ctx)

            
    @commands.command(aliases=["pn"])
    async def playnext(self, ctx, *, query):
        """Plays a song next (adds it to the top of the queue)"""
        async with ctx.typing():
            if not ctx.voice_client.is_playing():
                await ctx.send(embed=qb.send_msg(f'Nothing is playing'))
            
            info = await search(query)
            self.queue.insert(0, info)

            await ctx.send(embed=qb.send_msg(f'**{info[0]}** will play next'))

    @commands.command(aliases=['c'])
    async def current(self, ctx: Context):
        """
        Prints the song that is currently playing.
        """
        await ctx.send(embed=qb.send_msg(f'**{self.currently_playing[0]}** is currently playing'))

    @commands.command(aliases=['s'])
    async def skip(self, ctx: Context):
        """
      Skips the current song
      """
        if not ctx.voice_client.is_playing():
            return await ctx.send(embed=qb.send_msg("Nothing is playing right now."))
        
        await ctx.send(embed=qb.send_msg('Skipped!'))
        ctx.voice_client.stop()

    @commands.command()
    async def loop(self, ctx: Context):
        """
        Toggles loop mode
      """
        self.loop = not self.loop
        await ctx.send(embed=qb.send_msg("Queue loop turned {status}".format(status="on 🔁" if self.loop else "off ▶️")))
        if self.loop and ctx.voice_client.is_playing():
            self.queue.append(self.now_playing)
        if not self.loop:
            if self.now_playing == self.queue[0]:
                self.queue.pop(0)

    @commands.command(aliases=['queue','q'])
    async def list(self, ctx: Context):
        """
      Shows the current music queue as an embed in discord
      """
        async with ctx.typing():
            loop_tag = " 🔁" if self.loop else ""
            await ctx.send(embed=qb.c_playing(f'{self.now_playing[0]} {loop_tag}'))
            await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue) > 25 else None)

    @commands.command(aliases=['clr'])
    async def clear(self, ctx: Context):
        """
        Clears the queue
        """
        self.queue.clear()
        await ctx.send(embed=qb.send_msg('Cleared the queue!'))

    @commands.command(aliases=['c'])
    async def current(self, ctx: Context):
        """
        Prints the song that is currently playing.
        """
        await ctx.send(embed=qb.send_msg(self.now_playing[0]))

    @commands.command(aliases=['r', 'rm'])
    async def remove(self, ctx: Context , *, message: str):
        """
        Removes song from the queue by index
        """
        try:
            song = self.queue.pop(int(message)-1)
            await ctx.send(embed=qb.removed_song(song[0]))
        except IndexError: 
            await ctx.send(embed=qb.send_msg("Index error"))

    @commands.command(aliases=['ps'])
    async def playskip(self, ctx: Context, *, message: str):
        """
        Playskips to a specific song in the queue
        """
        try:
            song = self.queue.pop(int(message)-1)
            self.queue.insert(0, song)
            await ctx.send(embed=qb.send_msg(f"Skipped to {int(message)}. **{song[0]}**!"))
            ctx.voice_client.stop()
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles the current queue"""
        if not self.queue:
            return await ctx.send(embed=qb.send_msg("There is no current queue"))

        random.shuffle(self.queue)
        await ctx.send(embed=qb.send_msg("Queue shuffled!"))
        await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

    @commands.command(aliases=['stop', 'hold'])
    async def pause(self, ctx: Context):
        """
        Pauses audio playing
        """
        await ctx.send(embed=qb.send_msg('Stopped playing')) 
        await ctx.voice_client.pause() 

    @commands.command(aliases=['continue'])
    async def resume(self, ctx: Context):
        """
        Resumes audio playing
        """
        await ctx.send(embed=qb.send_msg('Resumed playing'))
        await ctx.voice_client.resume() 

    @commands.command()
    async def prandy(self, ctx: Context, message: str = None):
        """
        Play random songs   
        """
        async with ctx.typing():
            data = await random_songs(ctx, amount=int(message) if message else 5)
            # Add the music
            self.queue.extend(data)
            if not ctx.voice_client.is_playing():
                await self.play_after(ctx)
            
            await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

    @commands.command()
    async def partist(self, ctx: Context, *, message: str):
        """
        Play song from specific artist chosen by the user
        """
        async with ctx.typing():
            data = await artist_songs(ctx, message)
            # Add the music
            self.queue.extend(data)
            if not ctx.voice_client.is_playing():
                await self.play_after(ctx)

            await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

    @commands.command(aliases=['ap'])
    async def autoplay(self, ctx: Context, message: str = None):
        """
        Play random songs when queue is empty forever   
        """
        async with ctx.typing():
            self.auto_play = not self.auto_play
            await ctx.send(embed=qb.send_msg("Autoplay turned {status}".format(status="on 🤖" if self.auto_play else "off ▶️")))
            if not ctx.voice_client.is_playing():
                await self.play_after(ctx)

    @commands.command(aliases=['B'])
    async def blacklist(self, ctx: Context, *args):
        """
        add argument or current song to blacklist   
        """
        async with ctx.typing():
            if args:
                song = ' '.join(args)
            elif self.now_playing:
                song = self.now_playing[0]
            else:
                await ctx.send(embed=qb.send_msg(f"Nothing is playing and no argument!"))
                return
            await blacklist(ctx, song)

    @commands.command(aliases=['BL', 'gb'])
    async def getblacklist(self, ctx: Context):
        """
        display the full blacklist   
        """
        async with ctx.typing():
            data = await get_blacklist(ctx)
            await ctx.send(embed=qb.queue_list(data, title="BlackList:"), view = Qbuttons(data) if len(data)> 25 else None)
    

    @commands.command()
    async def leave(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    #precondition checks

    @play.before_invoke
    @playnext.before_invoke
    @remove.before_invoke
    @skip.before_invoke
    @clear.before_invoke
    @playskip.before_invoke
    @shuffle.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @leave.before_invoke
    @prandy.before_invoke
    @partist.before_invoke
    @blacklist.before_invoke
    @autoplay.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(embed=qb.send_msg("You are not connected to a voice channel."))
                raise commands.CommandError("User not connected to a voice channel.")

    @list.before_invoke
    @remove.before_invoke
    @clear.before_invoke
    @shuffle.before_invoke
    @playskip.before_invoke  
    async def ensure_queue_not_empty(self, ctx):
        if not self.queue:
            await ctx.send(embed=qb.send_msg("There is no current queue"))
            raise commands.CommandError("Queue is empty.")


