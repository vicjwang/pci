from pydelicious import get_popular, get_userposts, get_urlposts
import time

def initialize_user_dict( tag, count=5 ):
    user_dict = {}
    
    # get the top "count" popular posts
    for p1 in get_popular( tag=tag )[0:count]:
        # find all users who postsed this
        for p2 in get_urlposts( p1['url'] ):
            user = p2['user']
            user_dict[user] = {}
    return user_dict

def fill_items( user_dict ):
    all_items = {}
    # find links posted by all users
    for user in user_dict:
        posts = []
        for i in range( 3 ):
            try:
                posts = get_userposts( user )
                break
            except:
                print "failed user" + user + ", retrying"
                time.sleep( 4 )
        for post in posts:
            url = post['url']
            user_dict[user][url] = 1.0
            all_items[url] = 1
    print "filling in missing items" 
    # fill in missing items w 0
    for raitings in user_dict.values():
        for item in all_items:
            if item not in ratings:
                ratings[item] = 0.0





