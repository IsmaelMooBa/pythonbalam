from flask import Flask
from flask import render_template, request, redirect, Response, url_for, session
from flask_mysqldb import MySQL, MySQLdb  # pip install Flask-MySQLdb

app = Flask(__name__, template_folder='template')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


@app.route('/listar-productos')
def listar_productos():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template("admin.html", productos=productos)


@app.route('/agregar-producto', methods=["GET", "POST"])
def agregar_producto():
    if request.method == "POST":
        nombre = request.form['nombre']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO productos (nombre, precio, cantidad) VALUES (%s, %s, %s)", (nombre, precio, cantidad))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('listar_productos'))
    
    return render_template("agregar_producto.html")


# Editar producto
@app.route('/editar-producto/<int:id>', methods=["GET", "POST"])
def editar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()
    
    if request.method == "POST":
        nombre = request.form['nombre']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        
        cur.execute("UPDATE productos SET nombre = %s, precio = %s, cantidad = %s WHERE id = %s", 
                    (nombre, precio, cantidad, id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('listar_productos'))
    
    return render_template("editar_producto.html", producto=producto)


# Eliminar producto
@app.route('/eliminar-producto/<int:id>', methods=["GET", "POST"])
def eliminar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('listar_productos'))

@app.route('/')
def home():
    return render_template('index.html')   


@app.route('/admin')
def admin():
    return render_template('admin.html')   

@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s AND password = %s', (_correo, _password,))
        account = cur.fetchone()

        if account:
            session['logueado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']

            if session['id_rol'] == 1:
                return render_template("admin.html")
            elif session['id_rol'] == 2:
                return render_template("usuario.html")
        else:
            return render_template('index.html', mensaje="Usuario o Contraseña Incorrectos")


@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/comprar')
def comprar():
    return render_template('comprar.html')  # Asegúrate de que "comprar.html" esté en la carpeta "templates".

@app.route('/crear-registro', methods=["GET", "POST"])
def crear_registro(): 
    correo = request.form['txtCorreo']
    password = request.form['txtPassword']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (correo, password, id_rol) VALUES (%s, %s, '2')", (correo, password))
    mysql.connection.commit()
    
    return render_template("index.html", mensaje2="Usuario Registrado Exitosamente")

@app.route('/listar', methods=["GET", "POST"])
def listar(): 
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()
    cur.close()
    
    return render_template("listar_usuarios.html", usuarios=usuarios)


if __name__ == '__main__':
   app.secret_key = "pinchellave"
   app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
