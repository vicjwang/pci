from pysqlite2 import dbapi2 as sqlite
from ranker import normalize_scores, word_frequency_score, word_location_score, \
                    pagerank_score, word_distance_score, inbound_link_score

class Searcher:
    def __init__( self, dbname ):
        self.con = sqlite.connect(dbname)

        # CHANGE HERE
        self.weights = dict([ ( word_frequency_score, 1.0 ), 
                               ( word_location_score, 1.0 ),
                               ( word_distance_score, 1.0 ),
                               ( inbound_link_score,  1.0 ),
                               ( pagerank_score,      1.0 ) ])

    def __del__( self ):
        self.con.close()

    def set_weights( self, metric, weight ):
        self.weights[ metric ] = weight

    def get_weights( self, rows, con ):
        return [ ( metric( rows, con ), score ) for metric, score in self.weights.items() ]

    def print_weights( self ):
        print self.weights

    def get_match_rows( self, q ):
        # strings to build the query
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []

        # split the words by spaces
        words = q.split( ' ' )
        tablenumber = 0

        for word in words:
            # get the word id
            wordrow = self.con.execute( 
                        "select rowid from wordlist where word='%s'" % word ).fetchone()

            if wordrow != None:
                wordid = wordrow[0]
                wordids.append( wordid )
                if tablenumber > 0:
                    tablelist += ','
                    clauselist += ' and '
                    clauselist += 'w%d.urlid = w%d.urlid and ' % ( tablenumber - 1, tablenumber )
                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid=%d' % ( tablenumber, wordid )
                tablenumber += 1
        # create the query from the separate parts
        fullquery = 'select %s from %s where %s' % ( fieldlist, tablelist, clauselist )
        cur = self.con.execute( fullquery )
        rows = [ row for row in cur ]

        return rows, wordids

    def get_scored_list( self, rows, wordids ):
        total_scores = dict( [ (row[0], 0 ) for row in rows ] )
        
        weights = self.get_weights( rows, self.con )

        for ( scores, weight ) in weights:
            for url in total_scores:
                total_scores[url] += weight*scores[url]

        return total_scores

    def get_urlname( self, id ):
        return self.con.execute(
                "select url from urllist where rowid=%d" % id ).fetchone()[0]

    def query( self, q ):
        rows, wordids = self.get_match_rows( q )
        scores = self.get_scored_list( rows, wordids )
        ranked_scores = sorted( [ ( score, url ) for ( url, score ) in scores.items()], reverse=1 )

        for ( score, urlid ) in ranked_scores[0:10]:
            print '%f\t%s' % ( score, self.get_urlname( urlid ) )

    




