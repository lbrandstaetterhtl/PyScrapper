import os
import Session
import Archive

ses = Session.Session()
# url = "https://suno.com/song/69b1e7c1-5f6f-4aab-a30a-ed5a6cb61a9a"
# html = Suno.get_html(url="https://suno.com/song/69b1e7c1-5f6f-4aab-a30a-ed5a6cb61a9a", session=ses)

# strip = url.replace("https://suno.com/song/", "")
# identifier = strip


# mp3 = Suno.search_media(html=html, identifier=identifier, mediatype=".wav")
# print(mp3)

# out_path = os.path.join("Downloads")
# os.makedirs(out_path, exist_ok=True)

# out_file_mp3 = os.path.join(out_path, f"{identifier}.wav")

# Suno.download_to_file(session=ses, url=mp3, out_file=out_file_mp3)

search_query = input("> ")
docs = Archive.search(searchquery=search_query, session=ses)
print(docs)

