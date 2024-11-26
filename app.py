import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, Response, url_for, session
from flask_mysqldb import MySQL, MySQLdb
from decimal import Decimal  # Importa Decimal para manejar las conversiones de precio

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


@app.route('/historial')
def historial_ventas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM reseñas")  # Obtiene todas las reseñas
    reseñas = cur.fetchall()  # Recupera todas las filas
    cur.close()

    # Organiza las reseñas por producto_id
    historial_reseñas = {}
    for reseña in reseñas:
        producto_id = reseña['producto_id']  # Usa la clave 'producto_id' en lugar de un índice
        if producto_id not in historial_reseñas:
            historial_reseñas[producto_id] = []
        historial_reseñas[producto_id].append({
            'nombre': reseña['nombre'],  # Accede por nombre de columna
            'opinion': reseña['opinion'],
            'estrellas': reseña['estrellas'],
            'fecha': reseña['fecha'],
        })

    return render_template("historial.html", historial_reseñas=historial_reseñas)

@app.route('/agregar-administrador')
def agregar_administrador():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template("agregarAdmin.html", productos=productos)



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
            filename = secure_filename(imagen.filename)
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(imagen_path)
        else:
            filename = producto['imagen']
        
        cur.execute("UPDATE productos SET nombre = %s, precio = %s, cantidad = %s, imagen = %s WHERE id = %s", 
                    (nombre, precio, cantidad, filename, id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('listar_productos'))
    
    return render_template("editar_producto.html", producto=producto)


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
    cur.execute("SELECT * FROM productos")  
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

            if session['id_rol'] == 1: 

                cur.execute("SELECT * FROM productos")
                productos = cur.fetchall()
                cur.close()
                return render_template("admin.html", productos=productos)

            elif session['id_rol'] == 2: 
                
                cur.execute("SELECT * FROM productos") 
                productos = cur.fetchall()
                cur.close()
                return render_template("usuario.html", productos=productos)
        else:
            return render_template('index.html', mensaje="Usuario o Contraseña Incorrectos")


@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/comprar')
def comprar(id):
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

@app.route('/procesar_pago/<int:id>/<int:cantidad>', methods=["POST"])
def procesar_pago(id, cantidad):
    metodo_pago = request.form['metodo_pago']
    
    # Obtener detalles del producto
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()

    # Verificar si hay suficiente cantidad
    if cantidad > producto['cantidad']:
        cur.close()
        return render_template('producto_detalle.html', producto=producto, error="Cantidad no disponible.")

    # Actualizar cantidad en inventario
    nueva_cantidad = producto['cantidad'] - cantidad
    cur.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_cantidad, id))
    mysql.connection.commit()
    cur.close()

    # Calcular el total
    precio_total = Decimal(producto['precio']) * cantidad

    # Renderizar la página `pago_confirmado.html` con datos dinámicos
    return render_template('pago_confirmado.html', 
                           producto=producto, 
                           cantidad=cantidad, 
                           total=precio_total, 
                           metodo_pago=metodo_pago)


@app.route('/producto-detalle/<int:id>', methods=["GET", "POST"])
def producto_detalle(id):
    cur = mysql.connection.cursor()
    
    # Obtener detalles del producto
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()
    
    # Obtener las reseñas del producto
    cur.execute("SELECT opinion, estrellas, fecha, nombre FROM reseñas WHERE producto_id = %s", (id,))
    reseñas = cur.fetchall()
    
    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])  # Cantidad seleccionada por el usuario
        metodo_pago = request.form['metodo_pago']
        
        # Verificar si hay suficiente cantidad disponible
        if cantidad > producto['cantidad']:
            return render_template('producto_detalle.html', producto=producto, reseñas=reseñas, error="Cantidad no disponible.")

        # Calcular el precio total
        precio_total = Decimal(producto['precio']) * cantidad

        # Actualizar la base de datos: restar la cantidad comprada
        nueva_cantidad = producto['cantidad'] - cantidad
        cur.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nueva_cantidad, id))
        mysql.connection.commit()

        # Opcional: Guardar registro de la compra (si tienes una tabla de compras)
        # cur.execute("INSERT INTO compras (producto_id, cantidad, total, metodo_pago) VALUES (%s, %s, %s, %s)", (id, cantidad, precio_total, metodo_pago))
        # mysql.connection.commit()

        cur.close()

        # Redirigir o mostrar confirmación de compra
        return render_template('compra_confirmada.html', producto=producto, cantidad=cantidad, total=precio_total, metodo_pago=metodo_pago)

    cur.close()
    return render_template('producto_detalle.html', producto=producto, reseñas=reseñas)


@app.route('/pago_confirmado', methods=["GET", "POST"])
def pago_confirmado():
    if request.method == "POST":
        # Guardar reseña en la base de datos
        opinion = request.form['opinion']
        estrellas = request.form['estrellas']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO reseñas (producto_id, opinion, estrellas) VALUES (%s, %s, %s)", (request.form['producto_id'], opinion, estrellas))
        mysql.connection.commit()
        cur.close()

    return render_template("pago_confirmado.html")

@app.route('/guardar-reseña', methods=["POST"])
def guardar_reseña():
    producto_id = request.form['producto_id']
    opinion = request.form['opinion']
    estrellas = request.form['estrellas']
    nombre = request.form['nombre']  # Capturar el nombre del usuario

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO reseñas (producto_id, opinion, estrellas, nombre) VALUES (%s, %s, %s, %s)", 
                (producto_id, opinion, estrellas, nombre))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('usuario'))

if __name__ == '__main__':
   app.secret_key = "pinchellave"
   app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
