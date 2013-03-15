from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import datetime
import encrypt

def jobkey(linkedin_id, company_id, eDate) :
	#my linkedin id is a-XWIKlbew  pattern of 
	return encrypt.make_hash(str(linkedin_id)+'|'+str(company_id)+'|'+eDate.strftime("%Y-%m-%d"))

#def content_hash(fname, lname, industry, location)

def getJob(jobkey):
	if not memcache.get(jobkey):
		jobs = db.GqlQuery("SELECT * FROM Job where jobkey ='%s'"%jobkey)
		jobs.fetch(1)
		for j in jobs:
			setJob(jobkey=jobkey, job=j)
	return memcache.get(jobkey)

def getPerson(linkedin_id):
	if not memcache.get(linkedin_id):
		persons = db.GqlQuery("SELECT * FROM Person where linkedin_id ='%s'"%linkedin_id)
		persons.fetch(1)
		for p in persons:
			memcache.set(linkedin_id, p)
	return memcache.get(linkedin_id)

def getCompany(company_id):
	if not memcache.get(str(company_id)):
		companies = db.GqlQuery("SELECT * FROM Company where company_id =%s"%company_id)
		companies.fetch(1)
		for c in companies:
			memcache.set(str(company_id), c)
	return memcache.get(str(company_id))

def setJob(jobkey, job):
	#TODO make checks here on validity of jobkey or job variable
	memcache.set(jobkey, job)


def fetchPicture(pictureUrl):
	""" returns blob object given a picture url"""
	return db.Blob(urlfetch.Fetch(pictureUrl).content)


def getJobIdsForFunction(function):
	""" returns list of jobids for a given function"""
	if not memcache.get(function):	
		jobids = []
		jobs = db.GqlQuery("SELECT * FROM Job where function='%s'"%function)
    		for j in jobs: 
    			jobids.append(j.jobkey)
    		memcache.set(function, jobids)
	return memcache.get(function)

#TODO what if somebody changes job function; would need to delete jobid from older function as well
def addJob2FunctionList(function, jobkey) :
	jobids = getJobIdsForFunction(function)
	jobids.append(jobkey)
	memcache.set(function, jobids)

class Company (db.Model):
	company_id = db.IntegerProperty(required=False) # some jobs may not have company id
	company_name = db.StringProperty(required=True)
	company_type = db.StringProperty(default="")
	company_industry = db.StringProperty(default="")
	company_size = db.StringProperty(default="")

class School(db.Model):
		schoolname = db.StringProperty(required=True)

class Person(db.Model):
		fname = db.StringProperty(required=True)
		lname = db.StringProperty(default="")
		linkedin_id = db.StringProperty(default="")
		industry = db.StringProperty(default="")
		location = db.StringProperty(default="")
		picture = db.BlobProperty(default=None)
		keyschool = db.ReferenceProperty(School, collection_name='person_keyschool')
		public_profile_url = db.StringProperty(default="")
		picture_url = db.StringProperty(default="")
		access_token = db.StringProperty(default="")
		access_token_secret = db.StringProperty(default="")
		oauth_expires_in = db.IntegerProperty(default=0)
		#content_hash=db.StringProperty(required=True)

class Job(db.Model):
	person = db.ReferenceProperty(Person,collection_name='person_job')
	company =  db.ReferenceProperty(Company,collection_name='person_company')
	person_linkedin_id = db.StringProperty(required=True)
	company_id = db.IntegerProperty(required=True)
	sdate = db.DateTimeProperty(required=False)
	edate = db.DateTimeProperty(required=True)
	title = db.StringProperty(default="")
	jobkey = db.StringProperty(required=True)
	function = db.StringProperty(required=False) #ideally this should have been enum. but enum doesn't look to be supported
	location = db.StringProperty(default="")
	dayinoffice = db.TextProperty(default = "I start my day at ...")
	jlove = db.TextProperty(default = "")
	jhate = db.TextProperty(default="")
	work_opportunity = db.StringProperty(required=False)
	work_culture = db.StringProperty(required=False)
	salary_growth = db.StringProperty(required=False)
	work_life_balance = db.StringProperty(required=False)
	fixed_salary = db.StringProperty(default="") #let it be string for now. it can be INR or $
	#variable_salary = db.StringProperty(default="") #let it be string for now. it can be INR or $
	yearly_bonus = db.StringProperty(default="") #it can % or absolute
	joining_bonus = db.StringProperty(default="") #let it be string for now
	stock = db.StringProperty(default="")
	alum_base = db.StringProperty(required=False)
	interview_question = db.TextProperty(default = "")
	exit_option = db.TextProperty(default = "")
	posted_by_text = db.StringProperty(default="")
	modify_date = db.DateTimeProperty(auto_now=True)

class Education(db.Model):
	person = db.ReferenceProperty(Person,collection_name='person_edu')
	school = db.ReferenceProperty(School,collection_name='person_school')
	degree = db.StringProperty(required=False)
	fieldofstudy = db.StringProperty(required = False)
	syear = db.IntegerProperty(required=False)
	eyear = db.IntegerProperty(required=False)

	
	