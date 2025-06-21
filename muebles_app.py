import streamlit as st
import sqlite3
import os
from PIL import Image
from datetime import datetime

# --- Configuración inicial ---
CARPETA_IMAGENES = "imagenes_muebles"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

conn = sqlite3.connect("muebles.db")
c = conn.cursor()

# --- Configuración de página ---
st.set_page_config(
    page_title="Inventario El Jueves",
    page_icon="https://raw.githubusercontent.com/poladrados/muebles-app/main/images/web-app-manifest-192x192.png",
    layout="wide"
)
st.markdown("""<meta name="viewport" content="width=device-width, initial-scale=1.0">""", unsafe_allow_html=True)

# --- CSS personalizado ---
st.markdown("""
    <style>
    /* Aquí puedes poner estilos CSS personalizados si quieres */
    </style>
""", unsafe_allow_html=True)

# --- HEADER centrado ---
st.markdown(
    """
    <h1 style='text-align: center; color: #023e8a; font-weight: bold; margin-bottom: 1rem;'>
        Inventario de Antigüedades El Jueves
    </h1>
    """,
    unsafe_allow_html=True
)

# --- Formulario para añadir muebles ---
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

        st.markdown("### Medidas (cm) - Rellena las que correspondan")
        medida1 = st.number_input("Medida 1", min_value=0.0, step=0.1, format="%.1f")
        medida2 = st.number_input("Medida 2", min_value=0.0, step=0.1, format="%.1f")
        medida3 = st.number_input("Medida 3", min_value=0.0, step=0.1, format="%.1f")

        imagen = st.file_uploader("Sube una imagen*", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Guardar")
        if submitted:
            if imagen and nombre and precio > 0 and tipo:
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
                    medida1 if medida1 > 0 else None,
                    medida2 if medida2 > 0 else None,
                    medida3 if medida3 > 0 else None
                ))
                conn.commit()
                st.success("✅ ¡Antigüedad registrada!")
                st.experimental_rerun()
            else:
                st.warning("⚠️ Completa los campos obligatorios (*)")

# --- Pestañas para mostrar muebles ---
tab1, tab2 = st.tabs(["📦 En venta", "💰 Vendidos"])

def mostrar_medidas(tipo, m1, m2, m3):
    if m1 is None and m2 is None and m3 is None:
        return "Sin medidas registradas"
    partes = []
    if m1 is not None:
        partes.append(f"{m1}cm (medida1)")
    if m2 is not None:
        partes.append(f"{m2}cm (medida2)")
    if m3 is not None:
        partes.append(f"{m3}cm (medida3)")
    return " × ".join(partes)

with tab1:
    st.markdown("## 🏷️ Muebles disponibles")
    c.execute("SELECT id, nombre, precio, descripcion, ruta_imagen, fecha, tienda, tipo, medida1, medida2, medida3 FROM muebles WHERE vendido = 0 ORDER BY id DESC")
    muebles = c.fetchall()

    if not muebles:
        st.info("No hay muebles disponibles")
    else:
        for mueble in muebles:
            with st.container():
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
            with st.container():
                st.markdown(f"### {mueble[1]} ({mueble[6]})")
                st.markdown(f"**Tipo:** {mueble[7]}")
                st.markdown(f"**Precio de venta:** {mueble[2]} €")
                st.markdown(f"**Medidas:** {mostrar_medidas(mueble[7], mueble[8], mueble[9], mueble[10])}")
                st.markdown(f"**Fecha de venta:** {mueble[5]}")

conn.close()



