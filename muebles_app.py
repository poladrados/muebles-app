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
    /* Reset de estilos de Streamlit */
    .stApp > header {
        display: none;
    }
    
    /* Fondo general */
    .stApp {
        background-color: #E6F0F8;
        padding: 2rem;
    }
    
    /* Texto general en NEGRO */
    body, .stTextInput>label, .stNumberInput>label, 
    .stSelectbox>label, .stMultiselect>label,
    .stCheckbox>label, .stRadio>label, .stTextArea>label,
    .stMarkdown, .stAlert {
        color: #000000 !important;
    }
    
    /* Header personalizado */
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
    
    /* Logo */
    .header-logo {
        flex: 0 0 auto;
    }
    
    .header-logo img {
        height: 80px;
        width: auto;
    }
    
    /* Título */
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
    
    /* Color AZUL solo para encabezados */
    h1, h2, h3, h4, h5, h6 {
        color: #023e8a !important;
    }
    
    /* Botones */
    .stButton>button {
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    /* Botón eliminar */
    button[data-testid="baseButton-secondary"] {
        background-color: #e63946 !important;
        color: white !important;
        border: 1px solid #e63946 !important;
    }
    
    /* Botón marcar como vendido */
    button[data-testid="baseButton-primary"] {
        background-color: #023e8a !important;
        color: white !important;
        border: 1px solid #023e8a !important;
    }
    
    /* Versión móvil */
    @media (max-width: 768px) {
        .stApp {
            padding: 1rem;
        }
        
        .header-logo img {
            height: 50px;
        }
        
        .header-title {
            font-size: 1.8rem;
        }
        
        .stButton>button {
            width: 100% !important;
            margin: 6px 0 !important;
        }
        
        /* Textos en móvil */
        .stMarkdown, 
        .stCheckbox>label, 
        .stRadio>label, 
        .stTextInput>label {
            color: #000000 !important;
            font-size: 14px !important;
        }
    }
    </style>
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
        # Campos del formulario (se mantienen igual)
        # ... (tu código existente para el formulario)

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

# Pestaña 1: Muebles en venta (con borrado)
with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    
    # Filtros (se mantienen igual)
    # ... (tu código existente de filtros)
    
    # Mostrar resultados con botón de eliminar
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
                    
                    # Botones de acción con confirmación
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🗑️ Eliminar", key=f"eliminar_{mueble[0]}"):
                            st.session_state[f'confirm_eliminar_{mueble[0]}'] = True
                        
                        if st.session_state.get(f'confirm_eliminar_{mueble[0]}'):
                            if st.button(f"✅ Confirmar eliminar", key=f"conf_elim_{mueble[0]}"):
                                # Borrar imagen si existe
                                if mueble[4] and os.path.exists(mueble[4]):
                                    os.remove(mueble[4])
                                # Borrar de BD
                                c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                                conn.commit()
                                del st.session_state[f'confirm_eliminar_{mueble[0]}']
                                st.rerun()
                            if st.button("❌ Cancelar", key=f"cancel_elim_{mueble[0]}"):
                                del st.session_state[f'confirm_eliminar_{mueble[0]}']
                                st.rerun()
                    
                    with col2:
                        if st.button(f"✔️ Marcar como vendido", key=f"vendido_{mueble[0]}"):
                            c.execute("UPDATE muebles SET vendido = 1 WHERE id = ?", (mueble[0],))
                            conn.commit()
                            st.rerun()

# Pestaña 2: Muebles vendidos (con borrado)
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
                
                # Botones de acción con confirmación
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🗑️ Eliminar", key=f"eliminar_v_{mueble[0]}"):
                        st.session_state[f'confirm_eliminar_v_{mueble[0]}'] = True
                    
                    if st.session_state.get(f'confirm_eliminar_v_{mueble[0]}'):
                        if st.button(f"✅ Confirmar eliminar", key=f"conf_elim_v_{mueble[0]}"):
                            if mueble[4] and os.path.exists(mueble[4]):
                                os.remove(mueble[4])
                            c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                            conn.commit()
                            del st.session_state[f'confirm_eliminar_v_{mueble[0]}']
                            st.rerun()
                        if st.button("❌ Cancelar", key=f"cancel_elim_v_{mueble[0]}"):
                            del st.session_state[f'confirm_eliminar_v_{mueble[0]}']
                            st.rerun()
                
                with col2:
                    if st.button(f"↩️ Marcar como disponible", key=f"revertir_{mueble[0]}"):
                        c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                        conn.commit()
                        st.rerun()

# Cerrar conexión a la BD al final
conn.close()

