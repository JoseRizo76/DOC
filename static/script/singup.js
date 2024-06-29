function validarDatos() {
    var usuario = document.getElementById("usuario").value.trim();
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirm_password").value;

    document.getElementById("usuario_error").style.display = 'none';
    document.getElementById("password_error").style.display = 'none';
    let time = 2000;

    //VALIDAR USUARIO
    if (usuario.includes(' ') || usuario.includes('-') || usuario.includes('+')) {
        document.getElementById("usuario_error").style.display = 'block';
        document.getElementById("usuario_error").innerText = "El usuario no puede contener espacios ni simbolos.";
        setTimeout(function() {
            document.getElementById("fusuario_error").style.display = 'none';
        }, time);
        return false;
    }
    //VALIDAR CONTRASEÑA
    if (password !== confirmPassword) {
        document.getElementById("password_error").style.display = 'block';
        document.getElementById("password_error").innerText = "Las contraseñas no coinciden.";
        setTimeout(function() {
            document.getElementById("password_error").style.display = 'none';
        }, time);
        return false;
    }
    //VALIDAR LONGITUD DE CONTRASEÑA
    if(password.length < 6){
        document.getElementById("password_error").style.display = 'block';
        document.getElementById("password_error").innerText = "Tu Contraseña debe tener almenos 6 Caracteres";
        setTimeout(function() {
            document.getElementById("password_error").style.display = 'none';
        }, time);
        return false;
    }
    return true;
}
