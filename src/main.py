# -*- coding: utf-8 -*-
"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

from collections.abc import Callable

import gestor
import almacen
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        texto = input(mensaje)
        try:
            return float(texto)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def _imprimir_error() -> None:
    """Muestra el ultimo error registrado por el gestor."""
    print("Error:", gestor.ultimo_error)


def _imprimir_menu() -> None:
    """Imprime las opciones del menu."""
    print("")
    print("1) Agregar producto")
    print("2) Registrar venta")
    print("3) Cotizar")
    print("4) Reporte de inventario")
    print("5) Resumen de ventas")
    print("6) Mas vendidos")
    print("7) Alertas de stock bajo")
    print("8) Guardar y salir")


def _agregar_producto() -> None:
    """Opcion 1: pide los datos y da de alta un producto."""
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        _imprimir_error()


def _registrar_venta() -> None:
    """Opcion 2: registra una venta e imprime su ticket."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is None:
        _imprimir_error()
        return
    print(venta["ticket"])


def _cotizar() -> None:
    """Opcion 3: cotiza una compra con IVA."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is None:
        _imprimir_error()
        return
    print("Total estimado (con IVA): $" + str(total))


def _mostrar_inventario() -> None:
    """Opcion 4: muestra el reporte de inventario."""
    reportes.reporte_inventario()


def _mostrar_resumen_ventas() -> None:
    """Opcion 5: muestra el resumen de ventas."""
    reportes.resumen_ventas()


def _mostrar_mas_vendidos() -> None:
    """Opcion 6: lista los productos mas vendidos."""
    for par in reportes.mas_vendidos():
        print(par[0], "->", par[1], "unidades")


def _mostrar_alertas_stock() -> None:
    """Opcion 7: avisa de los productos con stock bajo."""
    bajos = reportes.productos_stock_bajo()
    if len(bajos) == 0:
        print("No hay productos con stock bajo.")
        return
    for producto in bajos:
        print(
            "OJO:",
            producto["nombre"],
            "solo tiene",
            producto["stock"],
            "unidades",
        )


def _guardar_y_salir() -> None:
    """Opcion 8: guarda los datos y se despide."""
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")


OPCIONES: dict[str, Callable[[], None]] = {
    "1": _agregar_producto,
    "2": _registrar_venta,
    "3": _cotizar,
    "4": _mostrar_inventario,
    "5": _mostrar_resumen_ventas,
    "6": _mostrar_mas_vendidos,
    "7": _mostrar_alertas_stock,
}


def menu() -> None:
    """Ejecuta el bucle del menu interactivo hasta guardar y salir."""
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.hay_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)
    while True:
        _imprimir_menu()
        opcion = input("Opcion: ")
        if opcion == "8":
            _guardar_y_salir()
            break
        handler = OPCIONES.get(opcion)
        if handler is None:
            print("Opcion no valida.")
            continue
        handler()


if __name__ == "__main__":
    menu()
