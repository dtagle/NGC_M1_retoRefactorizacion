"""Tests de caracterizacion: casos limite descubiertos durante la refactorizacion.

Fijan el comportamiento observable que se debe conservar (incluidas rarezas
conocidas, como que `cotizar` no aplica el descuento VIP). Solo usan la API
publica que ya usaban los tests originales, asi que tambien pasan contra el
codigo original del reto.
"""

import json

import pytest

import almacen
import gestor
import reportes


def _alta(codigo, nombre, precio, stock):
    assert gestor.agregarProducto(codigo, nombre, precio, stock) is True


# ---------------------------------------------------------------- descuentos
@pytest.mark.parametrize(
    "precio, descuento",
    [
        (499.99, 0),  # justo debajo del umbral medio
        (500, 25.0),  # umbral medio inclusivo (>=): 5 %
        (999.99, 50.0),  # justo debajo del umbral alto (5 %, redondeado)
        (1000, 100.0),  # umbral alto inclusivo (>=): 10 %
    ],
)
def test_umbrales_de_descuento_son_inclusivos(precio, descuento):
    _alta("A", "Producto", precio, 1)
    venta = gestor.registrar_venta("A", 1)
    assert venta["descuento"] == pytest.approx(descuento, abs=0.01)


def test_cotizar_no_aplica_descuento_vip_pero_la_venta_si():
    _alta("A", "Producto", 555, 5)
    cotizacion = gestor.cotizar("A", 1)
    venta = gestor.registrar_venta("A", 1, "VIP001")
    assert cotizacion == 611.61
    assert venta["descuento"] == 38.85  # 5 % por volumen + 2 % VIP
    assert venta["total"] == 598.73
    assert venta["total"] < cotizacion


def test_descuento_vip_requiere_compra_mayor_a_200_estricto():
    _alta("A", "Exacto", 200, 2)
    _alta("B", "Mayor", 200.01, 2)
    assert gestor.registrar_venta("A", 1, "VIP1")["descuento"] == 0
    assert gestor.registrar_venta("B", 1, "VIP1")["descuento"] == 4.0


@pytest.mark.parametrize("cliente", ["vip001", "VI", "XVIP", "", None, "Juan"])
def test_solo_el_prefijo_VIP_en_mayusculas_da_descuento_extra(cliente):
    _alta("A", "Producto", 300, 5)
    venta = gestor.registrar_venta("A", 1, cliente)
    assert venta["descuento"] == 0
    assert venta["total"] == 348.0


# --------------------------------------------------- validaciones de ventas
@pytest.mark.parametrize(
    "codigo, cantidad, error",
    [
        (None, 1, "codigo vacio"),
        ("", 1, "codigo vacio"),
        ("NOEXISTE", 1, "producto no existe"),
        ("NOEXISTE", 0, "producto no existe"),  # existencia antes que cantidad
        ("A", None, "cantidad invalida"),
        ("A", 0, "cantidad invalida"),
        ("A", -3, "cantidad invalida"),
        ("A", 99, "stock insuficiente"),
    ],
)
def test_orden_y_mensaje_de_cada_validacion_de_venta(codigo, cantidad, error):
    _alta("A", "Producto", 10, 5)
    assert gestor.registrar_venta(codigo, cantidad) is None
    assert gestor.ultimo_error == error


def test_una_venta_fallida_no_consume_folio_ni_stock():
    _alta("A", "Producto", 10, 2)
    assert gestor.registrar_venta("A", 5) is None
    venta = gestor.registrar_venta("A", 2)
    assert venta["folio"] == 1
    assert gestor.INVENTARIO["A"]["stock"] == 0


def test_cotizar_valida_distinto_que_registrar_venta():
    _alta("A", "Producto", 10, 1)
    assert gestor.cotizar("", 1) is None
    assert gestor.ultimo_error == "producto no existe"  # no "codigo vacio"
    assert gestor.cotizar("A", 0) is None
    assert gestor.ultimo_error == "cantidad invalida"
    assert gestor.cotizar("A", 500) == 5220.0  # no revisa el stock (10 % de desc.)


def test_ticket_omite_la_linea_de_descuento_si_no_hay():
    _alta("A", "Cafe", 100, 20)
    sin_descuento = gestor.registrar_venta("A", 1)["ticket"]
    con_descuento = gestor.registrar_venta("A", 10)["ticket"]
    assert "Descuento" not in sin_descuento
    assert "Descuento: -$100.0" in con_descuento
    assert sin_descuento.startswith("TIENDA LA ESQUINA\n")
    assert sin_descuento.endswith("TOTAL: $116.0\n")


def test_la_venta_tiene_las_claves_esperadas():
    _alta("A", "Cafe", 100, 20)
    venta = gestor.registrar_venta("A", 1, "Ana")
    assert list(venta) == [
        "folio", "codigo", "nombre", "cantidad", "subtotal", "descuento",
        "impuesto", "total", "cliente", "fecha", "ticket",
    ]  # fmt: skip
    assert gestor.VENTAS == [venta]


