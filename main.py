from flask import Flask, render_template ,request, redirect, url_for,flash,session
from flask_mysqldb import MySQL
import bcrypt
from secrets import token_hex
import easyocr
import os
import re

app = Flask(__name__)
app.secret_key = token_hex(16)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_spd'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

baca = easyocr.Reader(['id', 'en'])

mysql= MySQL(app)
    

@app.route('/regis', methods=['GET','POST'])
def regis():
    if request.method=='POST':
        nama=request.form['nama']
        username=request.form['username']
        password=request.form['password']
        role='Desa'
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        if role=='Desa':
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (Nama,username,password,role ) VALUES (%s,%s,%s,%s)" ,(nama,username,hashed.decode('utf-8'),role))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))
        else:
            return redirect(url_for('regis'))
    
    return render_template('signup.html')

@app.route('/')
def index():
    return redirect(url_for('login'))
#desa
@app.route('/Beranda_desa')
def Beranda_desa():
    if 'id_users' not in session :
        return redirect(url_for('login')) 
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS dusun FROM dusun")
    dusun= cur.fetchone()['dusun'] or 0
    cur.execute("SELECT COUNT(*) AS jumlah_penduduk FROM penduduk")
    jp=cur.fetchone()['jumlah_penduduk'] or 0
    return render_template('Desa/Beranda.html', dusun=dusun, jp=jp)

@app.route('/Data')
def Data():
    if 'id_users' not in session:
        return redirect(url_for('login')) 
    cur= mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS jumlah_dusun FROM dusun")
    jd=cur.fetchone()['jumlah_dusun'] or 0
    
    cur.execute("SELECT * FROM dusun JOIN users ON dusun.id_users = users.id_users")
    dusun=cur.fetchall()
    return render_template('Desa/Data.html',jd=jd,dusun=dusun)

@app.route('/penduduk_desa/<int:id_kk>')
def penduduk(id_kk):
    if 'id_users' not in session:
        return redirect(url_for('login')) 
    cur= mysql.connection.cursor()
    cur.execute("SELECT * FROM penduduk WHERE id_kk = %s", (id_kk,))
    result = cur.fetchall()
    cur.close()
    return render_template('Desa/Penduduk.html',penduduk=result)

