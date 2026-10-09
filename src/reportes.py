# -*- coding: utf-8 -*-
"""Reportes de la tienda: inventario, ventas y mas vendidos."""

import gestor


def formatear_dinero(valor):
    # le da formato de dinero al numero
    return "$" + str(round(valor, 2))


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    productos_bajos = []
    for codigo in gestor.INVENTARIO:
        if gestor.INVENTARIO[codigo]["stock"] < gestor.STOCK_MINIMO:
            productos_bajos.append(gestor.INVENTARIO[codigo])
    return productos_bajos


def reporte_inventario():
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


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    total = 0
    for venta in gestor.VENTAS:
        total = total + venta["total"]
    return round(total, 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades)."""
    unidades_por_codigo = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        if codigo in unidades_por_codigo:
            unidades_por_codigo[codigo] = (
                unidades_por_codigo[codigo] + venta["cantidad"]
            )
        else:
            unidades_por_codigo[codigo] = venta["cantidad"]
    ranking = []
    for codigo in unidades_por_codigo:
        ranking.append((codigo, unidades_por_codigo[codigo]))
    # ordenamiento de burbuja (TODO: algun dia usar sorted)
    for i in range(len(ranking)):
        for j in range(0, len(ranking) - i - 1):
            if ranking[j][1] < ranking[j + 1][1]:
                anterior = ranking[j]
                ranking[j] = ranking[j + 1]
                ranking[j + 1] = anterior
    return ranking[0:n]


def resumen_ventas():
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