# -------------------------------------------------------------- inventario
def test_actualizar_stock_rechaza_dejarlo_negativo_y_producto_inexistente():
    _alta("A", "Producto", 10, 3)
    assert gestor.actualizar_stock("A", -4) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"
    assert gestor.INVENTARIO["A"]["stock"] == 3
    assert gestor.actualizar_stock("ZZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"


def test_buscar_producto_ignora_mayusculas_y_texto_vacio_devuelve_todo():
    _alta("A", "Cafe de grano", 10, 1)
    _alta("B", "Azucar", 10, 1)
    assert [p["codigo"] for p in gestor.buscarProducto("CAFE")] == ["A"]
    assert len(gestor.buscarProducto("")) == 2
    assert gestor.buscarProducto("zzz") == []


# ---------------------------------------------------------------- reportes
def test_mas_vendidos_empates_en_orden_de_primera_aparicion():
    for codigo in "ABCD":
        _alta(codigo, f"Producto {codigo}", 1, 100)
    for codigo, cantidad in [("B", 2), ("A", 2), ("C", 5), ("D", 2), ("A", 3)]:
        gestor.registrar_venta(codigo, cantidad)
    assert reportes.mas_vendidos() == [("A", 5), ("C", 5), ("B", 2)]
    assert reportes.mas_vendidos(0) == []
    assert len(reportes.mas_vendidos(100)) == 4


def test_stock_bajo_es_estricto_menor_a_cinco():
    _alta("A", "Cinco", 1, 5)
    _alta("B", "Cuatro", 1, 4)
    assert [p["codigo"] for p in reportes.productos_stock_bajo()] == ["B"]


def test_reportes_vacios_y_formato_de_dinero_sin_forzar_dos_decimales(capsys):
    assert reportes.total_vendido() == 0
    assert reportes.mas_vendidos() == []
    _alta("A", "Cafe", 23.2, 2)
    texto = reportes.reporte_inventario()
    assert capsys.readouterr().out == texto + "\n"  # imprime y regresa lo mismo
    assert "A | Cafe | $23.2 | stock: 2  <-- STOCK BAJO\n" in texto
    assert texto.endswith("Valor total del inventario: $46.4\n")


def test_resumen_de_ventas_imprime_y_regresa_el_mismo_texto(capsys):
    _alta("A", "Cafe", 100, 5)
    gestor.registrar_venta("A", 2)
    texto = reportes.resumen_ventas()
    assert capsys.readouterr().out == texto + "\n"
    assert "Folio 1: Cafe x2 = $232.0\n" in texto
    assert texto.endswith("Numero de ventas: 1\nTotal del dia: $232.0\n")


# --------------------------------------------------------------- persistencia
def test_cargar_reemplaza_el_estado_en_el_sitio_sin_reasignar(tmp_path):
    _alta("VIEJO", "Viejo", 1, 1)
    inventario, ventas = gestor.INVENTARIO, gestor.VENTAS
    ruta = tmp_path / "datos.json"
    ruta.write_text(
        json.dumps({"inventario": {"N": {"codigo": "N", "nombre": "Nuevo",
                                         "precio": 1, "stock": 1}},
                    "ventas": [{"folio": 1}], "contador": 4}),
        encoding="utf-8",
    )  # fmt: skip
    assert almacen.cargar_datos(str(ruta)) is True
    assert gestor.INVENTARIO is inventario and gestor.VENTAS is ventas
    assert list(gestor.INVENTARIO) == ["N"]
    _alta("A", "Producto", 10, 1)
    assert gestor.registrar_venta("A", 1)["folio"] == 5  # el folio continua


@pytest.mark.parametrize(
    "contenido",
    [b"{no es json", b"", b"\xff\xfe\x00\x80"],
    ids=["mal_formado", "vacio", "no_utf8"],
)
def test_archivo_corrupto_devuelve_false_y_no_toca_el_estado(tmp_path, contenido):
    _alta("A", "Producto", 10, 1)
    ruta = tmp_path / "malo.json"
    ruta.write_bytes(contenido)
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert list(gestor.INVENTARIO) == ["A"]


def test_json_sin_claves_obligatorias_lanza_keyerror_como_antes(tmp_path):
    ruta = tmp_path / "incompleto.json"
    ruta.write_text(json.dumps({"ventas": []}), encoding="utf-8")
    with pytest.raises(KeyError):
        almacen.cargar_datos(str(ruta))


def test_guardar_escribe_json_indentado_y_con_acentos_legibles(tmp_path):
    _alta("A", "Café", 10, 1)
    ruta = tmp_path / "salida.json"
    assert almacen.guardar_datos(str(ruta)) is True
    texto = ruta.read_text(encoding="utf-8")
    assert "Café" in texto  # ensure_ascii=False
    assert texto.startswith('{\n  "inventario": {')  # indent=2
    assert json.loads(texto)["contador"] == 0
