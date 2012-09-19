import urllib2
from bs4 import BeautifulSoup 
from urlparse import urljoin
from pysqlite2 import dbapi2 as sqlite
import re


# words to ignore
ignore_words = set( ['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it' ] )

class Crawler: 

    # initialize the crawler with the name of database
    def __init__(self, dbname):
        self.con = sqlite.connect( dbname ) 

    def __del__(self):
        self.con.close()

    def db_commit(self):
        self.con.commit()

    # aux function for getting an entry id and adding
    # it if it's not present
    def get_entry_id( self, table, field, value, create_new = True):
        cur = self.con.execute( "select rowid from %s where %s='%s'" % ( table, field, value ) )
        res = cur.fetchone()
        if res == None:
            cur = self.con.execute( "insert into %s (%s) values ('%s')" % ( table, field, value ) )
            return cur.lastrowid
        else: return res[0]

    # index an individuall page
    def add_to_index( self, url, soup):
        if self.is_indexed( url ): return
        print "indexing %s" % url
    
        # get the indiv words
        text = self.get_text_only( soup )
        words = self.separate_words( text )

        # get the url id
        urlid = self.get_entry_id( 'urllist', 'url', url )
        
        # link each word to this url
        for i in range( len( words )):
            word = words[i]
            if word in ignore_words:
                continue
            wordid = self.get_entry_id( 'wordlist', 'word', word )
            self.con.execute( 'insert into wordlocation(urlid, wordid, location) \
                                values (%d, %d, %d)' % ( urlid, wordid, i ) )
        

    # extract text from an html page (no tags)
    def get_text_only( self, soup):
        v = soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.get_text_only(t)
                resulttext += subtext + '\n'
            return resulttext
        else:
            return v.strip()

    # separate the words by any non-whitespace char
    def separate_words( self, text):
        splitter = re.compile('\\W*')
        return [ s.lower() for s in splitter.split(text) if s != '' ]

    # return true if this url is already indexed
    def is_indexed( self, url ):
        u = self.con.execute( "select rowid from urllist where url='%s'" % url ).fetchone()
        if u != None:
            # check if has been crawled
            v = self.con.execute( 'select * from wordlocation where urlid=%d' % u[0] ).fetchone()
            if v!= None: return True
        return False

    # add a link between two pages
    def add_link_ref( self, url_from, url_to, link_text ):
        words = self.separate_words( link_text )
        fromid = self.get_entry_id( 'urllist', 'url', url_from )
        toid = self.get_entry_id( 'urllist', 'url', url_to )
        if fromid == toid: return
        cur = self.con.execute( "insert into link(fromid, toid) values (%d, %d)" % (fromid, toid) )
        linkid = cur.lastrowid
        for word in words:
            if word in ignore_words: continue
            wordid = self.get_entry_id( 'wordlist', 'word', word )
            self.con.execute( "insert into linkwords(linkid, wordid) values (%d, %d)" % (linkid, wordid) )

    # starting with list of pages, do bfs to given depth,
    # indexing as we go
    def crawl( self, pages, depth = 2 ):
        for i in range(depth):
            new_pages = set()
            for page in pages:
                try:
                    c = urllib2.urlopen( page )
                except:
                    print "could not open %s" % page
                    continue
                soup = BeautifulSoup( c.read() )
                self.add_to_index( page, soup )

                links = soup( 'a' )
                for link in links:
                    if ( 'href' in dict( link.attrs ) ):
                        url = urljoin( page, link['href'] )
                        if url.find( "'" ) != -1: continue
                        url = url.split( '#' )[0] # remove location portion

                        if url[0:4] == 'http' and not self.is_indexed( url ):
                            new_pages.add( url )
                        link_text = self.get_text_only( link )
                        self.add_link_ref( page, url, link_text )

                self.db_commit()
            pages = new_pages


    # create db tables
    def create_index_tables( self ):
        self.con.execute( 'create table urllist(url)' )
        self.con.execute( 'create table wordlist(word)' )
        self.con.execute( 'create table wordlocation(urlid, wordid, location)' )
        self.con.execute( 'create table link(fromid integer, toid integer)' )
        self.con.execute( 'create table linkwords(wordid, linkid)' )
        self.con.execute( 'create index wordidx on wordlist(word)' )
        self.con.execute( 'create index urlidx on urllist(url)' )
        self.con.execute( 'create index wordurlidx on wordlocation(wordid)' )
        self.con.execute( 'create index urltoidx on link(toid)' )
        self.con.execute( 'create index urlfromidx on link(fromid)' )
        self.db_commit()

    # makes sense to put in crawler class
    def calculate_pagerank( self, iterations = 20 ):
        # clear out current pagerank tables
        self.con.execute( 'drop table if exists pagerank' )
        self.con.execute( 'create table pagerank(urlid primary key, score)' )

        # initialize every url with a pagerank of 1
        self.con.execute( 'insert into pagerank select rowid, 1.0 from urllist' )
        self.db_commit()

        for i in range(iterations):
            print "iteration %d" % (i)
            for (urlid,) in self.con.execute('select rowid from urllist'):
                pr = 0.15

                # loop thru all the pages that link to this one
                for (linker,) in self.con.execute( 'select distinct fromid from link where toid=%d' % urlid):
                    # get pagerank of the linker
                    linking_pagerank = self.con.execute( 'select score from pagerank where urlid=%d' % linker ).fetchone()[0]

                    # get total number of links from linker
                    linking_count = self.con.execute( 'select count(*) from link where fromid=%d' % linker).fetchone()[0]
                    pr += .85* linking_pagerank / linking_count

                self.con.execute( 'update pagerank set score=%f where urlid=%d' % (pr, urlid) )
            self.db_commit()



