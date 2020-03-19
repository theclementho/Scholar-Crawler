"""scholarly.py"""

from __future__ import absolute_import, division, print_function, unicode_literals

from bs4 import BeautifulSoup

import arrow
import bibtexparser
import codecs
import hashlib
import pprint
import random
import re
import requests
import sys
import time
import datetime

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml'
    }
_HOST = 'https://scholar.google.com'
_AUTHSEARCH = '/citations?view_op=search_authors&hl=en&mauthors={0}'
_CITATIONAUTH = '/citations?user={0}&hl=en'
_CITATIONPUB = '/citations?view_op=view_citation&citation_for_view={0}'
_KEYWORDSEARCH = '/citations?view_op=search_authors&hl=en&mauthors=label:{0}'
_LABELSEARCH = '/citations?view_op=search_authors&hl=en&mauthors=label:{0}'
_ORGSEARCH = '/citations?view_op=view_org&hl=en&org={0}'
_PUBSEARCH = '/scholar?q={0}'
_SCHOLARPUB = '/scholar?oi=bibs&hl=en&cites={0}'
_AUTHPROFILE = '/citations?hl=en&user='
_SORTAUTHPROFILEBYYEAR = '&view_op=list_works&sortby=pubdate'
_AUTHALLCOAUTHORS = '/citations?hl=en&user={0}#d=gsc_md_cod&u=%2Fcitations%3Fview_op%3Dlist_colleagues%26hl%3Den%26json%3D%26user%3D{0}%23t%3Dgsc_cod_lc'

_CITATIONAUTHRE = r'user=([\w-]*)'
_ORGAUTHRE = r'org=([0-9]*)'
_CITATIONPUBRE = r'citation_for_view=([\w-]*:[\w-]*)'
_SCHOLARCITERE = r'gs_ocit\(event,\'([\w-]*)\''
_SCHOLARPUBRE = r'cites=([\w-]*)'
_EMAILAUTHORRE = r'Verified email at '
_AUTHPROFILERE = r'(?<=user\=)[a-zA-Z0-9-_]*'

_SESSION = requests.Session()
_PAGESIZE = 100


def use_proxy(http='socks5://127.0.0.1:9050', https='socks5://127.0.0.1:9050'):
    """ Routes scholarly through a proxy (e.g. tor).
        Requires pysocks
        Proxy must be running."""
    _SESSION.proxies ={
            'http': http,
            'https': https
    }


def _handle_captcha(url):
    # TODO: PROBLEMS HERE! NEEDS ATTENTION
    # Get the captcha image
    captcha_url = _HOST + '/sorry/image?id={0}'.format(g_id)
    captcha = _SESSION.get(captcha_url, headers=_HEADERS)
    # Upload to remote host and display to user for human verification
    img_upload = requests.post('http://postimage.org/',
        files={'upload[]': ('scholarly_captcha.jpg', captcha.text)})
    print(img_upload.text)
    img_url_soup = BeautifulSoup(img_upload.text, 'html.parser')
    img_url = img_url_soup.find_all(alt='scholarly_captcha')[0].get('src')
    print('CAPTCHA image URL: {0}'.format(img_url))
    # Need to check Python version for input
    if sys.version[0]=="3":
        g_response = input('Enter CAPTCHA: ')
    else:
        g_response = raw_input('Enter CAPTCHA: ')
    # Once we get a response, follow through and load the new page.
    url_response = _HOST+'/sorry/CaptchaRedirect?continue={0}&id={1}&captcha={2}&submit=Submit'.format(dest_url, g_id, g_response)
    resp_captcha = _SESSION.get(url_response, headers=_HEADERS, cookies=_COOKIES)
    print('Forwarded to {0}'.format(resp_captcha.url))
    return resp_captcha.url


