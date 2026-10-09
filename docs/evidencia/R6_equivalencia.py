import io, random, sys, contextlib
sys.path.insert(0, "src")
sys.path.insert(0, sys.argv[1])
import gestor, reportes, reportes_anterior as viejo

def prod(i, stock, precio):
    return {"codigo": f"P{i}", "nombre": f"Prod {i}", "precio": precio, "stock": stock}

def venta(i, cod, cant, total):
    return {"folio": i, "codigo": cod, "nombre": f"Prod {cod}", "cantidad": cant, "total": total}

def silencioso(f, *a):
    with contextlib.redirect_stdout(io.StringIO()) as o:
        r = f(*a)
    return r, o.getvalue()

def escenarios():
    yield [], []
    yield [prod(1, 2, 10.5)], []
    # empates en unidades, distinto orden de primera aparicion
    yield [prod(1, 1, 1.1), prod(2, 50, 0.1)], [
        venta(1, "B", 2, 0.1), venta(2, "A", 2, 0.2), venta(3, "C", 5, 0.3),
        venta(4, "D", 2, 0.7), venta(5, "A", 3, 1.1), venta(6, "B", 3, 2.3)]
    rnd = random.Random(7)
    for _ in range(300):
        inv = [prod(i, rnd.randint(0, 12), round(rnd.uniform(0, 99), 2))
               for i in range(rnd.randint(0, 8))]
        ven = [venta(i, rnd.choice("ABCDEF"), rnd.randint(1, 4),
                     rnd.uniform(0, 500) * rnd.choice([1, 0.1, 1.005]))
               for i in range(rnd.randint(0, 15))]
        yield inv, ven

n = 0
for inv, ven in escenarios():
    gestor.INVENTARIO.clear(); gestor.INVENTARIO.update({p["codigo"]: p for p in inv})
    gestor.VENTAS[:] = ven
    for nombre in ("productos_stock_bajo", "reporte_inventario", "total_vendido",
                   "resumen_ventas", "mas_vendidos"):
        for args in ([(), (0,), (1,), (2,), (100,), (-1,)] if nombre == "mas_vendidos" else [()]):
            assert silencioso(getattr(reportes, nombre), *args) == \
                   silencioso(getattr(viejo, nombre), *args), (nombre, args, inv, ven)
            n += 1
    for v in (0, 1, 2.675, 1234.5678, -3.14159):
        assert reportes.formatear_dinero(v) == viejo.formatear_dinero(v); n += 1
print("OK, comparaciones identicas:", n)