@app.route('/catatan_peristiwa', methods=['GET', 'POST'])
def catatan_peristiwa():
    if 'id_users' not in session:
        return redirect(url_for('login')) 
    cur = mysql.connection.cursor()
    
    # Proses form pindah dusun
    if request.method == 'POST':
        id_penduduk = request.form['id_penduduk']
        dusun_tujuan = request.form['dusun_tujuan']
        alasan = request.form['alasan']
        tanggal_pindah = request.form['tanggal_pindah']
        
        # Ambil dusun asal
        cur.execute("""
            SELECT d.nama as dusun_asal 
            FROM penduduk p 
            JOIN kk k ON p.id_kk = k.id 
            JOIN dusun d ON k.id_dusun = d.id 
            WHERE p.id_penduduk = %s
        """, (id_penduduk,))
        penduduk = cur.fetchone()
        
        if penduduk:
            # Simpan ke riwayat
            cur.execute("""
                INSERT INTO riwayat_pindah (id_penduduk, dusun_asal, dusun_tujuan, alasan, tanggal_pindah) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_penduduk, penduduk['dusun_asal'], dusun_tujuan, alasan, tanggal_pindah))
            
            mysql.connection.commit()
            flash('Data perpindahan berhasil disimpan!', 'success')
        else:
            flash('Data penduduk tidak ditemukan!', 'danger')
        
        cur.close()
        return redirect(url_for('catatan_peristiwa'))
    
    # GET request - ambil semua data
    # Data untuk form pindah
    cur.execute("SELECT id_penduduk, nama FROM penduduk ORDER BY nama")
    penduduk_list = cur.fetchall()
    
    cur.execute("SELECT id, nama FROM dusun ORDER BY nama")
    dusun_list = cur.fetchall()
    
    # Data riwayat
    cur.execute("""
        SELECT r.*, p.nama as nama_penduduk 
        FROM riwayat_pindah r
        JOIN penduduk p ON r.id_penduduk = p.id_penduduk
        ORDER BY r.tanggal_pindah DESC
    """)
    riwayat = cur.fetchall()
    cur.close()
    
    return render_template('Desa/Catatan_peristiwa.html', 
                         penduduk_list=penduduk_list, 
                         dusun_list=dusun_list,
                         riwayat=riwayat)

# Hapus riwayat
@app.route('/hapus_riwayat/<int:id_riwayat>')
def hapus_riwayat(id_riwayat):
    if 'id_users' not in session :
        return redirect(url_for('login')) 
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM riwayat_pindah WHERE id = %s", (id_riwayat,))
    mysql.connection.commit()
    cur.close()
    
    flash('Riwayat berhasil dihapus!', 'success')
    return redirect(url_for('catatan_peristiwa'))

@app.route('/tambah_dusun', methods=['GET', 'POST'])
def tambah_dusun():
    if 'id_users' not in session :
        return redirect(url_for('login')) 
    if request.method == 'POST':
        nama = request.form['nama']
        nama_dusun = request.form['nama_dusun']
        password = request.form['password']
        username = request.form['username']
        role= "dusun"

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (Nama, username, password, role) VALUES (%s, %s, %s, %s)", (nama, username, hashed.decode('utf-8'), role))
        id_users = cur.lastrowid
        cur.execute("INSERT INTO dusun (id_users,kepala_dusun, nama) VALUES (%s,%s, %s)", (id_users,nama,nama_dusun))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Beranda_desa'))
    return render_template('Desa/Tambah_dusun.html')

@app.route('/hapus_dusun/<int:id_dusun>')
def hapus_dusun(id_dusun):
    if 'id_users' not in session:
        return redirect(url_for('login')) 
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_users FROM dusun WHERE id=%s",(id_dusun,))
    result=cur.fetchone()
    if result:
        id_users=result['id_users']
        cur.execute("DELETE FROM dusun WHERE id=%s",(id_dusun,))
        cur.execute("DELETE FROM users WHERE id_users=%s ",(id_users,))
        mysql.connection.commit()
        return redirect(url_for('Data'))
    else:
        return "Data tidak ada"

@app.route('/edit_dusun/<int:id_dusun>', methods=['GET','POST'])
def edit_dusun(id_dusun):
    if 'id_users' not in session :
        return redirect(url_for('login')) 
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM dusun JOIN users ON dusun.id_users=users.id_users WHERE dusun.id = %s",(id_dusun,))
    dusun=cur.fetchone()
    cur.close()
    if request.method == 'POST':
        nama=request.form['nama']
        nama_dusun=request.form['nama_dusun']
        username=request.form['username']
        password=request.form['password']
        
        cur= mysql.connection.cursor()
        cur.execute("UPDATE dusun SET kepala_dusun=%s,nama=%s WHERE id=%s", (nama,nama_dusun,id_dusun))
        if password:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute("UPDATE users SET nama=%s, username=%s password=%s WHERE id_users=(SELECT id_users FROM dusun WHERE id=%s)",
                        (nama,username,hashed.decode('utf-8'),id_dusun))
        else:
            cur.execute("UPDATE users SET nama=%s, username=%s WHERE id_users=(SELECT id_users FROM dusun WHERE id=%s)",
                        (nama,username,id_dusun))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Data'))
    
    return render_template('Desa/edit_dusun.html', d=dusun)

@app.route('/data_diri/<int:id_penduduk>')
def data_diri(id_penduduk):
    if 'id_users' not in session:
        return redirect(url_for('login')) 
    cur= mysql.connection.cursor()
    cur.execute("SELECT * FROM penduduk WHERE id_penduduk = %s", (id_penduduk,))
    result = cur.fetchone()
    cur.close()
    return render_template('Desa/Data_diri.html',result=result)

@app.route('/KK_desa')
def KK_desa():
    if 'id_users' not in session :
        return redirect(url_for('login')) 
    cur=mysql.connection.cursor()
    cur.execute("SELECT COUNT(*)AS kk FROM kk")
    kk=cur.fetchone()['kk'] or 0
    cur.execute("SELECT * FROM kk JOIN dusun ON kk.id_dusun=dusun.id ")
    kk2= cur.fetchall()
    return render_template('Desa/KK_desa.html',kk=kk,kk2=kk2)


#dusun
@app.route('/Beranda_dusun')
def Beranda_dusun():
    if 'id_users' not in session :
        return redirect(url_for('login'))
    cur= mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS ttl_penduduk FROM penduduk JOIN kk ON penduduk.id_kk = kk.id JOIN dusun ON kk.id_dusun = dusun.id WHERE id_users = %s",(session.get('id_users'),))
    ttl_penduduk= cur.fetchone()['ttl_penduduk']
    return render_template('Dusun/Beranda.html', ttl_pendudukk=ttl_penduduk)

@app.route('/penduduk_dusun/<int:id_kk>')
def penduduk_dusun(id_kk):
    if 'id_users' not in session:
        return redirect(url_for('login'))
    cur= mysql.connection.cursor()
    cur.execute("SELECT * FROM penduduk WHERE id_kk = %s", (id_kk,))
    result = cur.fetchall()
    cur.close()
    return render_template('Dusun/Penduduk.html', penduduk=result)

@app.route('/delete/<int:id_penduduk>')
def delete(id_penduduk):
    if 'id_users' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM penduduk WHERE id_penduduk = %s", (id_penduduk,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('Beranda_dusun'))
@app.route('/tambah_kk', methods=['GET', 'POST'])
def tambah_kk():
    if 'id_users' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        no_kk = request.form['no_kk']
        nama = request.form['nama']
        dusun = request.form['dusun']
        alamat = request.form['alamat']
        cur= mysql.connection.cursor()
        cur.execute("INSERT INTO kk (no_kk, kepala_keluarga,alamat,id_dusun) VALUES (%s,%s,%s,%s)", (no_kk, nama, alamat, dusun))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('KK_dusun'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM dusun WHERE id_users = %s", (session.get('id_users'),))
    dusun = cur.fetchone()
    cur.close()
    
    return render_template('Dusun/Tambahkk.html', dusun=dusun)
@app.route('/delete_kk/<int:id_kk>')
def hapus_kk(id_kk):
    if 'id_users' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM kk WHERE id = %s", (id_kk,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('KK_dusun'))
@app.route('/KK_dusun')
def KK_dusun():
    if 'id_users' not in session:
        return redirect(url_for('login'))
    cur= mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS ttl_kk FROM kk JOIN dusun ON KK.id_dusun = dusun.id WHERE dusun.id_users = %s" , (session.get('id_users'),))
    ttl_kk= cur.fetchone()['ttl_kk']
    cur.execute("SELECT * FROM kk JOIN dusun ON kk.id_dusun = dusun.id WHERE dusun.id_users = %s ",(session.get('id_users'),))
    kk = cur.fetchall()
    cur.close()
    return render_template('Dusun/KK_dusun.html', ttl_kk=ttl_kk, kk=kk)
@app.route('/data_diri_dusun/<int:id_penduduk>')
def data_diri_dusun(id_penduduk):
    if 'id_users' not in session:
        return redirect(url_for('login'))
    cur= mysql.connection.cursor()
    cur.execute("SELECT * FROM penduduk WHERE id_penduduk = %s", (id_penduduk,))
    result = cur.fetchone()
    cur.close()
    return render_template('Dusun/Data_diri.html',result=result )
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
                session.permanent = True
                session['id_users'] = user['id_users']
                session['nama'] = user['Nama']
                session['username'] = user['username']
                session['role'] = user['role']
                
                if session.get('role') == 'Desa':
                    return redirect(url_for('Beranda_desa'))
                elif session.get('role')== 'Dusun':
                    return redirect(url_for('Beranda_dusun'))
                else:
                    error = "Role tidak valid"
        else:
            error = "Username atau password salah"
    return render_template('login.html', error=error)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/OCR')
def OCR():
    if 'id_users' not in session :
        return redirect(url_for('login'))
    return render_template('dusun/ocr_kk.html')

@app.route('/ocr', methods=['GET', 'POST'])
def ocr_page_kk():
    if 'id_users' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        resul = baca.readtext(filepath)
        
        text = ""
        for data in resul:
            text += data[1] + "\n"
        lines = text.split('\n')
        
        kk_match = re.search(r'\d{16}', text)
        no_kk = kk_match.group() if kk_match else "No KK tidak ditemukan"
        
        nama = "-"
        for i in range(len(lines)):
            if "KEPALA KELUARGA" in lines[i].upper():
                if i + 1 < len(lines):
                    nama = lines[i+1]
                    break
        alamat = "-" 
        for i in range(len(lines)):
            line = lines[i].upper().strip() 
            if "ALAMAT" in line: 
                alamat = line.replace("ALAMAT", "") 
                alamat = alamat.replace(":", "") 
                alamat = alamat.strip()
                if alamat == "" and i + 1 < len(lines):
                    alamat = lines[i + 1] 
                break
            
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM dusun WHERE id_users = %s", (session.get('id_users'),))
    dusun = cur.fetchone()
    cur.close()
        
    return render_template('dusun/ocr_kk.html',no_kk=no_kk, nama=nama, alamat=alamat, dusun=dusun)

#KK
@app.route('/ocr_kk',methods=['GET', 'POST'])
def ocr_kk():
    if 'id_users' not in session :
        return redirect(url_for('login'))
    if request.method == 'POST':
        no_kk = request.form['no_kk']
        nama = request.form['nama']
        dusun = request.form['dusun']
        alamat = request.form['alamat']
        
        cur= mysql.connection.cursor()
        cur.execute("INSERT IGNORE INTO kk (no_kk, kepala_keluarga,alamat,id_dusun) VALUES (%s,%s,%s,%s)", (no_kk, nama, alamat, dusun))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('KK_dusun'))

@app.route('/tambahpenduduk', methods=['GET','POST'])
def tambahpenduduk():
    if 'id_users' not in session:
        return redirect(url_for('login'))
    error=None
    if request.method=='POST':
        nama=request.form['nama']
        nik=request.form['Nik']
        jk=request.form['Jenis_kelamin']
        tl=request.form['tempat_lahir']
        tanggal=request.form['tanggal']
        status=request.form['status']
        kk=request.form['kk']
        agama=request.form['agama']
        
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM penduduk WHERE nik= %s ", (nik,))
        existing=cur.fetchone()
        if existing :
            error=f"Nik{nik} sudah ada"
        else:
            cur= mysql.connection.cursor()
            cur.execute("INSERT INTO penduduk (id_kk,nama,nik,jk,tempat_lahir,tanggal_lahir,status_hubungan,agama) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (kk,nama,nik,jk,tl,tanggal,status,agama))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('KK_dusun'))
    
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM kk  JOIN dusun ON kk.id_dusun = dusun.id WHERE dusun.id_users = %s ", (session.get('id_users'),))
    result=cur.fetchall()
    return render_template('Dusun/tambahpenduduk.html',result=result,error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    