def _get_page(pagerequest):
    """Return the data for a page on scholar.google.com"""
    # Note that we include a sleep to avoid overloading the scholar server
    time.sleep(5+random.uniform(0, 5))
    resp = _SESSION.get(pagerequest, headers=_HEADERS, cookies=_COOKIES)
    if resp.status_code == 200:
        return resp.text
    if resp.status_code == 503:
        # Inelegant way of dealing with the G captcha
        raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))
        # TODO: Need to fix captcha handling
        # dest_url = requests.utils.quote(_SCHOLARHOST+pagerequest)
        # soup = BeautifulSoup(resp.text, 'html.parser')
        # captcha_url = soup.find('img').get('src')
        # resp = _handle_captcha(captcha_url)
        # return _get_page(re.findall(r'https:\/\/(?:.*?)(\/.*)', resp)[0])
    else:
        raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))


def _get_soup(pagerequest):
    """Return the BeautifulSoup for a page on scholar.google.com"""
    html = _get_page(pagerequest)
    html = html.replace(u'\xa0', u' ')
    return BeautifulSoup(html, 'html.parser')


def _search_scholar_soup(soup):
    """Generator that returns Publication objects from the search page"""
    while True:
        for row in soup.find_all('div', 'gs_or'):
            yield Publication(row, 'scholar')
        if soup.find(class_='gs_ico gs_ico_nav_next'):
            url = soup.find(class_='gs_ico gs_ico_nav_next').parent['href']
            soup = _get_soup(_HOST+url)
        else:
            break

