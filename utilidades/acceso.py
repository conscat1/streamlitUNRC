# utilidades/acceso.py
import streamlit as st
import asyncio
from .sesion import login_to_site
from .obtener_contenido import fetch_url
from .extraccion_datos import extraer_datos_articulos
from .main import extraer_datos_de_urls #importar la funcion correcta
import aiohttp


def gestionar_acceso():
    """
    Gestiona la lógica de acceso y extracción de datos.
    """
    st.header("Loguéate con tus llaves de acceso")
    username = st.text_input("Usuario", type="password")
    password = st.text_input("Password", type="password")
    login_url = st.text_input("URL de acceso")
    urls_to_fetch = st.text_area("URL de extracción (separadas por comas)")

    if st.button("Procesar"):
        # Convertir la cadena de URLs en una lista
        urls_to_fetch = [url.strip() for url in urls_to_fetch.split(",") if url.strip()]
        # Validar que urls_to_fetch no esté vacío
        if not urls_to_fetch:
            st.error("Por favor, ingresa al menos una URL para extraer datos.")
            return  # Detener la ejecución si no hay URLs
        # Mostrar un spinner mientras se realiza la extracción
        with st.spinner("Extrayendo datos..."):
            # Ejecutar la función principal de forma asíncrona
            html_content, nombres_extraidos = asyncio.run(main(login_url, username, password, urls_to_fetch))

            # Mostrar mensajes de éxito o error en Streamlit
            if any(html_content):  # Verificar si se extrajo contenido de alguna URL
                st.write("Extracción de datos exitosa.")
            else:
                st.write("Error al extraer datos de las URLs.")

            # Guardar el contenido HTML y los nombres en la sesión de estado
            st.session_state.nombres_extraidos = nombres_extraidos
            st.session_state.extraccion_realizada = True  # Actualizar la variable de control
            st.header("Nombres extraídos")

            # Mostrar los nombres extraídos solo si la extracción se ha realizado
            if st.session_state.extraccion_realizada:
                if st.session_state.nombres_extraidos:
                    for nombre in st.session_state.nombres_extraidos:
                        st.write(nombre)
                else:
                    st.write("No se encontraron nombres en las URLs proporcionadas.")
'''
async def main(login_url, username, password, urls_to_fetch):
    """Función principal para ejecutar la extracción."""
    html_content = []  # Lista para almacenar el contenido HTML de cada URL
    nombres_extraidos = []  # Lista para almacenar los nombres extraídos

    async with aiohttp.ClientSession() as session:
        login_successful = await login_to_site(session, login_url, username, password)
        if login_successful:
            for url_to_fetch in urls_to_fetch:
                st.write(f"Procesando URL: {url_to_fetch}")
                html = await fetch_url(session, url_to_fetch)
                if html:
                    html_content.append(html)
                    # Extraer los nombres y agregarlos a la lista
                    nombres = extraer_datos_articulos(html)
                    if nombres is not None:  # Verificar si nombres no es None
                        nombres_extraidos.extend(nombres)
                    else:
                        print(f"No se encontraron nombres en la URL: {url_to_fetch}")

    return html_content, nombres_extraidos  # Devolver ambas listas
'''