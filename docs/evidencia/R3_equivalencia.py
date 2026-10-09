import sys, importlib.util, itertools
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
old = load("gestor_old", sys.argv[1]); new = load("gestor_new", sys.argv[2])
def setup(m):
    m.reiniciar_sistema()
    m.agregarProducto("A", "Cafe", 185.0, 12); m.agregarProducto("B", "Azucar", 32.5, 40)
    m.agregarProducto("C", "Caro", 999.99, 100)
setup(old); setup(new)
codigos = [None, "", "Z", "A", "B", "C"]
cants = [None, 0, -1, 1, 2, 3, 5, 13, 40, 41]
clientes = ["", None, "VIP", "VIP9", "vip", "VI", "Juan"]
n = bad = 0
for c, q, cli in itertools.product(codigos, cants, clientes):
    ro = old.registrar_venta(c, q, cli); rn = new.registrar_venta(c, q, cli)
    n += 1
    if ro is not None: ro.pop("fecha"); 
    if rn is not None: rn.pop("fecha")
    if ro != rn or old.ultimo_error != new.ultimo_error or old.contadorVentas != new.contadorVentas or old.INVENTARIO != new.INVENTARIO:
        bad += 1; print("DIFF", c, q, cli, ro, rn)
print("casos:", n, "diferencias:", bad, "ventas:", len(old.VENTAS), len(new.VENTAS))
