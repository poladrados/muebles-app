import streamlit as st
import sqlite3
import os
import hashlib  # Usamos hashlib en lugar de passlib
from PIL import Image
from datetime import datetime

# --- Configuración inicial ---
CARPETA_IMAGENES = "imagenes_muebles"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

# --- Configuración de Acceso Admin ---
# Contraseña: "admin123" (cámbiala después)
ADMIN_PASSWORD_HASH = "c1c560d0e2bf0d3c36c85714d22c16be0be30efc9f480eff623b486778be2110"

def init_session():
    if 'es_admin' not in st.session_state:
        st.session_state.es_admin = False

def verificar_admin(password):
    hash_input = hashlib.sha256(password.encode()).hexdigest()
    return hash_input == ADMIN_PASSWORD_HASH


# --- Inicialización de sesión ---
init_session()

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

    /* ESTILOS PARA EL INDICADOR DE MODO */
    .mode-indicator {
        margin-left: auto;
        display: flex;
        align-items: center;
        margin-right: 20px;
        color: #023e8a;
        font-weight: bold;
    }
    
    /* ESTILOS MÓVIL */
    @media (max-width: 768px) {
        .custom-header {
            padding: 0.8rem 1rem !important;
            justify-content: space-between !important;
        }
        
        .custom-header h1.header-title {
            font-size: 1.5rem !important;
            margin-left: 0 !important;
            padding-left: 0 !important;
            text-align: left !important;
        }
        
        .header-logo img {
            height: 50px !important;
        }
        
        .header-title-container {
            justify-content: flex-start;
            padding-left: 10px;
        }
        
        .mode-indicator {
            display: none !important;
        }
        
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: white !important;
            background: #023e8a !important;
        }
        
        .stApp {
            padding: 0.8rem !important;
        }
        
        .stButton>button {
            width: 100% !important;
            margin: 6px 0 !important;
        }
    }
    # Busca tu sección de ESTILOS PERSONALIZADOS y añade esto al final, antes del cierre </style>:

    /* Estilos para el carrusel de imágenes */
    .image-carousel {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 15px;
    }
    .image-carousel img {
        border-radius: 8px;
        object-fit: cover;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    /* Estilo para botones de edición */
    .btn-editar {
        background-color: #4CAF50 !important;
        color: white !important;
        border: 1px solid #4CAF50 !important;
        margin-left: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER modificado ---
st.markdown(f"""
    <div class="custom-header">
        <div class="header-logo">
            <img src="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png" alt="Logo">
        </div>
        <div class="header-title-container">
            <h1 class="header-title">Inventario de Antigüedades El Jueves</h1>
        </div>
        <div class="mode-indicator">
            {'🔓 Modo Admin' if st.session_state.es_admin else '🔒 Modo Cliente'}
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Barra lateral para login de admin ---
with st.sidebar:
    if not st.session_state.es_admin:
        with st.expander("🔑 Acceso Administradores", expanded=False):
            password = st.text_input("Contraseña de administrador", type="password")
            if st.button("Ingresar como administrador"):
                if verificar_admin(password):
                    st.session_state.es_admin = True
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
    else:
        st.success("Modo administrador activo")
        if st.button("🚪 Salir del modo admin"):
            st.session_state.es_admin = False
            st.rerun()
            
    # --- Estadísticas ---
    st.markdown("## 📊 Estadísticas")
    c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 0 AND tienda = 'El Rastro'")
    en_rastro = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 0 AND tienda = 'Regueros'")
    en_regueros = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM muebles WHERE vendido = 1")
    vendidos = c.fetchone()[0]

    st.sidebar.metric("🔵 En El Rastro", en_rastro)
    st.sidebar.metric("🔴 En Regueros", en_regueros)
    st.sidebar.metric("💰 Vendidos", vendidos)

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
c.execute("""
    CREATE TABLE IF NOT EXISTS imagenes_muebles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mueble_id INTEGER,
        ruta_imagen TEXT,
        es_principal BOOLEAN DEFAULT 0,
        FOREIGN KEY(mueble_id) REFERENCES muebles(id)
    )
""")
conn.commit()

# --- Formulario solo visible para admin ---
if st.session_state.es_admin:
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
                "Copa", "Asiento", "Otro artículo"
            ])
            
            # --- Todos los campos de medidas posibles ---
            st.markdown("**Medidas (rellena solo las necesarias):**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                largo = st.number_input("Largo (cm)", min_value=0, key="largo")
                alto = st.number_input("Alto (cm)", min_value=0, key="alto")
                diametro_base = st.number_input("Diámetro base (cm)", min_value=0, key="diam_base")
                
            with col2:
                ancho = st.number_input("Ancho (cm)", min_value=0, key="ancho")
                fondo = st.number_input("Fondo (cm)", min_value=0, key="fondo")
                diametro_boca = st.number_input("Diámetro boca (cm)", min_value=0, key="diam_boca")
                
            with col3:
                lados_base = st.number_input("Lados base", min_value=3, max_value=8, value=4, key="lados")
                # Espacio vacío para alinear
                
            # Nota sobre las medidas requeridas según el tipo
            medidas_requeridas = {
                "Mesa": ["largo", "alto", "fondo"],
                "Consola": ["largo", "alto", "fondo"],
                "Buffet": ["largo", "alto", "fondo"],
                "Cómoda": ["largo", "alto", "fondo"],
                "Biblioteca": ["alto", "ancho", "fondo"],
                "Armario": ["alto", "ancho", "fondo"],
                "Columna": ["alto", "lados"],
                "Espejo": ["alto", "ancho"],
                "Copa": ["alto", "diam_base", "diam_boca"],
                "Asiento": [],  # Opcionales
                "Otro artículo": []  # Opcionales
            }
            
            st.caption(f"ℹ️ Medidas requeridas para {tipo}: {', '.join(medidas_requeridas[tipo]) if medidas_requeridas[tipo] else 'Opcionales'}")
            
                        # Reemplaza TODO el bloque desde el file_uploader hasta el final del if submitted con esto:
            imagenes = st.file_uploader("Sube imágenes* (primera será la principal)", 
                                     type=["jpg", "jpeg", "png"], 
                                     accept_multiple_files=True)
            
            submitted = st.form_submit_button("Guardar")
            if submitted:
                if imagenes and nombre and precio > 0 and tipo:
                    # Validar medidas requeridas
                    medidas_faltantes = []
                    for medida in medidas_requeridas[tipo]:
                        if medida == "largo" and largo <= 0:
                            medidas_faltantes.append("largo")
                        elif medida == "alto" and alto <= 0:
                            medidas_faltantes.append("alto")
                        elif medida == "ancho" and ancho <= 0:
                            medidas_faltantes.append("ancho")
                        elif medida == "fondo" and fondo <= 0:
                            medidas_faltantes.append("fondo")
                        elif medida == "lados" and lados_base <= 0:
                            medidas_faltantes.append("lados base")
                        elif medida == "diam_base" and diametro_base <= 0:
                            medidas_faltantes.append("diámetro base")
                        elif medida == "diam_boca" and diametro_boca <= 0:
                            medidas_faltantes.append("diámetro boca")
                    
                    if medidas_faltantes:
                        st.error(f"Faltan medidas obligatorias para {tipo}: {', '.join(medidas_faltantes)}")
                        st.stop()
                    
                    # Mapeo de medidas a guardar en medida1, medida2, medida3 según el tipo
                    medida_map = {
                        "Mesa": [largo, alto, fondo],
                        "Consola": [largo, alto, fondo],
                        "Buffet": [largo, alto, fondo],
                        "Cómoda": [largo, alto, fondo],
                        "Biblioteca": [alto, ancho, fondo],
                        "Armario": [alto, ancho, fondo],
                        "Columna": [alto, lados_base, None],
                        "Espejo": [alto, ancho, None],
                        "Copa": [alto, diametro_base, diametro_boca],
                        "Asiento": [alto, ancho, None],
                        "Otro artículo": [alto, ancho, None]
                    }
                    
                    medida1, medida2, medida3 = medida_map[tipo]
                    
                    # Insertar el mueble (sin ruta_imagen)
                    c.execute("""
                        INSERT INTO muebles (
                            nombre, precio, descripcion, fecha, 
                            vendido, tienda, tipo, medida1, medida2, medida3
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nombre, precio, descripcion, 
                        datetime.now().strftime("%Y-%m-%d"), 
                        int(vendido), tienda, tipo, 
                        medida1, medida2, medida3
                    ))
                    mueble_id = c.lastrowid
                    
                    # Guardar las imágenes
                    for i, imagen in enumerate(imagenes):
                        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mueble_id}_{i}_{imagen.name}"
                        ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                        
                        with open(ruta_imagen, "wb") as f:
                            f.write(imagen.getbuffer())
                        
                        # La primera imagen es la principal
                        es_principal = 1 if i == 0 else 0
                        
                        c.execute("""
                            INSERT INTO imagenes_muebles (mueble_id, ruta_imagen, es_principal)
                            VALUES (?, ?, ?)
                        """, (mueble_id, ruta_imagen, es_principal))
                    
                    conn.commit()
                    st.success("✅ ¡Antigüedad registrada con éxito!")
                    st.rerun()
                else:
                    st.warning("⚠️ Completa los campos obligatorios (*)")

