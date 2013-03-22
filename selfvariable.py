class k:
    i = 'foo'
    def get_static_i(self):
    	k.i = '2'
        return k.i
    def get_instance_i(self):
    	return self.i
	def __init__(self):
		print "initialized"
		k.i = 'not foo'

print k.i
c = k()
print "c " + c.get_static_i()
print k().get_static_i()
print k().get_instance_i()

(aa, bb ) = [1,2]
print aa

def m1(value):
	if value == 1:
		return 1
	else:
		return 'a'

print m1(2)


