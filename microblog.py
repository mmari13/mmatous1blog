from app import app, db
from app.models import User, Post

#decorator that registers the funciton as a shell context function
#when flask shell runs it will invoke htis and register items returned by it in the 
#shell session
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}