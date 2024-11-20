import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, Response, url_for, session
from flask_mysqldb import MySQL, MySQLdb


app = Flask(__name__, template_folder='templates')

app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        imagen = request.files['imagen']
        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(imagen_path)
        else:
            filename = None  # En caso de que no se haya subido una imagen válida
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO productos (nombre, precio, cantidad, imagen) VALUES (%s, %s, %s, %s)", (nombre, precio, cantidad, filename))
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
        
        imagen = request.files['imagen']
        if imagen and allowed_file(imagen.filename):
            # Si hay una nueva imagen, la subimos y reemplazamos la anterior
            filename = secure_filename(imagen.filename)
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(imagen_path)
        else:
            # Si no se sube una nueva imagen, mantenemos la actual
            filename = producto['imagen']
        
        cur.execute("UPDATE productos SET nombre = %s, precio = %s, cantidad = %s, imagen = %s WHERE id = %s", 
                    (nombre, precio, cantidad, filename, id))
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

@app.route('/usuario')
def usuario():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")  # Consultar todos los productos
    productos = cur.fetchall()
    cur.close()
    return render_template("usuario.html", productos=productos)
 

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

            if session['id_rol'] == 1:  # Administrador
                # Consulta los productos para mostrarlos en la tabla
                cur.execute("SELECT * FROM productos")
                productos = cur.fetchall()
                cur.close()
                return render_template("admin.html", productos=productos)

            elif session['id_rol'] == 2:  # Usuario estándar
                cur.execute("SELECT * FROM productos")  # Obtener los productos
                productos = cur.fetchall()
                cur.close()
                return render_template("usuario.html", productos=productos)
        else:
            return render_template('index.html', mensaje="Usuario o Contraseña Incorrectos")



@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/comprar')
def comprar():
    return render_template('comprar.html')


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
