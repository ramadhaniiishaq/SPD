from flask import Flask, render_template ,request, redirect, url_for,session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

mysql= MySQL(app)
@app.route('/')
def index():
    return redirect(url_for('dashboard_desa'))

@app.route('/dashboard_desa')
def dashboard_desa():
    return render_template('Desa/Beranda.html')
@app.route('/data')
def data():
    return render_template('Desa/data.html')
if __name__ == '__main__':
    app.run(debug=True)