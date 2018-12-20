#!/opt/local/bin/python
import urllib.request
from urllib.request import FancyURLopener
from bs4 import BeautifulSoup
import pdb

outdirpat = '/Users/yetian/chess/uscf/top100/{}'
class MyOpener(FancyURLopener):
    version = 'My new User-Agent'   # Set this to a string you want for your user agent

myopener = MyOpener()

def bspage(url):
    ''' assuming url is correctly encoded for params'''
    print(url)
    try:
        ## html = urllib.request.urlopen(url)
        html = myopener.open(url)
        soup = BeautifulSoup(html, 'html.parser')
        #print(soup.prettify())
        return soup
    except:
        print('failed to query url {}'.format(url))
        raise

def query_mon(mon, age, link):
    ''' http://www.uschess.org/component/option,com_top_players/Itemid,458?op=list&month={}&f={}".format(mon, age) '''
    ## pdb.set_trace()
    ps = 1+link.find('?op=')
    baseurl = 'http://www.uschess.org{}'.format(link[:ps])
    qurl = '{}{}'.format(baseurl, link[ps:])
    soup = bspage(qurl)
    if soup is None:  return 
    table = soup.find_all("div", class_="top_players")
    rows = table[0].find_all('tr')
    if rows:
        with open(outdirpat.format('{}_{}'.format(mon, age)), 'w') as outfile:
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                outfile.write('\t'.join([ele for ele in cols]))
                outfile.write('\n')

def agelinks_for_month(mon, monlink):
    ''' 'http://www.uschess.org/component/option,com_top_players/Itemid,900/' '''
    mp = bspage(monlink)
    lis = mp.find_all('li')
    for li in lis:
        a = li.find('a','')
        if a and 'com_top_players' in a.attrs['href']:
            url = a.attrs['href']
            query_mon(mon, a.text, url)

def main():
    tp = bspage('http://www.uschess.org/component/option,com_top_players/Itemid,371?op=list&month=0804&f=8&h=Top%20Age%208')
    months = tp.find_all('a', 'sublevel-topplayers')
    for m in months:
        print(m.text, m.attrs['href'])
        agelinks_for_month(m.text, m.attrs['href'])

main()
#query_mon('test', 'test', '/component/option,com_top_players/Itemid,915?op=list&month=1811&f=usa&l=R:Top Women.')

