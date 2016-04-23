import eyed3
import json
import os
import shutil
import time
import urllib2

# Place your API Key here
# This can be found at https://developers.soundcloud.com
API_KEY = '?client_id=YOUR_API_KEY_HERE'
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
                if favourite['streamable']:
                    song = dict()
                    song['id'] = favourite['id']
                    song['title'] = favourite['title']
                    song['artist'] = favourite['user']['username']
                    song['artwork_url'] = favourite['artwork_url']
                    song['stream_url'] = favourite['stream_url'] + API_KEY
                    song['permalink_url'] = favourite['permalink_url']
                    songs.append(song)
                else:
                    # Song can't be streamed so we can't download
                    # it this way.
                    FAILED.append(favourite['permalink_url'])

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
        return dict()

def download(url, filename):
    response = urllib2.urlopen(url)
    fh = open(filename, 'wb')

    # Track progress
    meta = response.info()
    file_size = int(meta.getheaders("Content-Length")[0])
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
    count = 1
    for song in songs:
        print('[%s/%s]' % (count, len(songs)))
        if song['id'] in CACHE:
            print('Skipping song %s because already downloaded.' % song['title'])
            print('If you think is is a mistake, remove the number')
            print('%s from the cache file.\n' % song['id'])
            count += 1
            continue

        print('Processing song %s by %s\n' %(song['title'], song['artist']))
        mp3 = TMP_FOLDER + str(song['id']) + '.mp3'
        artwork = TMP_FOLDER + str(song['id']) + '.jpg'

        download(song['stream_url'], mp3)
        download(song['artwork_url'], artwork)
        print('\tUpdating metadata...')
        audio_fh = eyed3.load(mp3)
        audio_fh.initTag()
        audio_fh.tag.artist = song['artist']
        audio_fh.tag.title = song['title']
        audio_fh.tag.track_num = song['id']
        audio_fh.tag.images.set(3, open(artwork).read(), 'image/jpeg')
        audio_fh.tag.save()

        print('\tMoving downloaded song...\n')
        os.rename(mp3, FOLDER + song['title'] + '.mp3')
        CACHE.append(song['id'])

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

def main():
    print('Please your soundcloud username: ')
    username = raw_input()

    if is_valid_user(username):
        # Where to download
        print('\nDo you want us to add it to iTunes automatically? [yes/no]')
        print('If no, songs will be placed in your downloads folder.')
        FOLDER = raw_input()
        if FOLDER == 'yes':
            FOLDER = '~/Music/iTunes Media/Automatically Add to iTunes/'
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