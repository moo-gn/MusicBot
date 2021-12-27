from discord.ui.select import S
import yt_dlp
if __name__ == "__main__":
    YDL_OPTIONS = {'format':'bestaudio', 'playlistrandom': True, 'quiet' : False}
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info('https://www.youtube.com/watch?v=uCDE-S1AjuQ', download=False)
          for format in info['formats']:
              if 'url' in format:
                  s = format['url'].lstrip('https://')
                  if s[0] == 'r':
                      url2 = format['url']
                      break
          print(url2)
