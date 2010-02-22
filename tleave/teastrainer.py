from BeautifulSoup import BeautifulSoup
import urllib2

def getSchedule(route='NBRYROCK', direction='O', timing='W'):
    """returns a mapping of the commuter rail schedule"""
    #need to add timing=W, timing=S, timing=U
    url = 'http://mbta.com/schedules_and_maps/rail/lines/?route=%s&direction=%s&timing=%s' % (route, direction,timing)
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html)
    try:
        links = soup.table.nextSibling
        return stations(links)
    except AttributeError:
        return  None
    
def stations(links):
    stationtimes = {}
    #remove the first row
    removerow = links.find('tr')
    removerow.extract()
    links = links.findAll('tr')
    stationorder = 0
    for row in links:
        stationlist = row.findAll('td', 'hidden')
        try:
             station = stationlist[0].renderContents()
        except IndexError:
             station = ''
        if len(stationlist):
                times = cleanTimeTables(row)
                stationtimes.setdefault(station,(times,stationorder))
        stationorder += 1
    return stationtimes

def cleanTimeTables(row):
    cleantimes =[]
    #remove the station
    remove = row.find('td')
    remove.extract()
    row = row.findAll('td')

    for time in row:
        tt = time.renderContents()
        if tt != '&nbsp;':
            tt = tt.replace('<span>F</span>','')
            tt = tt.replace('<span class="flagstop">VIA</span>','')
            tt = tt.replace('<span class="flagstop">LOW</span>','')
            cleantimes.append(tt)
        if tt == '&nbsp;':
            cleantimes.append('NONE')
    return cleantimes
        
def prettyPrint(route='NBRYROCK',direction='O'):
    stationtimes = getSchedule(route,direction) 
    for station, times in stationtimes.items():
        print '\n' + station
        print '   '.join([time for time in times])

    
