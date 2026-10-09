"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Contiene la logica de productos (alta, baja, stock y busqueda), ventas con
descuentos e IVA, y cotizaciones. El estado vive en variables de modulo:
INVENTARIO, VENTAS, contador_ventas y ultimo_error (motivo del ultimo fallo).
"""

from datetime import datetime

# ---------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------
TASA_IVA = 0.16
UMBRAL_DESCUENTO_ALTO = 1000
DESCUENTO_ALTO = 0.10
UMBRAL_DESCUENTO_MEDIO = 500
DESCUENTO_MEDIO = 0.05
PREFIJO_VIP = "VIP"
MONTO_MINIMO_VIP = 200
DESCUENTO_VIP = 0.02
STOCK_MINIMO = 5

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contador_ventas = 0
ultimo_error = ""


def _registrar_error(mensaje: str) -> None:
    """Deja el motivo del ultimo fallo en la variable de modulo ultimo_error."""
    global ultimo_error
    ultimo_error = mensaje


def reiniciar_sistema() -> None:
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contador_ventas
    INVENTARIO.clear()
    VENTAS.clear()
    contador_ventas = 0
    _registrar_error("")


def agregarProducto(
    codigo: str | None, nombre: str, precio: float, stock: int
) -> bool:
    """Valida los datos y da de alta un producto. Regresa False si falla."""
    if codigo is None or codigo == "":
        _registrar_error("codigo vacio")
        return False
    if codigo in INVENTARIO:
        _registrar_error("el producto ya existe")
        return False
    if precio <= 0:
        _registrar_error("precio invalido")
        return False
    if stock < 0:
        _registrar_error("stock invalido")
        return False
    INVENTARIO[codigo] = {
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio,
        "stock": stock,
    }
    return True


def eliminar_producto(codigo: str) -> bool:
    """Quita un producto del inventario. Regresa False si no existe."""
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    _registrar_error("producto no existe")
    return False


def actualizar_stock(codigo: str, cantidad: int) -> bool:
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    if codigo not in INVENTARIO:
        _registrar_error("producto no existe")
        return False
    nuevo_stock = INVENTARIO[codigo]["stock"] + cantidad
    if nuevo_stock < 0:
        _registrar_error("el stock no puede quedar negativo")
        return False
    INVENTARIO[codigo]["stock"] = nuevo_stock
    return True


def buscarProducto(texto: str) -> list[dict]:
    """Busca productos cuyo nombre contenga el texto (sin importar mayusculas)."""
    return [
        producto
        for producto in INVENTARIO.values()
        if texto.lower() in producto["nombre"].lower()
    ]


def calcular_descuento_volumen(subtotal: float) -> float:
    """Descuento por volumen de compra según el subtotal (0 si no aplica)."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * DESCUENTO_MEDIO
    return 0


def _es_cliente_vip(cliente: str | None) -> bool:
    """Indica si el cliente es VIP (su código empieza con el prefijo VIP)."""
    if cliente is None or cliente == "":
        return False
    return cliente.startswith(PREFIJO_VIP)


def _validar_venta(codigo: str | None, cantidad: int | None) -> dict | None:
    """Valida los datos de la venta; devuelve el producto o None con error."""
    if codigo is None or codigo == "":
        _registrar_error("codigo vacio")
        return None
    if codigo not in INVENTARIO:
        _registrar_error("producto no existe")
        return None
    if cantidad is None or cantidad <= 0:
        _registrar_error("cantidad invalida")
        return None
    if INVENTARIO[codigo]["stock"] < cantidad:
        _registrar_error("stock insuficiente")
        return None
    return INVENTARIO[codigo]


def _crear_venta(
    folio: int,
    codigo: str,
    nombre: str,
    cantidad: int,
    montos: dict,
    cliente: str,
) -> dict:
    """Crea el registro de la venta con los montos ya redondeados."""
    return {
        "folio": folio,
        "codigo": codigo,
        "nombre": nombre,
        "cantidad": cantidad,
        "subtotal": round(montos["subtotal"], 2),
        "descuento": round(montos["descuento"], 2),
        "impuesto": round(montos["impuesto"], 2),
        "total": montos["total"],
        "cliente": cliente,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _armar_ticket(venta: dict, hay_descuento: bool) -> str:
    """Arma el ticket en texto plano; omite el descuento si no hay."""
    ticket = "TIENDA LA ESQUINA\n"
    ticket += "----------------------------\n"
    ticket += "Folio: " + str(venta["folio"]) + "\n"
    ticket += venta["nombre"] + " x" + str(venta["cantidad"]) + "\n"
    ticket += "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if hay_descuento:
        ticket += "Descuento: -$" + str(venta["descuento"]) + "\n"
    ticket += "IVA: $" + str(venta["impuesto"]) + "\n"
    ticket += "TOTAL: $" + str(venta["total"]) + "\n"
    return ticket


def registrar_venta(
    codigo: str | None, cantidad: int | None, cliente: str = ""
) -> dict | None:
    """Registra una venta completa y regresa el registro con su ticket.

    Orquesta la validacion, el calculo de descuentos e IVA, el descuento de
    stock, el folio y el ticket. Si la validacion falla regresa None y deja
    el motivo en ultimo_error.
    """
    global contador_ventas
    producto = _validar_venta(codigo, cantidad)
    if producto is None:
        return None
    subtotal = producto["precio"] * cantidad
    descuento = calcular_descuento_volumen(subtotal)
    # los clientes cuyo codigo empieza con VIP tienen un extra,
    # pero solo si su compra (ya con descuento) pasa de cierto monto
    if _es_cliente_vip(cliente) and subtotal - descuento > MONTO_MINIMO_VIP:
        descuento = descuento + subtotal * DESCUENTO_VIP
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    total = round(base + impuesto, 2)
    producto["stock"] = producto["stock"] - cantidad
    contador_ventas = contador_ventas + 1
    montos = {
        "subtotal": subtotal,
        "descuento": descuento,
        "impuesto": impuesto,
        "total": total,
    }
    venta = _crear_venta(
        contador_ventas, codigo, producto["nombre"], cantidad, montos, cliente
    )
    venta["ticket"] = _armar_ticket(venta, descuento > 0)
    VENTAS.append(venta)
    return venta


def cotizar(codigo: str, cantidad: int | None) -> float | None:
    """Calcula cuanto costaria una compra sin registrar la venta."""
    if codigo not in INVENTARIO:
        _registrar_error("producto no existe")
        return None
    if cantidad is None or cantidad <= 0:
        _registrar_error("cantidad invalida")
        return None
    subtotal = INVENTARIO[codigo]["precio"] * cantidad
    descuento = calcular_descuento_volumen(subtotal)
    base = subtotal - descuento
    total = base + base * TASA_IVA
    return round(total, 2)
