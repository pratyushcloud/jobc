import webapp2
import jinja2
import logging
import urlparse 
import time, os
import sys

import linkedinparser
import dbmodels
import encrypt

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
		
USERID_COOKIE = 'user_id'

# Use your API key and secret to instantiate consumer object
consumer_key    =   'gge7se1gxi53' #mentorme api
consumer_secret =   'Vlun3FqAAu7H5Yq3'
#consumer_key= 'yfn26ez21xqb' #localhost
#consumer_secret = '8k478hHqjam3273z' #localhost

logging.getLogger().setLevel(logging.DEBUG)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def getUserFromCookie(cookie_value) :
	if cookie_value:
	  	if encrypt.valid_cookie(cookie_value):
	  		userid = encrypt.getUserId(cookie_value)
	  		person =  dbmodels.Person.get_by_id(userid)#TODO handle case when memcache is flushed and database row itself gets deleted 
	  		return person


class MainPage(webapp2.RequestHandler) :
	
	#def __init__(self):
		#self.username= username

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
	  	cookie_value = self.request.cookies.get(USERID_COOKIE)
	  	person = None
	  	post_mba_jobs = []

	  	if cookie_value:
	  		if encrypt.valid_cookie(cookie_value):
	  			userid = encrypt.getUserId(cookie_value)
	  			logging.error("userid %d" %userid)
	  			person =  dbmodels.Person.get_by_id(userid)#TODO handle case when memcache is flushed and database row itself gets deleted 
	  			logging.error("person")
	  			logging.error(person)
	 			for pjob in person.person_job:
					post_mba_jobs.append((pjob.title, pjob.company.company_name,pjob.jobkey))

	  	oauth_token = self.request.get("oauth_token")
	  	
		if not person:
			if not oauth_token:
				# user has not attempted login yet, show him/her login page
				logging.error("user has not attempted on login in")
				self.response.out.write(render_str("login.html"))
	  		else:
				# user has attempted linkedin login
				logging.error("user has attempted linkedin login")
				consumer = oauth.Consumer(consumer_key, consumer_secret)
				logging.error("oauth_token: " + oauth_token)
				oauth_token_secret = memcache.get(oauth_token)
				oauth_verifier = self.request.get('oauth_verifier')
				token = oauth.Token(oauth_token, oauth_token_secret)
				token.set_verifier(oauth_verifier)
				client = oauth.Client(consumer, token)	 
				resp, content = client.request(access_token_url, "POST")
				access_token = dict(urlparse.parse_qsl(content))
				logging.error(access_token)
				oauth_expires_in = long(access_token['oauth_expires_in'])
				logging.error("oauth expires in %d" %oauth_expires_in)
				# API call to retrieve profile using access token 
				token = oauth.Token(key=access_token['oauth_token'],secret=access_token['oauth_token_secret'])
				url = "http://api.linkedin.com/v1/people/~:(id,first-name,last-name,email-address,headline,public-profile-url,picture-url,location:(name),industry,num-connections,positions:(title,start-date,end-date,is-current,company),educations:(school-name,field-of-study,start-date,end-date,degree),date-of-birth)?format=json"
				client = oauth.Client(consumer, token)
				resp3, content = client.request(url)
				logging.debug("content:" + content)
				(person, post_mba_jobs) = linkedinparser.parseContent(content, oauth_expires_in)
				logging.error(person)
				
				if not person:
					logging.error("print this ")
					self.redirect("/jobc/inviteonly/")
					return

				else:
					logging.error("person.fname " + person.fname)
					self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'%(USERID_COOKIE, encrypt.make_cookie(str(person.key().id()))))
      				self.response.out.write(render_str("alumpage.html", user = person.fname, fullname= person.fname, pictureUrl= person.picture_url,njobs=len(post_mba_jobs), job=post_mba_jobs))

		else: 
			# valid user
			if (person.oauth_expires_in - int(round(time.time()))) < 24*60*60 :
				logging.error("users access token has expired %d - %d" %(person.oauth_expires_in, int(round(time.time()))))
				self.response.out.write(render_str("login.html"))
			else: 
				self.username = person.fname
				self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'%(USERID_COOKIE, encrypt.make_cookie(str(person.key().id()))))
				self.response.out.write(render_str("alumpage.html", user = person.fname, fullname= person.fname, pictureUrl= person.picture_url,njobs=len(post_mba_jobs), job=post_mba_jobs))
      		
	def post(self):
		logging.error("MainPage Post")
		(oauth_token, oauth_token_secret) = self.setTokenAndSecret()
		url = "%s?oauth_token=%s" % (authorize_url, oauth_token)
 		self.redirect(url)

