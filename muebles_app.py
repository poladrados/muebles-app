# --- Configuraciones iniciales ---
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
from streamlit.components.v1 import html

st.set_page_config(
    page_title="Inventario El Jueves",
    page_icon="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png",
    layout="wide"
)

# --- Inicialización segura de variables de sesión ---
if 'es_admin' not in st.session_state:
    st.session_state.es_admin = False
if 'admin_token' not in st.session_state:
    st.session_state.admin_token = None
if 'editar_mueble_id' not in st.session_state:
    st.session_state.editar_mueble_id = None

# --- Estilos CSS unificados y globales ---
# --- Estilos CSS separados ---
css_global = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Playfair Display', serif !important;
}

.header-title,
.muebles-disponibles-title,
.vendidos-title {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    color: #023e8a !important;
    margin-bottom: 1rem !important;
    text-align: center !important;
}

.stApp > header { display: none; }
.stApp { background-color: #E6F0F8; padding: 2rem; }

.custom-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
    text-align: center;
}

.header-logo {
    margin-bottom: 0.5rem;
}

.header-logo img {
    height: 60px;
    width: auto;
}

.header-title {
    font-size: 1.8rem !important;
    margin: 0 !important;
}

/* En pantallas pequeñas (móvil) */
@media (max-width: 768px) {
    .header-title {
        font-size: 1.4rem !important;
        line-height: 1.4;
    }

    .header-logo img {
        height: 50px;
    }

    .custom-header {
        padding: 1rem;
    }
}


.mueble-image-container {
    position: relative;
    width: 100%;
    margin-bottom: 10px;
}

.mueble-image {
    width: 100%;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s;
    object-fit: cover;
    max-height: 300px;
}

.expand-button {
    position: absolute;
    bottom: 15px;
    right: 15px;
    background-color: rgba(0,0,0,0.7);
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 2;
    transition: all 0.3s;
}

.expand-button:hover {
    background-color: rgba(0,0,0,0.9);
    transform: scale(1.1);
}
</style>
"""

css_modal = """
<style>
.image-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.95);
    z-index: 2000;
    overflow: hidden;
    align-items: center;
    justify-content: center;
}

.modal-content {
    max-height: 90%;
    max-width: 90%;
    object-fit: contain;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0,0,0,0.7);
    animation: zoom 0.3s;
}

.close-modal {
    position: fixed;
    top: 20px;
    right: 35px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    z-index: 2001;
    transition: all 0.3s;
}

.close-modal:hover {
    color: #ccc;
}

