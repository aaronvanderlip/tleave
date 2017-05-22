from BeautifulSoup import BeautifulSoup
import urllib2


def getSchedule(route='NBRYROCK', direction='O', timing='W'):
    """returns a mapping of the commuter rail schedule"""
    url = 'http://mbta.com/schedules_and_maps/rail/lines/?route=%s&direction=%s&timing=%s' % (route, direction, timing)
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html)
    try:
        links = soup.table
        return stations(links)
    except AttributeError:
        return None


def stations(links):
    stationtimes = {}

    #first we find the row with the train numbers
    train_number_row = links.find('tr')
    #build a list of those train numbers, removing any elements in the row that are empty
    train_number_cols = train_number_row.findAll('td')
    train_numbers = [elem.contents[0] for elem in train_number_cols if elem.first() is not None]
    #remove the row so further processing can continue
    train_number_row.extract()
    links = links.findAll('tr')
    stationorder = 0
    for row in links:
        stationlist = row.findAll('u')
        try:
            station = stationlist[0].renderContents()
        # Set the train number using stationorder
        except IndexError:
            station = ''
        if len(stationlist):
                times = cleanTimeTables(row, train_numbers)
                stationtimes.setdefault(station, (times, stationorder))
        stationorder += 1
    return stationtimes


def cleanTimeTables(row, train_numbers):
    cleantimes = []
    row = row.findAll('td')

    # Assume that we are at the 0 column for appending train numbers as they are
    # at the head of each column
    col_num = 0
    # Inspect all colums in row for time information
    for time in row:
        tt = time.renderContents()
        if tt != '&nbsp;':
            tt = tt.replace('<span>F</span>','')
            tt = tt.replace('<span class="flagstop">VIA</span>','')
            tt = tt.replace('<span class="flagstop">LOW</span>','')
            train = {'train_num': train_numbers[col_num], 'time': tt}
            cleantimes.append(train)
        if tt == '&nbsp;':
            train = {'train_num': train_numbers[col_num], 'time': 'NONE'}
            cleantimes.append(train)
        col_num += 1
    return cleantimes


def prettyPrint(route='NBRYROCK',direction='O'):
    stationtimes = getSchedule(route, direction)
    for station, times in stationtimes.items():
        print '\n' + station
        print '   '.join([time for time in times])
