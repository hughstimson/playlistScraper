"""
playlistScraper

Hugh Stimson April 2012
http://hughstimson.org/2012/04/16/data-mining-my-radio-playlists/

Opens a radio podcast page, scans for episodes and their linked-to WCBN playlist pages,
extracts the tracks with their title/artist/album/label/playtime and episode data,
and dumps it all out into a .csv table.

Currently only works with the very specific HTML layout of the DJ Hugonaut podcast,
and the particular HTML layout of the WCBN auto-generated playlist pages.
So it's not very useful if that's not what you're trying to scan.
"""

# couldn't figure out how to install bs4 to anything but python26, so have to use that version for now
from bs4 import BeautifulSoup as bs
import urllib2

def main():

    rootUrl = 'http://hughstimson.org/projects/djhugo/'

    # open a link to the podcast page and read in the raw html
    opener = urllib2.build_opener()
    url_opener = opener.open(rootUrl)
    rootHtml = url_opener.read()

    # uncomment for testing:
    # rootHtml = open('djhugo_crop.html', 'r')

    # parse the raw html into a Beautiful Soup object
    soup = bs(rootHtml)

    tracks = getTracksByEpisode(soup)

    outputTracks(tracks)

    print 'All done.'

def getTracksByEpisode(soup):

    tracks = []

    # find all the per-episode divs in the soup object, based on their CSS class
    episodeDivs = soup.find_all('div', {'class' : 'entry radio'})

    for div in episodeDivs:

        hasPlaylist = False

        # get a list of every link in the episode div
        links = div.find_all('a')

        for link in links:

            u = link.get('href')

            # if there is a WCBN playlist page linked to in this episode div,
            # then it's for a real episode with tracks and worth scanning
            if 'http://www.wcbn.org/ryan-playlist/searchplaylist.php' in u:
                hasPlaylist = True
                break

        if hasPlaylist:

            for link in links:

                u = link.get('href')
                t = link.get('title')
                s = link.text

                showLinksList = []

                # using the presence of a 'title' attribute with the 'Permanent Link to' suffix
                # as a key to indicate that this link is the title of the episode
                # could check if the link's parent tags are <h2></h2> for the same purpose
                if t and 'Permanent Link to' in t:
                    # if it is the episode name, store the name and permalink
                    episodeUrl = u.encode('ascii', 'ignore')
                    episodeName = s.encode('ascii', 'ignore')

                # or if it looks like this is the link to the playlist, store that info
                elif 'http://www.wcbn.org/ryan-playlist/searchplaylist.php' in u:
                    playlistUrl = u.encode('ascii', 'ignore')

                # or if it looks like this is the link to the podcast audio mp3, store that info
                elif 'http://hughstimson.org' in u and '.mp3' in u:
                    mp3Url = u.encode('ascii', 'ignore')

                # otherwise, store it as an interesting link from the show (unless it's the adobe download warning)
                elif 'www.adobe.com/shockwave/download' not in u:
                    showLinksList.append(u.encode('ascii', 'ignore'))

            # assemble the list of show links (if any) into a space-seperated list to fit into a single column
            showLinks = ''
            for link in showLinksList:
                showLinks += (link + ' ')

            # build the episode post date from the permalink structure
            t = episodeUrl.split('/')
            y = t[3]
            m = t[4]
            d = t[5]
            postDate = '{0}-{1}-{2}'.format(y,m,d)

            print 'scanning {0} from {1}'.format(episodeName,postDate)

            # open a connection to the WCBN-generated playlist page
            # get the html from it, and parse it into a Beautiful Soup object
            opener = urllib2.build_opener()
            url_opener = opener.open(playlistUrl)
            html = url_opener.read()
            soup = bs(html)

            # find the form field showing the 'played from' time/date for the episode, and store it's value
            p = soup.find('input', {'name' : 'playedfrom'})
            playedFrom = p.get('value').encode('ascii', 'ignore')

            # likewise get the 'played to' value
            p = soup.find('input', {'name' : 'playedto'})
            playedTo = p.get('value').encode('ascii', 'ignore')

            # find the main table containing the playlist data, based on it's CSS id
            table = soup.find( 'table', {'id':'playlist'})

            # find all the table rows
            trs = table.findAll('tr')

            # using the enumerate function to loop through the table rows
            # so I can make choices based on the order of the row being scanned
            for pos, tr in enumerate(trs):

                # skip the headers
                if pos == 0:
                    pass

                else:

                    # break the row up into data cells, and loop through them
                    tds = tr.findAll('td', )

                    # first row has full-height showname and datetime trs
                    if pos == 1:
                        # get the track-specific values from the data cells based on their order
                        # encode converts to ascii and leaves out anything it can't hands, strip takes out whitespace, replace replaces csv-breaking commas with spaces
                        playtime = tds[3].contents[0].encode('ascii', 'ignore').strip()
                        artist = tds[4].contents[0].encode('ascii', 'ignore').strip()
                        title = tds[5].contents[0].encode('ascii', 'ignore').strip()
                        album = tds[6].contents[0].encode('ascii', 'ignore').strip()
                        label = tds[7].contents[0].encode('ascii', 'ignore').strip()

                    # after the first row use the same technique but don't have to skip the first two cells
                    else:
                        playtime = tds[0].contents[0].encode('ascii', 'ignore').strip()
                        artist = tds[1].contents[0].encode('ascii', 'ignore').strip().replace(',', ' ')
                        title = tds[2].contents[0].encode('ascii', 'ignore').strip().replace(',', ' ')
                        album = tds[3].contents[0].encode('ascii', 'ignore').strip().replace(',', ' ')
                        label = tds[4].contents[0].encode('ascii', 'ignore').strip().replace(',', ' ')

                    # either way, add quotes to prevent commas from breaking strings across the .csv and store the data
                    track = { 'playtime'    : '\"' + playtime + '\"',
                              'artist'      : '\"' + artist + '\"',
                              'title'       : '\"' + title + '\"',
                              'album'       : '\"' + album + '\"',
                              'label'       : '\"' + label + '\"',
                              'episodeName' : '\"' + episodeName + '\"',
                              'episodeUrl'  : '\"' + episodeUrl + '\"',
                              'postDate'    : '\"' + postDate + '\"',
                              'playlistUrl' : '\"' + playlistUrl + '\"',
                              'playedFrom'  : '\"' + playedFrom + '\"',
                              'playedTo'    : '\"' + playedTo + '\"',
                              'mp3Url'      : '\"' + mp3Url + '\"',
                              'showLinks'   : '\"' + showLinks + '\"' }
                    tracks.append(track)

        else:
            # if there was no link to a WCBN-generated playlist page
            # get enough data from the episode div to print a warning, and otherwise skip it
            for link in links:

                a = link.get('title')
                b = link.text
                c = link.get('href')

                if a and 'Permanent Link to' in a:
                    episodeName = b.encode('ascii', 'ignore')
                    episodeUrl = c.encode('ascii', 'ignore')

                    t = episodeUrl.split('/')
                    y = t[3]
                    m = t[4]
                    d = t[5]
                    postDate = '{0}-{1}-{2}'.format(y,m,d)

            print 'skipping {0} - {1}: no podcast found'.format(episodeName, postDate)

    return tracks

def outputTracks(tracks):

    # open a new file in the working directory
    file = open('tracks.csv', 'w')

    print '\nHere we go with the tracks:\n'

    # write out the column headers
    headers = 'title,artist,album,label,playtime,episodeName,postDate,episodeUrl,episodeStart,episodeEnd,playlistUrl,mp3Url,showLinks,\n'
    file.write(headers)
    print headers

    # loop through the list of tracks, writing the data for each one
    for track in tracks:

        # print out the data
        # todo surround all values with double quotes to prevent commas in the data breaking single values into multiple rows
        line = '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},\n'.format(
            track['title'],
            track['artist'],
            track['album'],
            track['label'],
            track['playtime'],
            track['episodeName'],
            track['postDate'],
            track['episodeUrl'],
            track['playedFrom'],
            track['playedTo'],
            track['playlistUrl'],
            track['mp3Url'],
            track['showLinks'])
        print line
        file.write(line)

    # close the file
    file.close()

if __name__ == "__main__":
    main()