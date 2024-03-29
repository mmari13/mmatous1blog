from flask import render_template, flash, redirect, url_for,  request
from app import app
from app.forms import LoginForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from app.forms import RegistrationForm
from app import db
from datetime import datetime 
from app.forms import PostForm


from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email

from app.forms import ResetPasswordRequestForm

from app.models import Post, User

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
	return render_template('index.html', title='Home', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
	#doesn let logged in user to get to the login form
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	
	form = LoginForm()
	if form.validate_on_submit():
		#filter returns the object have the matching username and returns
		#the user object .first if it exists or None if doesnt
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))

		#login_user comes from flask login 
		login_user(user, remember=form.remember_me.data)

		#redirect to next page 
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page =url_for('index')
		return redirect(next_page)
	return render_template('login.html',title='Sign In', form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user= User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Congratulations, you are now a registed user!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form = form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,next_url=next_url, prev_url=prev_url)
 
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
	#if submit was clicked 
    if form.validate_on_submit(): 
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
	#if requesting the page for the first time
	#retrieve current values from db
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
	#if something wrong then write nothing ie request.methon="POST"
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('explore', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('explore', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template("index.html", title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

#project addition
#also changed the _post.html to only show the delete link when appropriate
@app.route("/delete/<postid>")
@login_required
def delete_post(postid):
    if current_user.is_authenticated:
        post = Post.query.filter_by(id = postid).first()
        if post.user_id == current_user.id:
            #usr = post.user_id
            usrname = current_user.username
            db.session.delete(post)
            db.session.commit()
            flash('Post deleted!')
            #i would like to return back to whatever page the delete was clicked
            #but I couldn't figure out how 
            #maybe I would need to pass in the url as well as the post id?
            return redirect(url_for('user', username=usrname))
        flash("not allowed")
    
    return redirect(url_for('index'))
    
@app.route("/edit/<postid>", methods=['GET', 'POST'])
@login_required
def edit_post(postid):
    if current_user.is_authenticated:
        post = Post.query.filter_by(id = postid).first()
        form = PostForm()
        if post and post.user_id == current_user.id:
            if form.validate_on_submit(): 
                post.body=form.post.data
                db.session.commit()
                return redirect(url_for('user',username = current_user.username))
            else:
                form.post.data = post.body
                db.session.commit()
                flash('Your changes have been saved.')
                return render_template('edit_post.html', postid = postid, form =form)
    flash("not allowed")
    return redirect(url_for('user', username=current_user.username))


    
    