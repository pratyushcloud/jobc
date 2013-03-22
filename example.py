import datetime

t = datetime.datetime(2013, 02, 14) 
print t.strftime( '%m/%Y')


a = 7
b = 10

class A1:

	def printA(self):
		print "Value of a is %d, value of b is %d" % (a,b)

	def setA(self,value):
		c = 9
		global a
		global  b
		a = value
		b = 2* value
		print "Inside setA, a is now %d b is now %d" %(a,b)

class B1:

	def printA(self):
		print "Value of a is %d, value of b is %d" % (a,b)

	def setA(self,value):
		c = 9
		global a
		global  b
		a = value
		b = 2* value
		print "Inside setA, a is now %d b is now %d" %(a,b)

print "Before setA"
a1 = A1()
a1.printA()
a1.setA(42)
print "After setA"
a1.printA()
b1=B1()
b1.printA()

validschools = ['Indian Institute of Management, Calcutta']
school = 'IIM Calcutta'

if school in validschools:
	print school

s = None
if not s:
	print "s is None"

