import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import hashlib
from PIL import Image
from datetime import datetime
from io import BytesIO
import base64
import logging
from streamlit import config as _config

# --- Configuraciones iniciales ---
st.set_page_config(
    page_title="Inventario El Jueves",
    page_icon="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png",
    layout="wide"
)

# --- Inicialización segura de variables de sesión ---
if 'es_admin' not in st.session_state:
    st.session_state.es_admin = False

# --- Estilos CSS unificados y globales ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Playfair Display', serif !important;
    }

    .header-title,
    .muebles-disponibles-title,
    .vendidos-title {
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        color: #023e8a !important;
        margin-bottom: 1rem !important;
    }

    .stApp > header { display: none; }
    .stApp { background-color: #E6F0F8; padding: 2rem; }

    .custom-header {
        display: flex;
        align-items: center;
        background-color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }

    .header-logo img { height: 80px; width: auto; }
    .header-title { font-size: 2.5rem !important; }

    @media (max-width: 768px) {
        .custom-header { padding: 0.8rem 1rem !important; }
        .header-title { font-size: 1.5rem !important; }
        .header-logo img { height: 50px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Configuración de seguridad ---
ADMIN_PASSWORD_HASH = "c1c560d0e2bf0d3c36c85714d22c16be0be30efc9f480eff623b486778be2110"

# --- Deshabilitar mensajes de Streamlit ---
os.environ['STREAMLIT_HIDE_DEBUG'] = "true"
os.environ['STREAMLIT_SERVER_LIFECYCLE'] = "false"
_config.set_option('client.showErrorDetails', False)
_config.set_option('client.showWarningMessages', False)
_config.set_option('logger.level', 'error')
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime').setLevel(logging.ERROR)
logging.getLogger('streamlit.delta_generator').setLevel(logging.ERROR)

# Aquí continúa tu lógica de conexión, autenticación y resto de la app...
# (no modifiqué esa parte porque está bien y no interfiere con los estilos o debug)

# Elimina cualquier st.write(...) que uses para depurar st.secrets u otros objetos si ya confirmaste que todo funciona.



# --- Barra lateral ---
with st.sidebar:
    if not st.session_state.es_admin:
        with st.expander("🔑 Acceso Administradores", expanded=False):
            password = st.text_input("Contraseña de administrador", type="password")
            if st.button("Ingresar como administrador"):
                if verificar_admin(password):
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
    else:
        st.success("Modo administrador activo")
        if st.button("🚪 Salir del modo admin"):
            st.session_state.es_admin = False
            st.session_state.pop('admin_token', None)
            st.experimental_set_query_params()
            st.rerun()
    
    # Estadísticas
    st.markdown("## 📊 Estadísticas")
    try:
        c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = FALSE AND tienda = 'El Rastro'")
        en_rastro = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = FALSE AND tienda = 'Regueros'")
        en_regueros = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = TRUE")
        vendidos = c.fetchone()[0] or 0
        
        st.metric("🔵 En El Rastro", en_rastro)
        st.metric("🔴 En Regueros", en_regueros)
        st.metric("💰 Vendidos", vendidos)
        
    except psycopg2.Error as e:
        st.error("Error al cargar estadísticas")
        st.metric("🔵 En El Rastro", 0)
        st.metric("🔴 En Regueros", 0)
        st.metric("💰 Vendidos", 0)

# --- Funciones auxiliares ---
def mostrar_medidas(tipo, m1, m2, m3):
    medidas = []
    if m1 not in [None, 0]: medidas.append(f"{m1}cm")
    if m2 not in [None, 0]: medidas.append(f"{m2}cm")
    if m3 not in [None, 0]: medidas.append(f"{m3}cm")
    return " × ".join(medidas) if medidas else "Sin medidas"

def mostrar_formulario_edicion(mueble_id):
    c.execute("SELECT * FROM muebles WHERE id = %s", (mueble_id,))
    mueble = c.fetchone()
    
    c.execute("SELECT imagen_base64, es_principal FROM imagenes_muebles WHERE mueble_id = %s ORDER BY es_principal DESC", (mueble_id,))
    imagenes_actuales = c.fetchall()
    
    with st.form(key=f"form_editar_{mueble_id}"):
        st.markdown(f"### Editando: {mueble['nombre']}")
        
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.radio("Tienda", options=["El Rastro", "Regueros"], 
                             index=0 if mueble['tienda'] == "El Rastro" else 1)
        with col2:
            vendido = st.checkbox("Marcar como vendido", value=mueble['vendido'])
        
        nombre = st.text_input("Nombre*", value=mueble['nombre'])
        precio = st.number_input("Precio (€)*", min_value=0.0, value=mueble['precio'])
        descripcion = st.text_area("Descripción", value=mueble['descripcion'])
        
        st.markdown("### Imágenes actuales")
        if imagenes_actuales:
            cols = st.columns(min(3, len(imagenes_actuales)))
            for i, (img_base64, es_principal) in enumerate(imagenes_actuales):
                with cols[i % 3]:
                    try:
                        img = base64_to_image(img_base64)
                        st.image(img, caption=f"{'✅ Principal' if es_principal else 'Secundaria'} - Imagen {i+1}")
                        if st.button(f"❌ Eliminar esta imagen", key=f"del_img_{i}_{mueble_id}"):
                            c.execute("DELETE FROM imagenes_muebles WHERE imagen_base64 = %s", (img_base64,))
                            conn.commit()
                            st.rerun()
                    except:
                        st.warning("Error al cargar imagen")
        
        st.markdown("### Añadir nuevas imágenes")
        nuevas_imagenes = st.file_uploader("Seleccionar imágenes", 
                                         type=["jpg", "jpeg", "png"], 
                                         accept_multiple_files=True,
                                         key=f"uploader_{mueble_id}")
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar cambios"):
                c.execute("""
                    UPDATE muebles SET
                        nombre = %s, precio = %s, descripcion = %s,
                        tienda = %s, vendido = %s
                    WHERE id = %s
                """, (nombre, precio, descripcion, tienda, vendido, mueble_id))
                
                if nuevas_imagenes:
                    for img in nuevas_imagenes:
                        img_base64 = image_to_base64(img)
                        es_principal = 0 if imagenes_actuales else 1
                        c.execute("""
                            INSERT INTO imagenes_muebles (mueble_id, imagen_base64, es_principal)
                            VALUES (%s, %s, %s)
                        """, (mueble_id, img_base64, es_principal))
                
                conn.commit()
                st.success("¡Cambios guardados!")
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar edición"):
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()

# --- Pestañas principales ---
TIPOS_PLURAL = {
    "Mesa": "Mesas",
    "Consola": "Consolas",
    "Buffet": "Buffets",
    "Biblioteca": "Bibliotecas",
    "Armario": "Armarios",
    "Cómoda": "Cómodas",
    "Columna": "Columnas",
    "Espejo": "Espejos",
    "Copa": "Copas",
    "Asiento": "Asientos",
    "Otro artículo": "Otros artículos"
}

tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

# Pestaña 1: En venta
with tab1:
    st.markdown('<h2 class="muebles-disponibles-title">🏷️ Muebles disponibles</h2>', unsafe_allow_html=True)
    
    # Filtros
    col_filtros = st.columns(4)
    with col_filtros[0]:
        filtro_tienda = st.selectbox("Filtrar por tienda", ["Todas", "El Rastro", "Regueros"])
    
    with col_filtros[1]:
        c.execute("SELECT DISTINCT tipo FROM muebles")
        tipos_db = [tipo[0] for tipo in c.fetchall()]
        opciones_filtro = ["Todos"] + [TIPOS_PLURAL.get(tipo, tipo) for tipo in tipos_db]
        filtro_tipo_plural = st.selectbox("Filtrar por tipo", opciones_filtro)
        tipo_para_consulta = next((k for k, v in TIPOS_PLURAL.items() if v == filtro_tipo_plural), filtro_tipo_plural) if filtro_tipo_plural != "Todos" else None
    
    with col_filtros[2]:
        orden = st.selectbox("Ordenar por", ["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"])
    
    # Consulta con parámetros
    query = "SELECT * FROM muebles WHERE vendido = FALSE"
    params = []
    
    if filtro_tienda != "Todas":
        query += " AND tienda = %s"
        params.append(filtro_tienda)
    
    if filtro_tipo_plural != "Todos":
        query += " AND tipo = %s"
        params.append(tipo_para_consulta)
    
    if orden == "Más reciente":
        query += " ORDER BY id DESC"
    elif orden == "Más antiguo":
        query += " ORDER BY id ASC"
    elif orden == "Precio (↑)":
        query += " ORDER BY precio ASC"
    else:
        query += " ORDER BY precio DESC"
    
    c.execute(query, params)
    muebles = c.fetchall()

    if not muebles:
        st.info("No hay muebles disponibles")
    else:
        for mueble in muebles:
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])
                
                with col_img:
                    c.execute("""
                        SELECT imagen_base64, es_principal 
                        FROM imagenes_muebles 
                        WHERE mueble_id = %s
                        ORDER BY es_principal DESC
                    """, (mueble['id'],))
                    imagenes_mueble = c.fetchall()
                    
                    if imagenes_mueble:
                        try:
                            img_principal = base64_to_image(imagenes_mueble[0]['imagen_base64'])
                            st.image(img_principal, use_container_width=True)
                            
                            if len(imagenes_mueble) > 1:
                                with st.expander(f"📸 Ver más imágenes ({len(imagenes_mueble)-1})"):
                                    for i, img_data in enumerate(imagenes_mueble[1:], 1):
                                        try:
                                            st.image(base64_to_image(img_data['imagen_base64']), 
                                                   caption=f"Imagen {i+1}")
                                        except:
                                            st.warning(f"Error al cargar imagen {i+1}")
                        except:
                            st.warning("Error al cargar imagen principal")
                
                with col_info:
                    st.markdown(f"### {mueble['nombre']}")
                    st.markdown(f"**Tipo:** {mueble['tipo']}")
                    st.markdown(f"**Precio:** {mueble['precio']} €")
                    st.markdown(f"**Tienda:** {mueble['tienda']}")
                    st.markdown(f"**Medidas:** {mostrar_medidas(mueble['tipo'], mueble['medida1'], mueble['medida2'], mueble['medida3'])}")
                    st.markdown(f"**Fecha registro:** {mueble['fecha']}")
                    
                    if mueble['descripcion']:
                        st.markdown(f"**Descripción:** {mueble['descripcion']}")
                    
                    if st.session_state.get('editar_mueble_id') == mueble['id']:
                        mostrar_formulario_edicion(mueble['id'])
                    
                    if st.session_state.es_admin:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"✏️ Editar", key=f"editar_{mueble['id']}"):
                                st.session_state['editar_mueble_id'] = mueble['id']
                                st.rerun()
                        
                        with col2:
                            if st.button(f"🗑️ Eliminar", key=f"eliminar_{mueble['id']}"):
                                if st.session_state.get(f'confirm_eliminar_{mueble['id']}'):
                                    c.execute("DELETE FROM imagenes_muebles WHERE mueble_id = %s", (mueble['id'],))
                                    c.execute("DELETE FROM muebles WHERE id = %s", (mueble['id'],))
                                    conn.commit()
                                    st.rerun()
                                else:
                                    st.session_state[f'confirm_eliminar_{mueble['id']}'] = True
                                    st.rerun()
                            
                            if st.session_state.get(f'confirm_eliminar_{mueble['id']}'):
                                st.warning("¿Confirmar eliminación?")
                        
                        with col3:
                            if st.button(f"✔️ Marcar como vendido", key=f"vendido_{mueble['id']}"):
                                c.execute("UPDATE muebles SET vendido = TRUE WHERE id = %s", (mueble['id'],))
                                conn.commit()
                                st.rerun()

