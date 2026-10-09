"""Reportes de la tienda: inventario, ventas y mas vendidos."""

from typing import Any

import gestor

Producto = dict[str, Any]


def formatear_dinero(valor: float) -> str:
    """Da formato de dinero al valor, redondeado a dos decimales."""
    return "$" + str(round(valor, 2))


def productos_stock_bajo() -> list[Producto]:
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [
        producto
        for producto in gestor.INVENTARIO.values()
        if producto["stock"] < gestor.STOCK_MINIMO
    ]


def reporte_inventario() -> str:
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    reporte = "===== INVENTARIO =====\n"
    valor_total = 0
    for codigo in gestor.INVENTARIO:
        producto = gestor.INVENTARIO[codigo]
        linea = producto["codigo"] + " | " + producto["nombre"] + " | "
        linea = linea + formatear_dinero(producto["precio"])
        linea = linea + " | stock: " + str(producto["stock"])
        if producto["stock"] < gestor.STOCK_MINIMO:
            linea = linea + "  <-- STOCK BAJO"
        reporte = reporte + linea + "\n"
        valor_total = valor_total + producto["precio"] * producto["stock"]
    reporte = reporte + "Valor total del inventario: "
    reporte = reporte + formatear_dinero(valor_total) + "\n"
    print(reporte)
    return reporte


def total_vendido() -> float:
    """Suma el total (con IVA) de todas las ventas registradas."""
    return round(sum(venta["total"] for venta in gestor.VENTAS), 2)


def mas_vendidos(n: int = 3) -> list[tuple[str, int]]:
    """Regresa los n productos mas vendidos como lista de (codigo, unidades)."""
    unidades_por_codigo: dict[str, int] = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        unidades_por_codigo[codigo] = (
            unidades_por_codigo.get(codigo, 0) + venta["cantidad"]
        )
    ranking = sorted(
        unidades_por_codigo.items(), key=lambda par: par[1], reverse=True
    )
    return ranking[0:n]


def resumen_ventas() -> str:
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    resumen = "===== RESUMEN DE VENTAS =====\n"
    total = 0
    for venta in gestor.VENTAS:
        resumen = resumen + "Folio " + str(venta["folio"]) + ": " + venta["nombre"]
        resumen = resumen + " x" + str(venta["cantidad"]) + " = "
        resumen = resumen + formatear_dinero(venta["total"]) + "\n"
        total = total + venta["total"]
    resumen = resumen + "Numero de ventas: " + str(len(gestor.VENTAS)) + "\n"
    resumen = resumen + "Total del dia: " + formatear_dinero(total) + "\n"
    print(resumen)
    return resumen