def mostrar_medidas(tipo, m1, m2, m3):
    # Primero convertimos None a 0 para las medidas
    m1 = m1 or 0
    m2 = m2 or 0
    m3 = m3 or 0
    
    if tipo in ["Mesa", "Consola", "Buffet", "Cómoda"]:
        if m1 and m2 and m3:
            return f"{m1}cm (largo) × {m2}cm (alto) × {m3}cm (fondo)"
        elif m1 or m2 or m3:
            medidas = []
            if m1: medidas.append(f"{m1}cm (largo)")
            if m2: medidas.append(f"{m2}cm (alto)")
            if m3: medidas.append(f"{m3}cm (fondo)")
            return " × ".join(medidas)
    
    elif tipo in ["Biblioteca", "Armario"]:
        if m1 and m2 and m3:
            return f"{m1}cm (alto) × {m2}cm (ancho) × {m3}cm (fondo)"
        elif m1 or m2 or m3:
            medidas = []
            if m1: medidas.append(f"{m1}cm (alto)")
            if m2: medidas.append(f"{m2}cm (ancho)")
            if m3: medidas.append(f"{m3}cm (fondo)")
            return " × ".join(medidas)
    
    elif tipo == "Columna":
        if m1 and m2:
            return f"{m1}cm (alto) | {m2} lados en base"
        elif m1 or m2:
            medidas = []
            if m1: medidas.append(f"{m1}cm (alto)")
            if m2: medidas.append(f"{m2} lados")
            return " | ".join(medidas)
    
    elif tipo == "Espejo":
        if m1 and m2:
            return f"{m1}cm (alto) × {m2}cm (ancho)"
        elif m1 or m2:
            medidas = []
            if m1: medidas.append(f"{m1}cm (alto)")
            if m2: medidas.append(f"{m2}cm (ancho)")
            return " × ".join(medidas)
    
    elif tipo == "Copa":
        if m1 and m2 and m3:
            return f"{m1}cm (alto) | Base: Ø{m2}cm | Boca: Ø{m3}cm"
        elif m1 or m2 or m3:
            medidas = [f"{m1}cm (alto)"] if m1 else []
            if m2: medidas.append(f"Base: Ø{m2}cm")
            if m3: medidas.append(f"Boca: Ø{m3}cm")
            return " | ".join(medidas)
    
    elif tipo in ["Asiento", "Otro artículo"]:
        medidas = []
        if m1: medidas.append(f"{m1}cm (alto)")
        if m2: medidas.append(f"{m2}cm (ancho)")
        if m3: medidas.append(f"{m3}cm (profundo)")
        return " × ".join(medidas) if medidas else "Sin medidas"
    
    return "Sin medidas registradas"

