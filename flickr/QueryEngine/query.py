#!/usr/bin/python

# Image querying script written by Tamara Berg,
# and extended heavily James Hays

# 9/26/2007 added dynamic timeslices to query more efficiently.
# 8/18/2008 added new fields and set maximum time slice.
# 8/19/2008 this is a much simpler function which gets ALL geotagged photos of
# sufficient accuracy.  No queries, no negative constraints.
# divides up the query results into multiple files
# 1/5/2009
# now uses date_taken instead of date_upload to get more diverse blocks of images
# 1/13/2009 - uses the original im2gps keywords, not as negative constraints though

import time, socket
import flickrapi
from datetime import datetime
import os

# startTime default = 01/01/2008. First year of license '7' (using CC0)
# endTime default = 21/05/2016


def fetchMetadata(outfolder, flickrAPIKey, flickrSecret, startTime= 1199163600, endTime = 1463982185,
                  timeskip = 1204800 , startingQuery = 1, queriesFile = None, timeout = 30, pause = 1,
                  desiredPhotoBlock = 500):
    socket.setdefaulttimeout(timeout)  #30 second time out on sockets before they throw
    #an exception.  I've been having trouble with urllib.urlopen hanging in the
    #flickr API.  This will show up as exceptions.IOError.

    #the time out needs to be pretty long, it seems, because the flickr servers can be slow
    #to respond to our big searches.
    total_pics = 0
    if queriesFile is not None:
        print "Reading queries from file " + queriesFile
        query_file_name = queriesFile
    else:
        print "No command line arguments, reading queries from " + 'queries.txt'
        query_file_name = 'place_rec_queries.txt'
        #query_file_name = 'place_rec_queries_fall08.txt'

    ###########################################################################
    # Modify this section to reflect your data and specific search
    ###########################################################################
    # flickr auth information:
    # change these to your flickr api keys and secret
    try:
        query_file = open(query_file_name, 'r')
    except:
        print("Error opening queries file " + queriesFile)
    #aggregate all of the positive and negative queries together.
    pos_queries = []  #an empty list
    neg_queries = ''  #a string
    num_queries = 0

    for line in query_file:
        if line[0] != '#' and len(line) > 2:  #line end character is 2 long?
          #print line[0:len(line)-2]
          if line[0] != '-':
            pos_queries = pos_queries + [line[0:len(line)-2]]
            num_queries += 1
          if line[0] == '-':
            neg_queries = neg_queries + ' ' + line[0:len(line)-2]

    query_file.close()
    print 'positive queries:  '
    print pos_queries
    print 'negative queries:  ' + neg_queries
    print 'num_queries = ' + str(num_queries)

    # make a new FlickrAPI instance
    fapi = flickrapi.FlickrAPI(flickrAPIKey, flickrSecret)

    for current_tag in range(0, num_queries):
        if current_tag < startingQuery-1:
            neg_queries += " -" + pos_queries[current_tag]
            continue

        if not os.path.isdir(outfolder):
            os.mkdir(outfolder)
        if not os.path.isdir(os.path.join(outfolder, str(current_tag+1))):
            os.mkdir(os.path.join(outfolder, str(current_tag+1)))
        out_file = open(os.path.join(outfolder, str(current_tag+1), pos_queries[current_tag]) + '.txt','w')

        #form the query string.
        query_string = pos_queries[current_tag] + neg_queries
        print '\n\nquery_string is ' + query_string
        total_images_queried = 0

        mintime = startTime
        # first year with photos using license='7'
        maxtime = mintime + timeskip
        timeskipTemp = timeskip
        #endTime = time.time()
        #this is the desired number of photos in each block

        print datetime.fromtimestamp(mintime)
        print datetime.fromtimestamp(endTime)
        photosSelected = 0
        while (maxtime < endTime):
            #new approach - adjust maxtime until we get the desired number of images
            #within a block. We'll need to keep upper bounds and lower
            #lower bound is well defined (mintime), but upper bound is not. We can't
            #search all the way from endTime.

            lower_bound = mintime + 900 #lower bound OF the upper time limit. must be at least 15 minutes or zero results
            upper_bound = mintime + timeskipTemp * 20 #upper bound of the upper time limit
            maxtime     = .95 * lower_bound + .05 * upper_bound

            print '\nBinary search on time range upper bound'
            print 'Lower bound is ' + str(datetime.fromtimestamp(lower_bound))
            print 'Upper bound is ' + str(datetime.fromtimestamp(upper_bound))

            keep_going = 10 #search stops after a fixed number of iterations
            prev0 = 0
            while( keep_going > 0 and maxtime < endTime):
                try:
                    rsp = fapi.photos.search(ispublic="1",
                                        media="photos",
                                        per_page="250",
                                        page="1",
                                        text=query_string,
                                        license="7",
                                        extras = "tags, original_format, license, date_taken, date_upload, o_dims, views",
                                        min_upload_date=str(mintime),
                                        max_upload_date=str(maxtime),
                                        format="xmlnode")
                                        ##min_taken_date=str(datetime.fromtimestamp(mintime)),
                                        ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
                #we want to catch these failures somehow and keep going.
                except:
                    maxtime += 10000
                    #There is some kind of url exception this fixes
                    continue
                time.sleep(pause)
                total_images = rsp.photos[0]['total']
                null_test = int(total_images) # want to make sure this won't crash later on for some reason
                null_test = float(total_images)

                print '\nnumimgs: ' + total_images
                print 'mintime: ' + str(mintime) + ' maxtime: ' + str(maxtime) + ' timeskip:  ' + str(maxtime - mintime)
                if (float(total_images) < desiredPhotoBlock*1.4) and (float(total_images) > desiredPhotoBlock*.6):
                    print("close enough")
                    break
                elif( int(total_images) > desiredPhotoBlock ):
                    print 'too many photos in block, reducing maxtime'
                    upper_bound = maxtime
                    maxtime = (lower_bound + maxtime) / 2 # midpoint between current value and lower bound.
                elif ((maxtime - mintime) > 62899200):
                    maxtime = mintime + 62899200
                    break
                    print("no more than 1 year timeskip")
                elif( int(total_images) < desiredPhotoBlock):
                    print 'too few photos in block, increasing maxtime'
                    lower_bound = maxtime
                    maxtime = (upper_bound + maxtime) / 2

                print 'Lower bound is ' + str(datetime.fromtimestamp(lower_bound))
                print 'Upper bound is ' + str(datetime.fromtimestamp(upper_bound))

                if( int(total_images) > 0): #only if we're not in a degenerate case
                    prev0 = 0
                    if (maxtime-mintime  <= 1000): # timeskip is tiny already
                        break
                    keep_going = keep_going - 1
                else:
                    prev0 += 1 # Have a momentum of sorts so we are not stuck doing small updates when the difference is large
                    upper_bound = upper_bound + timeskipTemp* prev0

            #end of while binary search
            print 'finished binary search'

            s = '\nmintime: ' + str(mintime) + ' maxtime: ' + str(maxtime)
            print s
            out_file.write(s + '\n')

            i = getattr(rsp,'photos',None)
            if i:

                s = 'numimgs: ' + total_images
                print s
                out_file.write(s + '\n')

                current_image_num = 1

                num = int(rsp.photos[0]['pages'])
                s =  'total pages: ' + str(num)
                print s
                out_file.write(s + '\n')

                #only visit 16 pages max, to try and avoid the dreaded duplicate bug
                #16 pages = 4000 images, should be duplicate safe.  Most interesting pictures will be taken.

                num_visit_pages = min(16,num)

                s = 'visiting only ' + str(num_visit_pages) + ' pages ( up to ' + str(num_visit_pages * 250) + ' images)'
                print s
                out_file.write(s + '\n')

                total_images_queried = total_images_queried + min((num_visit_pages * 250), int(total_images))

                #print 'stopping before page ' + str(int(math.ceil(num/3) + 1)) + '\n'
                print("Current selected: " + str(total_pics) + "\n Tag "+ pos_queries[current_tag]+" selected: " + str(photosSelected) + '\n')
                pagenum = 1
                while( pagenum <= num_visit_pages ):
                #for pagenum in range(1, num_visit_pages + 1):  #page one is searched twice
                    print '  page number ' + str(pagenum)
                    try:
                        rsp = fapi.photos.search(ispublic="1",
                                            media="photos",
                                            per_page="250",
                                            page=str(pagenum),
                                            sort="interestingness-desc",
                                            text=query_string,
                                            license="7",
                                            extras = "tags, original_format, license, date_taken, date_upload, o_dims, views",
                                            min_upload_date=str(mintime),
                                            max_upload_date=str(maxtime),
                                            format="xmlnode")
                                            ##min_taken_date=str(datetime.fromtimestamp(mintime)),
                                            ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
                    except:
                        print("[Err:001]: Shouldn't be here, maybe page too high? forget the rest of this search")
                        break
                    time.sleep(pause)

                    # and print them
                    k = getattr(rsp,'photos',None)
                    if k:
                        m = getattr(rsp.photos[0],'photo',None)
                        if m:
                            for b in rsp.photos[0].photo:
                                if b!=None:
                                    try:
                                        # Get rid of photos that do not have these attributes
                                        photo_id = 'photo: ' + b['id'] + ' ' + b['secret'] + ' ' + b['server'] + ' '+ b['farm'] + '\n'
                                        owner_str = 'owner: ' + b['owner'] + '\n'
                                        title_str = 'title: ' + b['title'].encode("ascii","replace") + '\n'
                                        date_taken = 'datetaken: ' + b['datetaken'].encode("ascii","replace") + '\n'
                                        date_upload = 'dateupload: ' + b['dateupload'].encode("ascii","replace") + '\n'
                                        tags = 'tags: ' + b['tags'].encode("ascii","replace") + '\n'

                                        license_info = 'license: ' + b['license'].encode("ascii","replace") + '\n'
                                        interestingness = 'interestingness: ' + str(current_image_num) + ' out of ' + str(total_images) + '\n'
                                        views = 'views: ' + b['views'] + '\n'
                                    except:
                                        continue

                                    try:
                                        # Check if photo allows for access to original
                                        origSecret_id = 'originalsecret: ' + b['originalsecret'] + '\n'
                                        origFormat_str = 'originalformat: ' + b['originalformat'] + '\n'
                                        o_height = 'o_height: ' + b['o_height'] + '\n'
                                        o_width = 'o_width: ' + b['o_width'] + '\n'
                                    except:
                                        origSecret_id = 'originalsecret: null\n'
                                        origFormat_str = 'originalformat: null\n'
                                        o_height = 'o_height: 0\n'
                                        o_width = 'o_width: 0\n'



                                    out_file.write(photo_id)
                                    out_file.write(origSecret_id)
                                    out_file.write(origFormat_str)

                                    out_file.write(owner_str)
                                    out_file.write(title_str)

                                    out_file.write(o_height)
                                    out_file.write(o_width)


                                    out_file.write(date_taken)
                                    out_file.write(date_upload)

                                    out_file.write(tags)
                                    out_file.write(license_info)

                                    out_file.write(views)


                                    out_file.write(interestingness)

                                    # 15 lines + 1 blank line per photo
                                    out_file.write('\n')
                                    photosSelected+=1
                                    current_image_num += 1
                    pagenum = pagenum + 1

                timeskipTemp = (maxtime - mintime)/2
                #used for initializing next binary search, reducing maxtime
                #as there are more photos as time increases
                mintime = maxtime
                total_pics += current_image_num-1

        out_file.write('Total images queried: ' + str(total_images_queried) + ', Total images selected: '+ str(photosSelected) + '\n')
        out_file.close

        # Add current tag to the negative query of next search
        neg_queries += " -" + pos_queries[current_tag]

    print(total_pics)