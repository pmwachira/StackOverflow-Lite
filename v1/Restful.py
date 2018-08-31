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

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):

        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap

@app.route('/')
def home():
    return render_template('home.html')

##route 1
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

                cur_values = cur.fetchone()

                user_id=cur_values[0]
                password=cur_values[1]

                if sha256_crypt.verify(password_candidate, password):

                    session['logged_in'] = True
                    session['username'] = username
                    session['user_id']=user_id

                    flash('Hi ' + username, 'success')
                    cur.close()
                    # implement tokens
                    token = jwt.encode({
                        'sub': username,
                        'iat': datetime.datetime.utcnow(),
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                        app.config['SECRET_KEY'])
                    return jsonify({'token': token.decode('UTF-8'),'message':'Log in success'})

                    ##redirect url
                    ##return redirect(url_for('dashboard',token=token))


                else:
                    ##redirect url
                    ##error = 'Invalid login'
                    ##return render_template('login.html', error=error)
                    return jsonify({ 'message': 'Log in failed'})
            else:
                cur.close()

                ##error = 'User not found'
                ##return render_template('login.html', error=error)

                return jsonify({'message': 'Log in failed<User not found>'})

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)

        finally:
            if conn is not None:
                conn.close()

    ##return render_template('login.html')
    return

##route 2
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
    ##if request.method == 'POST' and form.validate():
    if request.method == 'POST':
        ##from form
        # name = form.name.data
        # email = form.email.data
        #password_recieved=form.password.data
        #username = form.username.data
        ##from request
        name=request.form['name']
        email=request.form['email']
        username = request.form['username']
        password_recieved=request.form['password']

        password = sha256_crypt.encrypt(str(password_recieved))

        check = checkifemailexists(email)

        if not check:
            return jsonify({'message': 'Sign up fail,User with given email exists'})

        else:
            show = add_user(name, email, username, password)

            return jsonify({'message': 'Sign up success,Please log in with your credentials'})

        #flash('Login using username: ' + str(show)+" and your password", 'success')
        #return redirect(url_for('login'))

    #return render_template('register.html', form=form)


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

