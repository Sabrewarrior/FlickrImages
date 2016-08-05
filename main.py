from flickr.QueryEngine.query import fetchMetadata
from flickr.DownloadEngine.download import downloadphotos

flickr_APIKey = u'APIKEY'  # API key
flickr_Secret = u'SECRET'                  # shared "secret"

out_folder = ''
download_folder = ''
offset = 1

fetchMetadata(out_folder, flickr_APIKey, flickr_Secret, startingQuery= 1, pause=.2)


downloadphotos(out_folder, download_folder, numComments = 13)