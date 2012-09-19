





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
    

        
