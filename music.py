from discord import Bot, FFmpegOpusAudio
from discord.ext import commands
from discord.ext.commands import Context, Cog
from lyricsgenius import Genius
from sshtunnel import SSHTunnelForwarder
from pymysql import connect

import asyncio, random
import yt_dlp as youtube_dl

import embeds as qb
from search_yt import search
from qbuttons import Qbuttons

import sys
sys.path.append("..")
import credentials

# start the connection to pythonanywhere
connection = SSHTunnelForwarder((credentials.ssh_website),
                                ssh_username=credentials.ssh_username, ssh_password=credentials.ssh_password,
                                remote_bind_address=(credentials.remote_bind_address, 3306),
                             ) 
connection.start()

def db_init():
  """
  Connects to the remote database, returns the database and its cursor
  """
  # Connect
  db = connect(
      user=credentials.db_user,
      passwd=credentials.db_passwd,
      host=credentials.db_host, port=connection.local_bind_port,
      db=credentials.db,
  )

  # Return cursor and db
  return db.cursor(), db 

def db_add_song(song: str, link: str, ctx: Context = None):
  """
  Adds a song to the database. If the song exists it increments its uses by 1 
  """
  # Init the cursor and database
  cursor, db = db_init()

  try:
    cursor.execute(f"SELECT song FROM music WHERE song='{song}';")
    exists = cursor.fetchall()
    if exists:
      cursor.execute(f"UPDATE music SET uses=uses+1 WHERE song='{song}';")
    else:
      cursor.execute(f"INSERT INTO music(song, uses, link) values ('{song}', '1', '{link}');")            
    db.commit()
  except Exception as e:
    ctx.send(content=e)

  # Close the database
  db.close()

async def setup(client: Bot, genius_token: str):
  """
  Function used to enlist the commands to the music bot 
  """
  client.add_cog(music(client, genius_token))   