# Busca la función mostrar_medidas() y AÑADE JUSTO DESPUÉS esta nueva función:

def mostrar_detalle_mueble(mueble_id):
    # Obtener datos del mueble
    c.execute("SELECT * FROM muebles WHERE id = ?", (mueble_id,))
    mueble = c.fetchone()
    
    # Obtener todas las imágenes del mueble
    c.execute("SELECT ruta_imagen FROM imagenes_muebles WHERE mueble_id = ? ORDER BY es_principal DESC", (mueble_id,))
    imagenes = c.fetchall()
    
    with st.expander(f"🔍 Ver detalles completos de {mueble[1]}", expanded=False):
        st.markdown(f"### {mueble[1]}")
        st.markdown(f"**Precio:** {mueble[2]} €")
        st.markdown(f"**Tienda:** {mueble[7]}")
        st.markdown(f"**Tipo:** {mueble[8]}")
        st.markdown(f"**Medidas:** {mostrar_medidas(mueble[8], mueble[9], mueble[10], mueble[11])}")
        
        if mueble[3]:  # Descripción
            st.markdown(f"**Descripción:** {mueble[3]}")
        
        # Mostrar todas las imágenes en un carrusel
        if imagenes:
            cols = st.columns(min(3, len(imagenes)))
            for i, img in enumerate(imagenes):
                try:
                    with cols[i % 3]:
                        imagen = Image.open(img[0])
                        st.image(imagen, use_container_width=True, caption=f"Foto {i+1}")
                except:
                    st.warning(f"No se pudo cargar la imagen {i+1}")
