# pedidos/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Pedido, DetallePedido, Cupon
from carrito.models import Carrito
from django.core.mail import send_mail
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@login_required
def confirmar_pedido(request):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    if not carrito.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')
    
    # Obtener cupón si existe en la sesión
    cupon = None
    if 'cupon_id' in request.session:
        try:
            cupon = Cupon.objects.get(id=request.session['cupon_id'])
            if not cupon.es_valido():
                cupon = None
                messages.warning(request, "El cupón ha expirado y no será aplicado.")
        except Cupon.DoesNotExist:
            pass
    
    # Calcular el total
    total = carrito.obtener_total()
    if cupon:
        total = carrito.aplicar_cupon(cupon)
    
    return render(request, 'pedidos/confirmar_pedido.html', {
        'carrito': carrito,
        'cupon': cupon,
        'total': total
    })

@login_required
@transaction.atomic
def procesar_pedido(request):
    if request.method == 'POST':
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        
        if not carrito.items.exists():
            messages.error(request, "Tu carrito está vacío.")
            return redirect('ver_carrito')
        
        # Obtener cupón si existe en la sesión
        cupon = None
        if 'cupon_id' in request.session:
            try:
                cupon = Cupon.objects.get(id=request.session['cupon_id'])
                if not cupon.es_valido():
                    cupon = None
            except Cupon.DoesNotExist:
                pass
        
        # Calcular el total
        total = carrito.obtener_total()
        if cupon:
            total = carrito.aplicar_cupon(cupon)
        
        # Crear pedido
        pedido = Pedido.objects.create(
            usuario=request.user,
            cupon=cupon,
            total=total,
            direccion_envio=request.POST.get('direccion', '')
        )
        
        # Crear detalles del pedido y actualizar stock
        for item in carrito.items.all():
            if item.cantidad > item.libro.stock:
                transaction.set_rollback(True)
                messages.error(request, f"No hay suficiente stock para '{item.libro.titulo}'.")
                return redirect('ver_carrito')
            
            DetallePedido.objects.create(
                pedido=pedido,
                libro=item.libro,
                cantidad=item.cantidad,
                precio_unitario=item.libro.precio
            )
            
            # Actualizar stock
            item.libro.stock -= item.cantidad
            item.libro.save()
        
        # Enviar email de confirmación
        try:
            '''send_mail(
                f'Confirmación de Pedido #{pedido.numero_orden}',
                f'Tu pedido #{pedido.numero_orden} ha sido procesado con éxito. Total: ${pedido.total}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            '''
            enviarCorreo([request.user.email],f'Tu pedido #{pedido.numero_orden} ha sido procesado con éxito. Total: ${pedido.total}')
        except Exception as e:
            # Continuar incluso si el correo falla
            print(f"Error al enviar email: {e}")
        
        # Vaciar carrito y sesión
        carrito.items.all().delete()
        if 'cupon_id' in request.session:
            del request.session['cupon_id']
        
        messages.success(request, f"¡Pedido #{pedido.numero_orden} completado con éxito!")
        return redirect('historial_pedidos')
    
    return redirect('confirmar_pedido')

@login_required
def historial_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'pedidos/historial_pedidos.html', {'pedidos': pedidos})

@login_required
def detalle_pedido(request, numero_orden):
    pedido = get_object_or_404(Pedido, numero_orden=numero_orden, usuario=request.user)
    return render(request, 'pedidos/detalle_pedido.html', {'pedido': pedido})

# pedidos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Pedido

def es_superusuario(user):
    return user.is_superuser

@login_required
@user_passes_test(es_superusuario)
def listar_pedidos(request):
    pedidos = Pedido.objects.all().order_by('-fecha_creacion')
    return render(request, 'pedidos/listar_pedidos.html', {'pedidos': pedidos})

@login_required
@user_passes_test(es_superusuario)
def actualizar_estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in [estado[0] for estado in Pedido.ESTADO_CHOICES]:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido #{pedido.numero_orden} actualizado a {nuevo_estado}')
        else:
            messages.error(request, 'Estado no válido')
    
    return redirect('listar_pedidos')

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