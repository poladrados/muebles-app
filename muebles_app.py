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
        
        # Nuevo campo: Tipo de mueble
        tipo = st.selectbox("Tipo de mueble*", [
            "Mesa", "Consola", "Buffet", "Biblioteca", 
            "Cómoda", "Columna", "Espejo", "Silla", "Tinaja", "Otro artículo"
        ])
        
        # Campos de medidas según el tipo
        if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Largo (cm)*", min_value=0)
            with col2:
                medida2 = st.number_input("Alto (cm)*", min_value=0)
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0)
                
        elif tipo in ["Biblioteca", "Armario"]:
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0)
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0)
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0)
                
        elif tipo == "Columna":
            col1, col2 = st.columns(2)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0)
            with col2:
                medida2 = st.number_input("Lados de la base (cm)*", min_value=3, max_value=8, value=4)
                
        elif tipo == "Espejo":
            col1, col2 = st.columns(2)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0)
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0)
                
        elif tipo == "Tinaja":
            col1, col2, col3 = st.columns(3)
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0)
            with col2:
                medida2 = st.number_input("Diámetro base (cm)*", min_value=0)
            with col3:
                medida3 = st.number_input("Diámetro boca (cm)*", min_value=0)
                
        else:  # Para sillas y otros artículos
            medida1 = st.number_input("Alto (cm)", min_value=0)
            medida2 = st.number_input("Ancho (cm)", min_value=0)
        
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])
        
        # Botón de guardar
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0 and tipo:
                # Validación de medidas según tipo
                if tipo in ["Mesa", "Consola", "Buffet", "Cómoda", "Biblioteca", "Armario", "Tinaja"]:
                    if medida1 <= 0 or medida2 <= 0 or medida3 <= 0:
                        st.error("Por favor, completa todas las medidas obligatorias")
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
                    medida1, medida2, medida3 if 'medida3' in locals() else None
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
    
    # Filtros mejorados
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
                    st.markdown(f"**Fecha registro:** {mueble[5]}")
                    
                    # Mostrar medidas según el tipo
                    if mueble[7] in ["Mesa", "Consola", "Buffet", "Cómoda"]:
                        st.markdown(f"**Medidas:** {mueble[8]}cm (largo) × {mueble[9]}cm (alto) × {mueble[10]}cm (fondo)")
                    elif mueble[7] in ["Biblioteca", "Armario"]:
                        st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho) × {mueble[10]}cm (fondo)")
                    elif mueble[7] == "Columna":
                        st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (lados base)")
                    elif mueble[7] == "Espejo":
                        st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho)")
                    elif mueble[7] == "Tinaja":
                        st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (diámetro base) × {mueble[10]}cm (diámetro boca)")
                    elif mueble[8] and mueble[9]:
                        st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho)")
                    
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
                st.markdown(f"**Fecha de venta:** {mueble[5]}")
                
                # Mostrar medidas para los vendidos también
                if mueble[7] in ["Mesa", "Consola", "Buffet", "Cómoda"]:
                    st.markdown(f"**Medidas:** {mueble[8]}cm (largo) × {mueble[9]}cm (alto) × {mueble[10]}cm (fondo)")
                elif mueble[7] in ["Biblioteca", "Armario"]:
                    st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho) × {mueble[10]}cm (fondo)")
                elif mueble[7] == "Columna":
                    st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (lados base)")
                elif mueble[7] == "Espejo":
                    st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho)")
                elif mueble[7] == "Tinaja":
                    st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (diámetro base) × {mueble[10]}cm (diámetro boca)")
                elif mueble[8] and mueble[9]:
                    st.markdown(f"**Medidas:** {mueble[8]}cm (alto) × {mueble[9]}cm (ancho)")
                
                # Opción para revertir a "no vendido"
                if st.button(f"Marcar como disponible", key=f"revertir_{mueble[0]}"):
                    c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                    conn.commit()
                    st.rerun()

# Cerrar conexión a la BD al final
conn.close()


