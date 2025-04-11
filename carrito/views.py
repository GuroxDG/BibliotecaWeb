# carrito/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Carrito, ItemCarrito
from libros.models import Libro
from pedidos.models import Cupon

@login_required
def ver_carrito(request):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, 'carrito/carrito.html', {'carrito': carrito})

@login_required
def agregar_al_carrito(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    # Verificar stock
    if libro.stock <= 0:
        messages.error(request, f"Lo sentimos, '{libro.titulo}' no está disponible en este momento.")
        return redirect('libro_detalle', libro_id=libro.id)
    
    # Verificar si el libro ya está en el carrito
    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        libro=libro,
        defaults={'cantidad': 1}
    )
    
    # Si ya existe, aumentar la cantidad
    if not created:
        if item.cantidad + 1 <= libro.stock:
            item.cantidad += 1
            item.save()
        else:
            messages.warning(request, f"No hay suficiente stock para más unidades de '{libro.titulo}'.")
    
    messages.success(request, f"'{libro.titulo}' añadido al carrito.")
    return redirect('ver_carrito')

@login_required
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    item.delete()
    messages.success(request, f"'{item.libro.titulo}' eliminado del carrito.")
    return redirect('ver_carrito')

@login_required
def actualizar_cantidad(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
        nueva_cantidad = int(request.POST.get('cantidad', 1))
        
        # Validar que la cantidad no exceda el stock
        if nueva_cantidad <= 0:
            item.delete()
            messages.success(request, f"'{item.libro.titulo}' eliminado del carrito.")
        elif nueva_cantidad <= item.libro.stock:
            item.cantidad = nueva_cantidad
            item.save()
            messages.success(request, "Carrito actualizado.")
        else:
            messages.error(request, f"No hay suficiente stock para {nueva_cantidad} unidades de '{item.libro.titulo}'.")
        
        return redirect('ver_carrito')
    return redirect('ver_carrito')

@login_required
def aplicar_cupon(request):
    if request.method == 'POST':
        codigo_cupon = request.POST.get('codigo_cupon', '')
        try:
            cupon = Cupon.objects.get(codigo=codigo_cupon)
            if cupon.es_valido():
                request.session['cupon_id'] = cupon.id
                messages.success(request, f"Cupón '{cupon.codigo}' aplicado con éxito. Descuento: {cupon.descuento}%")
            else:
                messages.error(request, "Este cupón ha expirado o no está activo.")
        except Cupon.DoesNotExist:
            messages.error(request, "Cupón inválido.")
        
        return redirect('ver_carrito')
    return redirect('ver_carrito')