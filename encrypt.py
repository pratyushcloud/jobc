import hashlib
import hmac
import random
import string

SALT_LENGTH = 5
SEPARATOR = "|"

# make secure password 
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(SALT_LENGTH))


def make_hash(text) :
     #h = hashlib.sha256(text).hexdigest() sha256 was giving bigger string so settling for md5
     h = hashlib.md5(text).hexdigest()
     return h

def make_pw_hash(username, pw, salt=None):
    if not salt:
    	salt = make_salt()
    h = hashlib.sha256(username + pw + salt).hexdigest()
    return (h, salt)

#pw = user inputted password
#hpw = hashed password stored in db for user username
def valid_pwd(username, pw, salt, hpw):
	h_salt = make_pw_hash(username, pw, salt)
	if h_salt[0] == hpw:
		return True
	return False


# hash cookie

SECRET = 'du.uyX9fE~Tb6.pp&U3D-0smY0,Gqi$^jT34tzu9'

def make_cookie(userid):
	return '%s%s%s' % (userid, SEPARATOR, hmac.new(SECRET, userid).hexdigest())

def valid_cookie(cookie_val):
    """ returns True if cookie is a valid cookie"""
    user_id = cookie_val.split(SEPARATOR)[0]
    if cookie_val == make_cookie(user_id):
        return True
	
def decode_cookie(cookie_val):
    if cookie_val:
    	 idx = cookie_val.index(SEPARATOR)
       	 return (cookie_val[:idx], cookie_val[idx+1:])

def getUserId(cookie_val) :
    if cookie_val:
        idx = cookie_val.index(SEPARATOR)
        try :
            userid = long(cookie_val[:idx])
            return userid
        except ValueError:
            return -1
    return -1 

h = make_pw_hash('rrr', 'rrr')

#print make_hash('a-XWIKlbew-5944-1900-01-01 00:00:00')
#print valid_cookie('12|97f9c20c1f2a2841b7f7adf11f5c5c54')