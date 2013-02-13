import webapp2
import jinja2
import logging
import urlparse 
import time, os
import sys
import json
import datetime

import dbmodels

from google.appengine.api import urlfetch

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import oauth2 as oauth
import httplib2

from google.appengine.ext import db
from google.appengine.api import memcache


consumer_key    =   'gge7se1gxi53'
consumer_secret =   'Vlun3FqAAu7H5Yq3'
validschools = ['Indian Institute of Management, Calcutta']

#oauth_token = 'f0087255-7077-491f-b89c-561baf0d36ea'
#oauth_token_secret='f3dde1ad-9d9e-44d4-a259-04bbfdbf0303'

#consumer_key      =   'abcd123456'
#consumer_secret  =   'efgh987654'

# Use your API key and secret to instantiate consumer object

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken?scope=r_fullprofile+r_emailaddress'
authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
people_info_url = "http://api.linkedin.com/v1/people/~"
		

consumer = None
client = None

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def getJob(jobkey):
	if not memcache.get(jobkey):
		jobs = db.GqlQuery("SELECT * FROM Job where jobkey ='%s'"%jobkey)
		jobs.fetch(1)
		for j in jobs:
			memcache.set(jobkey, j)
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

class MainPage(webapp2.RequestHandler) :
	request_token = None	
	def get(self) :
		self.response.out.write(render_str("login.html"))
	
	def post(self):
		logging.error("MainPage Post")
		url = "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
		#print "Go to the following link in your browser:"
 		self.redirect(url)
 
	def initialize(self, *a, **kw):
		global request_token, consumer, client
		
		webapp2.RequestHandler.initialize(self, *a, **kw)
		consumer = oauth.Consumer(consumer_key, consumer_secret)
		client = oauth.Client(consumer)
		resp, content = client.request(request_token_url, "POST")
		if resp['status'] != '200':
			raise Exception("Invalid response %s." % resp['status'])
			 
		request_token = dict(urlparse.parse_qsl(content))
				
		logging.error("Request Token:")
		logging.error("    - oauth_token        = %s" % request_token['oauth_token'])
		logging.error("    - oauth_token_secret = %s" % request_token['oauth_token_secret']) 


