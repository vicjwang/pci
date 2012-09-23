import neural_net as nn

net = nn.SearchNet("nn.db")


def normalize_scores( scores, small_is_better = 0 ):
    vsmall = .00001 # avoid div by zero
    if small_is_better:
        minscore = min( scores.values() )
        return dict( [ ( u, float( minscore ) / max( vsmall, l ) ) for ( u, l ) in scores.items() ] )
    else:
        maxscore = max( scores.values() )
        if maxscore == 0: maxscore = vsmall
        return dict( [ ( u, float( c ) / maxscore ) for ( u, c ) in scores.items() ] )

def word_frequency_score( rows, con ):
    counts = dict( [ (row[0], 0) for row in rows ] )
    for row in rows: counts[row[0]] += 1
    return normalize_scores( counts )


def word_location_score( rows, con ):
    locs = dict( [ ( row[0], 1000000 ) for row in rows ] )
    for row in rows:
        loc = sum( row[1:])
        if loc < locs[row[0]]: locs[row[0]] = loc
    return normalize_scores( locs, small_is_better = 1 )

def word_distance_score( rows, con ):
    # if there's only one word, everyone wins!
    if len (rows[0] ) <= 2: return dict( [ (row[0], 1.0) for row in rows ] )

    # initialize the dictionary with large values
    min_distance = dict( [ (row[0], 1000000) for row in rows ] )

    for row in rows:
        dist = sum( [ abs(row[i] - row[i-1]) for i in range(2, len(row)) ] )
        if dist < min_distance[row[0]]: min_distance[row[0]] = dist
    return normalize_scores( min_distance, small_is_better = 1 )

def inbound_link_score( rows, con ):
    unique_urls = set( [ row[0] for row in rows ] )
    inbound_count = dict( [ (u, con.execute( \
                        'select count(*) from link where toid=%d' % u).fetchone()[0] ) \
                        for u in unique_urls ] )
    return normalize_scores( inbound_count )

def pagerank_score( rows, con ):
    pageranks = dict( [ (row[0], con.execute( 'select score from pagerank where urlid=%d' % row[0] ).fetchone()[0]) for row in rows] )
    maxrank = max( pageranks.values() )
    normalized_scores = dict([ ( u,float(l)/maxrank ) for (u,l) in pageranks.items() ])
    return normalized_scores
    
def link_text_score( rows, con, wordids=[] ):
    link_scores = dict( [ (row[0],0) for row in rows] )
    if not wordids: return dict( [ ( u, 0 ) for u,l in link_scores.items() ] )
    for wordid in wordids:
        cur = con.execute( "select link.fromid, link.toid from linkwords, link where wordid=%d and linkwords.linkid=link.rowid" % wordid)
        for ( fromid, toid ) in cur:
            if toid in link_scores:
                pr = con.execute( "select score from pagerank where urlid=%d" % fromid ).fetchone()[0]
                link_scores[toid] += pr
    maxscore = max( link_scores.values() )
    normalized_scores = dict( [ ( u, float(l)/maxscore ) for ( u,l ) in link_scores.items() ] )
    return normalized_scores

def nn_score( self, rows, wordids ):
    # get unique url ids as ordered list
    urlids = [urlid for urlid in set([row[0] for row in rows])]
    nnres = net.get_result( wordids, urlids )
    scores = dict( [ (urlids[i], nnres[i]) for i in range(len(urlids))])
    return self.normalize_scores(scores)
     

