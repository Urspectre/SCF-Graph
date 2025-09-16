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

# Cargar/buscar imagenes y crear nodos
for name in df.index:
    image_path = None
    for ext in [".png", ".jpg", ".jpeg", ".gif"]:
        test_path = os.path.join(image_folder, f"{name}{ext}")
        if os.path.exists(test_path):
            image_path = f"{image_folder}/{name}{ext}"
            #print("✅ Imagen encontrada:", image_path)
            break

    if image_path:
        G.add_node(name, label=name, shape="circularImage", image=image_path)
    else:
        G.add_node(name, label=name, shape="dot")




# === Crear aristas ===
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
                # 🔹 UNA sola arista, pero con flechas en ambos extremos
                G.add_edge(source, target, tipo=int(val_s_t), arrows={"to": True, "from": True})
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
    10: "#5ce1e6",
    11: "gray",
    12:"#0000ff"
}

# Crear red en PyVis
net = Network(height="1920px", width="1080px%", bgcolor="#222222", font_color="white", directed=True)
net.barnes_hut(gravity=-7000000, central_gravity=10, spring_length=1000, spring_strength=0.01)

# Pasar grafo a PyVis
net.from_nx(G)

# Ajustar tamaño y tooltip de nodos según cardinalidad
for node in net.nodes:
    nodo_id = node["id"]
    card = cardinalidad.get(nodo_id, 0)
    node["size"] = 10 + card * 5
    node["title"] = f"<b>{nodo_id}</b><br>Cardinalidad: {card}"
    node["label"] = f"{nodo_id}\n({card})"

# Colorear aristas y agregar dirección
for e in net.edges:
    datos = G.get_edge_data(e['from'], e['to'])
    if datos:
        tipo = list(datos.values())[0].get("tipo", 1)  # tomar el primer valor
        e["color"] = colores.get(tipo, "gray")
        e["tipo"] = tipo   # 🔹 guardar tipo en el JSON

    # Si la arista ya trae {"to":True,"from":True}, PyVis la respeta
    if not isinstance(e.get("arrows"), dict):
        e["arrows"] = "to"   # por defecto, solo hacia el destino

    e["smooth"] = {"enabled": True, "type": "vertical"}  # curva para diferenciar



# Guardar resultado
net.write_html("grafo_imagenes.html")
# Guardar resultado inicial
output_file = "grafo_imagenes.html"
net.write_html(output_file)

# Inyectar código JS para selector de filtros
with open(output_file, "r", encoding="utf-8") as f:
    html = f.read()

# Script de filtros
script = """
<script>
function toggleEdges(tipo) {
    var edges = network.body.data.edges;  // vis.DataSet
    edges.forEach(function (edge) {
        if (edge.tipo == tipo) {
            edges.update({id: edge.id, hidden: !edge.hidden});
        }
    });
}

window.addEventListener("load", function () {
    var container = document.createElement("div");
    container.style.position = "fixed";
    container.style.top = "10px";
    container.style.right = "10px";
    container.style.background = "rgba(0,0,0,0.7)";
    container.style.padding = "10px";
    container.style.borderRadius = "8px";
    container.style.color = "white";
    container.style.zIndex = "9999";
    container.innerHTML = "<b>Filtrar Relaciones</b><br>";

    var nombres = {
        1: "odio",
        2: "enemistad",
        3: "neutralidad",
        4: "conocido",
        5: "respeto",
        6: "amistad",
        7: "interes amoroso",
        8: "mejores amigos",
        9: "relacion amorosa",
        10: "familia",
        11: "miedo",
        12: "rivalidad"
    };

    for (let i = 1; i <= 12; i++) {
        let cb = document.createElement("input");
        cb.type = "checkbox";
        cb.id = "tipo" + i;
        cb.checked = true;
        cb.onclick = function() { toggleEdges(i); };

        let label = document.createElement("label");
        label.htmlFor = cb.id;
        label.style.marginRight = "10px";
        label.innerText = nombres[i];

        container.appendChild(cb);
        container.appendChild(label);
        container.appendChild(document.createElement("br"));
    }

    document.body.appendChild(container);

    // Guardamos estado inicial de visibilidad de aristas
    var originalEdges = {};
    network.body.data.edges.forEach(function(edge) {
        originalEdges[edge.id] = edge.hidden || false;
    });

    // Evento: clic en nodo
    network.on("selectNode", function (params) {
        var selectedNode = params.nodes[0];
        var edges = network.body.data.edges;

        edges.forEach(function (edge) {
            if (edge.from == selectedNode || edge.to == selectedNode) {
                edges.update({id: edge.id, hidden: false}); // mostrar conexión
            } else {
                edges.update({id: edge.id, hidden: true});  // ocultar lo demás
            }
        });
    });

    // Evento: clic fuera de un nodo (para restaurar)
    network.on("deselectNode", function () {
        var edges = network.body.data.edges;
        edges.forEach(function (edge) {
            edges.update({id: edge.id, hidden: originalEdges[edge.id]});
        });
    });

    network.on("click", function (params) {
        if (params.nodes.length === 0) {
            var edges = network.body.data.edges;
            edges.forEach(function (edge) {
                edges.update({id: edge.id, hidden: originalEdges[edge.id]});
            });
        }
    });
});
</script>
"""


# Insertar script antes del cierre </body>
html = html.replace("</body>", script + "\n</body>")

# Guardar HTML con el filtro
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)


print("✅ Grafo con selector de filtros guardado en 'grafo_imagenes.html'")