def mostrar_formulario_edicion(mueble_id):
    # Obtener datos actuales del mueble
    c.execute("SELECT * FROM muebles WHERE id = ?", (mueble_id,))
    mueble = c.fetchone()
    
    # Obtener imágenes actuales
    c.execute("SELECT ruta_imagen, es_principal FROM imagenes_muebles WHERE mueble_id = ? ORDER BY es_principal DESC", (mueble_id,))
    imagenes_actuales = c.fetchall()
    
    with st.form(key=f"form_editar_{mueble_id}"):
        st.markdown(f"### Editando: {mueble[1]}")
        
        # Sección 1: Información básica
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.radio("Tienda", options=["El Rastro", "Regueros"], 
                             index=0 if mueble[7] == "El Rastro" else 1)
        with col2:
            vendido = st.checkbox("Marcar como vendido", value=bool(mueble[6]))
        
        nombre = st.text_input("Nombre*", value=mueble[1])
        precio = st.number_input("Precio (€)*", min_value=0.0, value=mueble[2])
        descripcion = st.text_area("Descripción", value=mueble[3])
        
        # Sección 2: Imágenes
        st.markdown("### Imágenes actuales")
        if imagenes_actuales:
            cols = st.columns(min(3, len(imagenes_actuales)))
            for i, (ruta_imagen, es_principal) in enumerate(imagenes_actuales):
                with cols[i % 3]:
                    try:
                        img = Image.open(ruta_imagen)
                        st.image(img, caption=f"{'✅ Principal' if es_principal else 'Secundaria'} - Imagen {i+1}")
                        if st.button(f"❌ Eliminar esta imagen", key=f"del_img_{i}_{mueble_id}"):
                            os.remove(ruta_imagen)
                            c.execute("DELETE FROM imagenes_muebles WHERE ruta_imagen = ?", (ruta_imagen,))
                            conn.commit()
                            st.rerun()
                    except:
                        st.warning("Imagen no encontrada")
        else:
            st.warning("Este mueble no tiene imágenes aún")
        
        st.markdown("### Añadir nuevas imágenes")
        nuevas_imagenes = st.file_uploader("Seleccionar imágenes", 
                                         type=["jpg", "jpeg", "png"], 
                                         accept_multiple_files=True,
                                         key=f"uploader_{mueble_id}")
        
        # Sección 3: Medidas (adaptada a tu estructura actual)
        st.markdown("### Medidas")
        col1, col2, col3 = st.columns(3)
        with col1:
            medida1 = st.number_input("Largo/Alto (cm)", min_value=0, value=int(mueble[9]) if mueble[9] else 0)
        with col2:
            medida2 = st.number_input("Ancho (cm)", min_value=0, value=int(mueble[10]) if mueble[10] else 0)
        with col3:
            medida3 = st.number_input("Fondo/Diámetro (cm)", min_value=0, value=int(mueble[11]) if mueble[11] else 0)
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar cambios"):
                # Actualizar datos básicos
                c.execute("""
                    UPDATE muebles SET
                        nombre = ?, precio = ?, descripcion = ?,
                        tienda = ?, vendido = ?, 
                        medida1 = ?, medida2 = ?, medida3 = ?
                    WHERE id = ?
                """, (
                    nombre, precio, descripcion, tienda, int(vendido),
                    medida1 if medida1 > 0 else None,
                    medida2 if medida2 > 0 else None,
                    medida3 if medida3 > 0 else None,
                    mueble_id
                ))
                
                # Añadir nuevas imágenes
                if nuevas_imagenes:
                    for img in nuevas_imagenes:
                        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mueble_id}_{img.name}"
                        ruta = os.path.join(CARPETA_IMAGENES, nombre_archivo)
                        with open(ruta, "wb") as f:
                            f.write(img.getbuffer())
                        
                        # La primera imagen se marca como principal si no hay imágenes
                        es_principal = 0 if imagenes_actuales else 1
                        c.execute("""
                            INSERT INTO imagenes_muebles (mueble_id, ruta_imagen, es_principal)
                            VALUES (?, ?, ?)
                        """, (mueble_id, ruta, es_principal))
                
                conn.commit()
                st.success("¡Cambios guardados!")
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar edición"):
                st.session_state.pop('editar_mueble_id', None)
                st.rerun()

