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
    <style>
    /* ESTILOS GENERALES */
    .stApp > header {
        display: none;
    }
    
    .stApp {
        background-color: #E6F0F8;
        padding: 2rem;
    }
    
    body, .stTextInput>label, .stNumberInput>label, 
    .stSelectbox>label, .stMultiselect>label,
    .stCheckbox>label, .stRadio>label, .stTextArea>label,
    .stMarkdown, .stAlert {
        color: #000000 !important;
    }
    
    .custom-header {
        display: flex;
        align-items: center;
        background-color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        width: 100%;
    }
    
    .header-logo {
        flex: 0 0 auto;
    }
    
    .header-logo img {
        height: 80px;
        width: auto;
    }
    
    .header-title-container {
        flex: 1;
        display: flex;
        justify-content: center;
    }
    
    .header-title {
        color: #023e8a !important;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #023e8a !important;
    }
    
    .stButton>button {
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    button[data-testid="baseButton-secondary"] {
        background-color: #e63946 !important;
        color: white !important;
        border: 1px solid #e63946 !important;
    }
    
    button[data-testid="baseButton-primary"] {
        background-color: #023e8a !important;
        color: white !important;
        border: 1px solid #023e8a !important;
    }

    /* ESTILOS MÓVIL */
    @media (max-width: 768px) {
        .custom-header h1.header-title {
            font-size: 1.5rem !important;
            margin-left: 0 !important;
            padding-left: 0 !important;
        }
        
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label {
            color: #000000 !important;
            font-weight: 600 !important;
            background: white !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            margin: 4px 0 !important;
            border: 1px solid #023e8a !important;
        }
        
        div[data-testid="stTabs"] button {
            color: #000000 !important;
            background: #E6F0F8 !important;
            border: 1px solid #023e8a !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: white !important;
            background: #023e8a !important;
        }
        
        .stApp {
            padding: 0.8rem !important;
        }
        
        .header-logo img {
            height: 50px !important;
        }
        
        .stButton>button {
            width: 100% !important;
            margin: 6px 0 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
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
        tipo = st.selectbox("Tipo de mueble*", [
            "Mesa", "Consola", "Buffet", "Biblioteca", 
            "Armario", "Cómoda", "Columna", "Espejo", 
            "Tinaja", "Silla", "Otro artículo"
        ])
        
        # --- Campos de medidas dinámicos ---
        st.markdown("**Medidas requeridas:**")
        col1, col2, col3 = st.columns(3)
        
        if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
            with col1:
                medida1 = st.number_input("Largo (cm)*", min_value=0, key="largo")
            with col2:
                medida2 = st.number_input("Alto (cm)*", min_value=0, key="alto")
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0, key="fondo")
                
        elif tipo in ["Biblioteca", "Armario"]:
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, key="alto")
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0, key="ancho")
            with col3:
                medida3 = st.number_input("Fondo (cm)*", min_value=0, key="fondo")
                
        elif tipo == "Columna":
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, key="alto_col")
            with col2:
                medida2 = st.number_input("Lados base*", min_value=3, max_value=8, value=4, key="lados")
            medida3 = None
                
        elif tipo == "Espejo":
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, key="alto_esp")
            with col2:
                medida2 = st.number_input("Ancho (cm)*", min_value=0, key="ancho_esp")
            medida3 = None
                
        elif tipo == "Tinaja":
            with col1:
                medida1 = st.number_input("Alto (cm)*", min_value=0, key="alto_tin")
            with col2:
                medida2 = st.number_input("Diámetro base (cm)*", min_value=0, key="base_tin")
            with col3:
                medida3 = st.number_input("Diámetro boca (cm)*", min_value=0, key="boca_tin")
                
        else:  # Para sillas y otros artículos
            st.markdown("**Medidas opcionales:**")
            with col1:
                medida1 = st.number_input("Alto (cm)", min_value=0, key="alto_gen")
            with col2:
                medida2 = st.number_input("Ancho (cm)", min_value=0, key="ancho_gen")
            medida3 = None
        
        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0 and tipo:
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
                
                nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
                ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen.getbuffer())
                
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

# --- Pestañas ---
tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

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


