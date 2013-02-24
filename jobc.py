import webapp2
import jinja2
import logging
import urlparse 
import time, os
import sys

import linkedinparser
import dbmodels

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import oauth2 as oauth
import httplib2

from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken?scope=r_fullprofile+r_emailaddress'
authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
people_info_url = "http://api.linkedin.com/v1/people/~"
		
# Use your API key and secret to instantiate consumer object
consumer_key    =   'gge7se1gxi53' #mentorme api
consumer_secret =   'Vlun3FqAAu7H5Yq3'
#consumer_key= 'yfn26ez21xqb' #localhost
#consumer_secret = '8k478hHqjam3273z' #localhost

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class MainPage(webapp2.RequestHandler) :
		
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		logging.error("MainPage initialize")

	def setTokenAndSecret(self):
		logging.error("in MainPage setTokenAndSecret")
		consumer = oauth.Consumer(consumer_key, consumer_secret)
		client = oauth.Client(consumer)
		resp, content = client.request(request_token_url, "POST")
		if resp['status'] != '200':
			logging.error("linkedin exception")
			raise Exception("Invalid response %s." % resp['status'])
			 
		request_token = dict(urlparse.parse_qsl(content))
		oauth_token = request_token['oauth_token']
		oauth_token_secret = request_token['oauth_token_secret']
		memcache.set(oauth_token, oauth_token_secret)
		return (oauth_token, oauth_token_secret)

	def get(self) :
	  logging.error("MainPage Get")
	  oauth_token = self.request.get("oauth_token")

	  if not oauth_token:
			self.response.out.write(render_str("login.html"))
	  else:
		logging.error("consumer_key:"+consumer_key + " consumer_secret:" + consumer_secret )
		oauth_token_secret = memcache.get(oauth_token)
		oauth_verifier = self.request.get('oauth_verifier')
		logging.error("verifier: " + oauth_verifier)
		logging.error("oauth_token:"+oauth_token)
		logging.error("oauth_token_secret:" + oauth_token_secret)
		
		consumer = oauth.Consumer(consumer_key, consumer_secret)
		token = oauth.Token(oauth_token, oauth_token_secret)
		token.set_verifier(oauth_verifier)
		
		client = oauth.Client(consumer, token)
			 
		#resp, content = client.request(people_info_url, "GET", "")
		resp, content = client.request(access_token_url, "POST")
		
		access_token = dict(urlparse.parse_qsl(content))
		logging.error(access_token)

		oauth_expires_in = long(access_token['oauth_expires_in'])

		# API call to retrieve profile using access token 
		token = oauth.Token(key=access_token['oauth_token'],secret=access_token['oauth_token_secret'])
		#token = oauth.Token('f2bdafbf-e678-49dc-8930-ec479af8d93b', '5600a5ed-b028-48f1-a3dd-3f9b1f507b52')
		client = oauth.Client(consumer, token)
		
		#resp1, content = client.request("http://api.linkedin.com/v1/people/~")
		
		url = "http://api.linkedin.com/v1/people/~:(id,first-name,last-name,email-address,headline,public-profile-url,picture-url,location:(name),industry,num-connections,positions:(title,start-date,end-date,is-current,company),educations:(school-name,field-of-study,start-date,end-date,degree),date-of-birth)?format=json"
		resp3, content = client.request(url)
		logging.error("content:" + content)
		(person, post_mba_jobs) = linkedinparser.parseContent(content)
		
		if not person:
			self.redirect("/jobc/inviteonly/?fname="+fname)
		
		njobs= len(post_mba_jobs)		
		self.response.out.write(render_str("alumpage.html", fullname= person.fname, pictureUrl= person.picture_url,njobs=njobs, job=post_mba_jobs))

	def post(self):
		logging.error("MainPage Post")
		(oauth_token, oauth_token_secret) = self.setTokenAndSecret()
		url = "%s?oauth_token=%s" % (authorize_url, oauth_token)
 		self.redirect(url)

