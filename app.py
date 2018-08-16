from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask (__name__)

app.config['SECRET_KEY']='qwerty123'

# Config Mysql
app.config['SQLALCHEMY_DATABASE_URI']= 'mysql://root:''@localhost/myflaskapp'
db =SQLAlchemy(app)

# CREATE A DBMODEL TO LINK TO EXISTING USERS table in DATABASE
class Users(db.Model):
    __tablename__ ='users'
    id =db.Column('id', db.Integer, primary_key=True)
    name =db.Column('name', db.Unicode,)
    email =db.Column('email', db.Unicode,)
    username =db.Column('username', db.Unicode,)
    password =db.Column('password', db.Unicode,)
    register_date =db.Column('register_date', db.DateTime,)

    # Create constructor to insert data into table
    def __init__(self, name, email, username, password,):
        self.name= name
        self.email= email
        self.username= username
        self.password= password
   
# CREATE A DBMODEL TO LINK TO EXISTING Articles in  DATABASE
class Articles(db.Model):
    __tablename__ ='articles'
    id =db.Column('id', db.Integer, primary_key=True)
    title =db.Column('title', db.Unicode,)
    body =db.Column('body', db.Unicode,)
    author = db.Column('author', db.Unicode)
    create_date =db.Column('create_date', db.DateTime,)

    # Create constructor to insert data into table
    def __init__(self, title, body, author):
        self.title= title
        self.body= body
        self.author =author
   


# Articles = Articles()

# INDEX 
@app.route('/')
def index():
  return render_template('home.html')

# ABOUT
@app.route('/about')
def about():
  return render_template('about.html')

# ARTICLES
@app.route('/articles')
def articles():
  
    # Get all articles
    articles = Articles.query.all()

    if articles:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    
    # Close Db connection
    db.session.close()

# SINGLE ARTICLE
@app.route('/article/<string:id>/')
def article(id):

    # Get single article by  ID filter
    article = Articles.query.filter_by(id=id).first()
    return render_template('article.html', article=article)

# FORM TO REGISTER USER WITH WTFORMS AND VALIDATORS
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=4, max=50), validators.DataRequired()])
    username = StringField('Username',[validators.Length(min=4, max=25), validators.DataRequired()])
    email = StringField('Email',[validators.Length(min=6, max=50), validators.DataRequired()])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
        ])
    confirm = PasswordField('Confirm Password')

# REGISTER A USER TO DATABASE
@app.route('/register', methods= ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))

            # initiate and excute commands
            new_user =  Users(name, email, username, password)
            db.session.add(new_user)
            db.session.commit()
            db.session.close()

            flash('You are now registered and log in', 'success')
            return redirect (url_for('dashboard'))
    return render_template('register.html', form=form)

# LOGIN A USER VERIFY FROM DATABASE
@app.route('/login', methods= ['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form fields
        post_username= str(request.form['username'])
        post_password = str(request.form['password'])

        # Session = sessionmaker(bind=engine)
        # s = Session()
        user = Users.query.filter_by(username =post_username).first()

        if user:
            if sha256_crypt.verify(post_password, user.password):
                # Passed and save details in flask session
                session['logged_in']= True
                session['username']=post_username

                flash('You are log in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
                # Close connection to db
            db.session.close()

        else:
            error = 'Username Not Found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# CHECK IF USER LOGGED IN TO DENY ACCESS TO ROUTES
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#LOGOUT
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are Logged out', 'success')
    return redirect(url_for('login'))

# DASHBOARD
@app.route('/dashboard')
@is_logged_in
def dashboard():

    # Get all articles
    articles = Articles.query.all()

    if articles:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    
    # Close Db connection
    db.session.close()

    


# ARTCILE FORM
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    body = TextAreaField('Body',[validators.Length(min=20,)])

# ADD ARTICLE
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data 
        body  = form.body.data
        author = session['username']

        new_article =  Articles(title, body, author)
        db.session.add(new_article)
        db.session.commit()
        db.session.close()
        
        flash ('Articles Created', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_article.html', form=form)


# EDIT ARTICLE
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):

    # Get article by id
    article = Articles.query.filter_by(id=id).first()

    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article.title
    form.body.data = article.body

    if request.method == 'POST' and form.validate():
        title = str(request.form['title'])
        body  = str(request.form['body'])
        author = session['username']

        #Assign new article connetent to existing article being instantiated already
        article.title= title
        article.body= body
        db.session.commit()
        db.session.close()
        
        flash ('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_article.html', form=form)

# DEELETE ARTICLE
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Get artcle by id from Database
    article = Articles.query.filter_by(id=id).first()

    #Delete article from database
    db.session.delete(article)
    db.session.commit()
    db.session.close()

    #Notify for delete item.
    flash ('Article Deleted', 'danger')
    return redirect(url_for('dashboard'))






if __name__ == '__main__':
    app.run(debug=True)

