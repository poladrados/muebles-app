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
# --- MIGRACIÓN: Añade columnas si no existen (SOLO EJECUTA UNA VEZ) ---
try:
    c.execute("ALTER TABLE muebles ADD COLUMN vendido BOOLEAN DEFAULT 0")
    c.execute("ALTER TABLE muebles ADD COLUMN tienda TEXT DEFAULT 'El Rastro'")
    conn.commit()
    st.success("✅ Base de datos actualizada con las nuevas columnas")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):  # Si las columnas ya existen
        pass  # No hagas nada
    else:
        st.error(f"Error al actualizar la BD: {e}")

# Crear tabla (con los nuevos campos)
c.execute("""
    CREATE TABLE IF NOT EXISTS muebles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL,
        descripcion TEXT,
        ruta_imagen TEXT,
        fecha TEXT,
        vendido BOOLEAN DEFAULT 0,
        tienda TEXT
    )
""")
conn.commit()

# --- Interfaz de la app ---
st.title("🪑 Gestión de Antigüedades - El Jueves")

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
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])
        
        # Botón de guardar
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0:
                # Guardar imagen
                nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
                ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen.getbuffer())
                
                # Insertar en BD
                c.execute("""
                    INSERT INTO muebles (nombre, precio, descripcion, ruta_imagen, fecha, vendido, tienda)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, precio, descripcion, 
                    ruta_imagen, datetime.now().strftime("%Y-%m-%d"), 
                    int(vendido), tienda
                ))
                conn.commit()
                st.success("✅ ¡Antigüedad registrada!")
                st.rerun()
            else:
                st.warning("⚠️ Completa los campos obligatorios (*)")

# --- Pestañas principales ---
tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

# Pestaña 1: Muebles en venta
with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    
    # Filtros
    col_filtros = st.columns(3)
    with col_filtros[0]:
        filtro_tienda = st.selectbox(
            "Filtrar por tienda",
            options=["Todas", "El Rastro", "Regueros"]
        )
    with col_filtros[1]:
        orden = st.selectbox(
            "Ordenar por",
            options=["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"]
        )
    
    # Consulta SQL con filtros
    query = "SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda FROM muebles WHERE vendido = 0"
    if filtro_tienda != "Todas":
        query += f" AND tienda = '{filtro_tienda}'"
    
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
                    st.markdown(f"**Precio:** {mueble[2]} €")
                    st.markdown(f"**Tienda:** {mueble[6]}")
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
        SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda 
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
                st.markdown(f"**Precio de venta:** {mueble[2]} €")
                st.markdown(f"**Fecha de venta:** {mueble[5]}")
                
                # Opción para revertir a "no vendido"
                if st.button(f"Marcar como disponible", key=f"revertir_{mueble[0]}"):
                    c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                    conn.commit()
                    st.rerun()

# Cerrar conexión a la BD al final
conn.close()

