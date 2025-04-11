import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviarCorreo(destinatario, mensajeConfirmacion):
    # Configura los detalles del correo
    remitente = "pruebas.envio.correos@outlook.com"  # o @outlook.com
    destinatario = "destinatario@ejemplo.com"
    contraseña = "Pruebas*2025"

    # Crea el mensaje
    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = "Confirmación de pedido"

    # Cuerpo del mensaje
    cuerpo = mensajeConfirmacion
    mensaje.attach(MIMEText(cuerpo, "plain"))

    # Establece conexión con el servidor SMTP de Hotmail/Outlook
    try:
        servidor = smtplib.SMTP("smtp-mail.outlook.com", 587)
        servidor.starttls()  # Habilita la seguridad
        servidor.login(remitente, contraseña)
        
        # Envía el correo
        texto = mensaje.as_string()
        servidor.sendmail(remitente, destinatario, texto)
        print("Correo enviado con éxito!")
        
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
    finally:
        servidor.quit()