class InviteOnly(webapp2.RequestHandler) :
	def get(self) :
		fname = self.request.get("fname")
		self.response.out.write(render_str("errorpage.html", fname= fname))

class RealJD(webapp2.RequestHandler) :
	def get(self, job_id):
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = dbmodels.getJob(job_id)
		if not job:
			#throw some error
			self.redirect("/jobc")
		title = job.title 
		company = dbmodels.getCompany(job.company_id)
		companyname = company.company_name
		companyurl = "http://www.linkedin.com/company/" + str(job.company_id)
		author = job.posted_by_text
		authorurl = ''
		if author == "self":
			person = dbmodels.getPerson(job.person_linkedin_id)
			author = person.fname + " (Alumnus of " + person.keyschool.schoolname+")"
			authorurl = "http://www.linkedin.com/profile/view?id="+person.linkedin_id
		date = job.modify_date.strftime('%m/%Y')
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
		self.response.out.write(render_str("onejd.html", title=title, author=author, authorurl = authorurl, companyname=companyname, companyurl=companyurl, date=date, jd=jd, salary=salary, jlove = jlove, jhate= jhate,
			iq = iq, eo = eo, wop = wop, wc = wc, wsg = wsg, wlb=wlb))

class RealJDEdit(webapp2.RequestHandler) :
	def get(self, job_id):
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = dbmodels.getJob(job_id)

		if not job:
			# some error here
			self.redirect("/jobc")
		p= dbmodels.getPerson(job.person_linkedin_id)
		if not page:
			school = "Alum of " + p.keyschool.schoolname
			fullname = p.fname
			location = p.location
			title = job.title
			logging.error("companyid")
			logging.error(job.company_id)
			company = dbmodels.getCompany(job.company_id).company_name
			sdate = job.sdate
			authorcheck = job.posted_by_text
			if (authorcheck == ""):
				authorcheck = "alum"
			logging.error("authorcheck " + authorcheck)
			if sdate:
				sdate = job.sdate.strftime('%m/%Y')
			edate = job.edate.strftime('%m/%Y')
			jd = job.dayinoffice
			jlove = job.jlove
			jhate = job.jhate
			jfunction = job.function
			self.response.out.write(render_str("jd.html", authorcheck = authorcheck, schoolname=school,oneself= fullname, location=location, 
				school=school, title=title, company=company, sdate = sdate, edate = edate, jhate = jhate, jlove=jlove, jd = jd, jfunction = jfunction))
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
			#logging.error("work culter = " + wc)
			self.response.out.write(render_str("jd2.html", wopcheck = wop, iq=iq, eo=eo, abasecheck=alum_base, wccheck = wc, wsgcheck=wsg,
				stockcheck = stock, wlbcheck = wlb,  fsalary=fixed_salary))
        #else:
			# some exception code here
		#	self.redirect("/jobc")

	def post(self, job_id) :
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = dbmodels.getJob(job_id)
		if not job :
			#some error handling here
			self.redirect("/jobc")
		if not page:
			logging.error(self.request.arguments())
			logging.error("jobf "+ self.request.get("jobfunction"))
			job.location = self.request.get("location")
			job.title = self.request.get("title")
			#sdate = job.sdate 
			#edate = job.edate
			job.function = self.request.get("jobfunction")
			job.dayinoffice = self.request.get("jd")
			job.jlove = self.request.get("jlove")
			job.jhate = self.request.get("jhate")
			job.posted_by_text = self.request.get("postas")
			#logging.error("postas " + self.request.get("postas"))
			dbmodels.setJob(jobkey=job.jobkey, job = job)
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
			dbmodels.setJob(jobkey=job.jobkey, job=job)
			job.put()
			url = "/jobc/realjd/"+job_id
			logging.error("url: " + url)
			self.redirect(url)
		else:
			#some error handling here
			# either redirect to first page
			self.redirect("/jobc")