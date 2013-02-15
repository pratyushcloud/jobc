from google.appengine.ext import db
from google.appengine.api import memcache
import datetime
import encrypt

def jobkey(linkedin_id, company_id, eDate) :
	#my linkedin id is a-XWIKlbew  pattern of 
	return encrypt.make_hash(str(linkedin_id)+'|'+str(company_id)+'|'+eDate.strftime("%Y-%m-%d"))

class Company (db.Model):
	company_id = db.IntegerProperty(required=True)
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

	
	