from functools import wraps

import psycopg2
import psycopg2.extras
from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

app = Flask(__name__, template_folder="templates")


# app= connexion.App(__name__,specification_dir='./')


@app.route('/')
def home():
    return render_template('home.html')


# @app.route('/auth/signup')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password_candidate = request.form['password']
        conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

        try:

            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE user_name = %s", [username])

            if cur.rowcount > 0:
                cur.close()

                password = cur.fetchone()[0]
                if sha256_crypt.verify(password_candidate, password):
                    session['logged_in'] = True
                    session['username'] = username

                    flash('Hi ' + username, 'success')
                    return redirect(url_for('dashboard'))

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


# @app.route('/auth/login')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route('/dashboard')
@is_logged_in
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


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

        try:

            cur = conn.cursor()
            cur.execute("INSERT INTO articles (title,body,author) VALUES (%s,%s,%s)",
                        (title, body, session['username']))

            conn.commit()

            cur.close()

            flash('Article created', 'success')

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


@app.route('/logout')
@is_logged_in
def logout():
    name = session['username']
    session.clear()
    flash('You have logged out, see you soon ' + name, 'success')
    return redirect(url_for('login'))


@app.route('/questions')
def questions():
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if cur.rowcount > 0:
        cur.close()
        return render_template('questions.html', questions=articles)

    else:
        cur.close()
        msg = 'No articles found'
        return render_template('questions.html', msg=msg)


@app.route('/question/<string:id>/')
def question(id):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM articles WHERE id=%s", [id])

    question = cur.fetchone()

    if cur.rowcount > 0:
        cur.close()
        return render_template('question.html', question=question)

    else:
        cur.close()
        msg = 'No articles matching found'
        return render_template('question.html', msg=msg)


# @app.route('/questions')
# @app.route('/questions/<questionId>')
# @app.route('/questions/<questionId>/answers')
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        show = add_user(name, email, username, password)
        flash('You are now registered' + str(show), 'success')
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

    return user_id


if __name__ == '__main__':
    app.secret_key = 'my very unsecured secret key'
    app.run(host='0.0.0.0', port=5000, debug=True)