def _search_citation_soup(soup):
    """Generator that returns Author objects from the author search page"""
    while True:
        for row in soup.find_all('div', 'gsc_1usr'):
            yield Author(row)
        next_button = soup.find(class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
        if next_button and 'disabled' not in next_button.attrs:
            url = next_button['onclick'][17:-1]
            url = codecs.getdecoder("unicode_escape")(url)[0]
            soup = _get_soup(_HOST+url)
        else:
            break

def _search_authIDs_soup(soup):
    """Generator that returns Author IDs, names, interests from search page"""
    while True:
        for row in soup.find_all('div', 'gsc_1usr'):
            id = re.findall(_CITATIONAUTHRE, row('a')[0]['href'])[0]
            name = row.find('h3', class_=_find_tag_class_name(row, 'h3', 'name')).text
            interests = set([i.text.strip() for i in 
                        row.find_all('a', class_=_find_tag_class_name(row, 'a', 'one_int'))])
            yield id, name, interests
        next_button = soup.find(class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
        if next_button and 'disabled' not in next_button.attrs:
            url = next_button['onclick'][17:-1]
            url = codecs.getdecoder("unicode_escape")(url)[0]
            soup = _get_soup(_HOST+url)
        else:
            break

def _find_tag_class_name(__data, tag, text):
    elements = __data.find_all(tag)
    for element in elements:
        if 'class' in element.attrs and text in element.attrs['class'][0]:
            return element.attrs['class'][0]


class Publication(object):
    """Returns an object for a single publication"""
    def __init__(self, __data, pubtype=None):
        self.bib = dict()
        self.source = pubtype
        if self.source == 'citations':
            self.bib['title'] = __data.find('a', class_='gsc_a_at').text
            self.id_citations = re.findall(_CITATIONPUBRE, __data.find('a', class_='gsc_a_at')['data-href'])[0]
            citedby = __data.find(class_='gsc_a_ac')
            if citedby and not (citedby.text.isspace() or citedby.text == ''):
                self.citedby = int(citedby.text)
            year = __data.find(class_='gsc_a_h')
            if year and year.text and not year.text.isspace() and len(year.text)>0:
                self.bib['year'] = int(year.text)
        elif self.source == 'scholar':
            databox = __data.find('div', class_='gs_ri')
            title = databox.find('h3', class_='gs_rt')
            if title.find('span', class_='gs_ctu'): # A citation
                title.span.extract()
            elif title.find('span', class_='gs_ctc'): # A book or PDF
                title.span.extract()
            self.bib['title'] = title.text.strip()
            if title.find('a'):
                self.bib['url'] = title.find('a')['href']
            authorinfo = databox.find('div', class_='gs_a')
            # self.bib['author'] = ' and '.join([i.strip() for i in authorinfo.text.split(' - ')[0].split(',')])
            self.bib['author'] = set([i.strip() for i in authorinfo.text.split(' - ')[0].split(',')])
            if databox.find('div', class_='gs_rs'):
                self.bib['abstract'] = databox.find('div', class_='gs_rs').text
                if self.bib['abstract'][0:8].lower() == 'abstract':
                    self.bib['abstract'] = self.bib['abstract'][9:].strip()
            lowerlinks = databox.find('div', class_='gs_fl').find_all('a')
            for link in lowerlinks:
                if 'Import into BibTeX' in link.text:
                    self.url_scholarbib = link['href']
                if 'Cited by' in link.text:
                    self.citedby = int(re.findall(r'\d+', link.text)[0])
                    self.id_scholarcitedby = re.findall(_SCHOLARPUBRE, link['href'])[0]
            if __data.find('div', class_='gs_ggs gs_fl'):
                self.bib['eprint'] = __data.find('div', class_='gs_ggs gs_fl').a['href']
        self._filled = False

    def fill(self):
        """Populate the Publication with information from its profile"""
        if self.source == 'citations':
            url = _CITATIONPUB.format(self.id_citations)
            soup = _get_soup(_HOST+url)
            self.bib['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                self.bib['url'] = soup.find('a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text
                val = item.find(class_='gsc_vcd_value')
                if key == 'Authors' or key == "Inventors":
                    # self.bib['author'] = ' and '.join([i.strip() for i in val.text.split(',')])
                    self.bib['author'] = set([i.strip() for i in val.text.split(',')])
                elif key == 'Journal':
                    self.bib['journal'] = val.text
                elif key == 'Volume':
                    self.bib['volume'] = val.text
                elif key == 'Issue':
                    self.bib['number'] = val.text
                elif key == 'Pages':
                    self.bib['pages'] = val.text
                elif key == 'Publisher':
                    self.bib['publisher'] = val.text
                elif key == 'Publication date':
                    year = re.findall(r'20[0-9][0-9]', val.text)[0]
                    if self.bib['year'] == None:
                        print("Error in regex looking for the year!")
                    else:
                        year = int(year)
                        self.bib['year'] = year
                        # self.bib['year'] = arrow.get(val.text).year
                elif key == 'Description':
                    if val.text[0:8].lower() == 'abstract':
                        val = val.text[9:].strip()
                    self.bib['abstract'] = val
                elif key == 'Total citations':
                    self.id_scholarcitedby = re.findall(_SCHOLARPUBRE, val.a['href'])[0]

            # number of citation per year
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            self.cites_per_year = dict(zip(years, cites))

            if soup.find('div', class_='gsc_vcd_title_ggi'):
                self.bib['eprint'] = soup.find('div', class_='gsc_vcd_title_ggi').a['href']
            self._filled = True
        elif self.source == 'scholar':
            bibtex = _get_page(self.url_scholarbib)
            self.bib.update(bibtexparser.loads(bibtex).entries[0])
            self._filled = True
        return self

    def get_citedby(self):
        """Searches GScholar for other articles that cite this Publication and
        returns a Publication generator.
        """
        if not hasattr(self, 'id_scholarcitedby'):
            self.fill()
        if hasattr(self, 'id_scholarcitedby'):
            url = _SCHOLARPUB.format(requests.utils.quote(self.id_scholarcitedby))
            soup = _get_soup(_HOST+url)
            return _search_scholar_soup(soup)
        else:
            return []

    def __str__(self):
        return pprint.pformat(self.__dict__)

class AuthorProfile(object):
    """Returns an AuthorProfile object containing all CoAuthors of an Author"""
    def __init__(self, __data, id):
        reqURL = __data.find('link', {'rel': 'canonical'})['href']
        selfID = re.findall(_AUTHPROFILERE, reqURL)[0]
        self.id = selfID
        self.name = __data.find('div', id='gsc_prf_in').text
        affiliation = __data.find('div', class_='gsc_prf_il')
        if affiliation:
            self.affiliation = affiliation.text
        organization = __data.find_all('a', class_='gsc_prf_ila')
        if organization:
            for htmlTag in organization:
                if re.findall(_ORGAUTHRE, htmlTag['href']):
                    self.organization = re.findall(_ORGAUTHRE, htmlTag['href'])[0]
                    break
        self.interests = set([i.text.strip() for i in __data.find_all('a', class_='gsc_prf_inta')])
        self.coauthors = {}
        coauthor_section = __data.find('ul', class_='gsc_rsb_a')
        if coauthor_section:
            for row in coauthor_section.find_all('li'):
                id = row.find("span", id=lambda x: x and x.startswith('gsc_rsb-'))['id'][8:]
                if (re.findall(r'^[a-zA-Z0-9-_]*', id)[0] != id):
                    print ("Weird character. Change regex for ID! ID in question: ", id)
                name = row.find(tabindex="-1").text
                affiliation = row.find(class_="gsc_rsb_a_ext").text
                self.coauthors[id] = ({
                    'id': id,
                    'name': name,
                    'affiliation': affiliation
                })

        self.publications = list()
        pubstart = 0
        url_citations = _CITATIONAUTH.format(selfID)
        within_5_years = True
        this_year = datetime.datetime.now().year
        while within_5_years:
            for row in __data.find_all('tr', class_='gsc_a_tr'):
                new_pub = Publication(row, 'citations')
                if this_year - new_pub.bib['year'] > 5:
                    within_5_years = False
                    break
                else:
                    new_pub.fill()
                    # print("Adding publication: {0}".format(new_pub.bib['title']))
                    # Putting relevant data into return object
                    pub_info = {}
                    if (new_pub.bib['title']):
                        pub_info['title'] = new_pub.bib['title']
                    if (new_pub.bib['author']):
                        new_pub.bib['author'].discard(self.name)
                        pub_info['author'] = new_pub.bib['author']
                        # print("Authors: {0}".format(pub_info['author']))
                    if (new_pub.bib['year']):
                        pub_info['year'] = new_pub.bib['year']
                    self.publications.append(pub_info)

            if 'disabled' not in __data.find('button', id='gsc_bpf_more').attrs and within_5_years:
                pubstart += _PAGESIZE
                url = '{0}&cstart={1}&pagesize={2}'.format(url_citations, pubstart, _PAGESIZE)
                __data = _get_soup(_HOST+url+_SORTAUTHPROFILEBYYEAR)
            else:
                break

class Author(object):
    """Returns an object for a single author"""
    def __init__(self, __data):
        if isinstance(__data, str):
            self.id = __data
        else:
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
            self.url_picture = _HOST+'/citations?view_op=medium_photo&user={}'.format(self.id)
            self.name = __data.find('h3', class_=_find_tag_class_name(__data, 'h3', 'name')).text
            affiliation = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'aff'))
            if affiliation:
                self.affiliation = affiliation.text
            email = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'eml'))
            if email:
                self.email = re.sub(_EMAILAUTHORRE, r'@', email.text)
            self.interests = [i.text.strip() for i in
                           __data.find_all('a', class_=_find_tag_class_name(__data, 'a', 'one_int'))]
            citedby = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'cby'))
            if citedby and citedby.text != '':
                self.citedby = int(citedby.text[9:])
        self._filled = False

    def fill(self):
        """Populate the Author with information from their profile"""
        url_citations = _CITATIONAUTH.format(self.id)
        url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
        soup = _get_soup(_HOST+url+_SORTAUTHPROFILEBYYEAR)
        self.name = soup.find('div', id='gsc_prf_in').text
        self.affiliation = soup.find('div', class_='gsc_prf_il').text
        organization = soup.find_all('a', class_='gsc_prf_ila')
        if organization:
            for htmlTag in organization:
                if re.findall(_ORGAUTHRE, htmlTag['href']):
                    self.organization = re.findall(_ORGAUTHRE, htmlTag['href'])[0]
                    break

        self.interests = [i.text.strip() for i in soup.find_all('a', class_='gsc_prf_inta')]
        
        # h-index, i10-index and h-index, i10-index in the last 5 years
        index = soup.find_all('td', class_='gsc_rsb_std')
        if index:
            self.citedby = int(index[0].text)
            self.citedby5y = int(index[1].text)
            self.hindex = int(index[2].text)
            self.hindex5y = int(index[3].text)
            self.i10index = int(index[4].text)
            self.i10index5y = int(index[5].text)
        else:
            self.hindex = self.hindex5y = self.i10index = self.i10index5y = 0

        # number of citations per year
        years = [int(y.text) for y in soup.find_all('span', class_='gsc_g_t')]
        cites = [int(c.text) for c in soup.find_all('span', class_='gsc_g_al')]
        self.cites_per_year = dict(zip(years, cites))

        # co-authors
        self.coauthors = []
        for row in soup.find_all('span', class_='gsc_rsb_a_desc'):
            new_coauthor = Author(re.findall(_CITATIONAUTHRE, row('a')[0]['href'])[0])
            new_coauthor.name = row.find(tabindex="-1").text
            new_coauthor.affiliation = row.find(class_="gsc_rsb_a_ext").text
            self.coauthors.append(new_coauthor)


        self.publications = list()
        pubstart = 0
        within_5_years = True
        this_year = datetime.datetime.now().year
        while within_5_years:
            for row in soup.find_all('tr', class_='gsc_a_tr'):
                new_pub = Publication(row, 'citations')
                if this_year - new_pub.bib['year'] > 5:
                    within_5_years = False
                    break
                else:
                    new_pub.bib['author'].discard(self.name)
                    self.publications.append(new_pub)
            if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs and within_5_years:
                pubstart += _PAGESIZE
                url = '{0}&cstart={1}&pagesize={2}'.format(url_citations, pubstart, _PAGESIZE)
                soup = _get_soup(_HOST+url+_SORTAUTHPROFILEBYYEAR)
            else:
                break

        self._filled = True
        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)


