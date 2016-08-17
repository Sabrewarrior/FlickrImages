import time
#originally written by Tamara Berg, extended by James Hays

#download images listed in every text file in this directory
# search_result_dir = '/home/ujash/flickr_scripts/search_results/'
search_result_dir = '/home/ujash/images_flickr/3/'
#directory where you want to download the images
output_dir = ['/home/ujash/images_filckr/3/downloads']
#the algorithm will create subdirs and subsubdirs in the above dir.

#with the number of images we're expecting we will need two levels of
#subdirectories.  The first level will be the tag, of which there will be
#roughly 100, then the second level will be subdirs of 1000 images.  The
#images will be named such that they can be traced back to their flickr
#source.

##############################################################################

###########################################################
import fnmatch
import requests
import os
import urllib2
import cStringIO
from PIL import Image, ImageChops


def url2imageArray(urlReq, timeout = 10, timeoutDelta = 5, maxtries = 3):
    imageArray = None
    while maxtries > 0:
        try:
            stream = urllib2.urlopen(urlReq, timeout=10)
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
def normalizeArray(imageArray, resizeDims = (224,224), RGBtoBW = False):
    dims = imageArray.size
    normArray = None
    landscape = "True"

    if imageArray.mode != 'RGB':
        return normArray, landscape
    elif RGBtoBW:
        #TODO: Make image RGB
        pass

    if dims[1] > dims[0]:
        landscape = "False"

    # Cannot normalize if resizeDims are larger than the image
    if (dims[0] >= resizeDims[0]) and (dims[1] >= resizeDims[1]):
        normArray = imageArray.resize(resizeDims, Image.ANTIALIAS)

    return normArray, landscape

def removeFrame(imgArray):
    bg = Image.new(imgArray.mode, imgArray.size, imgArray.getpixel((0, 0)))
    diff = ImageChops.difference(imgArray, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return imgArray.crop(bbox)
    else:
        return imgArray

def downloadphotos(search_result_dir, output_dir, numComments = 13, resizeDims= (277,277), BW = False):
    print 'Reading image metadata from ' + search_result_dir

    search_results = []
    for root, dirnames, filenames in os.walk(search_result_dir):
        for filename in fnmatch.filter(filenames, '*.txt'):
            search_results.append([root, filename])

    num_results = len(search_results)
    print 'Downloading the images from ' + str(num_results) + ' search results'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    for i in range (0, len(search_results)):
        current_file = search_results[i]
        current_filename_fh = current_file[1][:-4] #cutting off .txt extension


        #The presence of an output directory is a lock
        if not os.path.exists(os.path.join(output_dir, current_filename_fh)):
            #lock the file by creating the output directory
            curImgDir = os.path.join(output_dir, current_filename_fh)
            curMetaDir = os.path.join(output_dir, current_filename_fh + 'Meta')
            os.mkdir(curImgDir)
            os.mkdir(curMetaDir)
            os.mkdir(os.path.join(curImgDir, 'L'))
            os.mkdir(os.path.join(curMetaDir, 'L'))
            os.mkdir(os.path.join(curImgDir, 'P'))
            os.mkdir(os.path.join(curMetaDir, 'P'))
            # file where the metadata is located
            fid = open(os.path.join(current_file[0], current_file[1]), 'r')
            print '   Reading search results in file ' + current_file[1]

            count=0

            # downloads images, 1000 images per directory
            while True:
                line = fid.readline()
                if not line:
                    break

                #example entry
                # photo: 3654964457 59eb0dc7b6 3642 4
                # originalsecret: 46782aeaeb
                # originalformat: jpg
                # owner: 34586311@N05
                # title: Pumpkins in the Rogue River Valley, Oregon
                # o_height: 1949
                # o_width: 2410
                # datetaken: 2009-07-15 16:17:42
                # dateupload: 1247670509
                # tags: field workers farm harvest flickrhome takeatrip osuarchives shastasunsetroutes dc:identifier = archives3010
                # license: 7
                # views: 5511
                # interestingness: 34 out of 189

                if line.startswith('photo:'):
                    line = line.rstrip().split()
                    id = line[1]
                    secret = line[2]
                    server = line[3]
                    farm = line[4]

                    line = fid.readline().rstrip() #original_secret
                    origSecret = line.split()[-1]

                    line = fid.readline().rstrip() #original_format
                    origFormat = line.split()[-1]

                    line = fid.readline().rstrip()
                    owner = line.split()[-1]





                    # Add the rest of the attributes
                    comment_field = 'id: ' + id + '\n' + 'secret: ' + secret + '\n' + \
                                    'server: ' + server + '\n' + \
                                    'farm: ' + farm + '\n' + \
                                    'origSecret: ' + origSecret + '\n' + \
                                    'origFormat: ' + origFormat + '\n' + \
                                    'owner: ' + owner

                    while True:
                        line = fid.readline().rstrip()
                        if not line:
                            break
                        else:
                            comment_field += '\n' + line

                    #dimension = 1024 pixels (but there are bugs).
                    urlReq = 'https://farm' + farm + '.staticflickr.com/' + server +'/' + id +'_'+ secret +'_b.jpg'

                    #download the file to a temporary, local location
                    #before saving it in the full path in order to minimize network
                    #traffic using the /tmp/ space on any machine.

                    #we want the file name to identify the image still.  not just be numbered.
                    #use the -O [output file name] option
                    #-t specifies number of retries
                    #-T specifies all timeouts, in seconds.  if it times out does it retry?
                    imgArr = url2imageArray(urlReq, timeout=10, timeoutDelta=5, maxtries=2)

                    #Check if download worked, otherwise skip this image
                    if not imgArr:
                        #TODO: Try original image if current size doesn't work.
                        continue
                    imgArr = removeFrame(imgArr)

                    # If aspect ratio is too wide or tall don't use the image
                    dims = imgArr.size
                    aspect_ratio = float(dims[0])/dims[1]
                    if aspect_ratio > 1.6 or aspect_ratio < .625:
                        continue

                    #Normalize the size
                    imgArr, landscape = normalizeArray(imgArr, resizeDims = resizeDims)

                    if not imgArr:
                        continue


                    # save all the metadata in the comment field of the file


                    try:
                        if landscape == 'True':
                            text_file = open(os.path.join(curMetaDir, 'L', str(count) + ".txt"), "w")
                            text_file.write(comment_field)
                            text_file.close()
                            imgArr.save(os.path.join(curImgDir, 'L', str(count) + '.jpg'), 'JPEG')
                        else:
                            text_file = open(os.path.join(curMetaDir, 'P', str(count) + ".txt"), "w")
                            text_file.write(comment_field)
                            text_file.close()
                            imgArr.save(os.path.join(curImgDir, 'P', str(count) + '.jpg'), 'JPEG')
                    except:
                        continue
                    count += 1
            fid.close()
            print '    Downloaded: ' + str(count)
