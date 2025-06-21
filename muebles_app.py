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

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    /* ESTILOS GENERALES (DESKTOP) */
    .stApp > header {display: none;}
    .stApp {background-color: #E6F0F8; padding: 2rem;}
    body, .stTextInput>label, .stNumberInput>label,
    .stSelectbox>label, .stMultiselect>label,
    .stCheckbox>label, .stRadio>label, .stTextArea>label,
    .stMarkdown, .stAlert {color: #000 !important;}
    .custom-header {display: flex; align-items: center; background-color: white; padding: 1rem 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem; width: 100%;}
    .header-logo img {height: 80px; width: auto;}
    .header-title {color: #023e8a !important; font-size: 2.5rem; font-weight: bold; margin: 0; text-align: center;}
    h1, h2, h3, h4, h5, h6 {color: #023e8a !important;}
    .stButton>button {background-color: white; color: #023e8a; border: 1px solid #023e8a; border-radius: 4px;}
    /* MÓVIL */
    @media (max-width: 768px) {
        .custom-header h1.header-title {font-size: 1.5rem !important;}
        /* Forms & expander */
        div[role="form"], div[role="group"] {background-color: #E6F0F8 !important; padding: 1rem !important; border-radius: 8px !important;}
        div[role="form"] label, div[role="group"] label,
        div[role="form"] input, div[role="form"] textarea, div[role="form"] select,
        div[role="group"] input, div[role="group"] textarea, div[role="group"] select {color: #000 !important; background-color: white !important;}
        /* Radios & Checkbox */
        div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {color: #000 !important; font-weight: 600 !important; background: white !important; padding: 8px 12px !important; border-radius: 8px !important; margin: 4px 0 !important; border: 1px solid #023e8a !important;}
        /* Tabs */
        button[role="tab"] {color: #000 !important; background: #E6F0F8 !important; border: 1px solid #023e8a !important; font-weight: 600 !important;}
        button[role="tab"][aria-selected="true"] {color: white !important; background: #023e8a !important;}
        .stApp {padding: 0.8rem !important;}
        .header-logo img {height: 50px !important;}
    }
    </style>
    <script>
    const applyMobile = () => { if(window.innerWidth<=768) { document.querySelectorAll('div[role="form"], div[role="group"]').forEach(el=>el.style.backgroundColor='#E6F0F8'); document.querySelectorAll('div[role="form"] label, div[role="group"] label').forEach(l=>l.style.color='#000'); }};
    window.addEventListener('load', ()=>setTimeout(applyMobile,300)); window.addEventListener('resize', applyMobile);
    </script>
""", unsafe_allow_html=True)

# --- HEADER PERSONALIZADO ---
st.markdown("""
    <div class="custom-header">
        <div class="header-logo">
            <img src="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png" alt="Logo">
        </div>
        <div class="header-title-container">
            <h1 class="header-title">Inventario de Antigüedades El Jueves</h1>
        </div>
    </div>
""", unsafe_allow_html=True)



# --- Inicialización BD ---
try:
    c.execute("ALTER TABLE muebles ADD COLUMN tipo TEXT DEFAULT 'Otro'")
    c.execute("ALTER TABLE muebles ADD COLUMN medida1 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida2 REAL")
    c.execute("ALTER TABLE muebles ADD COLUMN medida3 REAL")
    conn.commit()
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e):
        st.error(f"Error al actualizar la BD: {e}")

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

# --- Sidebar ---
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

# --- Formulario ---
# --- Formulario ---
with st.expander("📥 Añadir nueva antigüedad", expanded=False):
    with st.form(key="form_mueble"):
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.radio("Tienda", options=["El Rastro", "Regueros"], horizontal=True)
        with col2:
            vendido = st.checkbox("Marcar como vendido")
        
        nombre = st.text_input("Nombre de la antigüedad*")
        precio = st.number_input("Precio (€)*", min_value=0.0, step=1.0)
        descripcion = st.text_area("Descripción")
        
        tipo = st.selectbox(
            "Tipo de mueble*",
            ["Mesa", "Consola", "Buffet", "Biblioteca", "Armario", "Cómoda", "Columna", "Espejo", "Copa", "Asiento", "Otro artículo"]
        )
        
        # Campos de medidas según tipo
        if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
            medida1 = st.number_input("Largo (cm)*", min_value=0.0, step=0.1)
            medida2 = st.number_input("Alto (cm)*", min_value=0.0, step=0.1)
            medida3 = st.number_input("Fondo (cm)*", min_value=0.0, step=0.1)
        elif tipo in ["Biblioteca", "Armario"]:
            medida1 = st.number_input("Alto (cm)*", min_value=0.0, step=0.1)
            medida2 = st.number_input("Ancho (cm)*", min_value=0.0, step=0.1)
            medida3 = st.number_input("Fondo (cm)*", min_value=0.0, step=0.1)
        elif tipo == "Columna":
            medida1 = st.number_input("Alto (cm)*", min_value=0.0, step=0.1)
            medida2 = st.number_input("Número de lados en base*", min_value=1, step=1)
            medida3 = None
        elif tipo == "Espejo":
            medida1 = st.number_input("Alto (cm)*", min_value=0.0, step=0.1)
            medida2 = st.number_input("Ancho (cm)*", min_value=0.0, step=0.1)
            medida3 = None
        elif tipo == "Copa":
            medida1 = st.number_input("Alto (cm)*", min_value=0.0, step=0.1)
            medida2 = st.number_input("Diámetro base (cm)*", min_value=0.0, step=0.1)
            medida3 = st.number_input("Diámetro boca (cm)*", min_value=0.0, step=0.1)
        elif tipo in ["Asiento", "Otro artículo"]:
            medida1 = None
            medida2 = None
            medida3 = None
        else:
            medida1 = None
            medida2 = None
            medida3 = None
        
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("Guardar")
        if submitted:
            # Validar campos obligatorios
            campos_validos = nombre and precio > 0 and tipo
            # Además, si hay medidas requeridas, comprobar que no sean None o 0
            if tipo in ["Mesa", "Consola", "Buffet", "Cómoda", "Biblioteca", "Armario", "Copa"]:
                if not (medida1 and medida2 and (medida3 if medida3 is not None else True)):
                    campos_validos = False
            if tipo in ["Columna", "Espejo"]:
                if not (medida1 and medida2):
                    campos_validos = False
            
            if imagen and campos_validos:
                nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
                ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen.getbuffer())
                
                # Insert en BD, poner None para medida3 si no aplica
                c.execute("""
                    INSERT INTO muebles (
                        nombre, precio, descripcion, ruta_imagen, fecha, 
                        vendido, tienda, tipo, medida1, medida2, medida3
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nombre, precio, descripcion, ruta_imagen, 
                    datetime.now().strftime("%Y-%m-%d"), 
                    int(vendido), tienda, tipo, 
                    medida1, medida2, medida3
                ))
                conn.commit()
                st.success("✅ ¡Antigüedad registrada!")
                st.rerun()
            else:
                st.warning("⚠️ Completa los campos obligatorios (*) y las medidas requeridas")


# --- Pestañas ---
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

# Pestaña 1: En venta
with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    
    col_filtros = st.columns(4)
    with col_filtros[0]:
        filtro_tienda = st.selectbox("Filtrar por tienda", options=["Todas", "El Rastro", "Regueros"])
    with col_filtros[1]:
        filtro_tipo = st.selectbox("Filtrar por tipo", options=["Todos"] + [tipo[0] for tipo in c.execute("SELECT DISTINCT tipo FROM muebles").fetchall()])
    with col_filtros[2]:
        orden = st.selectbox("Ordenar por", options=["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"])
    
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

    if not muebles:
        st.info("No hay muebles disponibles")
    else:
        for mueble in muebles:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])
                with col_img:
                    try:
                        img = Image.open(mueble[4])
                        st.image(img, use_container_width=True)
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
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🗑️ Eliminar", key=f"eliminar_{mueble[0]}"):
                            if st.session_state.get(f'confirm_eliminar_{mueble[0]}'):
                                if mueble[4] and os.path.exists(mueble[4]):
                                    os.remove(mueble[4])
                                c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                                conn.commit()
                                st.rerun()
                            else:
                                st.session_state[f'confirm_eliminar_{mueble[0]}'] = True
                                st.rerun()
                        
                        if st.session_state.get(f'confirm_eliminar_{mueble[0]}'):
                            st.warning("¿Confirmar eliminación? Pulsa Eliminar nuevamente")
                    
                    with col2:
                        if st.button(f"✔️ Marcar como vendido", key=f"vendido_{mueble[0]}"):
                            c.execute("UPDATE muebles SET vendido = 1 WHERE id = ?", (mueble[0],))
                            conn.commit()
                            st.rerun()

# Pestaña 2: Vendidos
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
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🗑️ Eliminar", key=f"eliminar_v_{mueble[0]}"):
                        if st.session_state.get(f'confirm_eliminar_v_{mueble[0]}'):
                            if mueble[4] and os.path.exists(mueble[4]):
                                os.remove(mueble[4])
                            c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                            conn.commit()
                            st.rerun()
                        else:
                            st.session_state[f'confirm_eliminar_v_{mueble[0]}'] = True
                            st.rerun()
                    
                    if st.session_state.get(f'confirm_eliminar_v_{mueble[0]}'):
                        st.warning("¿Confirmar eliminación? Pulsa Eliminar nuevamente")
                
                with col2:
                    if st.button(f"↩️ Marcar como disponible", key=f"revertir_{mueble[0]}"):
                        c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                        conn.commit()
                        st.rerun()

conn.close()