# --- Pestañas ---
tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])
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

# Pestaña 1: En venta
with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    
    col_filtros = st.columns(4)
    with col_filtros[0]:
        filtro_tienda = st.selectbox("Filtrar por tienda", options=["Todas", "El Rastro", "Regueros"])
    
    with col_filtros[1]:
        # Obtenemos los tipos únicos de la base de datos
        c.execute("SELECT DISTINCT tipo FROM muebles")
        tipos_db = [tipo[0] for tipo in c.fetchall()]
        
        # Creamos opciones con "Todos" primero y luego los tipos en plural
        opciones_filtro = ["Todos"] + [TIPOS_PLURAL.get(tipo, tipo) for tipo in tipos_db]
        
        # Mostramos el selectbox con nombres en plural
        filtro_tipo_plural = st.selectbox("Filtrar por tipo", options=opciones_filtro)
        
        # Convertimos el plural seleccionado de vuelta a singular para la consulta
        tipo_para_consulta = None
        if filtro_tipo_plural != "Todos":
            tipo_para_consulta = next((k for k, v in TIPOS_PLURAL.items() if v == filtro_tipo_plural), filtro_tipo_plural)
    
    with col_filtros[2]:
        orden = st.selectbox("Ordenar por", options=["Más reciente", "Más antiguo", "Precio (↑)", "Precio (↓)"])
    
    # Construimos la consulta SQL
    query = "SELECT * FROM muebles WHERE vendido = 0"
    
    # Aplicamos filtros
    if filtro_tienda != "Todas":
        query += f" AND tienda = '{filtro_tienda}'"
    if filtro_tipo_plural != "Todos":
        query += f" AND tipo = '{tipo_para_consulta}'"
    
    # Aplicamos orden
    if orden == "Más reciente":
        query += " ORDER BY id DESC"
    elif orden == "Más antiguo":
        query += " ORDER BY id ASC"
    elif orden == "Precio (↑)":
        query += " ORDER BY precio ASC"
    else:
        query += " ORDER BY precio DESC"
    
    # Ejecutamos la consulta
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
                        # Obtener la imagen principal
                        c.execute("""
                            SELECT ruta_imagen 
                            FROM imagenes_muebles 
                            WHERE mueble_id = ? AND es_principal = 1 
                            LIMIT 1
                        """, (mueble[0],))
                        img_principal = c.fetchone()
                        
                        if img_principal:
                            imagen = Image.open(img_principal[0])
                            st.image(imagen, use_container_width=True)
                        else:
                            st.warning("Sin imagen principal")
                    except Exception as e:
                        st.warning(f"Error al cargar imagen: {str(e)}")
                
                with col_info:
                    st.markdown(f"### {mueble[1]}")
                    st.markdown(f"**Tipo:** {mueble[7]}")
                    st.markdown(f"**Precio:** {mueble[2]} €")
                    st.markdown(f"**Tienda:** {mueble[6]}")
                    st.markdown(f"**Medidas:** {mostrar_medidas(mueble[7], mueble[8], mueble[9], mueble[10])}")
                    st.markdown(f"**Fecha registro:** {mueble[5]}")
                    
                    if mueble[3]:
                        st.markdown(f"**Descripción:** {mueble[3]}")
                    
                    # --- NUEVO: Bloque de edición ---
                    if st.session_state.get('editar_mueble_id') == mueble[0]:
                        mostrar_formulario_edicion(mueble[0])
                    else:
                        mostrar_detalle_mueble(mueble[0])
                        
                        # --- CONTROLES SOLO PARA ADMIN (3 columnas) ---
                        if st.session_state.es_admin:
                            col1, col2, col3 = st.columns(3)
                            
                            # Columna 1: Editar
                            with col1:
                                if st.button(f"✏️ Editar", key=f"editar_{mueble[0]}"):
                                    st.session_state['editar_mueble_id'] = mueble[0]
                                    st.rerun()
                            
                            # Columna 2: Eliminar
                            with col2:
                                if st.button(f"🗑️ Eliminar", key=f"eliminar_{mueble[0]}"):
                                    if st.session_state.get(f'confirm_eliminar_{mueble[0]}'):
                                        # Eliminar imágenes asociadas
                                        c.execute("SELECT ruta_imagen FROM imagenes_muebles WHERE mueble_id = ?", (mueble[0],))
                                        imagenes = c.fetchall()
                                        for img in imagenes:
                                            if img[0] and os.path.exists(img[0]):
                                                os.remove(img[0])
                                        c.execute("DELETE FROM imagenes_muebles WHERE mueble_id = ?", (mueble[0],))
                                        
                                        # Eliminar mueble
                                        c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                                        conn.commit()
                                        st.rerun()
                                    else:
                                        st.session_state[f'confirm_eliminar_{mueble[0]}'] = True
                                        st.rerun()
                                
                                if st.session_state.get(f'confirm_eliminar_{mueble[0]}'):
                                    st.warning("¿Confirmar eliminación? Pulsa Eliminar nuevamente")
                            
                            # Columna 3: Marcar como vendido
                            with col3:
                                if st.button(f"✔️ Marcar como vendido", key=f"vendido_{mueble[0]}"):
                                    c.execute("UPDATE muebles SET vendido = 1 WHERE id = ?", (mueble[0],))
                                    conn.commit()
                                    st.rerun()