class PostLoginPage(webapp2.RequestHandler):
	def get(self) :
		token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
		oauth_verifier = self.request.get('oauth_verifier')
		token.set_verifier(oauth_verifier)
		
		client = oauth.Client(consumer, token)
			 
		#resp, content = client.request(people_info_url, "GET", "")
		resp, content = client.request(access_token_url, "POST", "")
		
		#self.response.out.write("resp")
		#self.response.out.write(resp)
		#self.response.out.write("content")
		#self.response.out.write(content)
		#self.response.out.write("<br>")
		
		access_token = dict(urlparse.parse_qsl(content))
		
		# API call to retrieve profile using access token 
		token = oauth.Token(key=access_token['oauth_token'],secret=access_token['oauth_token_secret'])
		client = oauth.Client(consumer, token)
		
		self.response.out.write("<a href=\"http://localhost:8080/jobc\">Home Page</a> <br><br>")
		resp1, content = client.request("http://api.linkedin.com/v1/people/~")
		#self.response.out.write(content)
		#self.response.out.write("<br>")
		

		#self.response.out.write("resp")
		#self.response.out.write(resp)
		
		
		#resp2, content = client.request("http://api.linkedin.com/v1/people/~/connections?count=10")
		#self.response.out.write(content)
		#self.response.out.write("<br><br>")
		
		url = "http://api.linkedin.com/v1/people/~:(id,first-name,last-name,email-address,headline,picture-url,location:(name),industry,num-connections,positions:(title,start-date,end-date,is-current,company),educations:(school-name,field-of-study,start-date,end-date,degree),date-of-birth)?format=json"

		resp3, content = client.request(url)
		#self.response.out.write(content)
		
		j = json.loads(content)
		nconnection = int(j['numConnections'])

		fname = ''
		lname = '' 
		linkedin_id = ''
		industry = ''
		location = ''
		pictureUrl = ''

		if j.has_key('firstName'):
			fname = j['firstName']
		if j.has_key('lastName'):
			lname = j['lastName']
		if j.has_key('id'):
			linkedin_id = j['id']

		if j.has_key('industry'):
	 		industry = j['industry']
		if j.has_key('location'):
			if j['location'].has_key('name'):
				location = j['location']['name']
		if j.has_key('pictureUrl'):
			pictureUrl = j['pictureUrl']

		logging.error("pictureUrl = " +pictureUrl)
		if (nconnection < 10) :
			self.redirect("/jobc/inviteonly/?fname="+fname)
		
		person = dbmodels.Person.all().filter('linkedin_id = ', linkedin_id).get()
		if not person:
			person = dbmodels.Person(fname=fname, lname = lname, linkedin_id=linkedin_id, industry=industry, location=location)
			#logging.error("pictureUrl " + pictureUrl)
			if pictureUrl and pictureUrl != '':
				person.picture = db.Blob(urlfetch.Fetch(pictureUrl).content)
			person.put()



		school_list = []

		if j.has_key('educations'):
			if j['educations'].has_key('values'):
				school_list = j['educations']['values']
		#print school_list

		isvalidSchool = False
		syear_validSchool = 0
		eyear_validSchool = 0
		validSchool= None
		for school in school_list:
			syear = 0
			eyear = 0
			schoolName = ''
			degree = ''
			study_field = ''
			if school.has_key('endDate'):
				if school['endDate'].has_key('year'):
					eyear = int(school['endDate']['year'])
			if school.has_key('startDate'):
				if school['startDate'].has_key('year'):
					syear = int(school['startDate']['year'])
			if school.has_key('degree'):
				degree = school['degree']
			if school.has_key('fieldOfStudy'):
				study_field = school['fieldOfStudy']			
			if school.has_key('schoolName'):
				schoolName = school['schoolName']
				if any(schoolName in s for s in validschools):
					isvalidSchool = True
					logging.error("schoolName " + schoolName)
					schooldb = dbmodels.School.all().filter('schoolname = ', schoolName).get()
					if not schooldb:
						schooldb = dbmodels.School(schoolname=schoolName)
						schooldb.put()
					validschool = schooldb 
					person.keyschool = validschool
					person.put() # not recommended to do double db write
					education = dbmodels.Education(person=person, school=schooldb, degree=degree, fieldofstudy=study_field, syear=syear, eyear=eyear)
					# take the minimum year. person might have had two degrees from a school. we take the oldest one
					if (syear_validSchool >  0 and eyear_validSchool > 0 and syear > 0 and eyear > 0) :
						if (eyear_validSchool > eyear) :
								syear_validSchool = syear
								eyear_validSchool = eyear
					if (syear_validSchool == 0 and eyear_validSchool == 0) :
						syear_validSchool = syear
						eyear_validSchool = eyear

			#print "%s (%s-%s) %s (%s)" %(schoolName, syear, eyear, degree, study_field)
		
		if not isvalidSchool:
			self.redirect("/jobc/inviteonly/?fname="+fname)

		if (eyear_validSchool - syear_validSchool <= 1):
			# Guy must have done certification or short term course
			self.redirect("/jobc/inviteonly/?fname="+fname)



		job_list = []
		if j.has_key('positions'):
			if j['positions'].has_key('values'):
				job_list = j['positions']['values']

		for job in job_list:
			isCurrent = False
			sDate = None
			eDate = datetime.datetime(1900, 1,1)
			title = ''
			company_id = ''
			company_name = ''
			company_type = ''
			company_industry = ''
			company_size = ''

			if job.has_key('startDate'):
				year = 0
				month = 1
			if job['startDate'].has_key('year'):
				year = int(job['startDate']['year'])
			if job['startDate'].has_key('month'):
				month = int(job['startDate']['month'])
			if (year > 0):
				sDate = datetime.datetime(year, month, 1)
				
			if job.has_key('endDate'):
				year = 0
				month = 1
				if job['endDate'].has_key('year'):
					year = int(job['endDate']['year'])
				if job['endDate'].has_key('month'):
					month = int(job['endDate']['month'])
				if (year > 0):
					eDate = datetime.datetime(year, month, 1)

			if eyear_validSchool == 0 or datetime.datetime(eyear_validSchool, 1,1) > sDate :
				#this is pre mba job
				continue

			if job.has_key('company'):
				if job['company'].has_key('id'):
					company_id = job['company']['id']		
				if job['company'].has_key('industry'):
					company_industry = job['company']['industry']
				if job['company'].has_key('name'):
					company_name = job['company']['name']
				if job['company'].has_key('size'):
					company_size = job['company']['size']
				if job['company'].has_key('type'):
					company_type = job['company']['type']

			company = dbmodels.Company.all().filter('company_id = ', company_id).get()
			if not company:
				company = dbmodels.Company(company_id=int(company_id), company_name=company_name, company_industry=company_industry, company_size=company_size, company_type=company_type)
				company.put()

			if job.has_key('isCurrent'):
				isCurrent = bool(job['isCurrent'])
			if job.has_key('title'):
				title = job['title']

			jobkey = dbmodels.jobkey(linkedin_id = person.linkedin_id, company_id=company.company_id, eDate=eDate)
			logging.error("eDate " )
			logging.error(eDate)
			jobdb = dbmodels.Job.all().filter('jobkey = ', jobkey).get()
			if not jobdb:
				jobdb = dbmodels.Job(title=title, person=person, company=company, person_linkedin_id = person.linkedin_id, company_id = company.company_id, sdate = sDate, edate=eDate, jobkey=jobkey)
				jobdb.put()
			#print '%s - %s (%s) %s %s' %(company_name, company_industry, company_id, company_size, company_type)
			#print '%s (%s - %s) %s \n' %(title, sDate, eDate, isCurrent)
		
		post_mba_jobs = []
		for pjob in person.person_job:
			post_mba_jobs.append((pjob.title, pjob.company.company_name,pjob.jobkey))
		njobs= len(post_mba_jobs)
		self.response.out.write(render_str("alumpage.html", fullname= fname, pictureUrl= pictureUrl,njobs=njobs, job=post_mba_jobs))
   
