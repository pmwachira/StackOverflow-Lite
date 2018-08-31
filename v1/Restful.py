from functools import wraps

import psycopg2
import psycopg2.extras
from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify, make_response
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

import jwt
import datetime

app = Flask(__name__, template_folder="../static/templates")

app.config['JWT_SECRET_KEY'] = 'my very unsecured secret key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)



@app.route('/')
def home():
    return render_template('home.html')


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()

        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            data = jwt.decode(token, app.config['SECRET_KEY'])
            user = session['username']

            if user != data['sub']:
                raise RuntimeError('User not found')
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password_candidate = request.form['password']
        conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

        try:

            cur = conn.cursor()
            cur.execute("SELECT user_id,password FROM users WHERE user_name = %s", [username])

            if cur.rowcount > 0:
                user={

                }

                cur_values = cur.fetchone()

                user_id=cur_values[0]
                password=cur_values[1]

                if sha256_crypt.verify(password_candidate, password):

                    session['logged_in'] = True
                    session['username'] = username

                    flash('Hi ' + username, 'success')
                    cur.close()
                    # implement tokens
                    token = jwt.encode({
                        'sub': username,
                        'iat': datetime.datetime.utcnow(),
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                        app.config['SECRET_KEY'])
                    return jsonify({'token': token.decode('UTF-8')})


                    ##return redirect(url_for('dashboard',token=token))


                else:

                    error = 'Invalid login'
                    return render_template('login.html', error=error)
            else:
                cur.close()

                error = 'User not found'
                return render_template('login.html', error=error)

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)

        finally:
            if conn is not None:
                conn.close()

    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):

        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap





@app.route('/dashboard')
##@is_logged_in
@token_required_
def dashboard():
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()
    cur.close()
    if cur.rowcount > 0:

        return render_template('dashboard.html', articles=articles)

    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Username', [validators.Length(min=30)])

@app.route('/questions',methods=['POST'])
@is_logged_in
def add_question():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        question = form.question.data
        ##todo get user id from session
        ##session['username']
        ##user_id=session['id']
        user_id=1
        conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

        try:

            cur = conn.cursor()
            cur.execute("INSERT INTO questions (question,user_id) VALUES (%s,%s)",
                        (question,user_id ))

            conn.commit()

            cur.close()

            flash('Question created', 'success')

            return redirect(url_for('dashboard'))

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)

        finally:
            if conn is not None:
                conn.close()

    return render_template('add_article.html', form=form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM articles WHERE id=%s", id)

    article = cur.fetchone()

    cur.close()
    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        try:

            cur = conn.cursor()
            cur.execute("UPDATE articles SET title = %s, body= %s WHERE id=%s", (title, body, id))

            conn.commit()

            cur.close()

            flash('Article updated', 'success')

            return redirect(url_for('dashboard'))

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)

        finally:
            if conn is not None:
                conn.close()

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_article(id):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("UPDATE articles SET deleted = 1 WHERE id=%s", id)

    conn.commit()

    cur.close()

    flash('Article deleted', 'success')

    return redirect(url_for('dashboard'))


@app.route('/questions/<string:questionId>/answers/<string:answerId>', methods=['GET', 'POST'])
@is_logged_in
def edit_answer(answerId):
    ##todo get current session userid
    session_user_id=1
    ##get questionid
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT question_id FROM answers WHERE answer_id=%s",answerId)

    question_id = cur.fetchone()
    cur.close()
    ##getquestion owner
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT user_id FROM questions WHERE question_id=%s", question_id)

    user_id = cur.fetchone()
    cur.close()
    ##mark as answer as preffered
    if session_user_id==user_id:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET preffered=1 WHERE answer_id=%s", answerId)
        conn.commit()
        cur.close()
        flash('Answer marked as prefferred', 'success')

        return redirect(url_for('dashboard'))
    else:
        ##edit the answer
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET answer=%s WHERE answer_id=%s", (answer,answerId))
        conn.commit()
        cur.close()

        flash('Answer Edited', 'success')

        return redirect(url_for('dashboard'))




@app.route('/logout')
@is_logged_in
def logout():
    name = session['username']
    session.clear()
    flash('You have logged out, see you soon ' + name, 'success')
    return redirect(url_for('login'))


@app.route('/questions',methods=['GET'])
def questions():
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM questions")

    articles = cur.fetchall()

    if cur.rowcount > 0:
        cur.close()
        return render_template('questions.html', questions=articles)

    else:
        cur.close()
        msg = 'No articles found'
        return render_template('questions.html', msg=msg)


@app.route('/questions/<string:id>/')
def question(id):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM questions WHERE id=%s", [id])

    question = cur.fetchone()

    if cur.rowcount > 0:
        cur.close()
        return render_template('question.html', question=question)

    else:
        cur.close()
        msg = 'No articles matching found'
        return render_template('question.html', msg=msg)


@app.route('/questions/<string:questionId>/answers')
def answer(questionId):
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        answer = form.answer.data
        ##todo get userid from session
        user_id=1

        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
        try:

            sql = """INSERT INTO answer(answer,question_id,user_id) VALUES (%s,%s,%s) RETURNING answer_id"""
            cur = conn.cursor()

            cur.execute(sql, (answer, questionId,user_id    ))

            answer_id = cur.fetchone()[0]

            conn.commit()

            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)
        finally:
            if conn is not None:
                conn.close()
# @app.route('/questions/<questionId>/answers/<answerId>')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/auth/signup', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        show = add_user(name, email, username, password)
        flash('Login using username: ' + str(show)+" and your password", 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


def add_user(name, email, username, password):
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    try:

        sql = """INSERT INTO users(user_name,user_email,password) VALUES (%s,%s,%s) RETURNING user_id"""
        cur = conn.cursor()

        cur.execute(sql, (name, email, password))

        user_id = cur.fetchone()[0]

        conn.commit()

        cur.close()

    except(Exception, psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return name


if __name__ == '__main__':
    app.secret_key = 'my very unsecured secret key'
    app.run(host='0.0.0.0', port=5000, debug=True)
