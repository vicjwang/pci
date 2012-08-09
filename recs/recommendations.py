from math import sqrt
import numpy as np
from vector_util import magnitude


# library to do user-based collaborative filtering and item-based collaborative filtering


# data (aka preference list/dict or prefs) must look like:
# { <person> : { <product> : <rating> } }
# OR
# { <product> : { <person> : <rating> } }

# example data set
critics = { 'lisa rose': { 'lady in the water': 2.5, 'snakes on a plane':3.5, 'just my luck':3.0,
                           'superman returns':3.5, 'you, me and dupree':2.5, 'the night listener': 3.0 },
            'gene seymour': { 'lady in the water': 3.0, 'snakes on a plane': 3.5, 'just my luck': 1.5,
                              'superman returns': 5.0, 'the night listener': 3.0, 'you, me and dupree': 3.5 },
            'michael phillips': {'lady in the water': 2.5, 'snakes on a plane': 3.0,
                                 'superman returns': 3.5, 'the night listener': 4.0 }, 
            'claudia puig': { 'snakes on a plane': 3.5, 'just my luck': 3.0, 'the night listener':4.5,
                              'superman returns': 4.0, 'you, me and dupree':2.5 },
            'mick lasalle': {'lady in the water':3.0, 'snakes on a plane':4.0, 'just my luck': 2.0,
                             'superman returns':3.0, 'the night listener': 3.0, 'you, me and dupree':2.0 },
            'jack matthews': {'lady in the water': 3.0, 'snakes on a plane': 4.0, 'the night listener': 3.0,
                              'superman returns':5.0, 'you, me and dupree':3.5},
            'toby': {'snakes on a plane':4.5, 'you, me and dupree': 1.0, 'superman returns': 4.0 } 
            }

##########################################
##########                      ##########
########## similarity functions ##########
##########                      ##########
##########################################

# assumes params are vectors with same dim
# returns cosine of angle between person vectors, range from -1, 1 inclusive
def sim_cos( prefs, person1, person2 ):
    shared_items = get_shared_items( prefs, person1, person2 )

    if len( shared_items ) == 0: return 0
    
    p1_vec = prefs[person1].values()
    p2_vec = prefs[person2].values()

    p1_shared = [ prefs[person1][k] for k in shared_items ]
    p2_shared = [ prefs[person2][k] for k in shared_items ]

    dp = np.dot( p1_shared, p2_shared )
    p1_mag = magnitude( p1_vec )
    p2_mag = magnitude( p2_vec )

    return dp / ( p1_mag * p2_mag )


# returns distance based on ratio of common set divided by total set
def sim_tanimoto( prefs, person1, person2 ):
    shared_items = get_shared_items( prefs, person1, person2 )

    if len( shared_items ) == 0: return 0

    return len( shared_items )/ float( len( prefs[person1] ) + len( prefs[person2] ) - len( shared_items ) ) 
    
# returns a distance based similarity score for person1 and person2
# fake "euclidean" distance, doesn't account for vectors with different and overlapping dimensions
def sim_distance( prefs, person1, person2 ):
    # get list of shared_items
    shared_items = get_shared_items( prefs, person1, person2 )

    if len( shared_items ) == 0:
        return 0
    
    # add up the squares of all differences
    sum_of_squares = sum( [ pow(prefs[person1][item] - prefs[person2][item], 2 )for item in shared_items ] )

    return 1/( 1 + sqrt( sum_of_squares ) )

# deals with vectors of different sizes with overlapping dimensions
def sim_euclidean( prefs, person1, person2 ):
    person1_vec = prefs[person1]
    person2_vec = prefs[person2]
    
    total = 0 
    shared_items = get_shared_items_map( prefs, person1, person2 )
    
    for item, shared in shared_items.items():
        if shared == 1:
            total += ( person1_vec[item] - person2_vec[item] ) * ( person1_vec[item] - person2_vec[item] )
        elif shared == 0:
            x1 = person1_vec[item] if person1_vec.get( item ) else 0
            x2 = person2_vec[item] if person2_vec.get( item ) else 0
            total += x1*x1 + x2*x2
    print total 
    # assumes unit length components
    return 1/( 1 + sqrt( total ) )


