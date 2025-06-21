import streamlit as st
import sqlite3
import os
from PIL import Image
from datetime import datetime

CARPETA_IMAGENES = "imagenes_muebles"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

conn = sqlite3.connect("muebles.db")
c = conn.cursor()

st.set_page_config(
    page_title="Inventario El Jueves",
    page_icon="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png",
    layout="wide"
)

st.title("🪑 Inventario de Antigüedades El Jueves")

# --- Migración de columnas nuevas si no existen ---
try:
    c.execute("ALTER TABLE muebles ADD COLUMN vendido BOOLEAN DEFAULT 0")
    c.execute("ALTER TABLE muebles ADD COLUMN tienda TEXT DEFAULT 'El Rastro'")
    c.execute("ALTER TABLE muebles ADD COLUMN tipo TEXT")
    c.execute("ALTER TABLE muebles ADD COLUMN medida1 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida2 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida3 REAL")
    conn.commit()
except sqlite3.OperationalError:
    pass

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

# Tipos de muebles disponibles
tipos_muebles = {
    "Mesa": ["Largo", "Alto", "Fondo"],
    "Consola": ["Largo", "Alto", "Fondo"],
    "Buffet": ["Largo", "Alto", "Fondo"],
    "Cómoda": ["Largo", "Alto", "Fondo"],
    "Biblioteca": ["Alto", "Ancho", "Fondo"],
    "Armario": ["Alto", "Ancho", "Fondo"],
    "Columna": ["Alto", "Lado base"],
    "Espejo": ["Alto", "Ancho"],
    "Tinaja": ["Alto", "Diámetro base", "Diámetro boca"],
    "Otro": []
}

with st.expander("📥 Añadir nueva antigüedad", expanded=False):
    with st.form(key="form_mueble"):
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.radio("Tienda", ["El Rastro", "Regueros"], horizontal=True)
        with col2:
            vendido = st.checkbox("Marcar como vendido")

        tipo = st.selectbox("Tipo de mueble", list(tipos_muebles.keys()))
        nombre = st.text_input("Nombre de la antigüedad*")
        precio = st.number_input("Precio (€)*", min_value=0.0, step=1.0)
        descripcion = st.text_area("Descripción")
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])

        medidas = tipos_muebles[tipo]
        medida1 = medida2 = medida3 = None

        if len(medidas) >= 1:
            medida1 = st.number_input(f"{medidas[0]} (cm)", min_value=0.0, step=0.5)
        if len(medidas) >= 2:
            medida2 = st.number_input(f"{medidas[1]} (cm)", min_value=0.0, step=0.5)
        if len(medidas) >= 3:
            medida3 = st.number_input(f"{medidas[2]} (cm)", min_value=0.0, step=0.5)

        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0:
                nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
                ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen.getbuffer())

                c.execute("""
                    INSERT INTO muebles (nombre, precio, descripcion, ruta_imagen, fecha, vendido, tienda, tipo, medida1, medida2, medida3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, precio, descripcion,
                    ruta_imagen, datetime.now().strftime("%Y-%m-%d"),
                    int(vendido), tienda, tipo, medida1, medida2, medida3
                ))
                conn.commit()
                st.success("✅ ¡Antigüedad registrada!")
                st.rerun()
            else:
                st.warning("⚠️ Completa los campos obligatorios (*)")

tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

with tab1:
    st.markdown("## 🏧 Muebles disponibles")
    col_filtros = st.columns(3)
    with col_filtros[0]:
        filtro_tienda = st.selectbox("Filtrar por tienda", ["Todas", "El Rastro", "Regueros"])
    with col_filtros[1]:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos"] + list(tipos_muebles.keys()))
    with col_filtros[2]:
        orden = st.selectbox("Ordenar por", ["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"])

    query = "SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda, tipo FROM muebles WHERE vendido = 0"
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
                    st.markdown(f"**Precio:** {mueble[2]} €")
                    st.markdown(f"**Tienda:** {mueble[6]}")
                    st.markdown(f"**Tipo:** {mueble[7]}")
                    st.markdown(f"**Fecha registro:** {mueble[5]}")
                    if mueble[3]:
                        st.markdown(f"**Descripción:** {mueble[3]}")
                    if st.button(f"Marcar como vendido", key=f"vendido_{mueble[0]}"):
                        c.execute("UPDATE muebles SET vendido = 1 WHERE id = ?", (mueble[0],))
                        conn.commit()
                        st.rerun()

with tab2:
    st.markdown("## ✔️ Muebles vendidos")
    c.execute("SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda FROM muebles WHERE vendido = 1 ORDER BY fecha DESC")
    muebles_vendidos = c.fetchall()

    if not muebles_vendidos:
        st.info("No hay muebles vendidos registrados")
    else:
        for mueble in muebles_vendidos:
            with st.container(border=True):
                st.markdown(f"### {mueble[1]} ({mueble[6]})")
                st.markdown(f"**Precio de venta:** {mueble[2]} €")
                st.markdown(f"**Fecha de venta:** {mueble[5]}")
                if st.button(f"Marcar como disponible", key=f"revertir_{mueble[0]}"):
                    c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                    conn.commit()
                    st.rerun()

conn.close()


