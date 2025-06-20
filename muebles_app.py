import streamlit as st
import sqlite3
import os
from PIL import Image
from datetime import datetime

# Crear carpeta para guardar imágenes
CARPETA_IMAGENES = "imagenes_muebles"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

# Conexión a base de datos SQLite
conn = sqlite3.connect("muebles.db")
c = conn.cursor()

# Crear tabla si no existe
c.execute("""
    CREATE TABLE IF NOT EXISTS muebles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL,
        descripcion TEXT,
        ruta_imagen TEXT,
        fecha TEXT
    )
""")
conn.commit()

st.title("🪑 Registro de El Jueves")

st.subheader("📤 Añadir nueva antigüedad")

# Subida de imagen
imagen = st.file_uploader("Sube una imagen", type=["jpg", "jpeg", "png"])

# Información del mueble
nombre = st.text_input("Nombre de la antigüedad")
precio = st.number_input("Precio (€)", min_value=0.0, step=1.0)
descripcion = st.text_area("Descripción (opcional)")

# Botón de guardar
if st.button("Guardar"):
    if imagen and nombre and precio > 0:
        # Guardar imagen con nombre único
        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.name}"
        ruta_imagen = os.path.join(CARPETA_IMAGENES, nombre_archivo)
        with open(ruta_imagen, "wb") as f:
            f.write(imagen.read())

        # Insertar en la base de datos
        c.execute("""
            INSERT INTO muebles (nombre, precio, descripcion, ruta_imagen, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, precio, descripcion, ruta_imagen, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

        st.success("✅ Mueble guardado correctamente")
    else:
        st.warning("Por favor, completa todos los campos y sube una imagen.")

# Mostrar galería
st.subheader("🖼️ Galería de muebles registrados")

c.execute("SELECT nombre, precio, descripcion, ruta_imagen, fecha FROM muebles ORDER BY id DESC")
muebles = c.fetchall()

if muebles:
    for mueble in muebles:
        st.markdown("---")
        st.markdown(f"**🪑 {mueble[0]}** — {mueble[1]} €")
        st.markdown(f"📝 {mueble[2]}")
        st.markdown(f"📅 Fecha: {mueble[4]}")
        imagen = Image.open(mueble[3])
        st.image(imagen, width=300)
    else:
        st.info("Aún no hay muebles registrados.")

