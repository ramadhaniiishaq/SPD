from flask import Flask, render_template ,request, redirect, url_for,session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

mysql= MySQL(app)
@app.route('/')
def index():
    return redirect(url_for('Beranda_desa'))
#desa
@app.route('/Beranda_desa')
def Beranda_desa():
    return render_template('Desa/Beranda.html')

@app.route('/Data')
def Data():
    return render_template('Desa/Data.html')

@app.route('/penduduk')
def penduduk():
    return render_template('Desa/Penduduk.html')

@app.route('/catatan_peristiwa')
def catatan_peristiwa():
    return render_template('Desa/Catatan_peristiwa.html')

@app.route('/tambah_dusun')
def tambah_dusun():
    return render_template('Desa/Tambah_dusun.html')

@app.route('/data_diri')
def data_diri():
    return render_template('Desa/Data_diri.html')

@app.route('/KK_desa')
def KK_desa():
    return render_template('Desa/KK_desa.html')
#dusun
@app.route('/Beranda_dusun')
def Beranda_dusun():
    return render_template('Dusun/Beranda.html')
@app.route('/penduduk_dusun')
def penduduk_dusun():
    return render_template('Dusun/Penduduk.html')
@app.route('/tambah_kk')
def tambah_kk():
    return render_template('Dusun/Tambahkk.html')
@app.route('/KK_dusun')
def KK_dusun():
    return render_template('Dusun/KK_dusun.html')
@app.route('/data_diri_dusun')
def data_diri_dusun():
    return render_template('Dusun/Data_diri.html')
@app.route('/tambah_penduduk')
def tambah_penduduk():
    return render_template('Dusun/Tambah_penduduk.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')
if __name__ == '__main__':
    app.run(debug=True)