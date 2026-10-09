import sys, os, json, importlib.util
S = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, S)
import gestor_nuevo; sys.modules["gestor"] = gestor_nuevo
def cargar(ruta, n):
    sp = importlib.util.spec_from_file_location(n, ruta); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
v = cargar(f"{S}/alm/almacen_vieja.py","av"); n = cargar(os.path.join(sys.argv[1],"almacen.py"),"an")
gestor_nuevo.agregarProducto("A","Arroz",10,50); gestor_nuevo.registrar_venta("A",2,"VIP1")
v.guardar_datos(f"{S}/v.json"); n.guardar_datos(f"{S}/n.json")
print("JSON identico (sin fecha):", json.load(open(f"{S}/v.json")) | {} == json.load(open(f"{S}/n.json")) or "ver")
print("bytes iguales:", open(f"{S}/v.json").read() == open(f"{S}/n.json").read())
