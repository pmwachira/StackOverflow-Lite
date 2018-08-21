from flask import Flask,render_template,flash,redirect,url_for,sessions,logging,request
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

from data import Questions
import connexion
import psycopg2

app= Flask(__name__,template_folder="templates")
#app= connexion.App(__name__,specification_dir='./')
conn = None

Questions=Questions()

@app.route('/')

def home():
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    return render_template('home.html')

@app.route('/auth/signup')

def add_user(name,email,username,password):
    conn = psycopg2.connect("host= localhost dbname=StackOverflowLite user=postgres password=postgres")
    try:

        sql="""INSERT INTO users(user_name,user_email,password) VALUES (%s,%s,%s) RETURNING user_id"""
        cur=conn.cursor()

        cur.execute(sql,(name,email,password))

        user_id= cur.fetchone()[0]

        conn.commit()

        cur.close()


    except(Exception,psycopg2.DatabaseError) as error:
        print (error)
    finally:
        if conn is not None:
            conn.close()

    return user_id

#@app.route('/auth/login')

@app.route('/questions')
def questions():
    return render_template('questions.html',questions=Questions)

@app.route('/question/<string:id>/')
def question(id):
    return render_template('question.html', id=id)

# @app.route('/questions')
# @app.route('/questions/<questionId>')
# @app.route('/questions/<questionId>/answers')
# @app.route('/questions/<questionId>/answers/<answerId>')

class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm=PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        show=add_user(name,email,username,password)
        flash('You are now registered'+str(show), 'success')
        return redirect(url_for('login'))

    return render_template('register.html',form=form)


if __name__ == '__main__':
    app.secret_key='my very unsecured secret key'
    app.run(host='0.0.0.0',port=5000,debug=True)
