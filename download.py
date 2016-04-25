import eyed3
import json
import os
import shutil
import sys
import time
import traceback
import urllib2

# Place your API Key here
# This can be found at https://developers.soundcloud.com
API_KEY = '?client_id=02gUJC0hH2ct1EGOcYXQIzRFU91c72Ea&app_version=1461312517'
RATE_LIMIT = 50
API_HOST = 'https://api.soundcloud.com'

# Download files
CUR_DIR = os.getcwd()
TMP_FOLDER = CUR_DIR + '/TMP_SDL/'
CACHE_FOLDER = CUR_DIR + '/download_cache/'
FOLDER = os.path.expanduser('~/Downloads/')

CACHE = list()
# Songs that failed to download using script
FAILED = list()

# Check to see if the user is a valid
# soundcloud user
def is_valid_user(username):
    endpoint = "%s/users/%s%s" % (API_HOST, username, API_KEY)
    try:
        response = urllib2.urlopen(endpoint)
    except urllib2.HTTPError:
        return False

    return True

# Returns the song information for all the likes of a given user
# Relevant information:
# Array[
#    {
#        id,
#        title,
#        artist,
#        artwork_url,
#        stream_url
#    }, ...
# ]
def get_user_likes(username):
    print('\n=========================================')
    print('Getting likes for user %s' % username)
    print('=========================================')

    global FAILED
    songs = []
    # Pagination offset
    offset = 0

    # Loop until response is empty
    while True:
        endpoint = "%s/users/%s/favorites%s&limit=%d&offset=%d" % (
            API_HOST,
            username,
            API_KEY,
            RATE_LIMIT,
            offset
        )
        response = urllib2.urlopen(endpoint)
        favourites = json.load(response)

        # If no more favourites ie. last page
        if len(favourites) == 0:
            break

        for favourite in favourites:
            if favourite['kind'] == 'track':
                song = dict()
                song['id'] = favourite['id']
                song['title'] = favourite['title']
                song['artist'] = favourite['user']['username']
                song['artwork_url'] = favourite['artwork_url']
                song['permalink_url'] = favourite['permalink_url']
                songs.append(song)

        offset += len(favourites)
        print('Retrieved metadata on %d out of %d songs.' % (
            len(songs),
            offset
        ))

    return songs

def prepare_for_download(username):
    print('\nNOTE: The folder %s will be used temporarily' % TMP_FOLDER)
    print('DO NOT DELETE WHILE PROGRAM IS RUNNING.')

    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER);

    cache_filename = '%s%s_cache.json' % (CACHE_FOLDER, username)
    if os.path.exists(cache_filename):
        return json.loads(open(cache_filename).read())
    else:
        return list()

def download(url, filename):
    response = urllib2.urlopen(url)
    fh = open(filename, 'wb')

    # Track progress
    meta = response.info()
    if len(meta.getheaders("Content-Length")) > 0:
        file_size = int(meta.getheaders("Content-Length")[0])
    else:
        print('\t\033[93mFile size unknown: Guessing 5mb\033[0m')
        file_size = 5242880
    print('\tDownloading: %s Size: %s' % (url, file_size))
    print('\tSaving in file: %s' % filename)

    file_size_dl = 0
    block_size = 8192
    while True:
        buffer = response.read(block_size)
        if not buffer:
            break

        file_size_dl += len(buffer)
        fh.write(buffer)
        status = r"%20d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    # Flush buffer
    print('')
    fh.close()

def download_songs(songs):
    print('\n=========================================')
    print('Ready to Download %s songs...' % len(songs))
    print('Press ctrl + c to quit at anytime')
    print('=========================================')
    time.sleep(2)

    global CACHE
    global FAILED
    count = 1
    for song in songs:
        print('[%s/%s]' % (count, len(songs)))
        if song['id'] in CACHE:
            print('Skipping song %s because already downloaded.' % song['title'])
            print('If you think is is a mistake, remove the number')
            print('\033[92m%s\033[0m from the cache file.\n' % song['id'])
            count += 1
            continue

        print('Processing song %s by %s\n%s\n' %(song['title'], song['artist'], song['permalink_url']))
        try:
            mp3 = TMP_FOLDER + str(song['id']) + '.mp3'
            artwork = TMP_FOLDER + str(song['id']) + '.jpg'

            dl_link = "http://api.soundcloud.com/tracks/%s/stream%s" % (song['id'], API_KEY)
            download(dl_link, mp3)
            print('\tUpdating metadata...')
            audio_fh = eyed3.load(mp3)
            audio_fh.initTag()
            audio_fh.tag.artist = song['artist']
            audio_fh.tag.title = song['title']
            audio_fh.tag.track_num = song['id']
            if song['artwork_url']:
                print('\tUpdating album art...')
                download(song['artwork_url'], artwork)
                audio_fh.tag.images.set(3, open(artwork).read(), 'image/jpeg')
            audio_fh.tag.save()

            dest = FOLDER + song['title'].replace('/', '_') + '.mp3'
            print('\tMoving downloaded song to %s...\n' % dest)
            shutil.move(mp3, dest)
            CACHE.append(song['id'])
        except:
            print('\033[93m')
            traceback.print_exc(file=sys.stdout)
            print('\033[91mFailed to download song. Something went wrong ):')
            print('If youre a dev and you think you can check what happend, I would love you forever')
            print('Else, report to me the exact song and I can try to look into it.\033[0m')
            FAILED.append(song['permalink_url'])
            # Allow user to see error message
            time.sleep(3)
        count += 1

def clean_up(username):
    print('\n=========================================')
    print('Cleaning up...')
    print('=========================================')
    print('Removing temporary files...')
    shutil.rmtree(TMP_FOLDER)

    print('Writing downloads to cache...')
    cache_fh = open('%s%s_cache.json' % (CACHE_FOLDER, username), 'wb')
    json.dump(CACHE, cache_fh)
    cache_fh.close()

    print('\nNote: Failed to download %s songs.' % len(FAILED))
    for song in FAILED:
        print(song)

def main():
    print('Please your soundcloud username: ')
    username = raw_input()

    if is_valid_user(username):
        # Where to download
        print('\nDo you want us to add it to iTunes automatically? [yes/no]')
        print('If no, songs will be placed in your downloads folder.')
        FOLDER = raw_input()
        if FOLDER == 'yes':
            FOLDER = os.path.expanduser('~/Music/iTunes Media/Automatically Add to iTunes/')
        elif FOLDER != 'no':
            print('Please answer with yes/no')
            return -1;

        global CACHE
        CACHE = prepare_for_download(username)
        songs = get_user_likes(username)
        download_songs(songs)
        clean_up(username)
    else:
        print('That is not a valid username. Goodbye.')

if __name__ == "__main__":
    main()