def checkifemailexists(email):
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    try:

        sql = """SELECT * FROM users WHERE user_email=%s"""
        cur = conn.cursor()

        cur.execute(sql, (email))

        if cur.rowcount > 0:
            return True

        cur.close()
        return False

    except(Exception, psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

##route 3
@app.route('/questions',methods=['POST'])
def add_question():
    form = ArticleForm(request.form)
    # if request.method == 'POST' and form.validate():
    #     question = form.question.data

    if request.method == 'POST':
        question = request.form['question']

        ##todo get user id from session
        #user_id=session['user_id']
        user_id=1

        conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

        try:

            cur = conn.cursor()
            cur.execute("INSERT INTO questions (question,user_id) VALUES (%s,%s)",
                        (question,user_id ))

            conn.commit()

            cur.close()

            ##flash('Question created', 'success')

            ##return redirect(url_for('dashboard'))
            return jsonify({'message': 'Question created'})

        except(Exception, psycopg2.DatabaseError) as error:
            print (error)

        finally:
            if conn is not None:
                conn.close()

    ##return render_template('add_article.html', form=form)


##route 4
@app.route('/questions',methods=['GET'])
def questions():
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM questions")



    questions = cur.fetchall()


    if cur.rowcount > 0:
        cur.close()
        return jsonify({'Questions asked': questions})
        #return render_template('questions.html', questions=questions)

    else:
        cur.close()
        #msg = 'No questions found'
        #return render_template('questions.html', msg=msg)
        return jsonify({'message': 'No questions asked yet'})

##route 5
@app.route('/questions/<string:questionId>', methods=['DELETE'])
def delete_question(questionId):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT user_id FROM questions  WHERE question_id=%s", questionId)
        question_owner = cur.fetchone()[0]
        cur.close()
        user_id = 1
        #user_id=session['user_id']
        if user_id==question_owner:

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute("DELETE FROM questions  WHERE question_id=%s", questionId)

            conn.commit()
            cur.close()
            return jsonify({'message': 'Selected question deleted'})

        # flash('Article deleted', 'success')

        # return redirect(url_for('dashboard'))

        else:
            return jsonify({'message': 'Only question owner can perform this action'})
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({'message': 'Selected question not found'})

    finally:
        if conn is not None:
            conn.close()

#route 6
@app.route('/questions/<string:questionId>/answers',methods=['POST'])
def answer(questionId):
    # form = ArticleForm(request.form)
    # if request.method == 'POST' and form.validate():
    #     answer = form.answer.data
    if request.method == 'POST':
        answer = request.form['answer']

        ##todo get userid from session
        user_id=1
        # user_id=session['user_id']

        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
        try:

            sql = """INSERT INTO answers(answer,question_id,user_id) VALUES (%s,%s,%s)"""
            cur = conn.cursor()

            cur.execute(sql, (answer, questionId,user_id))

            conn.commit()

            cur.close()
            ##add count in questions table
            ##get current answers
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT answer_count FROM questions WHERE question_id=%s", questionId)

            answered_times = cur.fetchone()[0]
            cur.close()
            ##add answer count
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("UPDATE questions SET answer_count=%s WHERE question_id=%s", ((answered_times + 1), questionId))
            conn.commit()
            cur.close()
            return jsonify({'message': 'Your answer has been posted'})

        except(Exception, psycopg2.DatabaseError) as error:
            return jsonify({'error': error})
        finally:
            if conn is not None:
                conn.close()

#route 7
##error in route
#@app.route('/questions/<string:questionId>/answers/<string:answerId>', methods=['PUT'])
@app.route('/questions/answers/<string:answerId>', methods=['PUT'])
def edit_answer(answerId):
    ##todo get current session userid
    #session_user_id=session['user_id']
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

    user_id = cur.fetchone()[0]
    cur.close()
    ##mark as answer as preffered
    if session_user_id==user_id:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET preffered=1 WHERE answer_id=%s", answerId)
        conn.commit()
        cur.close()
        #flash('Answer marked as prefferred', 'success')
        return jsonify({'message': 'Answer marked as preferred'})

        return redirect(url_for('dashboard'))
    else:
        ##edit the answer
        answer_new = request.form['answer_new']
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET answer=%s WHERE answer_id=%s", (answer_new,answerId))
        conn.commit()
        cur.close()

        return jsonify({'message': 'Answer successfully edited'})

        #flash('Answer Edited', 'success')

        #return redirect(url_for('dashboard'))


#route 8
@app.route('/questions/answers/<string:answerId>/upvote', methods=['PUT'])
def upvote_answer(answerId):
    ##todo get current session userid
    #session_user_id=session['user_id']
    session_user_id=2
    ##get questionid
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT user_id FROM answers WHERE answer_id=%s",answerId)

    answer_owner = cur.fetchone()[0]
    cur.close()

    ##owner can not upvote own answer
    if session_user_id==answer_owner:
        return jsonify({'message': 'Owner of answer can not upvote own answer'})
    else:
        ##get current upvotes
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT upvoted FROM answers WHERE answer_id=%s", answerId)

        upvoted_times = cur.fetchone()[0]
        cur.close()
        ##add upvotes
        if upvoted_times==None:
            upvoted_times=0

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET upvoted=%s WHERE answer_id=%s", ((upvoted_times+1),answerId))
        conn.commit()
        cur.close()



        return jsonify({'message': 'Answer upvoted'})

        #flash('Answer Edited', 'success')

        #return redirect(url_for('dashboard'))

#route 9
@app.route('/questions/answers/<string:answerId>/downvote', methods=['PUT'])
def downvote_answer(answerId):
    ##todo get current session userid
    #session_user_id=session['user_id']
    session_user_id=2
    ##get questionid
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT user_id FROM answers WHERE answer_id=%s",answerId)

    answer_owner = cur.fetchone()[0]
    cur.close()

    ##owner can not upvote own answer
    if session_user_id==answer_owner:
        return jsonify({'message': 'Owner of answer can not upvote own answer'})
    else:
        ##get current upvotes
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT upvoted FROM answers WHERE answer_id=%s", answerId)

        upvoted_times = cur.fetchone()[0]
        cur.close()
        ##add upvotes
        if upvoted_times==None:
            upvoted_times=0


        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("UPDATE answers SET upvoted=%s WHERE answer_id=%s", ((upvoted_times-1),answerId))
        conn.commit()
        cur.close()



        return jsonify({'message': 'Answer downvoted'})

#route 10
@app.route('/answers/<string:answerId>/comments',methods=['POST'])
def add_comment(answerId):
    # form = ArticleForm(request.form)
    # if request.method == 'POST' and form.validate():
    #     answer = form.answer.data
    if request.method == 'POST':
        comment = request.form['comment']

        ##todo get userid from session
        user_id=1
        # user_id=session['user_id']

        conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
        try:

            sql = """INSERT INTO comments(comment_,answer_id,comment_user) VALUES (%s,%s,%s)"""
            cur = conn.cursor()

            cur.execute(sql, (comment, answerId,user_id))

            conn.commit()

            cur.close()
            return jsonify({'message': 'Your comment has been posted'})

        except(Exception, psycopg2.DatabaseError) as error:
            return jsonify({'error': error})
        finally:
            if conn is not None:
                conn.close()

##route 11
@app.route('/user/<string:userId>/questions',methods=['GET'])
def questions_by_user(userId):
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM questions WHERE user_id=%s",userId)

    questions = cur.fetchall()


    if cur.rowcount > 0:
        cur.close()
        return jsonify({'Questions asked by user': questions})
        #return render_template('questions.html', questions=questions)

    else:
        cur.close()
        #msg = 'No questions found'
        #return render_template('questions.html', msg=msg)
        return jsonify({'message': 'No questions asked by user yet'})

##route 12
@app.route('/questions_most_answered',methods=['GET'])
def questions_most_answered():
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM questions ORDER BY answer_count DESC LIMIT 5")

    questions = cur.fetchall()


    if cur.rowcount > 0:
        cur.close()
        return jsonify({'Most answered questions': questions})
        #return render_template('questions.html', questions=questions)

    else:
        cur.close()
        #msg = 'No questions found'
        #return render_template('questions.html', msg=msg)
        return jsonify({'message': 'No questions'})

##route 13
@app.route('/questions/search/',methods=['POST'])
def search_questions():
    search_text = request.form['search_text']
    conn = psycopg2.connect("host=localhost dbname=StackOverflowLite user=postgres password=postgres")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM questions WHERE question LIKE %s",[search_text])

    questions = cur.fetchall()


    if cur.rowcount > 0:
        cur.close()
        return jsonify({'Questions asked by user': questions})
        #return render_template('questions.html', questions=questions)

    else:
        cur.close()
        #msg = 'No questions found'
        #return render_template('questions.html', msg=msg)
        return jsonify({'message': 'No questions asked matching'})


@app.route('/dashboard')
##@is_logged_in
@token_required
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




@app.route('/logout')
@is_logged_in
def logout():
    name = session['username']
    session.clear()
    flash('You have logged out, see you soon ' + name, 'success')
    return redirect(url_for('login'))



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


if __name__ == '__main__':
    app.secret_key = 'my very unsecured secret key'
    app.run(host='0.0.0.0', port=5000, debug=True)
