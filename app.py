from flask import Flask, render_template, request, redirect, flash, jsonify, url_for , session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from configTokem import config, vendedor
from flask_session import Session



app = Flask(__name__)
app.config['SECRET_KEY'] = config['sesionpass']
app.config['SESSION_TYPE'] = config['tiposesion']


Session(app)

app = Flask(__name__)
app.secret_key =  config['secretkey']

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/singup', methods=['GET', 'POST'])
def singup():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        try:
            # Conexión a la base de datos SQLite
            conn = sqlite3.connect(config['databasename'])
            cursor = conn.cursor()

            # Verificar si el usuario ya existe
            cursor.execute("SELECT * FROM USUARIOS WHERE USUARIO = ?", (usuario,))
            if cursor.fetchone() is not None:
                flash("USUARIO EXISTENTE.", "UE")
                return redirect('/singup')

            # Obtener el último ID de usuario y generar el nuevo ID de usuario
            cursor.execute("SELECT MAX(ID_USUARIO) FROM USUARIOS")
            result = cursor.fetchone()
            ultimoID = result[0] if result[0] is not None else 9999
            id_usuario = int(ultimoID) + 1

            # Cifrar la contraseña
            hashed_password = generate_password_hash(password, method=config['hashedpass'], salt_length=8)

            # Insertar datos en las tablas correspondientes
            cursor.execute("INSERT INTO USUARIOS (USUARIO, ID_USUARIO) VALUES (?, ?)", (usuario, id_usuario))
            cursor.execute("INSERT INTO PASSWORD (CONTRASEÑA, ID_USUARIO) VALUES (?, ?)", (hashed_password, id_usuario))
            cursor.execute("INSERT INTO SALDO (DINERO, ID_USUARIO) VALUES (?, ?)", (0, id_usuario))
            conn.commit()

            # Cerrar la conexión con la base de datos
            cursor.close()
            conn.close()

            return redirect('/login')
        except sqlite3.Error as e:
            flash(f"Error al insertar datos: {e}", "error")
            return redirect('/singup')

    else:
        return render_template('singup.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")
        conn = sqlite3.connect(config['databasename'])
        cursor = conn.cursor()
        usuariodb = 0
        try:
            if not usuario.isdigit():
                cursor.execute("SELECT ID_USUARIO FROM USUARIOS WHERE USUARIO = ?", (usuario,))
                resultado = cursor.fetchone()
                if resultado:
                    usuariodb  = int(resultado[0])
                else:
                    flash("Usuario no encontrado", "error")
                    return redirect('/login')
            else:
                print("INGRESO POR ID")
                usuariodb = int(usuario)

            print(usuariodb)
            # OBTENER CONTRASEÑA DE LA BASE DE DATOS
            cursor.execute("SELECT CONTRASEÑA FROM PASSWORD WHERE ID_USUARIO = ?", (usuariodb,))
            resultado = cursor.fetchone()
            if resultado:
                hashed_password = resultado[0]
                if check_password_hash(hashed_password, password):
                    cursor.execute("SELECT DIA, MES, YEAR, SEGUNDO, MINUTO, HORA, MONTO FROM RECARGA WHERE ID_USUARIO = ?", (usuariodb,))
                    recargas = cursor.fetchall()
                    recargaH = []
                    for recarga in recargas:
                        recargaH.append({
                            'dia': recarga[0],
                            'mes': recarga[1],
                            'year': recarga[2],
                            'segundo': recarga[3],
                            'minuto': recarga[4],
                            'hora': recarga[5],
                            'monto': recarga[6]
                        })
                    
                    datos = cursor.execute("SELECT U.USUARIO, S.DINERO, U.ID_USUARIO FROM  USUARIOS U, PASSWORD P, SALDO S WHERE U.ID_USUARIO = ? AND S.ID_USUARIO = ? AND P.ID_USUARIO = ?",(usuariodb, usuariodb, usuariodb,))
                    datos = cursor.fetchone()
                    context = {
                        "USUARIO": datos[0],
                        "DINERO": datos[1],
                        "ID_USUARIO": datos[2],
                        'recargas': recargaH
                    }
                    print(datos)
                    return render_template("cuenta.html", **context)
                else:
                    flash("Contraseña incorrecta", "error")
                    return redirect('/login')
            else:
                flash("Usuario no encontrado", "error")
                return redirect('/login')

        except sqlite3.Error as e:
            flash(f"Error de base de datos: {e}", "error")
            return redirect('/login')
        finally:
            conn.close()
    else:
        return render_template("login.html")

@app.route('/esp32data', methods=['GET'])
def esp32data():
    user_id = request.args.get('id')
    password = request.args.get('pass')
    if not user_id or not password:
        return "Parámetro 'id' o 'pass' no proporcionado", 400
    try:
        conn = sqlite3.connect(config['databasename'])
        cursor = conn.cursor()
        cursor.execute("SELECT CONTRASEÑA FROM PASSWORD WHERE ID_USUARIO = ?", (user_id,))
        result = cursor.fetchone()

        if result:
            hashed_password = result[0]
            if check_password_hash(hashed_password, password):
                cursor.execute("SELECT DINERO FROM SALDO WHERE ID_USUARIO = ?", (user_id,))
                resultadoD = cursor.fetchone()
                dinero = resultadoD[0]
                return jsonify({"C": "IC", "D": dinero})
            else:
                return jsonify({"C": "CI"}), 401
        else:
            return jsonify({"M": "UI", }), 404
    except sqlite3.Error as err:
        return f"Error de base de datos: {err}", 500, jsonify({"M": "EBD", })
    finally:
        cursor.close()
        conn.close()

@app.errorhandler(404)
def not_found(error):
    print(error)
    return render_template('404.html', error=error)

@app.route('/loginvendedor', methods=["GET", "POST"])
def loginVendedor():
    if request.method == 'POST':
        USUARIO = request.form.get("VENDEDOR")
        PASSWORD = request.form.get("VENDEDORPASS")
        SVM_USUARIO = vendedor['USUARIO']
        SVM_PASSWORD = vendedor['PASSWORD']
           
        if USUARIO == SVM_USUARIO and PASSWORD == SVM_PASSWORD:
            session['sesion_activa'] = True
            return redirect(url_for('recarga'))
        else:
            return render_template("loginVendedor.html", mensaje = "Error en las credenciales")
        
    else:
        return render_template("loginVendedor.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('loginVendedor'))


@app.route('/recarga', methods=["GET", "POST"])
def recarga():
    sesion_activa = session.get('sesion_activa')
    if sesion_activa:
        if request.method == 'POST':

            if request.form.get("monto"):
                monto = request.form.get("monto")
                id_usuario = request.form.get("id_usuario")
                dia = request.form['dia']
                mes = request.form['mes']
                year = request.form['año']
                hora = request.form['hora']
                minutos = request.form['minutos']
                segundos = request.form['segundos']
                print( dia, mes , year, hora, minutos, segundos)

                try:
                    conn = sqlite3.connect(config['databasename'])
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO RECARGA (ID_USUARIO, MONTO, DIA, MES, YEAR, HORA, MINUTO, SEGUNDO) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (id_usuario, monto,dia, mes , year, hora, minutos, segundos, ))
                    cursor.execute("SELECT S.DINERO FROM SALDO S WHERE S.ID_USUARIO = ?", (id_usuario,))
                    resultadoD = cursor.fetchone()
                    dineroanterior = resultadoD[0]
                    cursor.execute("UPDATE SALDO SET DINERO = DINERO + ? WHERE ID_USUARIO = ?", (monto, id_usuario,))
                    conn.commit()
                    mensaje = "RECARGA EXITOSA"
                    cursor.execute("SELECT U.USUARIO, U.ID_USUARIO, S.DINERO FROM USUARIOS U, SALDO S WHERE U.ID_USUARIO = ? AND S.ID_USUARIO = ?", (id_usuario, id_usuario,))
                    resultadoD = cursor.fetchone()
                    content = {
                        'USUARIO': resultadoD[0],
                        'ID_USUARIO': resultadoD[1],
                        'DINEROACTUAL': resultadoD[2],
                        'DINEROANTERIOR': dineroanterior,
                        'monto': monto,
                        'mensaje': mensaje
                    }
                    session['sesion_activa'] = True
                    for key, value in content.items():
                        session[key] = value
                    return redirect(url_for('datos'))
                except sqlite3.Error as err:
                    return f"Error de base de datos: {err}", 500
                finally:
                    cursor.close()
                    conn.close()

            if request.form.get("id_usuario"):
                id_usuario = request.form.get("id_usuario")
                try:
                    conn = sqlite3.connect(config['databasename'])
                    cursor = conn.cursor()
                    cursor.execute("SELECT U.USUARIO, U.ID_USUARIO, S.DINERO FROM USUARIOS U, SALDO S WHERE U.ID_USUARIO = ? AND S.ID_USUARIO = ?", (id_usuario, id_usuario,))
                    resultadoD = cursor.fetchone()
                    if resultadoD:
                        content = {
                            'codigo' : 1,
                            'USUARIO': resultadoD[0],
                            'ID_USUARIO': resultadoD[1],
                            'DINERO': resultadoD[2],
                        }
                        print(resultadoD)
                        return render_template("recarga.html", **content)
                    else:
                        content = {
                            'codigo' : 2,
                            'mensaje': "Usuario no encontrado"
                        }
                        return render_template("recarga.html", **content)
                except sqlite3.Error as err:
                    return f"Error de base de datos: {err}", 500
                finally:
                    cursor.close()
                    conn.close()

        else:
            return render_template("recarga.html")
    else:
        return render_template("recarga.html", code = 404)


@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route("/recarga/recargaexitosa")
def datos():
    sesion_activa = session.get('sesion_activa')
    if sesion_activa:
        content = {
            'usuario': session.get('USUARIO'),
            'id_usuario': session.get('ID_USUARIO'),
            'dineroactual': session.get('DINEROACTUAL'),
            'dineroanterior': session.get('DINEROANTERIOR'),
            'monto': session.get('monto'),
            'mensaje': session.get('mensaje')
        }
        return render_template("datosRecarga.html", **content)
    else:
        return "<h1> ACCESO DENEGADO </h1>"


if __name__ == '__main__':
    app.run(debug=True)


