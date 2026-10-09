import importlib.util, sys, copy, json, os, tempfile
S = os.path.dirname(os.path.abspath(__file__))
def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, f"{S}/{nombre}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
V, N = cargar("gestor_viejo"), cargar("gestor_nuevo")

def limpia(r):
    if isinstance(r, dict):
        return {k: v for k, v in r.items() if k != "fecha"}
    return r

def correr(m, ops):
    out = []
    for nombre, args in ops:
        try:
            r = getattr(m, nombre)(*args)
            r = ("ok", copy.deepcopy(limpia(r)) if not isinstance(r, list) else [limpia(x) for x in copy.deepcopy(r)])
        except Exception as e:
            r = ("exc", type(e).__name__, str(e))
        ventas = [limpia(v) for v in m.VENTAS]
        out.append((nombre, args, r, m.ultimo_error, json.dumps(m.INVENTARIO, sort_keys=False),
                    json.dumps(ventas), m.contador_ventas))
    return out

ops = [("reiniciar_sistema", ())]
for a in [(None,"x",1,1),("","x",1,1),("A1","Arroz",10.5,100),("A1","dup",1,1),("B2","Frijol",0,5),
          ("B2","Frijol",-3,5),("B2","Frijol",5,-1),("B2","Frijol Negro",5,0),("C3","Cafe MOLIDO",300,10),
          ("D4","Tele",2500,3),("E5","Pan",1,"x")]:
    ops.append(("agregarProducto", a))
for t in ["a","ARROZ","cafe","zzz","","o"]:
    ops.append(("buscarProducto", (t,)))
ops.append(("buscarProducto", (None,)))
for a in [("A1",5),("A1",-1000),("A1",-5),("ZZ",1),("B2",0),("A1",None)]:
    ops.append(("actualizar_stock", a))
for cod, cant in [("A1",1),("A1",0),("A1",-2),("A1",None),("ZZ",1),("",1),(None,1),("C3",2),("C3",1),
                  ("D4",1),("D4",2),("A1",60),("A1",1000),("C3",4)]:
    for cli in ["", None, "VIP1", "vip", "Juan", "VIPX"]:
        ops.append(("registrar_venta", (cod, cant, cli)))
    ops.append(("registrar_venta", (cod, cant)))
    ops.append(("cotizar", (cod, cant)))
ops += [("eliminar_producto", ("A1",)), ("eliminar_producto", ("A1",)), ("cotizar", ("A1",1)),
        ("reiniciar_sistema", ()), ("registrar_venta", ("A1",1)), ("eliminar_producto", ("Q",))]

a, b = correr(V, ops), correr(N, ops)
difs = [(x, y) for x, y in zip(a, b) if x != y]
mensajes = {x[3] for x in a}
print("operaciones:", len(ops), "| diferencias:", len(difs))
print("mensajes de error cubiertos:", sorted(mensajes))
print("ventas OK:", sum(1 for x in a if x[0]=="registrar_venta" and x[2][0]=="ok" and x[2][1]),
      "| con descuento:", sum(1 for x in a if x[0]=="registrar_venta" and x[2][0]=="ok" and x[2][1] and x[2][1]["descuento"]>0))
print("excepciones en ambos:", sum(1 for x in a if x[2][0]=="exc"))
for d in difs[:5]: print(d)

# orden de claves de producto y persistencia
sys.path.insert(0, S)
for m in (V, N):
    m.reiniciar_sistema(); m.agregarProducto("K","k",1,1)
print("claves iguales:", list(V.INVENTARIO["K"]) == list(N.INVENTARIO["K"]) == ["codigo","nombre","precio","stock"])
sys.exit(1 if difs else 0)
