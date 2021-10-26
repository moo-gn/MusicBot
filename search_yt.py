import requests

def search(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    r = requests.get(url)
    # Parse response
    for idx, chr in enumerate(r.text):
        if chr == "?":
            if r.text[idx+1] == "v":
              link = f"https://www.youtube.com/watch{r.text[idx:idx+14]}"
              response = requests.get(link)
              txt = response.text.split()
              title = []
              for idx, word in enumerate(txt):
                if word == 'name="title"':
                  i = 1
                  word = txt[idx + i]
                  while word != 'name="description"':
                    title.append(word)
                    i += 1
                    word = txt[idx + i]
                  break  

              title = " ".join(title)
              title = title.strip('content="')
              title = title.strip('"><meta') 
              return[link, title]

    r = requests.get(url)

    # Parse response
    for idx, chr in enumerate(r.text):
        if chr == "?":
            if r.text[idx+1] == "v":
                return [f"https://www.youtube.com/watch{r.text[idx:idx+14]}", "video_title"]

if __name__ == "__main__":
    # pass
    # Test
    while True:
        query = input("Type video name: ")
        print(search(query))
    