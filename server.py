from flask import Flask, request, render_template, redirect, session, flash, url_for
from mysqlconnection import MySQLConnector
from datetime import datetime
from flask_bcrypt import Bcrypt
import re


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')

app = Flask(__name__)
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'the_wall')
app.secret_key = 'abcde12345fghij'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    passFlag = True
    if len(request.form['first_name']) < 1:
        flash('Error! Invalid first name!', 'error')
        passFlag = False
    elif not request.form['first_name'].isalpha():
        flash('First name has non-alpha character!', 'error')
        passFlag = False
    if len(request.form['last_name']) < 1:
        flash('Error! Invalid last name!', 'wrong')
        passFlag = False
    elif not request.form['last_name'].isalpha():
        flash('Last name has a non-alpha character!', 'error')
        passFlag = False
    if len(request.form['email']) < 1:
        flash('Error! Invalid email', 'error')
        passFlag = False
    elif not EMAIL_REGEX.match(request.form['email']):
        flash('Invalid email format!', 'error')
        passFlag = False
    if len(request.form['password']) < 6:
        flash('Password must contain at least 6 characters!', 'error')
        passFlag = False
    if request.form['password'] != request.form['confirm_password']:
        flash('Password does not match!', 'error')
        passFlag = False

    if passFlag == True:
        flash('Registration successful! Please log in.', 'success')
        password = request.form['password']
        pw_hash = bcrypt.generate_password_hash(password)
        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'pw_hash': pw_hash,
        }
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW(), NOW())"
        mysql.query_db(query, data)
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)
    if not user:
       flash("Please enter valid email.", 'login_error')
       return redirect ('/')
    elif bcrypt.check_password_hash(user[0]['password'], password):
        session['user_id'] = user[0]['id']
        return redirect('/wall')
    else:
        flash('Invalid login!', 'login_error')
        return render_template('index.html')

@app.route('/wall', methods=['GET'])
def wall():
    query = 'SELECT users.first_name, users.last_name, messages.message_content, messages.id, messages.created_at FROM messages JOIN users ON messages.user_id=users.id'
    comment_query = 'SELECT comments.users_id, comments.comment_content, comments.message_id, users.first_name, users.last_name FROM comments INNER JOIN users ON users.id=comments.users_id INNER JOIN messages ON messages.id = comments.message_id'
    messages = mysql.query_db(query)
    comments = mysql.query_db(comment_query)
    return render_template('wall.html', messages=messages, comments=comments)

@app.route('/makeMessage', methods=['POST'])
def makeMessage():
    data = {
            'currentsession': session['user_id'],
            'user_message': request.form['add_message']
            }
    query = 'INSERT INTO messages (user_id, message_content, created_at, updated_at) VALUES (:currentsession, :user_message, NOW(), NOW())'
    mysql.query_db(query,data)
    return redirect('/wall')

@app.route('/addcomment/<id>', methods=['POST'])
def addComment(id):
    data = {
            'specific_id': id,
            'currentsession': session['user_id'],
            'comment_content': request.form['addcomment']
           }
    query = 'INSERT INTO comments (message_id, users_id, comment_content, created_at, updated_at) VALUES (:specific_id, :currentsession, :comment_content, NOW(), NOW())'
    comments = mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/logout', methods=['POST'])
def reset():
    session.clear()
    return redirect('/')

app.run(debug=True)