class InviteOnly(webapp2.RequestHandler) :
	def get(self) :
		logging.error("InviteOnly")
		fname = self.request.get("fname")
		self.response.out.write(render_str("errorpage.html", fname= fname))

class Logout(webapp2.RequestHandler) :
	def get(self) :
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'%(USERID_COOKIE, ''))
		self.response.out.write(render_str("logout.html"))


class AboutUs(webapp2.RequestHandler) :
	def get(self) :
		self.response.out.write(render_str("aboutus.html"))

def rating2sentence(rating, category):
	if category not in rating:
		return None
	rating_sentence = ''
	for i in range(0, len(rating[category])) :
		if i == len(rating[category]) - 2:
			rating_sentence= rating_sentence + rating[category][i] + ' and '
		elif i < len(rating[category]) - 1:
			rating_sentence= rating_sentence + rating[category][i] + ', '
		else:
			rating_sentence = rating_sentence + rating[category][i]
	if rating_sentence == '':
	 return None 
	if category == "Notok":
		category = "below average"
	if category == "Ok":
		category = "average"
	if category == "Excellent":
		category = "excellent"
	if category == "Good":
		category = "good"
	rating_sentence = "I would rate this firm as " + category + " in " + rating_sentence + "."
	return rating_sentence

def setRealJDContent(job) :
		params = {}
		params['title'] = job.title 
		company = dbmodels.getCompany(job.company_id)
		params['companyname'] = company.company_name
		params['companyurl'] = "http://www.linkedin.com/company/" + str(job.company_id)
		params['author'] = job.posted_by_text
		params['authorurl'] = ""
		if params['author'] == "self":
			person = dbmodels.getPerson(job.person_linkedin_id)
			params['author'] = person.fname + " (Alumnus of " + person.keyschool.schoolname+")"
			params['authorurl'] = "href=http://www.linkedin.com/profile/view?id="+person.linkedin_id

		params['date'] = job.modify_date.strftime('%m/%Y')
		params['jd'] = job.dayinoffice
		params['salary'] = "Fixed: " + job.fixed_salary + " Variable:" + job.variable_salary + " Stock: " + job.stock 
		params['jlove'] = job.jlove
		params['jhate'] = job.jhate
		params['iq'] = job.interview_question
		params['eo'] = job.exit_option
		rating = {}
		if job.work_opportunity:
			rating[job.work_opportunity] = []
			rating[job.work_opportunity].append('work opportunity')
		if job.work_culture:
			if job.work_culture not in rating:
				rating[job.work_culture] = []
			rating[job.work_culture].append('work culture')
		if job.salary_growth:
			if job.salary_growth not in rating :
				rating[job.salary_growth] = []			
			rating[job.salary_growth].append('salary growth')
		if job.work_life_balance:
			if job.work_life_balance not in rating :
				rating[job.work_life_balance] = []			
			rating[job.work_life_balance].append('work life balance')

		rating_ex = rating2sentence(rating, 'Excellent')
		rating_good = rating2sentence(rating, 'Good')
		rating_ok = rating2sentence(rating, 'Ok')
		rating_notok = rating2sentence(rating, 'Notok')

		rating_sentence = ''
		if not rating_ex and not rating_good and not rating_notok and not rating_ok:
			params['rating_sentence'] = None
		else :
			rating_sentence = "I would rate this firm as "
			count_ratings = len(rating)
			i = 0
			if rating_ex:
				rating_sentence = rating_ex
			if rating_good:
				rating_sentence = rating_sentence + " " + rating_good
			if rating_ok:
				rating_sentence = rating_sentence + " " + rating_ok 
			if rating_notok:
				rating_sentence = rating_sentence + " " + rating_notok
			params['rating_sentence'] = rating_sentence	
		
		params['wc'] = job.work_culture
		params['wsg'] = job.salary_growth
		params['wlb'] = job.work_life_balance
		params['abase'] = job.alum_base
		params['wop'] = job.work_opportunity
		params['jdpage2'] = '/jobc/realjd/_edit/' + job.jobkey+'?page=1'
		params['jdpage1'] = '/jobc/realjd/_edit/' + job.jobkey
		return params

