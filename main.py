from flickr.QueryEngine.query import fetchMetadata
from flickr.DownloadEngine.download import downloadphotos

flickr_APIKey = u'7ce34bfaac4515ea8db607438cb967cb'  # API key
flickr_Secret = u'4bb0860deadc5abe'                  # shared "secret"

meta_folder = '/home/ujash/images_flickr/1/'
download_folder = '/home/ujash/images_flickr/down1/'
offset = 1

fetchMetadata(meta_folder, flickr_APIKey, flickr_Secret, startingQuery= 1, pause=.2)


downloadphotos(meta_folder, download_folder, numComments = 13)