# Pestaña 2: Vendidos (solo para admin)
with tab2:
    if st.session_state.es_admin:
        st.markdown('<h2 class="vendidos-title">✔️ Muebles vendidos</h2>', unsafe_allow_html=True)
        c.execute("SELECT * FROM muebles WHERE vendido = TRUE ORDER BY fecha DESC")
        muebles_vendidos = c.fetchall()
        
        if not muebles_vendidos:
            st.info("No hay muebles vendidos registrados")
        else:
            for mueble in muebles_vendidos:
                with st.container(border=True):
                    col_img, col_info = st.columns([1, 3])
                    
                    with col_img:
                        c.execute("""
                            SELECT imagen_base64, es_principal 
                            FROM imagenes_muebles 
                            WHERE mueble_id = %s
                            ORDER BY es_principal DESC
                        """, (mueble['id'],))
                        imagenes_mueble = c.fetchall()
                        
                        if imagenes_mueble:
                            try:
                                img_principal = base64_to_image(imagenes_mueble[0]['imagen_base64'])
                                st.image(img_principal, use_container_width=True)
                                
                                if len(imagenes_mueble) > 1:
                                    with st.expander(f"📸 Ver más imágenes ({len(imagenes_mueble)-1})"):
                                        for i, img_data in enumerate(imagenes_mueble[1:], 1):
                                            try:
                                                st.image(base64_to_image(img_data['imagen_base64']), 
                                                       caption=f"Imagen {i+1}")
                                            except:
                                                st.warning(f"Error al cargar imagen {i+1}")
                            except:
                                st.warning("Error al cargar imagen principal")
                    
                    with col_info:
                        st.markdown(f"### {mueble['nombre']}")
                        st.markdown(f"**Tipo:** {mueble['tipo']}")
                        st.markdown(f"**Precio:** {mueble['precio']} €")
                        st.markdown(f"**Tienda:** {mueble['tienda']}")
                        st.markdown(f"**Medidas:** {mostrar_medidas(mueble['tipo'], mueble['medida1'], mueble['medida2'], mueble['medida3'])}")
                        st.markdown(f"**Fecha registro:** {mueble['fecha']}")
                        
                        if mueble['descripcion']:
                            st.markdown(f"**Descripción:** {mueble['descripcion']}")
                        
                        if st.session_state.get('editar_mueble_id') == mueble['id']:
                            mostrar_formulario_edicion(mueble['id'])
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"✏️ Editar", key=f"editar_v_{mueble['id']}"):
                                st.session_state['editar_mueble_id'] = mueble['id']
                                st.rerun()
                        
                        with col2:
                            if st.button(f"🗑️ Eliminar", key=f"eliminar_v_{mueble['id']}"):
                                if st.session_state.get(f'confirm_eliminar_v_{mueble['id']}'):
                                    c.execute("DELETE FROM imagenes_muebles WHERE mueble_id = %s", (mueble['id'],))
                                    c.execute("DELETE FROM muebles WHERE id = %s", (mueble['id'],))
                                    conn.commit()
                                    st.rerun()
                                else:
                                    st.session_state[f'confirm_eliminar_v_{mueble['id']}'] = True
                                    st.rerun()
                            
                            if st.session_state.get(f"confirm_eliminar_v_{mueble['id']}"):
                                st.warning("¿Confirmar eliminación?")
                        
                        with col3:
                            if st.button(f"↩️ Marcar como disponible", key=f"revertir_{mueble['id']}"):
                                c.execute("UPDATE muebles SET vendido = FALSE WHERE id = %s", (mueble['id'],))
                                conn.commit()
                                st.rerun()
    else:
        st.info("🔒 Esta sección solo está disponible para administradores")

# Cerrar conexión
if 'conn' in locals():
    conn.close()