class RealJD(webapp2.RequestHandler) :
	def get(self, job_id):
		page = self.request.get("page")
		if job_id[0] == "/":
			job_id = job_id[1:]
		job = dbmodels.getJob(job_id)

		if not job:
			#throw some error
			self.redirect("/jobc")

		cookie_value = self.request.cookies.get(USERID_COOKIE)
		person = getUserFromCookie(cookie_value)
		params = setRealJDContent(job)
		params['user'] = ""
		if person:
			params['user'] = person.fname
		self.response.out.write(render_str("onejd.html", **params))

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
		fullname = p.fname

		if not page:
			school = p.keyschool.schoolname
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
			self.response.out.write(render_str("jd.html", user = fullname, authorcheck = authorcheck, schoolname=school,oneself= fullname, location=location, 
				school=school, title=title, company=company, sdate = sdate, edate = edate, jhate = jhate, jlove=jlove, jd = jd, jfunction = jfunction))
		elif page == "1":
			iq = job.interview_question
			eo = job.exit_option
			alum_base = job.alum_base
			stock = job.stock
			vsalary = job.variable_salary
			wop = job.work_opportunity
			wc = job.work_culture
			wsg = job.salary_growth
			wlb = job.work_life_balance
			fixed_salary = job.fixed_salary
			#logging.error("work culter = " + wc)
			self.response.out.write(render_str("jd2.html", user = fullname, wopcheck = wop, iq=iq, eo=eo, abasecheck=alum_base, wccheck = wc, wsgcheck=wsg,
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
			dbmodels.addJob2FunctionList(function=job.function, jobkey=job.jobkey)
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
			#job.yearly_bonus = self.request.get("ybonus")
			#job.joining_bonus = self.request.get("jbonus")
			job.variable_salary = self.request.get("vsalary")
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


class ReviewDashboard(webapp2.RequestHandler) :
	def get(self):
		self.response.out.write(render_str("jobfunctions.html"))


def jobbycompany(jobids):
	jobbycompany = {}
	i = 0
	for jid in jobids:
		job = dbmodels.getJob(jid)
		company = dbmodels.getCompany(job.company_id)
		companyname = company.company_name
		jobtitle = job.title
		if not companyname in jobbycompany:
			jobbycompany[companyname] = {}
		jobbycompany[companyname][i] = {}
		jobbycompany[companyname][i]['jobtitle'] = jobtitle
		jobbycompany[companyname][i]['joburl'] = '/jobc/realjd/'+jid
	return jobbycompany

class Marketing(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('Marketing')
		jobbyc =jobbycompany(jobids)
		if not jobbyc or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "Marketing"))
			return
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function="Marketing"))

class IT(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('IT')
		logging.error(jobids)
		jobbyc =jobbycompany(jobids)
		if (not jobbyc) or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "IT"))
			return
		logging.error( jobbyc)
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function = "IT"))

class Sales(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('Sales')
		jobbyc =jobbycompany(jobids)
		if (not jobbyc) or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "Sales"))
			return
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function = "Sales"))

class Finance(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('Finance')
		jobbyc =jobbycompany(jobids)
		if (not jobbyc) or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "Finance"))
			return
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function = "Finance"))

class Consulting(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('Consulting')
		jobbyc =jobbycompany(jobids)
		if (not jobbyc) or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "Consulting"))
			return
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function = "Consulting"))

class SupplyChain(webapp2.RequestHandler):
	def get(self):
		jobids = dbmodels.getJobIdsForFunction('SupplyChain')
		jobbyc =jobbycompany(jobids)
		if (not jobbyc) or len(jobbyc) == 0:
			self.response.out.write(render_str("nojobyet.html",function = "Supply Chain"))
			return
		self.response.out.write(render_str("jddashboard.html", jobbycompany=jobbyc, function = "Supply Chain"))