from flask import(
    Flask,
    render_template
)
import connexion
import psycopg2

#app= Flask(__name__,template_folder="templates")
app= connexion.App(__name__,specification_dir='./')

app.add_api('swagger.yml')

@app.route('/')

def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