# Pestaña 2: Vendidos - solo visible para admin
if st.session_state.es_admin:
    with tab2:
        st.markdown("## ✔️ Muebles vendidos")
        c.execute("SELECT * FROM muebles WHERE vendido = 1 ORDER BY fecha DESC")
        muebles_vendidos = c.fetchall()
        
        if not muebles_vendidos:
            st.info("No hay muebles vendidos registrados")
        else:
            for mueble in muebles_vendidos:
                with st.container(border=True):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        try:
                            # Obtener la imagen principal
                            c.execute("""
                                SELECT ruta_imagen 
                                FROM imagenes_muebles 
                                WHERE mueble_id = ? AND es_principal = 1 
                                LIMIT 1
                            """, (mueble[0],))
                            img_principal = c.fetchone()
                            
                            if img_principal:
                                imagen = Image.open(img_principal[0])
                                st.image(imagen, use_container_width=True)
                            else:
                                st.warning("Sin imagen principal")
                        except Exception as e:
                            st.warning(f"Error al cargar imagen: {str(e)}")
                    
                    with col_info:
                        st.markdown(f"### {mueble[1]}")
                        st.markdown(f"**Tipo:** {mueble[7]}")
                        st.markdown(f"**Precio:** {mueble[2]} €")
                        st.markdown(f"**Tienda:** {mueble[6]}")
                        st.markdown(f"**Medidas:** {mostrar_medidas(mueble[7], mueble[8], mueble[9], mueble[10])}")
                        st.markdown(f"**Fecha registro:** {mueble[5]}")
                        
                        if mueble[3]:
                            st.markdown(f"**Descripción:** {mueble[3]}")
                        
                        # --- NUEVO: Bloque de edición ---
                        if st.session_state.get('editar_mueble_id') == mueble[0]:
                            mostrar_formulario_edicion(mueble[0])
                        else:
                            mostrar_detalle_mueble(mueble[0])
                            
                            # --- CONTROLES SOLO PARA ADMIN (3 columnas) ---
                            if st.session_state.es_admin:
                                col1, col2, col3 = st.columns(3)
                                
                                # Columna 1: Editar
                                with col1:
                                    if st.button(f"✏️ Editar", key=f"editar_v_{mueble[0]}"):
                                        st.session_state['editar_mueble_id'] = mueble[0]
                                        st.rerun()
                                
                                # Columna 2: Eliminar
                                with col2:
                                    if st.button(f"🗑️ Eliminar", key=f"eliminar_v_{mueble[0]}"):
                                        if st.session_state.get(f'confirm_eliminar_v_{mueble[0]}'):
                                            # Eliminar imágenes asociadas
                                            c.execute("SELECT ruta_imagen FROM imagenes_muebles WHERE mueble_id = ?", (mueble[0],))
                                            imagenes = c.fetchall()
                                            for img in imagenes:
                                                if img[0] and os.path.exists(img[0]):
                                                    os.remove(img[0])
                                            c.execute("DELETE FROM imagenes_muebles WHERE mueble_id = ?", (mueble[0],))
                                            
                                            # Eliminar mueble
                                            c.execute("DELETE FROM muebles WHERE id = ?", (mueble[0],))
                                            conn.commit()
                                            st.rerun()
                                        else:
                                            st.session_state[f'confirm_eliminar_v_{mueble[0]}'] = True
                                            st.rerun()
                                    
                                    if st.session_state.get(f"confirm_eliminar_v_{mueble[0]}"):
                                        st.warning("¿Confirmar eliminación? Pulsa Eliminar nuevamente")
                                
                                with col3:
                                    if st.button(f"↩️ Marcar como disponible", key=f"revertir_{mueble[0]}"):
                                        c.execute("UPDATE muebles SET vendido = 0 WHERE id = ?", (mueble[0],))
                                        conn.commit()
                                        st.rerun()
else:
    # Para clientes, mostrar solo un mensaje en la pestaña Vendidos
    with tab2:
        st.info("🔒 Esta sección solo está disponible para administradores")

conn.close()


