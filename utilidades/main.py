# utilidades/main.py
#se agrega cuando no se requier mostar estudiantes.26 de marzo
import streamlit as st
from .sesion_manager import SesionManager
from .obtener_contenido import fetch_url
from .extraccion_datos import extraer_datos_articulos 
from .extraccion_datos import extraer_datos_filas, extraer_datos_spec
from .extraccion_datos import extraer_datos_tabla
from bs4 import BeautifulSoup  # Asegúrate de importar BeautifulSoup aquí
import json
import os

def cargar_configuracion(archivo='configuracion.json'):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return []

def guardar_configuracion(configuraciones, archivo='configuracion.json'):
    with open(archivo, 'w') as f:
        json.dump(configuraciones, f, indent=4)

#esta función será de utillidad para capturar ciertos datos
async def extraer_datos_de_url_espcs(login_url, username, password, urls_a_extraer):
    """Extrae datos de múltiples URLs utilizando SesionManager."""
    sesion_manager = SesionManager() # utilidades/sesion_manager.py
    if not await sesion_manager.iniciar_sesion(login_url, username, password):
        return []
    resultados = []
    for url in urls_a_extraer:
        html = await fetch_url(await sesion_manager.obtener_sesion(), url)
        if html:
            nombres = extraer_datos_spec(html) # utilidades/extraccion_datos.py
            resultados.append({"url": url, "nombres": nombres})
        else:
            resultados.append({"url": url, "nombres": None})

    await sesion_manager.cerrar_sesion()
    return resultados

async def extraer_datos_de_urls(login_url, username, password, urls_a_extraer):
    """Extrae datos de múltiples URLs utilizando SesionManager, incluyendo información de tiempo."""
    sesion_manager = SesionManager()
    if not await sesion_manager.iniciar_sesion(login_url, username, password):
        return []

    resultados = []
    for url in urls_a_extraer:
        html = await fetch_url(await sesion_manager.obtener_sesion(), url)
        if html:
            datos_articulos = extraer_datos_articulos(html)  # Esta función ahora devuelve más información
            resultados.append({"url": url, "articulos": datos_articulos}) # Cambio de "nombres" a "articulos"
        else:
            resultados.append({"url": url, "articulos": None})

    await sesion_manager.cerrar_sesion()
    return resultados

async def extraer_datos_actividad(login_url, username, password, urls_actividades):
    """Extrae datos de múltiples URLs utilizando SesionManager."""
    sesion_manager = SesionManager() # utilidades/sesion_manager.py
    if not await sesion_manager.iniciar_sesion(login_url, username, password):
        return []
    resultados_act = []
    for url in urls_actividades:
        html = await fetch_url(await sesion_manager.obtener_sesion(), url)
        if html:
            filas = extraer_datos_filas(html) # utilidades/extraccion_datos.py
            resultados_act.append(filas) # Ahora append para mantener la correspondencia URL-resultado
    await sesion_manager.cerrar_sesion()
    return resultados_act

#còdigo para la extraccion del status
async def extraer_datos_status(login_url, username, password, url_status):
    """Extrae datos de status después de simular un clic en 'Mostrar todos'."""
    sesion_manager = SesionManager()
    if not await sesion_manager.iniciar_sesion(login_url, username, password):
        return []
    session = await sesion_manager.obtener_sesion()
    html = await fetch_url(session, url_status)
    if html:
        html_actualizado = await simular_clic_mostrar_todos(session, html)
        if html_actualizado:
            datos_extraidos, headers = extraer_datos_tabla(html_actualizado)
            datos_extraidos = sorted(datos_extraidos, key=lambda item: item[3])
            data = []
            for nombre, c2, c4, c5 in datos_extraidos:
                data.append([nombre, c2, c4, c5])
            await sesion_manager.cerrar_sesion()
            return data
        else:#Se extrae de todos modos si no hay necesidad de darle click a mostar estudiantes
            await sesion_manager.cerrar_sesion()
            return []  # O maneja el error de otra manera
    await sesion_manager.cerrar_sesion()
    return []  # O maneja el error de otra manera

async def simular_clic_mostrar_todos(session, html_content):
    """Simula un clic en el botón 'Mostrar todos'."""
    soup = BeautifulSoup(html_content, 'html.parser')
    boton_mostrar_todos = soup.find('a', attrs={'data-action': 'showcount'})
    if boton_mostrar_todos:
        url_mostrar_todos = boton_mostrar_todos['href']
        async with session.get(url_mostrar_todos) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None
    return html_content #por si no hay boton se manteiene el html


    import streamlit as st
    import json
    import os

    def cargar_configuracion(archivo='configuracion.json'):
        if os.path.exists(archivo):
            with open(archivo, 'r') as f:
                return json.load(f)
        return []

    def guardar_configuracion(configuraciones, archivo='configuracion.json'):
        with open(archivo, 'w') as f:
            json.dump(configuraciones, f, indent=4)

    def app():
        st.title("Llenar Configuración JSON")
        st.subheader("Ingrese los valores para cada campo:")

        config_template = {
            "Nombre": "",
            "Grupos": [""],
            "op_M1j": True,
            "op_M2j": True,
            "op_M3j": True,
            "op_M4j": False,
            "Cbx_M2j": False,
            "Cbx_M3j": True,
            "Cbx_M4j": False,
            "Cbx_MAIj": False,
            "username": "",
            "password": "",
            "login_url": "",
            "url_Foro_M1": "",
            "url_Foro_M2": "",
            "url_Foro_M3": "",
            "url_Foro_M4": "",
            "urls_a_extraer": "",
            "urls_act_M2": "",
            "urls_act_M3": "",
            "urls_act_M4": "",
            "urls_act_AI": "",
            "url_status": "",
            "remitente": "",
            "contrasena": "",
            "RdB_Foro_M1": None,
            "RdB_Foro_M2": None,
            "RdB_Foro_M3": None,
            "RdB_Foro_M4": None,
            "url_Foro_M1_pub": "",
            "url_Foro_M2_pub": "",
            "url_Foro_M3_pub": "",
            "url_Foro_M4_pub": "",
            "ultimo_foro_seleccionado": ":rainbow[Foro M1]"
        }

        config_data = [config_template.copy()]  # Inicializamos con una copia del template

        # Función para mostrar los campos de entrada basados en el template
        def mostrar_campos(config):
            updated_config = config.copy()
            for key, value in config.items():
                if isinstance(value, str):
                    updated_config[key] = st.text_input(key, value)
                elif isinstance(value, bool):
                    updated_config[key] = st.checkbox(key, value)
                elif isinstance(value, list):
                    updated_config[key] = st.text_area(key, "\n".join(value), height=50) # Usamos text_area para listas
                elif value is None:
                    updated_config[key] = st.text_input(key, "") # Para None, mostramos un campo de texto
                else:
                    updated_config[key] = st.text_input(key, str(value)) # Para otros tipos, mostramos como texto
            return updated_config

        if len(config_data) > 0:
            config_data[0] = mostrar_campos(config_data[0])

        if st.button("Guardar Configuración"):
            guardar_configuracion(config_data)
            st.success("Configuración guardada exitosamente en configuracion.json")

    if __name__ == "__main__":
        app()
        



