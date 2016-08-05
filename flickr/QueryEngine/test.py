import requests
import urllib2
import cStringIO
from scipy.misc import imshow
from PIL import Image, ImageChops
import numpy
import pyexiv2
import exifread
import os

farm = '4'
server = '3204'
secret = 'bf37d327a0'
idNum = '2978047812'

urlReq = 'https://farm' + farm + '.staticflickr.com/' + server +'/' + idNum +'_'+ secret +'_bs.jpg'
print urlReq
#resp = requests.get(urlReq)
#print resp.headers
#print resp.json()
#print resp.text
try:
    stream = urllib2.urlopen(urlReq,timeout=10)
    print stream.geturl()
    print stream.info()
    print stream.getcode()
except:

    exit()

a = Image.open(cStringIO.StringIO(stream.read()))
def removeFrame(imgArray):
    bg = Image.new(imgArray.mode, imgArray.size, imgArray.getpixel((0, 0)))
    diff = ImageChops.difference(imgArray, bg)
    diff = ImageChops.add(diff, diff, 2.0, -110)
    bbox = diff.getbbox()
    print bbox
    if bbox:
        return imgArray.crop(bbox)
    else:
        return imgArray



def url2imageArray(urlReq, timeout = 10, timeoutDelta = 5, maxtries = 3):
    imageArray = None
    while maxtries > 0:
        try:
            stream = urllib2.urlopen(urlReq, timeout=10)
            print stream.getcode()
            if (stream.geturl() != urlReq or stream.getcode() != 200):
                raise Exception("Incorrect response")
            imageArray = Image.open(cStringIO.StringIO(stream.read()))
            break
        except:
            timeout += timeoutDelta
            maxtries -= 1
    return imageArray

###
### resizeDims = (width, height)
###
def normalizeArray(imageArray, resizeDims = (277,277), RGBtoBW = False):
    dims = imageArray.size
    normArray = None
    landscape = "True"

    if imageArray.mode != 'RGB':
        return normArray, landscape
    elif RGBtoBW:
        #TODO: Make image RGB
        pass

    if dims[0] > dims[1]:
        landscape = "False"

    # Cannot normalize if resizeDims are larger than the image
    if (dims[0] >= resizeDims[0]) and (dims[1] >= resizeDims[1]):
        normArray = imageArray.resize(resizeDims, Image.ANTIALIAS)

    return normArray, landscape


imgArr = url2imageArray(urlReq, timeout=10, timeoutDelta=5, maxtries=2)

# Check if download worked, otherwise skip this image
if not imgArr:
    # TODO: Try original image if current size doesn't work.
    exit()

imgArr = removeFrame(imgArr)

# Normalize the size
imgArr, landscape = normalizeArray(imgArr)

if not imgArr:
    exit()

#imgArr.save("123.jpg",'JPEG')


'''

#import flickrapi
import flickrapi

flickrAPIKey = u'7ce34bfaac4515ea8db607438cb967cb'  # API key
flickrSecret = u'4bb0860deadc5abe'                  # shared "secret"

fapi = flickrapi.FlickrAPI(flickrAPIKey,flickrSecret,format='etree')

query_string="dog"
year = 2000
for i in range(0,17):
    mintime=str(year)+'-01-01'
    print year,
    year=year+1
    maxtime=str(year)+'-01-01'

    xmlName = fapi.photos.search(ispublic="1", media="photos", per_page="250", text="", license='7', min_upload_date=mintime, max_upload_date=maxtime, format='xmlnode')
    print(xmlName.photos[0]['total'])
////////////////////////////////////////////


for x = 0:7
    search_result_dir = strcat(search_result_top, num2str(x), '/');
    fprintf('Reading image metadata from %s\n', search_result_dir);
    search_results = dir(fullfile(search_result_dir, '*.txt'));
    num_results = length(search_results);
    rand('twister', sum(100*clock)); %seed random number generator
    search_results = search_results(randperm(num_results)); %randomizing order
    search_results = [search_results]; %two passes through to make sure
    fprintf(' Downloading the images in %d search results\n',num_results)

    for i = 1:size(search_results,1)
        current_filename = search_results(i).name;
        current_filename_fh = current_filename(1:end-4); %cutting off .txt extension

        fprintf('\n !!! Checking for lock on %s\n', current_filename)

        %The presence of an output directory is a lock
        if ( ~exist([output_dir current_filename_fh], 'file'))

            fprintf(' locking %s\n', current_filename)
            %lock the file by creating the output directory
            cmd = ['mkdir ' output_dir current_filename_fh];
            unix(cmd);

            % file where the metadata is located
            fid = fopen([search_result_dir current_filename],'r');
            fprintf(' Reading search results in file %s\n', current_filename);

            count=0;
            dircount=0;

            % downloads images, 1000 images per directory
            while 1
                line = fgetl(fid);
                if (~ischar(line))
                    break
                end

                %example entry
                % photo: 27642011 8fa8ae33cd 23 4
                % owner: 72399739@N00
                % title: Mexico City - Chapultepec 03
                % originalsecret: null
                % originalformat: null
                % datetaken: 2005-07-21 14:41:58
                % tags: architecture digital landscape mexico mexicocity infrared trips skyview chapultepec
                % license: 0
                % latitude: 19.420934
                % longitude: -99.181416
                % accuracy: 16
                % interestingness: 2 out of 14

                %odd, it seems like original secret is always the same as the
                %standard secret.  And sometimes, if flickr won't give you the
                %original secret, you can still access the original.  So really
                %no point even looking for that.

                if strncmp(line,'photo:',6)

                    if mod(count,1000)==0
                        dircount = dircount + 1;
                        cmd = ['mkdir ' output_dir current_filename_fh '/' sprintf('%.5d', dircount)];
                        unix(cmd);
                    end
                    count=count+1;

                    first_line = line;

                    [t,r] = strtok(line);
                    [id,r] = strtok(r);
                    [secret,r] = strtok(r);
                    [server,r] = strtok(r);
                    [farm, r] = strtok(r);

                    line = fgetl(fid); %owner: line
                    second_line = line;
                    [t,r] = strtok(line);
                    [owner,r] = strtok(r);

                    line = fgetl(fid); %title
                    third_line = line;

                    line = fgetl(fid); %original_secret
                    fourth_line = line;
                    [t, r] = strtok(line);
                    [origSecret, r] = strtok(r);

                    line = fgetl(fid); %original_format
                    fifth_line = line;
                    [t, r] = strtok(line);
                    [origFormat, r] = strtok(r);
'''