import requests
from html.parser import HTMLParser


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
      self.title = data

class LinkParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.link = ''

  def handle_data(self, data):
    if data.find('watch?v=') != -1:
      self.link = data[data.find('watch?v='):data.find('watch?v=') + 19]


def search(query):

  #Fetch the HTML of the search page
  url = f"https://www.youtube.com/results?search_query={query}"
  response = requests.get(url)

  #Parse it for the first suggestion link
  parser = LinkParser()
  parser.feed(response.text)
  link = f"https://www.youtube.com/{parser.link}"

  #Prase the suggestion link for the title
  response = requests.get(link)
  parser = TitleParser()
  parser.feed(response.text)
  title = parser.title

  return[link, title]

if __name__ == "__main__":
    # pass
    # Test
    while True:
        query = input("Type video name: ")
        print(search(query))
    