import json	
import datetime
import logging
import time

import dbmodels
import exceptions

validschools = ['Indian Institute of Management, Calcutta', 'IIM Calcutta', 'Xavier Institute of Management']

def parseContent(content, expires_in) :
		""" content is linkedin json expires_in = expires in n seconds """
		logging.error(content)
		j = json.loads(content)
		post_mba_jobs = []

		nconnection = int(j['numConnections'])
		if (nconnection < 0) : #TODO removing this check as of now
			return (None, [])

		fname = ''
		lname = '' 
		linkedin_id = ''
		industry = ''
		location = ''
		pictureUrl = ''
		publicUrl = '' 

		expires_on = int(round(time.time())) + expires_in


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
		if j.has_key('public-profile-url'):
			publicUrl = j['public-profile-url']

		logging.error("publicUrl = " +publicUrl)
		
		person = dbmodels.Person.all().filter('linkedin_id = ', linkedin_id).get()

		if person:
			#check if there are any updates in fname, lname, picture_url, public_profile_url
			hasChanged = False
			if person.fname != fname:
				person.fname = fname
				hasChanged = True
			elif person.lname != lname:
				person.lname = lname
				hasChanged = True
			elif person.picture_url != pictureUrl:
				person.picture_url = pictureUrl
				hasChanged = True
			elif person.public_profile_url != publicUrl:
				person.public_profile_url = publicUrl
				hasChanged = True
			elif person.oauth_expires_in != expires_on:
				person.oauth_expires_in = expires_on
				hasChanged = True
			if hasChanged:
				person.put()
		if not person: # TODO how to check if something has changed in the profile
			person = dbmodels.Person(fname=fname, lname = lname, linkedin_id=linkedin_id, industry=industry, location=location, picture_url=pictureUrl, public_profile_url=publicUrl)
			if pictureUrl and pictureUrl != '':
				person.picture = dbmodels.fetchPicture(pictureUrl)
			person.oauth_expires_in = expires_in
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

		logging.error("school_list")
		logging.error(school_list)

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
				logging.error("school name " + schoolName)
				if schoolName in validschools:
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
		
		if not isvalidSchool:
			#self.redirect("/jobc/inviteonly/?fname="+fname)
			return (None, [])

		if (eyear_validSchool - syear_validSchool <= 1):
			# Guy must have done certification or short term course
			#self.redirect("/jobc/inviteonly/?fname="+fname)
			return (None, [])


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
			company_name = '?'
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
				logging.error("company_name $" +company_name+"$")
				company = dbmodels.Company(company_id=num(company_id), company_name=company_name, company_industry=company_industry, company_size=company_size, company_type=company_type)
				company.put()

			if job.has_key('isCurrent'):
				isCurrent = bool(job['isCurrent'])
			if job.has_key('title'):
				title = job['title']

			jobkey = dbmodels.jobkey(linkedin_id = person.linkedin_id, company_id=company.company_id, eDate=eDate)
			logging.error("eDate ")
			logging.error(eDate)
			jobdb = dbmodels.Job.all().filter('jobkey = ', jobkey).get()
			if not jobdb:
				jobdb = dbmodels.Job(title=title, person=person, company=company, person_linkedin_id = person.linkedin_id, company_id = company.company_id, sdate = sDate, edate=eDate, jobkey=jobkey)
				jobdb.put()
			#print '%s - %s (%s) %s %s' %(company_name, company_industry, company_id, company_size, company_type)
			#print '%s (%s - %s) %s \n' %(title, sDate, eDate, isCurrent)
		
		for pjob in person.person_job:
			post_mba_jobs.append((pjob.title, pjob.company.company_name,pjob.jobkey))
		
		return (person, post_mba_jobs)


def num (s):
    try:
        return int(s)
    except ValueError:
        return 0
	