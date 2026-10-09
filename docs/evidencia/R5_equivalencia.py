"""Compara almacen.py (version anterior vs nueva) ante varios archivos de entrada."""
import importlib, json, os, sys, tempfile

def cargar(raiz):
    for m in ("gestor", "almacen"):
        sys.modules.pop(m, None)
    sys.path.insert(0, raiz)
    try:
        return importlib.import_module("gestor"), importlib.import_module("almacen")
    finally:
        sys.path.remove(raiz)

def casos(tmp):
    def w(nombre, datos, modo="w", **kw):
        ruta = os.path.join(tmp, nombre)
        with open(ruta, modo, **kw) as f:
            f.write(datos)
        return ruta
    inv = {"A": {"codigo": "A", "nombre": "Café", "precio": 1.5, "stock": 2}}
    ok = json.dumps({"inventario": inv, "ventas": [{"folio": 1}], "contador": 7})
    return {
        "inexistente": os.path.join(tmp, "no_existe.json"),
        "valido": w("ok.json", ok, encoding="utf-8"),
        "sin_contador": w("sc.json", json.dumps({"inventario": inv, "ventas": []}), encoding="utf-8"),
        "json_mal_formado": w("mal.json", "{no es json", encoding="utf-8"),
        "vacio": w("vacio.json", "", encoding="utf-8"),
        "no_utf8": w("bin.json", b"\xff\xfe\x00\x80", "wb"),
        "falta_inventario": w("fi.json", json.dumps({"ventas": []}), encoding="utf-8"),
        "falta_ventas": w("fv.json", json.dumps({"inventario": inv}), encoding="utf-8"),
        "directorio": tmp,
        "anidado_profundo": w("deep.json", "[" * 100000 + "]" * 100000, encoding="utf-8"),
    }

def correr(raiz, tmp):
    gestor, almacen = cargar(raiz)
    res = {}
    for nombre, ruta in casos(tmp).items():
        gestor.reiniciar_sistema()
        gestor.agregarProducto("PREVIO", "Previo", 1, 1)
        try:
            r = almacen.cargar_datos(ruta)
        except BaseException as e:
            r = "EXC:" + type(e).__name__
        res[nombre] = (r, gestor.ultimo_error, json.dumps(gestor.INVENTARIO, sort_keys=True),
                       list(gestor.VENTAS), gestor.contador_ventas if hasattr(gestor, "contador_ventas") else gestor.contadorVentas,
                       almacen.hay_archivo(ruta) if hasattr(almacen, "hay_archivo") else almacen.hayArchivo(ruta))
    # guardar_datos: contenido byte a byte
    gestor.reiniciar_sistema(); gestor.agregarProducto("A", "Azúcar", 32.5, 4)
    salida = os.path.join(tmp, "salida.json")
    r = almacen.guardar_datos(salida)
    res["guardar"] = (r, open(salida, "rb").read())
    return res

with tempfile.TemporaryDirectory() as tmp:
    old = correr(sys.argv[1], tmp)
    new = correr(sys.argv[2], tmp)
dif = 0
for k in old:
    igual = old[k] == new[k]
    dif += not igual
    print(("IGUAL   " if igual else "DIFERENTE"), k, "| antes:", str(old[k][0])[:40], "| ahora:", str(new[k][0])[:40])
print("casos:", len(old), "diferencias:", dif)
