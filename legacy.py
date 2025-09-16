from pyvis.network import Network
import networkx as nx
import pandas as pd
import os

# === Cargar datos desde Excel ===
file_path = "Tabla relaciones_T.xlsx"
df = pd.read_excel(file_path, sheet_name="Hoja1", index_col=0)

# Crear grafo dirigido que soporte múltiples aristas
G = nx.MultiDiGraph()

# Carpeta de imágenes
image_folder = "a"

# Crear nodos
for name in df.index:
    image_path = None
    for ext in [".png", ".jpg", ".jpeg", ".gif"]:
        test_path = os.path.join(image_folder, f"{name}{ext}")
        if os.path.exists(test_path):
            image_path = f"{image_folder}/{name}{ext}"
            print("✅ Imagen encontrada:", image_path)
            break

    if image_path:
        G.add_node(name, label=name, shape="circularImage", image=image_path)
    else:
        G.add_node(name, label=name, shape="dot")




# === Crear aristas ===
nombres = df.index.tolist()

for i, source in enumerate(nombres):
    for j, target in enumerate(nombres):
        if j <= i:  # evita diagonal y duplicados (solo pares i<j)
            continue

        val_s_t = df.loc[source, target]  # source -> target
        val_t_s = df.loc[target, source]  # target -> source

        s_exists = pd.notna(val_s_t) and val_s_t != 0
        t_exists = pd.notna(val_t_s) and val_t_s != 0

        # Ambos existen
        if s_exists and t_exists:
            if val_s_t == val_t_s:
                G.add_edge(source, target, tipo=int(val_s_t), arrows="to, from")
            else:
                # Distintos -> 2 aristas: cada una en su dirección
                G.add_edge(source, target, tipo=int(val_s_t), dir="forward")
                G.add_edge(target, source, tipo=int(val_t_s), dir="forward")

        # Solo source -> target
        elif s_exists:
           G.add_edge(source, target, tipo=int(val_s_t), dir="forward")

        # Solo target -> source
        elif t_exists:
            G.add_edge(target, source, tipo=int(val_t_s), dir="forward")



# === Calcular cardinalidad según grafo construido ===
cardinalidad = {}
for nodo in G.nodes():
    out_count = G.out_degree(nodo)
    in_count = G.in_degree(nodo)
    cardinalidad[nodo] = out_count + in_count

# Colores de relaciones
colores = {
    0: "black",
    1: "black",
    2: "#6f370f",
    3: "#ab00af",
    4: "#71ec6b",
    5: "#7049bd",
    6: "#f27523",
    7: "#ff66c4",
    8: "#faff00",
    9: "#ff3131",
    10: "#5ce1e6"
}

# Crear red en PyVis
net = Network(height="1920px", width="100%", bgcolor="#222222", font_color="white", directed=True)
net.barnes_hut(gravity=-7000000, central_gravity=0, spring_length=200, spring_strength=0.01)

# Pasar grafo a PyVis
net.from_nx(G)

# Ajustar tamaño y tooltip
for node in net.nodes:
    nodo_id = node["id"]
    card = cardinalidad.get(nodo_id, 0)
    node["size"] = 10 + card * 5
    node["title"] = f"<b>{nodo_id}</b><br>Cardinalidad: {card}"
    node["label"] = f"{nodo_id}\n({card})"

# Colorear aristas y agregar dirección
for e in net.edges:
    # Como es MultiDiGraph, puede haber varias aristas entre los mismos nodos
    datos = G.get_edge_data(e['from'], e['to'])
    if datos:
        tipo = list(datos.values())[0].get("tipo", 1)  # tomar el primer valor
        e["color"] = colores.get(tipo, "gray")
    e["arrows"] = "to"
    e["smooth"] = {"enabled": True, "type": "curvedCW"}  # 🔹 curva para diferenciar

# Guardar resultado
net.write_html("grafo_imagenes.html")
print("✅ Grafo guardado en 'grafo_imagenes.html'")