def search_pubs_query(query):
    """Search by scholar query and return a generator of Publication objects"""
    url = _PUBSEARCH.format(requests.utils.quote(query))
    soup = _get_soup(_HOST+url)
    return _search_scholar_soup(soup)


def search_author(name):
    """Search by author name and return a generator of Author objects"""
    url = _AUTHSEARCH.format(requests.utils.quote(name))
    soup = _get_soup(_HOST+url)
    return _search_authIDs_soup(soup)


def search_keyword(keyword):
    """Search by keyword and return a generator of Author objects"""
    url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)

def search_interests(interest):
    """Search by interest and return a generator of Author IDs, names, interests from search page"""
    url = _LABELSEARCH.format(requests.utils.quote(interest))
    soup = _get_soup(_HOST+url)
    return _search_authIDs_soup(soup)

def search_org(orgnum):
    """Search by organization number and return a generator of Author IDs, names, interests from search page"""
    url = _ORGSEARCH.format(requests.utils.quote(orgnum))
    soup = _get_soup(_HOST+url)
    return _search_authIDs_soup(soup)

def search_pubs_custom_url(url):
    """Search by custom URL and return a generator of Publication objects
    URL should be of the form '/scholar?q=...'"""
    soup = _get_soup(_HOST+url)
    return _search_scholar_soup(soup)

def search_author_custom_url(url):
    """Search by custom URL and return a generator of Publication objects
    URL should be of the form '/citation?q=...'"""
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)

def auth_all_coauthors(id):
    """Open an author profile given their ID and return a generator of Author objects"""
    # print(_HOST+_AUTHPROFILE+id)
    soup = _get_soup(_HOST+_AUTHPROFILE+id+_SORTAUTHPROFILEBYYEAR)
    return AuthorProfile(soup, id)