@keyframes zoom {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

@media (max-width: 768px) {
    .expand-button {
        width: 36px;
        height: 36px;
        font-size: 18px;
        bottom: 10px;
        right: 10px;
    }

    .modal-content {
        max-width: 95%;
        max-height: 95%;
    }

    .close-modal {
        top: 15px;
        right: 20px;
        font-size: 35px;
    }
}
</style>
"""

# Aplicar los estilos al inicio de tu aplicación
st.markdown(css_global, unsafe_allow_html=True)
st.markdown(css_modal, unsafe_allow_html=True)
# --- Encabezado principal ---
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

# --- Funciones faltantes que se habían omitido ---
def image_to_base64(image, max_size=800, quality=85):
    img = Image.open(image)
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size))
    buffered = BytesIO()
    img.save(buffered, format="WEBP", quality=quality)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_image(base64_str):
    return Image.open(BytesIO(base64.b64decode(base64_str)))

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            dbname=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"],
            sslmode="require",
            connect_timeout=3
        )
        return conn
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        st.stop()

def init_session():
    if 'es_admin' not in st.session_state:
        st.session_state.es_admin = False
    query_params = st.query_params.to_dict()
    if 'admin_token' in query_params:
        token = query_params['admin_token']
        if token == ADMIN_PASSWORD_HASH:
            st.session_state.es_admin = True
            st.session_state.admin_token = token

def verificar_admin(password):
    hash_input = hashlib.sha256(password.encode()).hexdigest()
    if hash_input == ADMIN_PASSWORD_HASH:
        st.session_state.es_admin = True
        st.session_state.admin_token = ADMIN_PASSWORD_HASH
        st.query_params.clear()
        st.query_params["admin_token"] = ADMIN_PASSWORD_HASH
        js = f"""
        <script>
            localStorage.setItem('admin_token', '{ADMIN_PASSWORD_HASH}');
        </script>
        """
        st.components.v1.html(js, height=0, width=0)
        return True
    return False

init_session()

check_auth_js = """
<script>
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

if (!getQueryParam('admin_token') && localStorage.getItem('admin_token')) {
    window.location.search = '?admin_token=' + localStorage.getItem('admin_token');
}
</script>
"""
st.components.v1.html(check_auth_js, height=0, width=0)

conn = get_db_connection()
c = conn.cursor(cursor_factory=RealDictCursor)

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


if st.session_state.es_admin:
    with st.expander("📥 Añadir nueva antigüedad", expanded=False):
        with st.form(key="form_nuevo_mueble"):
            col1, col2 = st.columns(2)
            with col1:
                tienda = st.radio("Tienda", options=["El Rastro", "Regueros"], horizontal=True)
            with col2:
                vendido = st.checkbox("Marcar como vendido", value=False)

            nombre = st.text_input("Nombre del mueble*")
            precio = st.number_input("Precio (€)*", min_value=0.0, step=1.0)
            descripcion = st.text_area("Descripción")
            tipo = st.selectbox("Tipo de mueble", list(TIPOS_PLURAL.keys()))

            st.markdown("**Medidas (rellena solo las necesarias):**")
            medidas = {
                "alto": st.number_input("Alto (cm)", min_value=0.0),
                "largo": st.number_input("Largo (cm)", min_value=0.0),
                "fondo": st.number_input("Fondo (cm)", min_value=0.0),
                "diametro": st.number_input("Diámetro (cm)", min_value=0.0),
                "diametro_base": st.number_input("Ø Base (cm)", min_value=0.0),
                "diametro_boca": st.number_input("Ø Boca (cm)", min_value=0.0)
            }



            # Reglas de validación por tipo
            medidas_requeridas = {
                "Mesa": ["medida1", "medida2", "medida3"],
                "Consola": ["medida1", "medida2", "medida3"],
                "Buffet": ["medida1", "medida2", "medida3"],
                "Biblioteca": ["medida1", "medida2", "medida3"],
                "Armario": ["medida1", "medida2", "medida3"],
                "Cómoda": ["medida1", "medida2", "medida3"],
                "Columna": ["medida1"],
                "Espejo": ["medida1", "medida2"],
                "Copa": ["medida1", "medida2", "medida3"],
                "Asiento": [],
                "Otro artículo": []
            }

            st.caption(f"ℹ️ Medidas requeridas para {tipo}: {', '.join(medidas_requeridas[tipo]) if medidas_requeridas[tipo] else 'Opcionales'}")
            imagenes = st.file_uploader("Seleccionar imágenes", 
                                type=["jpg", "jpeg", "png"], 
                                accept_multiple_files=True)

            guardar = st.form_submit_button("Guardar")
            if guardar:
                if not nombre or precio <= 0 or not imagenes:
                    st.warning("Por favor, rellena todos los campos obligatorios, incluyendo al menos una imagen.")
                    st.stop()

                    st.warning("Por favor, rellena todos los campos obligatorios.")
                    st.stop()
            
                # Validar medidas requeridas según el tipo
                claves_medidas = {
                    "medida1": "alto",
                    "medida2": "largo",
                    "medida3": "fondo"
                }
                errores = []
                for requerida in medidas_requeridas[tipo]:
                    clave = claves_medidas.get(requerida)
                    if clave and medidas[clave] <= 0:
                        errores.append(requerida)
            
                if errores:
                    st.error(f"Faltan las siguientes medidas requeridas: {', '.join(errores)}")
                    st.stop()


                # Insertar en muebles
                c.execute("""
                    INSERT INTO muebles (
                        nombre, precio, descripcion, tienda, vendido, tipo, fecha,
                        alto, largo, fondo, diametro, diametro_base, diametro_boca
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s)
                """, (
                    nombre, precio, descripcion, tienda, vendido, tipo, datetime.now(),
                    medidas["alto"] or None,
                    medidas["largo"] or None,
                    medidas["fondo"] or None,
                    medidas["diametro"] or None,
                    medidas["diametro_base"] or None,
                    medidas["diametro_boca"] or None
                ))

                c.execute("SELECT LASTVAL() AS lastval")
                mueble_id = c.fetchone()['lastval']


                # Insertar imágenes
                for i, imagen in enumerate(imagenes):
                    base64_str = image_to_base64(imagen)
                    es_principal = i == 0
                    c.execute("""
                        INSERT INTO imagenes_muebles (mueble_id, imagen_base64, es_principal)
                        VALUES (%s, %s, %s)
                    """, (mueble_id, base64_str, es_principal))

                conn.commit()
                st.success("✅ ¡Mueble añadido con éxito!")
                st.rerun()



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
            st.query_params.clear()
            st.rerun()
    
    # Estadísticas
    st.markdown("## 📊 Estadísticas")
    try:
        c.execute("SELECT COUNT(*) as count FROM muebles WHERE vendido = FALSE AND tienda = 'El Rastro'")
        en_rastro = c.fetchone()["count"] or 0
        
        c.execute("SELECT COUNT(*) as count FROM muebles WHERE vendido = FALSE AND tienda = 'Regueros'")
        en_regueros = c.fetchone()["count"] or 0
        
        c.execute("SELECT COUNT(*) as count FROM muebles WHERE vendido = TRUE")
        vendidos = c.fetchone()["count"] or 0

        
        st.metric("🔵 En El Rastro", en_rastro)
        st.metric("🔴 En Regueros", en_regueros)
        st.metric("💰 Vendidos", vendidos)
        
    except psycopg2.Error as e:
        st.error("Error al cargar estadísticas")
        st.metric("🔵 En El Rastro", 0)
        st.metric("🔴 En Regueros", 0)
        st.metric("💰 Vendidos", 0)

    if st.session_state.es_admin:
        if st.button("⬇️ Exportar inventario CSV"):
            c.execute("SELECT * FROM muebles")
            data = c.fetchall()
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                st.download_button("Descargar CSV", df.to_csv(index=False).encode(), "muebles.csv", "text/csv")

def mostrar_galeria_imagenes(imagenes, mueble_id):
    if not imagenes:
        return
    
    # Mostrar la imagen principal
    img_principal = imagenes[0]['imagen_base64']
    st.image(base64_to_image(img_principal), use_column_width=True)
    
    # Mostrar imágenes secundarias si existen
    if len(imagenes) > 1:
        with st.expander(f"📸 Ver más imágenes ({len(imagenes)-1})", expanded=False):
            cols = st.columns(min(3, len(imagenes)-1))
            for i, img_dict in enumerate(imagenes[1:], start=1):
                with cols[(i-1) % len(cols)]:
                    st.image(base64_to_image(img_dict['imagen_base64']), use_column_width=True)

def es_nuevo(fecha_str):
    formatos_posibles = [
        "%Y-%m-%d %H:%M:%S.%f",  # con microsegundos
        "%Y-%m-%d %H:%M:%S",     # con segundos
        "%Y-%m-%d"               # solo fecha
    ]
    for formato in formatos_posibles:
        try:
            fecha = datetime.strptime(str(fecha_str), formato)
            return (datetime.now() - fecha).days <= 1
        except ValueError:
            continue
    return False  # Si ninguno de los formatos funcionó


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
            try:
                mostrar_galeria_imagenes(imagenes_actuales, mueble_id)
            except:
                st.warning("Error al cargar la galería de imágenes")
            
            # Mantener la lógica para marcar como principal y eliminar
            cols = st.columns(min(3, len(imagenes_actuales)))
            for i, img_dict in enumerate(imagenes_actuales):
                img_base64 = img_dict['imagen_base64']
                es_principal = img_dict['es_principal']
                with cols[i % 3]:
                    if st.radio("Marcar como principal", ["Sí", "No"], 
                               index=0 if es_principal else 1, 
                               key=f"principal_{i}_{mueble_id}") == "Sí":
                        c.execute("UPDATE imagenes_muebles SET es_principal = FALSE WHERE mueble_id = %s", (mueble_id,))
                        c.execute("UPDATE imagenes_muebles SET es_principal = TRUE WHERE mueble_id = %s AND imagen_base64 = %s", (mueble_id, img_base64))
                        conn.commit()
                        st.rerun()
                    
                    if st.button(f"❌ Eliminar esta imagen", key=f"del_img_{i}_{mueble_id}"):
                        c.execute("DELETE FROM imagenes_muebles WHERE imagen_base64 = %s", (img_base64,))
                        conn.commit()
                        st.rerun

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
                            INSERT INTO muebles (nombre, precio, descripcion, tienda, vendido, tipo, fecha,
                                alto, largo, fondo, diametro, diametro_base, diametro_boca)
                            VALUES (%s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s)
                        """, (
                            nombre, precio, descripcion, tienda, vendido, tipo, datetime.now(),
                            medidas["alto"] or None,
                            medidas["largo"] or None,
                            medidas["fondo"] or None,
                            medidas["diametro"] or None,
                            medidas["diametro_base"] or None,
                            medidas["diametro_boca"] or None
                        ))

                
                conn.commit()
                st.success("¡Cambios guardados!")
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar edición"):
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()

