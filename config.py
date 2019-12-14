import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS=False

	#email server details
	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	#list of emails errros get sent out to
	ADMINS = ['testingt101390@gmail.com']
	POSTS_PER_PAGE = 3

#export MAIL_SERVER=smtp.googlemail.com
#export MAIL_PORT=587
#export MAIL_USE_TLS=1
#export MAIL_USERNAME=<your-gmail-username>
#export MAIL_PASSWORD=<your-gmail-password>