set("log.file", true)
set("log.level", 3)

# Playlist aus /tracks/*.mp3 — direkt durchreichen, kein Re-Encoding
myplaylist = playlist("/tracks/*.mp3")

# Crossfade mit Fade-In/Fade-Out
myplaylist = crossfade(myplaylist, fade_in=5.0, fade_out=5.0)

# Normalisierung
myplaylist = normalize(myplaylist)

# Direkte MP3-Ausgabe an Icecast ohne Re-Encoding
output.icecast(
  %mp3,
  host="127.0.0.1",
  port=8000,
  password="source_password",
  mount="stream",
  name="KI-DJ Stream",
  genre="Psytrance/Goa/Progressive",
  url="http://100.69.81.38:8000",
  description="KI-DJ Psytrance Stream",
  myplaylist
)