# Galería de imágenes mejorada con miniaturas, ampliación visual y scroll horizontal
from streamlit.components.v1 import html

def mostrar_medidas_extendido(mueble):
    etiquetas = {
        'alto': "Alto",
        'largo': "Largo",
        'fondo': "Fondo",
        'diametro': "Diámetro",
        'diametro_base': "Ø Base",
        'diametro_boca': "Ø Boca"
    }
    partes = []
    for clave, nombre in etiquetas.items():
        valor = mueble.get(clave)
        if valor not in [None, 0]:
            partes.append(f"{nombre}: {valor}cm")
    return " · ".join(partes) if partes else "Sin medidas"

if 'filtro_nombre' not in st.session_state:
    st.session_state.filtro_nombre = ""

filtro_nombre = st.text_input("🔍 Buscar por nombre", value=st.session_state.filtro_nombre)
if filtro_nombre != st.session_state.filtro_nombre:
    st.session_state.filtro_nombre = filtro_nombre

if filtro_nombre:
    query += " AND LOWER(nombre) LIKE %s"
    params.append(f"%{filtro_nombre.lower()}%")


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
        tipos_db = [tipo["tipo"] for tipo in c.fetchall()]
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
                            mostrar_galeria_imagenes(imagenes_mueble, mueble['id'])
                        except:
                            st.warning("Error al cargar imágenes")
                
                with col_info:
                    st.markdown(f"### {mueble['nombre']}")
                    if es_nuevo(mueble['fecha']):
                        st.markdown("<span style='color: green; font-size: 1.2em;'>🆕 Nuevo</span>", unsafe_allow_html=True)
                    st.markdown(f"**Tipo:** {mueble['tipo']}")
                    st.markdown(f"**Precio:** {mueble['precio']} €")
                    st.markdown(f"**Tienda:** {mueble['tienda']}")
                    st.markdown(f"**Medidas:** {mostrar_medidas_extendido(mueble)}")

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
                                mostrar_galeria_imagenes(imagenes_mueble, mueble['id'])
                            except:
                                st.warning("Error al cargar imágenes")
                                        
                    with col_info:
                        st.markdown(f"### {mueble['nombre']}")
                        if es_nuevo(mueble['fecha']):
                            st.markdown("<span style='color: green; font-size: 1.2em;'>🆕 Nuevo</span>", unsafe_allow_html=True)
                        st.markdown(f"**Tipo:** {mueble['tipo']}")
                        st.markdown(f"**Precio:** {mueble['precio']} €")
                        st.markdown(f"**Tienda:** {mueble['tienda']}")
                        st.markdown(f"**Medidas:** {mostrar_medidas_extendido(mueble)}")

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




