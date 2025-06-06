import aiohttp
from html.parser import HTMLParser
from urllib.parse import quote_plus


class TitleParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.title = ''

  def handle_starttag(self, tag, attributes):
    if tag == 'title':
      self.recording = 1

  def handle_endtag(self, tag):
    if tag == 'title' and self.recording:
      self.recording -= 1

  def handle_data(self, data):
    if self.recording:
     self.title = data[:-10]

class LinkParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.link = ''

  def handle_data(self, data):
    if data.find('watch?v=') != -1:
      self.link = data[data.find('watch?v='):data.find('watch?v=') + 19]


async def search(query: str):
  """
  Takes a query and returns a title and link of the first YouTube search response
  :params: query - str
  """

  #Add rule to check for audio
  query = query + ' Audio'
  #encode to URL safe 
  query = quote_plus(query)

  #Fetch the HTML of the search page
  url = f"https://www.youtube.com/results?search_query={query}"
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
      html = await resp.text()

    #Parse it for the first suggestion link
    parser = LinkParser()
    parser.feed(html)
    link = f"https://www.youtube.com/{parser.link}"

    #Parse the suggestion link for the title
    async with session.get(link) as resp:
      video_html = await resp.text()
    parser = TitleParser()
    parser.feed(video_html)
    title = parser.title

  return[title, link]

if __name__ == "__main__":
    # pass
    # Test
    while True:
        query = input("Type video name: ")
        print(search(query))
    
