import streamlit as st
import sqlite3
import os
from PIL import Image
from datetime import datetime

# --- Configuración inicial ---
CARPETA_IMAGENES = "imagenes_muebles"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

# Conexión a la base de datos
conn = sqlite3.connect("muebles.db")
c = conn.cursor()

# Configuración de la página
st.set_page_config(
    page_title="Inventario El Jueves",
    page_icon="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png",
    layout="wide"
)

st.title("🪑 Inventario de Antigüedades El Jueves")

# --- MIGRACIÓN: Añade columnas si no existen ---
try:
    c.execute("ALTER TABLE muebles ADD COLUMN tipo TEXT DEFAULT 'Otro'")
    c.execute("ALTER TABLE muebles ADD COLUMN medida1 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida2 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida3 REAL")
    conn.commit()
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e):
        st.error(f"Error al actualizar la BD: {e}")

# Crear tabla con los nuevos campos
c.execute("""
    CREATE TABLE IF NOT EXISTS muebles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL,
        descripcion TEXT,
        ruta_imagen TEXT,
        fecha TEXT,
        vendido BOOLEAN DEFAULT 0,
        tienda TEXT,
        tipo TEXT,
        medida1 REAL,
        medida2 REAL,
        medida3 REAL
    )
""")
conn.commit()

# --- Sidebar con estadísticas ---
st.sidebar.markdown("## 📊 Estadísticas")
c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 0 AND tienda = 'El Rastro'")
en_rastro = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 0 AND tienda = 'Regueros'")
en_regueros = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 1")
vendidos = c.fetchone()[0]

st.sidebar.metric("🔵 En El Rastro", en_rastro)
st.sidebar.metric("🔴 En Regueros", en_regueros)
st.sidebar.metric("💰 Vendidos", vendidos)

