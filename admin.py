#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request, make_response, render_template,session,redirect,url_for,flash
import pymysql as py
import os
import webbrowser
import cv2
import time
from urllib.request import Request,urlopen
import ast
#connection with mysql
conn = py.connect(host="localhost", user="root", passwd="your_db_password", db="your_db_name")
cur=conn.cursor()
#initializing flask
app = Flask(__name__)

#for first index page
@app.route('/')
def index():
	session['logged_in']=False
	return render_template("index.html")

"""def home():
    if not session.get('logged_in'):
        return render_template('admin.html')
    else:
        return "Hello Boss!"
"""
#for student login page
@app.route('/student')
def student():
	return render_template("student.html")

#for admin login
@app.route('/admin')
def admin():
	if session['logged_in']==True:
		return render_template("student_detail.html")
	else:
		return render_template("admin.html")

#checking the username and password from database and then login 
@app.route('/admin_login', methods=['POST'])
def admin_login():
	pasw=request.form['password']
	usr=request.form['username']
#before that make a table for admin having two must coloumn
	cur.execute("SELECT * from "your_admin_table_name" where ad_name='" + usr + "' and ad_pass='" + pasw + "'")
	data = cur.fetchone()
	if data is None:
		print("in else block")
		condition=1
		login_error="!!!!  Username or Password is Incorrect  !!!!"
		return render_template("admin.html",l_error=login_error,con=condition)
	else:
		lgin="!! you Logged in successfully !!"
		return render_template("student_detail.html",lgin=lgin,admin_user=data[2])
	'''if usr == 'admin' and pasw == 'password':
		session['logged_in']=True
		return render_template("student_detail.html")
	else :
		print("in else block")
		condition=1
		login_error="!!!!  Username or Password is Incorrect  !!!!"
		return render_template("admin.html",l_error=login_error,con=condition)
	'''

#for filling the details of student in database
@app.route('/studentFidding', methods=['POST'])
def studentFidding():
	cur = conn.cursor()
	s_name = request.form['s_name']
	s_id = request.form['s_id']
	email = request.form['email']
	dob = request.form['dob']
#make folder in static with name adimages
	image = "static/adimages/"+s_id+".jpg"
	os.system('sshpass -p "your_password" scp '+image+' "aws_instance_name"@aws_public_ip:')
	values='''
	{
	"image":"your aws account image path url",
	"subject_id": "%s",
	"gallery_name":"your_gallery_name_for_kairos"
	}'''%(s_id+".jpg",s_name)
	values=bytes(values,'utf-8')
	kairos(values)
	#cur.execute("INSERT INTO `your_table_name` (`sr`, `s_name`, `s_id`, `email`, `dob`, `image`) VALUES (NULL, '"+s_name+"', '"+s_id+"', '"+email+"', '"+dob+"', 'NOT NULL');")

#before that make table into database and make coloumns shows below
	cur.execute("INSERT INTO `your_table_name` (`s_name`, `s_id`, `email`, `dob`, `image`) VALUES (%s,%s,%s,%s,%s)",(s_name,s_id,email,dob,image))      
	filledCheck=conn.commit()
	if filledCheck == None:
		succ="successfully Enrolled"
	else :
		succ="!! Network Error try again !!"
	return render_template("student_detail.html",succ_message=succ)


#student login
@app.route('/student_login', methods=['POST'])
def student_login():
	usr=request.form['sname']
	pasw=request.form['spass']
	cur.execute("SELECT * from 'your_table_name' where s_name='" + usr + "' and s_id='" + pasw + "'")
	data = cur.fetchone()
	if data is None:
		print("in else block")
		condition=1
		login_error="!!!!  Username or Password is Incorrect  !!!!"
		return render_template("student.html",l_error=login_error,con=condition)
	else:
		lgin="!! you Logged in successfully !!"
		return render_template("face_recognition.html",sname=usr,spass=pasw)

#camera for clicking the pic of student while enrollment
@app.route('/camera',methods=['POST'])
def camera():
	s_name = request.form['s_name']
	s_id = request.form['s_id']
	email = request.form['email']
	dob = request.form['dob']
	imagename="static/adimages/"+s_id+".jpg"
	cap=cv2.VideoCapture(0)
	while cap.isOpened():
		status,frame=cap.read()
		cv2.imshow("Press C For Capture",frame)
		if cv2.waitKey(1) & 0xff==ord('c'):
			cv2.imwrite(imagename,frame)
			time.sleep(8)
			break
	cap.release()
	cv2.destroyAllWindows()
	return render_template("confirm.html",s_name=s_name,s_id=s_id,email=email,dob=dob,image=imagename)

#student face recognition with the help of karios and aws
@app.route('/student_recog',methods=['POST'])
def student_recog():
	sname = request.form['sname']
	spass = request.form['spass']
	imagename="static/stimages/"+spass+".jpg"
	cap=cv2.VideoCapture(0)
	while cap.isOpened():
		status,frame=cap.read()
		cv2.imshow("Press C For Capture",frame)
		if cv2.waitKey(1) & 0xff==ord('c'):
			cv2.imwrite(imagename,frame)
			os.system('sshpass -p 'your_instance_password_of_aws' scp '+imagename+' instance_name@instance_public_ip:recog/')
			break
	cap.release()
	cv2.destroyAllWindows()
	values = '''
	{
	"image": "image_url_for_karios",
	"gallery_name": "your_gallery_name"
	}
	'''%(spass+".jpg")
	values=bytes(values,'utf-8')
	headers = {
	'Content-Type': 'application/json',
	'app_id': 'app_id_of_kairos',
	'app_key': 'app_key_for_kairos'
	}
	output = Request('https://api.kairos.com/recognize', data=values, headers=headers)
	response_body = urlopen(output).read()
	response_body=response_body.decode("utf-8")
	response_body=ast.literal_eval(response_body)
	user=response_body['images'][0]['candidates'][0]['subject_id']
	result=check_student(user,sname)
	if result==True:
		return render_template('hello.html',user=sname)
	else:
		return render_template('hello.html',user="Not "+sname)


def kairos(values):
	protocol={
	'Content-Type':'application/json',
	'app_id':'your_app_id',
	'app_key':'your_app_key_of_kairos'
	}
	rp=Request('https://api.kairos.com/enroll',data=values,headers=protocol)	
	response_body=urlopen(rp).read()

def check_student(user,sname):
	if str(user).lower()==str(sname).lower():
		return True
	else:
		return False



if __name__ == '__main__':
	app.secret_key = os.urandom(12)
	webbrowser.open_new_tab("http://127.0.0.1:5000/")
	app.run("127.0.0.1",5000,debug = True)