class music(Cog):
  def __init__(self, client: Bot, genius_token: Genius):
    self.client: Bot = client
    self.genius: Genius = Genius(genius_token, timeout=5, retries=2, excluded_terms=['spotify', 'top hits', 'Release Calendar', 'Best Songs', 'Genius Picks'])
    self.increment = -1
    self.queue = []
    self.loop = False
    self.currently_playing = ''
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    self.yt_OPTIONS = {'format':'bestaudio', "noplaylist": "True", 'verbose': False}
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
    'partist: plays songs from the database from specific artist chosen by the user',
    'prandy: plays 5 random song from the database. You can specify a number to play'
    'Blacklist from prandy using Black or B, and remove by Unblack or UB, and display list with Blacklist or BL'
    ]

  @commands.command(aliases=['j'])
  async def join(self, ctx: Context):
    """
    Results in the bot joining the caller's voice channel.
    """
    if ctx.author.voice is None:
      await ctx.send('Please join a voice channel!')
    if ctx.voice_client is None:
      await ctx.author.voice.channel.connect()
    else:
      await ctx.voice_client.move_to(ctx.author.voice.channel)      
  
  @commands.command()
  async def leave(self, ctx: Context):
    """
    Results in the bot joining the caller's voice channel.
    """
    await ctx.voice_client.disconnect()  

  def song_info(self, inquiry: str):
    """
    Parses youtube for an inquiry and returns the name and audio link of the first result.
    :params: inquiry - (intended to be the inquiry of what is to be played)
    :return: fetch - (video_link, song_name), audio_link - (link of the audio of the youtube clip)
    """
    # Fetch search result from youtube
    fetch = search(inquiry)
    # Extract info from the URL
    info = youtube_dl.YoutubeDL(self.yt_OPTIONS).extract_info(fetch[0], download=False)
    # Get the audio link from the extract
    for format in info['formats']:
              if 'url' in format:
                  s = format['url'].lstrip('https://')
                  if s[0] == 'r':
                      audio_link = format['url']
                      break
    # Return the fetched search result and the audio link of the result
    return fetch, audio_link

  async def append_data(self, ctx: Context, data):
      """
      Appends the SQL data to the music queue
      """
      data = list(data)
      while len(data) > 0:
        # Add the song to the database
        entry = data[0]
        data.pop(0)
        db_add_song(song=entry[0], link=entry[1])
        # Fetch song audio url
        try:
          info = youtube_dl.YoutubeDL(self.yt_OPTIONS).extract_info(entry[1], download=False)
        except youtube_dl.utils.DownloadError:
          cursor, db = db_init()
          cursor.execute(f"DELETE FROM music WHERE song='{entry[0]}';")
          db.commit()
          await ctx.send(embed=qb.send_msg(f"'{entry[0]}' is unavailable and was removed from the DB!"))
          cursor.execute(f"select song,link FROM music WHERE uses > 5 AND blacklisted=0 ORDER BY rand() LIMIT {1};")
          new = cursor.fetchall()
          data.extend(new)
          db.close()
          continue
        # Get the audio link from the extract
        for format in info['formats']:
                  if 'url' in format:
                      s = format['url'].lstrip('https://')
                      if s[0] == 'r':
                          audio_link = format['url']
                          break
        # Append to the queue
        self.queue.append([entry[0], audio_link])

        # Connect the bot to the caller's voice channel if the bot is not connected
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if not ctx.voice_client.is_playing():
              fetch = self.queue.pop(0)
              ctx.voice_client.play(await FFmpegOpusAudio.from_probe(fetch[1], **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
              self.currently_playing = fetch[0]
              await ctx.send(embed=qb.song_playing(fetch[0]))


  def append_playlist(self, link: str):
    """
    Appends the youtube playlist to the music queue
    """
    info = youtube_dl.YoutubeDL(self.yt_OPTIONS).extract_info(link, download=False)
    for entry in info['entries']:
      # Add the song to the database
      db_add_song(song=entry['title'], link=entry['url'])
      # Append to the queue
      self.queue.append([entry['title'], entry['url']])
    

  @commands.command(aliases=['add', 'p'])
  async def play(self, ctx: Context, *, message: str):
    """
    Plays a song or playlist based on the query. If a song is playing it appends it to the queue
    """

    # Give a 0.01s wait between calling the fucntion
    await asyncio.sleep(0.01)

    # Connect the bot to the caller's voice channel if the bot is not connected
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    # Limit of songs in the queue to maintain 
    if len(self.queue) > 100:
        await ctx.send(embed=qb.send_msg('Queue limit reached!'))

    # Else if play a youtube playlist request, add each vid to the queue and play the first if its not playing
    elif message.startswith('https://www.youtube.com/playlist?list='):
        msg = await ctx.send(embed=qb.send_msg('Adding playlist, please wait as this might take some time.'))

        # Append songs from the playlist to the current queue
        self.append_playlist(message)

        # If audio is not playing start playing songs from the beginning of the queue
        if not ctx.voice_client.is_playing():
            fetch = self.queue.pop(0)
            ctx.voice_client.play(await FFmpegOpusAudio.from_probe(fetch[1], **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
            self.currently_playing = fetch[0]
            await ctx.send(embed=qb.song_playing(fetch[0]))
            
        # Display the new queue
        await msg.edit(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

    # Finally, if not a playlist and not above current queue limit, Search youtube for an inquiry and play the audio clip or add it to queue
    else:

        # Get information
        fetch, audio_url = self.song_info(message)
        print(fetch[1])

        # Add the song to the database
        db_add_song(song=fetch[1], link=fetch[0], ctx=ctx)

        # Play or add to list if already playing
        if ctx.voice_client.is_playing():
            self.queue.append([fetch[1],audio_url])
            await ctx.send(embed=qb.add_song_playing(fetch[1]))

        # Create ffmpegOpusAudio from link and play it and send a message, call play_after after the song ends
        else: 
            ctx.voice_client.play(await FFmpegOpusAudio.from_probe(audio_url, **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))
            self.currently_playing = fetch[1]
            await ctx.send(embed=qb.song_playing(fetch[1]))

  @commands.command(aliases=['pn'])
  async def playnext(self, ctx: Context, *, message: str):
    """
    If client voice is playing, load the information of a requested inquiry from youtube and add it to the top of the queue
    """
    # Check that the client is playing
    if ctx.voice_client and ctx.voice_client.is_playing():

        # Gather information
        fetch, audio_url = self.song_info(message)

        # Add the song to the database
        db_add_song(song=fetch[1], link=fetch[0], ctx=ctx)

        # Insert to the top of the queue
        self.queue.insert(0, [fetch[1],audio_url])
        await ctx.send(embed=qb.play_next(fetch[1]))

    # If the client is not playing send the following message
    else:
      await ctx.send(content= 'Nothing is playing')

  def load_next(self):
    """
    Returns the next song to play based on the current bot mode [normal, loop]
    """
    if self.loop:
        fetch = self.queue[self.increment]
        placement = str(self.increment + 1) + '. '
    else:  
        fetch = self.queue.pop(0)
        placement = ''
    return fetch, placement
    
  def play_after(self, ctx: Context):
    """
    This function is called after an audio finishes playing. If a queue exists, it will pop off the song at the beginning of the queue and play it. 
    If the shuffle condition is on, The function will not pop the song and it will keep it in the queue. It will use self.increment to determine the next song to play.
    """
    # If a queue exists do the following
    if self.queue:

      # Increment the position in the queue and Maintain the increment within bounds
      self.increment += 1
      self.increment %= len(self.queue)

      # Based on the play mode(normal or loop), determine the next song to be played and update the queue accordingly
      fetch, placement = self.load_next()

      # Add the song to the database
      db_add_song(song=fetch[1], link=fetch[0], ctx=ctx)

      # Create ffmpegOpusAudio from link and play it
      ctx.voice_client.play(FFmpegOpusAudio(fetch[1], **self.FFMPEG_OPTIONS), after= lambda x : self.play_after(ctx))

      # Update the song that is currently playing
      self.currently_playing = fetch[0]

      # Send the placement in the queue if its looping, and the name of song
      self.client.loop.create_task(ctx.send(embed=qb.song_playing(placement + fetch[0])))

  @commands.command()
  async def position(self, ctx: Context):
    """
    Prints the increment's current position in the queue.
    """
    await ctx.send(embed=qb.send_msg(self.increment))
  
  @commands.command(aliases=['c'])
  async def current(self, ctx: Context):
    """
    Prints the song that is currently playing.
    """
    await ctx.send(embed=qb.send_msg(str(self.increment) + ' ' + self.currently_playing))

  @commands.command(aliases=['ly','lyric'])
  async def lyrics(self, ctx: Context, *, message: str = None):
    """
    Prints the lyrics of the requested song.
    """
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
    
  @commands.command(aliases=['continue'])
  async def resume(self, ctx: Context):
    """
    Resumes audio playing
    """
    try:
      await ctx.voice_client.resume() 
      await ctx.send(embed=qb.send_msg('Resume playing'))
    except (TypeError,AttributeError):
      return  

  @commands.command(aliases=['pause, hold'])
  async def stop(self, ctx: Context):
    """
    Pauses audio playing
    """
    try:
      await ctx.voice_client.pause() 
      await ctx.send(embed=qb.send_msg('Stop playing'))
    except (TypeError,AttributeError):
      return        
  
  @commands.command(aliases=['queue', 'q', 'l'])
  async def list(self, ctx: Context):
    """
    Shows the current music queue as an embed in discord
    """
    if self.queue:
      await ctx.send(embed=qb.c_playing(self.currently_playing))
      await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue) > 25 else None)
    else:
      await ctx.send(embed=qb.send_msg('There is no current queue'))  
  
  @commands.command(aliases=['r', 'rm'])
  async def remove(self, ctx: Context , *, message: str):
    """
    Removes song from the queue by index
    """
    try:
      fetch = self.queue.pop(int(message)-1)
      await ctx.send(embed=qb.removed_song(fetch[0]))
    except IndexError: 
      await ctx.send("Index error")
  
  @commands.command(aliases=['clr'])
  async def clear(self, ctx: Context):
    """
    Clears the queue
    """
    self.queue.clear()
    await ctx.send(embed=qb.send_msg('Cleared the queue!'))
  
  @commands.command(aliases=['s'])
  async def skip(self, ctx: Context):
    """
    Skips the current song
    """
    try:
      await ctx.send(embed=qb.send_msg('Skipped!'))
      await ctx.voice_client.stop()
      self.play_after(ctx)
    except (TypeError,AttributeError):
      return 
  
  @commands.command(aliases=['h'])
  async def help(self, ctx: Context):
    """
    Displays a help embed in discord that showcases commands
    """
    await ctx.send(embed=qb.help_list(self.cmnds))  
  
  @commands.command()
  async def loop(self, ctx: Context):
    """
    Toggles loop mode
    """
    self.loop = not self.loop
    await ctx.send(embed=qb.send_msg("Queue loop turned {status}".format(status="on" if self.loop else "off")))
                 
  @commands.command()
  async def shuffle(self, ctx: Context):
    """
    Shuffles the queue
    """   
    await ctx.send(embed=qb.send_msg('Shuffled the queue!'))  
    random.shuffle(self.queue) 
    self.increment = -1 
  
  @commands.command(aliases=['ps'])
  async def playskip(self, ctx: Context, *, message: str):
    """
    Playskips to a specific song in the queue
    """
    try:
      fetch = self.queue.pop(int(message)-1)
      self.queue.insert(0, fetch)
      await ctx.voice_client.stop()
      self.play_after(ctx)
      await ctx.send(embed=qb.send_msg(f"Skipped to {int(message)}!"))
    except (TypeError, AttributeError, IndexError):
      return

  @commands.command()
  async def partist(self, ctx: Context, *, message: str):
    """
    Play song from specific artist chosen by the user
    """
    try: 
      # Intilizie cursor and db         
      cursor, db = db_init()          
      # #Select all the current data in the database and display it         
      cursor.execute(f"SELECT song,link FROM music WHERE song LIKE '%{message}%' ORDER BY rand() LIMIT 10;")         
      data = cursor.fetchall()        
      db.close()

      if data:
        await self.append_data(ctx,data)
        await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)  
      else:
        await ctx.send('**[ERROR 404]** Artist not found')

    except Exception as e:
      await ctx.send('**[ERROR 404]** partist error: ' + e)

  @commands.command()
  async def prandy(self, ctx: Context, message: str = None):
    """
    Play random songs
    """ 
    # Intilizie cursor and db
    cursor, db = db_init()   
    if message:
      # If limit is found
      try:
        cursor.execute(f"select song,link FROM music WHERE uses > 5 AND blacklisted=0 ORDER BY rand() LIMIT {message};")
      except:
        await ctx.send('**[ERROR 404]** Invalid number')   
    else:
      #Select all the current data in the database and display it         
      cursor.execute(f"select song,link FROM music WHERE uses > 5 AND blacklisted=0 ORDER BY rand() LIMIT 5;")         

    data = cursor.fetchall()        
    db.close()
    # Add the music
    await self.append_data(ctx,data)  
    await ctx.send(embed=qb.queue_list(self.queue), view = Qbuttons(self.queue) if len(self.queue)> 25 else None)

  @commands.command(aliases=['B'])
  async def black(self, ctx: Context, *args):
    cursor, db = db_init()
    print(' '.join(args))
    if args:
       song = ' '.join(args)
    elif self.currently_playing:
       song = self.currently_playing
    else:
       await ctx.send(embed=qb.send_msg(f"Nothing is playing and no argument!"))
       return

  
    cursor.execute(f"SELECT song FROM music WHERE song='{song}';")
    exists = cursor.fetchall()
    if exists:
      cursor.execute(f"UPDATE music SET blacklisted=1 WHERE song='{song}';")
      db.commit()
      await ctx.send(embed=qb.send_msg(f"Blacklisted {song}!"))
    else:
      await ctx.send(embed=qb.send_msg(f"{song} doesn't exist in The Database"))
    db.close()



  @commands.command(aliases=['UB'])
  async def unblack(self, ctx: Context, *args):
    song = ' '.join(args)
    cursor, db = db_init()
    cursor.execute(f"SELECT song FROM music WHERE song='{song}';")
    exists = cursor.fetchall()
    if exists:
      cursor.execute(f"UPDATE music SET blacklisted=0 WHERE song='{song}';")
      db.commit()
      await ctx.send(embed=qb.send_msg(f"Removed {song} from Blacklist"))
    else:
      await ctx.send(embed=qb.send_msg(f"{song} doesn't exist in The Database"))
    db.close()


  @commands.command(aliases=['BL'])
  async def blacklist(self, ctx: Context):
    cursor, db = db_init()
    cursor.execute(f"select song FROM music WHERE blacklisted=1 ORDER BY song;")
    data = cursor.fetchall()
    db.close()
    await ctx.send(embed=qb.queue_list(data, title="BlackList:"), view = Qbuttons(data) if len(data)> 25 else None)