#movie.picture = db.Blob(urlfetch.Fetch(picture_url).content)


#print '%s %s (%s) - %s at %s' %(fname, lname, linkedin_id, industry, location) 
#print 'nconnections %s' %nconnection

class InviteOnly(webapp2.RequestHandler) :
	def get(self) :
		fname = self.request.get("fname")
		self.response.out.write(render_str("errorpage.html", fname= fname))

class RealJD(webapp2.RequestHandler) :
	def get(self, job_id):
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = getJob(job_id)
		if not job:
			#throw some error
			self.redirect("/jobc")
		title = job.title
		author = job.posted_by_text
		date = job.modify_date
		jd = job.dayinoffice
		salary = "Fixed: " + job.fixed_salary + " Variable: Yearly Bonus:" + job.yearly_bonus+" Joining Bonus:" + job.joining_bonus + " Stock: " + job.stock 
		jlove = job.jlove
		jhate = job.jhate
		iq = job.interview_question
		eo = job.exit_option
		wop = job.work_opportunity
		wc = job.work_culture
		wsg = job.salary_growth
		wlb = job.work_life_balance
		self.response.out.write(render_str("onejd.html", title=title, author=author, date=date, jd=jd, salary=salary, jlove = jlove, jhate= jhate,
			iq = iq, eo = eo, wop = wop, wc = wc, wsg = wsg, wlb=wlb))

class RealJDEdit(webapp2.RequestHandler) :
	def get(self, job_id):
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = getJob(job_id)

		if not job:
			# some error here
			self.redirect("/jobc")
		p= getPerson(job.person_linkedin_id)
		if not page:
			school = p.keyschool
			fullname = p.fname
			location = p.location
			title = job.title
			logging.error("companyid")
			logging.error(job.company_id)
			company = getCompany(job.company_id).company_name
			sdate = job.sdate 
			edate = job.edate
			function = job.function
			jd = job.dayinoffice
			jlove = job.jlove
			jhate = job.jhate
			function = job.function
			self.response.out.write(render_str("jd.html", fullname= fullname, location=location, school=school, title=title, company=company, sdate = sdate, edate = edate, jhate = jhate, jlove=jlove, jd = jd, function = function))
		elif page == "1":
			iq = job.interview_question
			eo = job.exit_option
			alum_base = job.alum_base
			stock = job.stock
			vsalary = job.yearly_bonus
			vsalary= job.joining_bonus
			wop = job.work_opportunity
			wc = job.work_culture
			wsg = job.salary_growth
			wlb = job.work_life_balance
			fixed_salary = job.fixed_salary
			self.response.out.write(render_str("jd2.html", wopcheck = wop, iq=iq, eo=eo, abasecheck=alum_base, wccheck = wc, wsgcheck=wsg,stockcheck = stock, wlbcheck = wlb,  fsalary=fixed_salary))
        #else:
			# some exception code here
		#	self.redirect("/jobc")

	def post(self, job_id) :
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = getJob(job_id)
		if not job :
			#some error handling here
			self.redirect("/jobc")
		if not page:
			job.location = self.request.get("location")
			job.title = self.request.get("title")
			#sdate = job.sdate 
			#edate = job.edate
			job.function = self.request.get("function")
			job.dayinoffice = self.request.get("dayinoffice")
			job.jlove = self.request.get("jlove")
			job.jhate = self.request.get("jhate")
			job.put()
			url = "/jobc/realjd/_edit/"+job_id+"?page=1"
			#logging.error("url: " + url)
			self.redirect(url)
		elif page == "1":
			job.work_opportunity = self.request.get("wop")
			job.work_culture = self.request.get("wc")
			job.salary_growth = self.request.get("wsg")
			job.work_life_balance = self.request.get("wlb")
			job.fixed_salary = self.request.get("fsalary")
			job.yearly_bonus = self.request.get("ybonus")
			job.joining_bonus = self.request.get("jbonus")
			job.stock = self.request.get("stock")
			job.alum_base = self.request.get("abase")
			job.interview_question = self.request.get("iq")
			job.exit_option = self.request.get("eo")
			job.put()
			#updatejob(job.jobkey, job)
			url = "/jobc/realjd/"+job_id
			logging.error("url: " + url)
			self.redirect(url)
		else:
			#some error handling here
			# either redirect to first page
			self.redirect("/jobc") 


		
			