# returns the pearson correlation coeff for person1, person2
# pearsons algo: measures how well 2 sets of data fit on a striahgt line (works well if data isn't well normalized)
def sim_pearson( prefs, person1, person2 ):
    # get list of mutually rated items
    shared_items = get_shared_items( prefs, person1, person2 )

    # find the number of elements
    n = len( shared_items )
    if n == 0: return 0

    # add up all the preferences
    sum1 = sum( [ prefs[person1][it] for it in shared_items ] )
    sum2 = sum( [ prefs[person2][it] for it in shared_items ] )

    # sum up the squares
    sum1_squares = sum( [ pow( prefs[person1][it], 2 ) for it in shared_items ] )
    sum2_squares = sum( [ pow( prefs[person2][it], 2 ) for it in shared_items ] )

    # sum of products
    product_sum = sum( [ prefs[person1][it] * prefs[person2][it] for it in shared_items ] )

    # calc pearson score
    num = product_sum - ( sum1 * sum2/n )
    den = sqrt( ( sum1_squares - pow( sum1, 2 )/n ) * ( sum2_squares - pow( sum2, 2 )/n ) )
    if den == 0: return 0

    r = num/den

    return r


##########################################
##########                      ##########
##########  utility functions   ##########
##########                      ##########
##########################################

def get_shared_items( prefs, person1, person2 ):
    shared_items = set()
    for item in prefs[person1]:
        if item in prefs[person2]:
            shared_items.add( item )
    return shared_items


def get_shared_items_map( prefs, person1, person2 ):
    shared_items = {}

    for item in prefs[person1]:
        shared_items.setdefault( item, 0 )
        if item in prefs[person2]:
            shared_items[item] = 1

    for item in prefs[person2]:
        shared_items.setdefault( item, 0 )
        if item in prefs[person1]:
            shared_items[item] = 1
    return shared_items

# transform pref list (swap person <--> product )
def transform_prefs( prefs ):
    result = {}
    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})

            # flip item and person
            result[item][person] = prefs[person][item]
    return result

def calculate_similar_items( prefs, n=10 ):
    # create a dictionary of items showing which other items they are most similar to
    result = {}

    # invert the preference matrix to be item-centric
    item_prefs = transform_prefs( prefs )
    c = 0
    for item in item_prefs:
        # status updates for large datasets
        c += 1
        if c%100 == 0: print "%d / %d" % ( c, len( item_prefs ) )
        # find the most similar items to this one
        scores = top_matches( item_prefs, item, n=n, similarity=sim_euclidean )
        result[item] = scores
    return result
        


##########################################
##########                      ##########
##########    main functions    ##########
##########                      ##########
##########################################



# returns best matches for person from prefs
def top_matches( prefs, person, n=5, similarity=sim_pearson ):
    scores = [ ( similarity( prefs, person, other ), other ) for other in prefs if other != person ]

    # sort the list so highest scores appaer at top
    scores.sort()
    scores.reverse()
    return scores[0:n]

# gets recommendations for a person by using a weighted average of every other user's rankings
# user based collaborative filtering
def get_recommendations( prefs, person, similarity=sim_pearson ):
    totals = {}
    sim_sums = {}
    for other in prefs:
        # don't compare me to myself
        if other == person: continue
        sim = similarity( prefs, person, other )

        # ignore scores of zero or lower
        if sim <= 0: continue
        for item in prefs[other]:
            # only score movies I haven't seen yet
            if item not in prefs[person] or prefs[person][item] == 0:
                # similarity * score
                totals.setdefault( item, 0 )
                totals[item] += prefs[other][item]*sim
                # sum of similarities
                sim_sums.setdefault( item, 0 )
                sim_sums[item] += sim

    # create the normalized list
    rankings = [ ( total/sim_sums[item], item ) for item, total in totals.items() ]

    # return the sorted list
    rankings.sort()
    rankings.reverse()
    return rankings


# item based collaborative filtering
def get_recommended_items( prefs, item_match, user ):
    user_ratings = prefs[user]
    scores = {}
    total_sim = {}

    # loop over items rated by this user
    for ( item, rating ) in user_ratings.items():

        # loop over items similar to this one
        for ( similarity, item2 ) in item_match[item]:
            
            # ignore if tis user has already rated this item
            if item2 in user_ratings: continue

            # weighted sum of rating times similarity
            scores.setdefault( item2, 0 )
            scores[item2] += similarity*rating

            # sum of all the similarities
            total_sim.setdefault( item2, 0 )
            total_sim[item2] += similarity

    # divide each total score by total weighting to get an average
    rankings = [ ( score/total_sim[item], item ) for item, score in scores.items() ]

    # return the rankings from highest to lowest
    rankings.sort()
    rankings.reverse()
    return rankings
        