# --- Formulario para añadir muebles ---
with st.expander("📥 Añadir nueva antigüedad", expanded=False):
    with st.form(key="form_mueble"):
        # Campos del formulario
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.radio(
                "Tienda",
                options=["El Rastro", "Regueros"],
                horizontal=True
            )
        with col2:
            vendido = st.checkbox("Marcar como vendido")
        
        nombre = st.text_input("Nombre de la antigüedad*")
        precio = st.number_input("Precio (€)*", min_value=0.0, step=1.0)
        descripcion = st.text_area("Descripción")
        
        # Selector de tipo de mueble
        tipo = st.selectbox("Tipo de mueble*", [
            "Mesa", "Consola", "Buffet", "Biblioteca", 
            "Armario", "Cómoda", "Columna", "Espejo", 
            "Tinaja", "Silla", "Otro artículo"
        ])
        
        # Campos de medidas según el tipo
        if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
            st.markdown("**Medidas requeridas:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Largo (cm)*", min_value=0, help="Distancia entre los extremos más largos")
            with col2:
                medida2 = st.number_input("Alto (cm)*", min_value=0, help="Altura desde el suelo hasta la parte superior")
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0, help="Profundidad de frente a atrás")
                
        elif tipo in ["Biblioteca", "Armario"]:
            st.markdown("**Medidas requeridas:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, help="Altura total del mueble")
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0, help="Ancho total de lado a lado")
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0, help="Profundidad de los estantes")
                
        elif tipo == "Columna":
            st.markdown("**Medidas requeridas:**")
            col1, col2 = st.columns(2)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, help="Altura total de la columna")
            with col2:
                medida2 = st.number_input("Lados de la base*", min_value=3, max_value=8, value=4, help="Número de lados (ej: 4 para base cuadrada)")
                
        elif tipo == "Espejo":
            st.markdown("**Medidas requeridas:**")
            col1, col2 = st.columns(2)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, help="Altura del espejo sin marco")
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0, help="Ancho del espejo sin marco")
                
        elif tipo == "Tinaja":
            st.markdown("**Medidas requeridas:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, help="Altura total desde la base hasta el borde")
            with col2:
                medida2 = st.number_input("Diámetro base (cm)*", min_value=0, help="Ancho de la parte inferior")
            with col3:
                medida3 = st.number_input("Diámetro boca (cm)*", min_value=0, help="Ancho de la apertura superior")
                
        else:  # Para sillas y otros artículos
            st.markdown("**Medidas opcionales:**")
            col1, col2 = st.columns(2)
            with col1:
                medida1 = st.number_input("Alto (cm)", min_value=0, help="Altura aproximada")
            with col2:
                medida2 = st.number_input("Ancho (cm)", min_value=0, help="Ancho aproximado")
        
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])
        
        # Botón de guardar
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0 and tipo:
                # Validación de medidas según tipo
                required_fields = {
                    "Mesa": [medida1, medida2, medida3],
                    "Consola": [medida1, medida2, medida3],
                    "Buffet": [medida1, medida2, medida3],
                    "Cómoda": [medida1, medida2, medida3],
                    "Biblioteca": [medida1, medida2, medida3],
                    "Armario": [medida1, medida2, medida3],
                    "Columna": [medida1, medida2],
                    "Espejo": [medida1, medida2],
                    "Tinaja": [medida1, medida2, medida3]
                }
                
                if tipo in required_fields and any(x <= 0 for x in required_fields[tipo]):
                    st.error("Por favor, completa todas las medidas obligatorias con valores mayores a cero")
                    st.stop()
                
                # Guardar imagen
                nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
                ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen.getbuffer())
                
                # Insertar en BD
                c.execute("""
                    INSERT INTO muebles (
                        nombre, precio, descripcion, ruta_imagen, fecha, 
                        vendido, tienda, tipo, medida1, medida2, medida3
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, precio, descripcion, ruta_imagen, 
                    datetime.now().strftime("%Y-%m-%d"), 
                    int(vendido), tienda, tipo, 
                    medida1, medida2, medida3 if tipo not in ["Columna", "Espejo", "Silla", "Otro artículo"] else None
                ))
                conn.commit()
                st.success("✅ ¡Antigüedad registrada!")
                st.rerun()
            else:
                st.warning("⚠️ Completa los campos obligatorios (*)")

# --- Pestañas principales ---
tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

# Función para mostrar medidas según tipo
def mostrar_medidas(tipo, m1, m2, m3):
    if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
        return f"{m1}cm (largo) × {m2}cm (alto) × {m3}cm (fondo)"
    elif tipo in ["Biblioteca", "Armario"]:
        return f"{m1}cm (alto) × {m2}cm (ancho) × {m3}cm (fondo)"
    elif tipo == "Columna":
        return f"{m1}cm (alto) | {m2} lados en base"
    elif tipo == "Espejo":
        return f"{m1}cm (alto) × {m2}cm (ancho)"
    elif tipo == "Tinaja":
        return f"{m1}cm (alto) | Base: Ø{m2}cm | Boca: Ø{m3}cm"
    elif m1 and m2:
        return f"{m1}cm (alto) × {m2}cm (ancho)"
    return "Sin medidas registradas"

# Pestaña 1: Muebles en venta
with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    
    # Filtros
    col_filtros = st.columns(4)
    with col_filtros[0]:
        filtro_tienda = st.selectbox(
            "Filtrar por tienda",
            options=["Todas", "El Rastro", "Regueros"]
        )
    with col_filtros[1]:
        filtro_tipo = st.selectbox(
            "Filtrar por tipo",
            options=["Todos"] + [tipo[0] for tipo in c.execute("SELECT DISTINCT tipo FROM muebles").fetchall()]
        )
    with col_filtros[2]:
        orden = st.selectbox(
            "Ordenar por",
            options=["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"]
        )
    
    # Consulta SQL con filtros
    query = "SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda, tipo, medida1, medida2, medida3 FROM muebles WHERE vendido = 0"
    
    if filtro_tienda != "Todas":
        query += f" AND tienda = '{filtro_tienda}'"
    
    if filtro_tipo != "Todos":
        query += f" AND tipo = '{filtro_tipo}'"
    
    if orden == "Más reciente":
        query += " ORDER BY id DESC"
    elif orden == "Más antiguo":
        query += " ORDER BY id ASC"
    elif orden == "Precio (↑)":
        query += " ORDER BY precio ASC"
    else:
        query += " ORDER BY precio DESC"
    
    c.execute(query)
    muebles = c.fetchall()

    # Mostrar resultados
    if not muebles:
        st.info("No hay muebles disponibles")
    else:
        for mueble in muebles:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])
                with col_img:
                    try:
                        img = Image.open(mueble[4])
                        st.image(img, use_column_width=True)
                    except:
                        st.warning("Imagen no encontrada")
                
                with col_info:
                    st.markdown(f"### {mueble[1]}")
                    st.markdown(f"**Tipo:** {mueble[7]}")
                    st.markdown(f"**Precio:** {mueble[2]} €")
                    st.markdown(f"**Tienda:** {mueble[6]}")
                    st.markdown(f"**Medidas:** {mostrar_medidas(mueble[7], mueble[8], mueble[9], mueble[10])}")
                    st.markdown(f"**Fecha registro:** {mueble[5]}")
                    
                    if mueble[3]:
                        st.markdown(f"**Descripción:** {mueble[3]}")
                    
                    # Botones de acción
                    if st.button(f"Marcar como vendido", key=f"vendido_{mueble[0]}"):
                        c.execute("UPDATE muebles SET vendido = 1 WHERE id = ?", (mueble[0],))
                        conn.commit()
                        st.rerun()

# Pestaña 2: Muebles vendidos
with tab2:
    st.markdown("## ✔️ Muebles vendidos")
    c.execute("""
        SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda, tipo, medida1, medida2, medida3 
        FROM muebles 
        WHERE vendido = 1 
        ORDER BY fecha DESC
    """)
    muebles_vendidos = c.fetchall()
    
    if not muebles_vendidos:
        st.info("No hay muebles vendidos registrados")
    else:
        for mueble in muebles_vendidos:
            with st.container(border=True):
                st.markdown(f"### {mueble[1]} ({mueble[6]})")
                st.markdown(f"**Tipo:** {mueble[7]}")
                st.markdown(f"**Precio de venta:** {mueble[2]} €")
                st.markdown(f"**Medidas:** {mostrar_medidas(mueble[7], mueble[8], mueble[9], mueble[10])}")
                st.markdown(f"**Fecha de venta:** {mueble[5]}")
                
                # Opción para revertir a "no vendido"
                if st.button(f"Marcar como disponible", key=f"revertir_{mueble[0]}"):
                    c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                    conn.commit()
                    st.rerun()

# Cerrar conexión a la BD al final
conn.close()


