import numpy as np


# param: vec must be list
def magnitude( vec ):
    x = np.array( vec )
    return np.sqrt( x.dot( x ) )

def dot_product( vec1, vec2 ):
    total = 0
    size = len( vec1 ) if ( len( vec1) < len( vec2 ) ) else len( vec2 )

    for c in range( size ):
        total += vec1[c] * vec2[c]

    return total

def align_dims( vec1, vec2 ):
    pass
    
