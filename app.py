# app.py
#Versiòn 5 de abril, foros, comentarios
import streamlit as st
import asyncio
import pandas as pd
import re
from utilidades.main import extraer_datos_de_urls, extraer_datos_actividad, extraer_datos_status
from utilidades.main import guardar_configuracion, cargar_configuracion, extraer_datos_de_url_espcs
from utilidades.load import cargar_datos, verificar_tipo_archivo
from utilidades.envio_mail import enviar_correos
from utilidades.config import configuracion, configuracion2
from io import BytesIO
import numpy as np
import io




# ----> Streamlit App <----
st.set_page_config(page_title="Sistema UNRC", page_icon=":robot_face:")

#st.set_page_config(page_title="Sistema UNRC Versiòn Abril", page_icon="https://www.etsy.com/mx/listing/866410377/bender-futurama")
configuraciones = cargar_configuracion() #Carga el json,aqui està toda la confuguracón
usuario_json=0

if configuraciones:# Si se cargó la configuración (es decir, la variable 'configuraciones' no está vacía o es None).
    usuario_seleccionado = configuraciones[usuario_json]
    st.title(f"Hola {usuario_seleccionado['Nombre']}")
    # Muestra los grupos a los que pertenece el usuario. Se extrae la lista de grupos
    # del diccionario 'usuario_seleccionado' con la clave 'Grupos', se une en una cadena
    st.write(f"Tus grupos son: {', '.join(usuario_seleccionado['Grupos'])}")
    # Obtener los valores directamente del JSON
    username = usuario_seleccionado['username']
    password = usuario_seleccionado['password']
    login_url = usuario_seleccionado['login_url']
    urls_a_extraer = usuario_seleccionado['urls_a_extraer']
    urls_act = usuario_seleccionado['urls_act']
    url_status = usuario_seleccionado['url_status']
    remitente = usuario_seleccionado['remitente']
    contraseña = usuario_seleccionado['contrasena']
    # Se extraen diversas variables de configuración del diccionario 'usuario_seleccionado'.
    # Inicializar la variable de control en st.session_state
    if "extraccion_realizada" not in st.session_state:
        st.session_state.extraccion_realizada = False

tab1, tab2, tab3, tab4, tab5, tab6 , tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs(["Foros", "Actividades", "Status", "Envío de correos", "Publicación en foro", "HTML-RRR", "# 1 Lista-status","Personalizado","grupos","Json","Captura","Final"])


with tab1:#Foros
    # Sección para la extracción de pendientes en foros.
    st.header("Foros pendientes")
    # Divide el ancho de la pestaña en cuatro columnas para organizar los elementos.
    col1, col2, col3, col4 = st.columns(4)
    # Checkboxes para seleccionar los módulos a procesar. Los valores iniciales se toman de la configuración.
    op_M1 = col1.checkbox('Módulo 1', value=usuario_seleccionado.get('op_M1j'))
    op_M2 = col2.checkbox('Módulo 2', value=usuario_seleccionado.get('op_M2j'))
    op_M3 = col3.checkbox('Módulo 3', value=usuario_seleccionado.get('op_M3j'))
    op_M4 = col4.checkbox('Módulo 4', value=usuario_seleccionado.get('op_M4j'))
    # El valor inicial de cada checkbox se toma del diccionario 'usuario_seleccionado' usando la clave
    # correspondiente ('op_M1j', 'op_M2j', etc.) y el método '.get()' para evitar errores si la clave no existe.
    # Se asume que estas claves almacenan el estado de selección de los módulos de la sesión anterior.
    if st.button("Procesar"):
        # Guarda el estado de los checkboxes en la configuración.
        configuraciones[usuario_json]['op_M1j'] = op_M1
        configuraciones[usuario_json]['op_M2j'] = op_M2
        configuraciones[usuario_json]['op_M3j'] = op_M3
        configuraciones[usuario_json]['op_M4j'] = op_M4
        guardar_configuracion(configuraciones)

        urls_por_modulo = {} # Diccionario para almacenar las URLs por módulo seleccionado

        if op_M1:
            urls_m1 = usuario_seleccionado.get('url_Foro_M1', '')
            if urls_m1:
                urls_por_modulo["Módulo 1"] = [url.strip() for url in urls_m1.split(',') if url.strip()]
        if op_M2:
            urls_m2 = usuario_seleccionado.get('url_Foro_M2', '')
            if urls_m2:
                urls_por_modulo["Módulo 2"] = [url.strip() for url in urls_m2.split(',') if url.strip()]
        if op_M3:
            urls_m3 = usuario_seleccionado.get('url_Foro_M3', '')
            if urls_m3:
                urls_por_modulo["Módulo 3"] = [url.strip() for url in urls_m3.split(',') if url.strip()]
        if op_M4:
            urls_m4 = usuario_seleccionado.get('url_Foro_M4', '')
            if urls_m4:
                urls_por_modulo["Módulo 4"] = [url.strip() for url in urls_m4.split(',') if url.strip()]

        urls_a_extraer = [url for urls in urls_por_modulo.values() for url in urls]

        if not urls_a_extraer:
            st.error("Por favor, selecciona al menos un módulo para extraer datos.")
        else:
            with st.spinner("Extrayendo pendientes foros..."):
                resultados = asyncio.run(extraer_datos_de_urls(login_url, username, password, urls_a_extraer))

                if resultados:
                    st.write("Extracción de datos exitosa.")
                    resultado_index = 0
                    for modulo, urls_modulo in urls_por_modulo.items():
                        st.subheader(f":rainbow[{modulo}]")
                        for grupo, url in enumerate(urls_modulo, start=1):
                            if resultado_index < len(resultados):
                                resultado = resultados[resultado_index]
                                if resultado["articulos"]:
                                    st.write(f"Grupo: {grupo}")
                                    for articulo in resultado["articulos"]:
                                        nombre = articulo["nombre"]
                                        dentro_de_tiempo = articulo["dentro_de_tiempo"]
                                        if dentro_de_tiempo:
                                            st.write(f"- {nombre}")
                                        else:
                                            st.markdown(f"<span style='color:red;'>- {nombre}</span>", unsafe_allow_html=True)
                                else:
                                    st.write(f"No hay pendientes por calificar: Grupo: {grupo}") # Mensaje con el grupo
                                resultado_index += 1
                            else:
                                st.warning(f"No se encontraron resultados para la URL del {modulo}, Grupo {grupo}.")
                                break # Si no hay más resultados, salir del bucle de URLs
                else:
                    st.error("Error al extraer datos de las URLs.")




with tab2:#Actividades
    st.header("Actividades")

    col_1, col_2, col_3, col_4 = st.columns(4)
    # Checkboxes para seleccionar los módulos a procesar. Los valores iniciales se toman de la configuración.
    op_ActM2 = col_1.checkbox('Act M2', value=usuario_seleccionado.get('Cbx_M2j'))
    op_ActM3 = col_2.checkbox('Act M3', value=usuario_seleccionado.get('Cbx_M3j'))
    op_ActM4 = col_3.checkbox('Act M4', value=usuario_seleccionado.get('Cbx_M4j'))
    op_ActAI = col_4.checkbox('Act AI', value=usuario_seleccionado.get('Cbx_MAIj'))

    if st.button("Actividades"):
        # Guarda el estado de los checkboxes en la configuración.
        configuraciones[usuario_json]['Cbx_M2j'] = op_ActM2
        configuraciones[usuario_json]['Cbx_M3j'] = op_ActM3
        configuraciones[usuario_json]['Cbx_M4j'] = op_ActM4
        configuraciones[usuario_json]['Cbx_MAIj'] = op_ActAI
        guardar_configuracion(configuraciones)

        urls_por_modulo_act = {}

        if op_ActM2:
            urls_m2_act = usuario_seleccionado.get('urls_act_M2', '')
            if urls_m2_act:
                urls_por_modulo_act["Módulo 2"] = [url.strip() for url in urls_m2_act.split(',') if url.strip()]
        if op_ActM3:
            urls_m3_act = usuario_seleccionado.get('urls_act_M3', '')
            if urls_m3_act:
                urls_por_modulo_act["Módulo 3"] = [url.strip() for url in urls_m3_act.split(',') if url.strip()]
        if op_ActM4:
            urls_m4_act = usuario_seleccionado.get('urls_act_M4', '')
            if urls_m4_act:
                urls_por_modulo_act["Módulo 4"] = [url.strip() for url in urls_m4_act.split(',') if url.strip()]
        if op_ActAI:
            urls_mai_act = usuario_seleccionado.get('urls_act_AI', '')
            if urls_mai_act:
                urls_por_modulo_act["Act AI"] = [url.strip() for url in urls_mai_act.split(',') if url.strip()]

        all_urls_act = [url for urls in urls_por_modulo_act.values() for url in urls]

        if not all_urls_act:
            st.error("Por favor, selecciona al menos un módulo para extraer datos de actividades.")
        else:
            with st.spinner("Extrayendo datos de actividades..."):
                datos_por_url = asyncio.run(extraer_datos_actividad(login_url, username, password, all_urls_act))

            if datos_por_url:
                st.subheader("Actividades pendientes")
                resultado_index = 0
                for modulo, urls_modulo in urls_por_modulo_act.items():
                    st.subheader(f":rainbow[{modulo}]")
                    for grupo, url in enumerate(urls_modulo, start=1):
                        if resultado_index < len(datos_por_url):
                            datos_grupo = datos_por_url[resultado_index]
                            if datos_grupo:
                                df_grupo = pd.DataFrame(datos_grupo, columns=["Encabezado", "Valor"])
                                #st.write(f"**Grupo: {grupo} (URL: {url})**")
                                
                                st.write(f"Grupo: {grupo}")
                                st.dataframe(df_grupo)
                            else:
                                st.warning(f"No se encontraron datos para el Grupo: {grupo} del Módulo: {modulo} (URL: {url})")
                            resultado_index += 1
                        else:
                            st.warning(f"No se encontraron más resultados para el Módulo: {modulo}, Grupo: {grupo}.")
                            break
            else:
                st.error("Error al extraer datos de las actividades.")




with tab3:   #status
    st.header("Estatus de los estudiantes")
     # Este botón con la etiqueta "Extrae" activará la lógica para obtener el estatus de los estudiantes cuando se haga clic.
    if st.button("Extrae"):
        #En esta secciòn colocaremos la parte de los status de los estudiantess.
        
        if not url_status:
            st.error("Por favor, ingresa el URL para extraer el status.")
        else:
            with st.spinner("Extrayendo status"): # utilidades/main.py
                try:
                    datos_status = asyncio.run(extraer_datos_status(login_url, username, password, url_status))
                    # Se llama a la función 'extraer_datos_status' de forma asíncrona (usando 'asyncio.run').
                    # Esta función probablemente se encarga de:
                    # 1. Iniciar sesión en la URL especificada por 'login_url' usando las credenciales 'username' y 'password'.
                    # 2. Acceder a la URL de estatus proporcionada en 'url_status'.
                    # 3. Extraer la información relevante del estatus de los estudiantes.
                    # El resultado de esta función se guarda en la variable 'datos_status'.
                    if datos_status:
                        df_status = pd.DataFrame(datos_status, columns=["Nombre", "Mail", "Grupo", "Último acceso"])
                        st.dataframe(df_status)
                    else:
                        st.error("No se pudieron extraer los datos de status.")
                except Exception as e:
                    st.error(f"Error al extraer status: {e}")


with tab4:#"Envío de correos"
    
    
    st.write(remitente)
    st.header("Envío de Correos")
    st.subheader("Adjunta el archvio de HTML-RRR o Personalizado ")
    uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx", "xls"])
    if uploaded_file is not None:
        if verificar_tipo_archivo(uploaded_file):
            enviar_correos(uploaded_file,remitente,contraseña)
          
    
# El código anterior de tu app Streamlit va aquí...
# Asumo que tienes imports como 'import streamlit as st' antes

with tab5:# "Publica foro "



    # --- Inicio del Código para tu Pestaña/Sección de Publicación en Foro ---
    # Asumo que 'tab5' es una variable definida por st.tabs() o similar
    # y que 'st' (import streamlit as st) ya está importado globalmente.

    # Imports de Selenium y otros necesarios para esta sección
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    # --- IMPORTACIÓN CORREGIDA ---
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    # --- FIN IMPORTACIÓN CORREGIDA ---
    from selenium.webdriver.firefox.service import Service # Opcional, por si necesitas logs de geckodriver
    import logging
    import time
    import streamlit as st # Asegúrate que st esté importado y disponible

    # Configurar logging específico para esta sección (o usa tu logger global)
    log_formatter_foro = logging.Formatter('%(asctime)s - %(levelname)s - [Foro] - %(message)s')
    logger_foro = logging.getLogger("foro_logger")
    logger_foro.setLevel(logging.INFO)
    logger_foro.propagate = False # Evita que los mensajes suban al logger raíz si tienes uno global

    # Evitar duplicar handlers si esta parte del código se recarga en Streamlit
    if not logger_foro.handlers:
        ch = logging.StreamHandler() # Log a la consola donde corre Streamlit
        ch.setFormatter(log_formatter_foro)
        logger_foro.addHandler(ch)
        # Podrías añadir un FileHandler aquí si quieres logs persistentes en archivo
        # fh = logging.FileHandler('/ruta/a/tu/foro.log')
        # fh.setFormatter(log_formatter_foro)
        # logger_foro.addHandler(fh)

    def publicar_respuesta_foro(url_foro, texto_respuesta, login_url, username, password):
        """Intenta iniciar sesión, ir al foro, hacer clic en 'Responder', escribir y enviar."""
        logger_foro.info(f"Intentando responder en el foro: {url_foro}")
        driver = None
        try:
            firefox_options = Options()

            # --- Configuración Clave para Entorno de Servidor Ubuntu ---
            firefox_options.binary_location = "/usr/bin/firefox-esr" # Ruta correcta al binario
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--disable-gpu")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--window-size=1920,2600") # Definir tamaño puede ayudar
            # --- Fin Configuración Clave ---

            # Opcional: Configurar Service para log de Geckodriver
            # gecko_service = Service(executable_path='/usr/local/bin/geckodriver', log_path='/tmp/geckodriver_foro.log')
            # Si usas Service: driver = webdriver.Firefox(service=gecko_service, options=firefox_options)

            # Iniciar el driver usando las opciones modificadas
            driver = webdriver.Firefox(options=firefox_options)
            logger_foro.info(f"Navegador Firefox (ESR) iniciado. Usando binario: {firefox_options.binary_location}")

            # 1. Iniciar sesión
            driver.set_page_load_timeout(60) # Aumentar timeout de carga de página
            driver.get(login_url)
            logger_foro.info(f"Navegando a la página de inicio de sesión: {login_url}")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "loginbtn"))).click()
            logger_foro.info("Inicio de sesión completado.")
            time.sleep(4) # Pausa un poco más larga después del login

            # 2. Navegar al foro
            driver.get(url_foro)
            logger_foro.info(f"Navegando al foro: {url_foro}")
            time.sleep(5) # Pausa adicional para carga completa del foro

            # 3. Hacer clic en "Responder"
            try:
                logger_foro.info("Intentando encontrar el botón 'Responder'...")
                # Usar XPath combinado y aumentar espera
                responder_button = WebDriverWait(driver, 5).until( # Aumentado a 45s
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'discussion-reply')]//a[contains(text(), 'Responder')] | //input[@type='submit' and @value='Responder']"))
                )
                logger_foro.info("Botón 'Responder' encontrado, haciendo scroll y clic...")
                driver.execute_script("arguments[0].scrollIntoView(true);", responder_button)
                time.sleep(1)
                responder_button.click()
                logger_foro.info("Clic en el botón 'Responder' aparentemente exitoso.")
            except TimeoutException as e:
                logger_foro.warning(f"No se encontró/clickeó botón 'Responder' después de 45s. Verificando si el editor ya está visible.")
                # --- Guardar captura al no encontrar botón ---
                try:
                    screenshot_path = f"/tmp/error_boton_responder_{int(time.time())}.png"
                    if driver.save_screenshot(screenshot_path):
                        logger_foro.info(f"[SCREENSHOT] Captura (sin botón responder) guardada en {screenshot_path}")
                except Exception as ss_e:
                    logger_foro.error(f"Error al intentar guardar captura de pantalla: {ss_e}")
                # --- Fin guardar captura ---
                try:
                    # Verificar iframe directamente, aumentar espera
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "id_message_ifr"))) # Aumentado a 20s
                    logger_foro.info("El editor iframe parece estar ya presente sin necesidad de botón.")
                    # Si está presente, continuamos sin error
                except TimeoutException:
                    logger_foro.error("FALLO: No se encontró botón 'Responder' ni editor iframe visible directamente.")
                    # --- Guardar captura al no encontrar iframe tampoco ---
                    try:
                        screenshot_path = f"/tmp/error_sin_editor_{int(time.time())}.png"
                        if driver.save_screenshot(screenshot_path):
                            logger_foro.info(f"[SCREENSHOT] Captura (sin editor) guardada en {screenshot_path}")
                    except Exception as ss_e:
                        logger_foro.error(f"Error al intentar guardar captura de pantalla: {ss_e}")
                    # --- Fin guardar captura ---
                    raise # Relanzar la excepción para que falle la función

            # 4. Esperar a que el iframe del editor esté disponible y cambiar el contexto
            try:
                logger_foro.info("Esperando iframe del editor...")
                iframe = WebDriverWait(driver, 45).until( # Aumentado a 45s
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "id_message_ifr"))
                )
                logger_foro.info("Cambiado al contexto del iframe del editor.")

                # 5. Encontrar el elemento body dentro del iframe y enviar el texto
                logger_foro.info("Esperando cuerpo del editor (TinyMCE)...")
                body = WebDriverWait(driver, 30).until( # Aumentado a 30s
                    EC.presence_of_element_located((By.ID, "tinymce"))
                )
                body.clear()
                body.send_keys(texto_respuesta)
                logger_foro.info("Texto de la respuesta enviado al editor.")

                # 6. Volver al contexto principal del documento
                driver.switch_to.default_content()
                logger_foro.info("Vuelto al contexto principal.")

                # 7. Hacer clic en el botón "Enviar al foro"
                logger_foro.info("Intentando encontrar y clickear 'Enviar al foro'...")
                try:
                    enviar_button = WebDriverWait(driver, 30).until( # Aumentado a 30s
                        EC.element_to_be_clickable((By.ID, "id_submitbutton"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", enviar_button)
                    time.sleep(1)
                    enviar_button.click()
                    logger_foro.info("Clic en el botón 'Enviar al foro' exitoso.")
                    time.sleep(5) # Espera para posible redirección/confirmación
                    return True

                except Exception as e:
                    logger_foro.error(f"Error al hacer clic en 'Enviar al foro': {e}")
                    # --- Guardar captura al fallar envío ---
                    try:
                        screenshot_path = f"/tmp/error_envio_foro_{int(time.time())}.png"
                        if driver.save_screenshot(screenshot_path):
                            logger_foro.info(f"[SCREENSHOT] Captura (error envío) guardada en {screenshot_path}")
                    except Exception as ss_e:
                        logger_foro.error(f"Error al intentar guardar captura de pantalla: {ss_e}")
                    # --- Fin guardar captura ---
                    return False

            except TimeoutException as e: # Captura específica si falla el iframe/editor
                logger_foro.error(f"Timeout esperando el iframe o el cuerpo del editor: {e}")
                # --- Guardar captura al fallar iframe/editor ---
                try:
                    screenshot_path = f"/tmp/error_iframe_timeout_{int(time.time())}.png"
                    driver.switch_to.default_content() # Asegura estar fuera del iframe
                    if driver.save_screenshot(screenshot_path):
                        logger_foro.info(f"[SCREENSHOT] Captura (error iframe/editor) guardada en {screenshot_path}")
                except Exception as ss_e:
                    logger_foro.error(f"Error al intentar guardar captura de pantalla: {ss_e}")
                # --- Fin guardar captura ---
                return False
            except Exception as e: # Otros errores inesperados con iframe/editor
                logger_foro.exception(f"Error inesperado al interactuar con el iframe/editor: {e}")
                return False

        except Exception as e:
            logger_foro.exception(f"Ocurrió un error general durante el proceso del foro {url_foro}: {e}")
            # --- Guardar captura en error general ---
            if driver: # Solo si el driver se inicializó
                try:
                    screenshot_path = f"/tmp/error_general_{int(time.time())}.png"
                    if driver.save_screenshot(screenshot_path):
                        logger_foro.info(f"[SCREENSHOT] Captura (error general) guardada en {screenshot_path}")
                except Exception as ss_e:
                    logger_foro.error(f"Error al intentar guardar captura de pantalla general: {ss_e}")
            # --- Fin guardar captura ---
            return False
        finally:
            if driver:
                driver.quit()
                logger_foro.info("Navegador cerrado.")

    def publicar_en_multiples_foros(urls_foro_str, texto_respuesta, login_url, username, password):
        """Publica la misma respuesta en múltiples foros."""
        # Asegurar que st esté disponible aquí
        import streamlit as st

        # Limpiar URLs: aceptar comas y saltos de línea, quitar espacios extra, filtrar vacías
        urls_limpias = [url.strip() for url in urls_foro_str.replace('\n', ',').split(',') if url.strip()]

        if not urls_limpias:
            st.warning("No se proporcionaron URLs de foros válidas.")
            return

        total_foros = len(urls_limpias)
        progreso = st.progress(0, text=f"Iniciando publicación en {total_foros} foros...")
        resultados_ok = 0
        resultados_error = 0

        for i, url in enumerate(urls_limpias):
            logger_foro.info(f"Procesando foro {i+1}/{total_foros}: {url}")
            progreso.progress((i + 1) / total_foros, text=f"Procesando foro {i+1}/{total_foros}: {url.split('/')[-1]}") # Mostrar parte final de URL

            if publicar_respuesta_foro(url, texto_respuesta, login_url, username, password):
                # No mostrar success individual en la barra, solo en log y resumen
                resultados_ok += 1
                logger_foro.info(f"Publicación exitosa en: {url}")
            else:
                st.error(f"Hubo un problema al publicar la respuesta en: {url}. Revisa los logs (consola) para más detalles.")
                resultados_error += 1
            # Pausa opcional entre publicaciones
            time.sleep(3) # Pausa de 3 segundos

        progreso.empty() # Limpiar barra de progreso
        st.info(f"Proceso completado. Publicaciones exitosas: {resultados_ok}, Errores: {resultados_error}")
        if resultados_error > 0:
            st.warning("Algunas publicaciones fallaron. Revisa los errores mostrados arriba y los logs de la consola.")



    
    
    opciones_foro = [":rainbow[Foro M1]", ":rainbow[Foro M2]", ":rainbow[Foro M3]", ":rainbow[Foro M4]"]

    genre = st.radio(
        "Selecciona el foro a publicar",
        opciones_foro,
        captions=[
            "Publicara en todos los grupos del M1",
            "Publicara en todos los grupos del M2",
            "Publicara en todos los grupos del M3",
            "Publicara en todos los grupos del M4",
        ],
        horizontal=True,
        index=None  # Aseguramos que inicie sin selección
    )

    urls_a_extraer = []
    if genre:
        st.write(f"Foro seleccionado: {genre}")
        if genre == ":rainbow[Foro M1]":
            urls_foro_str = usuario_seleccionado.get('url_Foro_M1_pub', '')
        elif genre == ":rainbow[Foro M2]":
            urls_foro_str = usuario_seleccionado.get('url_Foro_M2_pub', '')
        elif genre == ":rainbow[Foro M3]":
            urls_foro_str = usuario_seleccionado.get('url_Foro_M3_pub', '')
        elif genre == ":rainbow[Foro M4]":
            urls_foro_str = usuario_seleccionado.get('url_Foro_M4_pub', '')
        else:
            urls_foro_str = ''  # Por si acaso hay una selección inesperada

        if urls_foro_str:
            urls_a_extraer = [url.strip() for url in urls_foro_str.split(',') if url.strip()]
            st.write("URLs a extraer:")
            st.write(urls_a_extraer)
        else:
            st.warning("No se encontraron URLs para el foro seleccionado.")
    else:
        st.info("Por favor, selecciona un foro.")




    #urls_foro_str = usuario_seleccionado['url_Foro_M4_pub']
    st.header("Publicador en Foros de Moodle")

    #urls_foro_str = st.text_area("URLs de los Foros (una por línea o separadas por coma):", height=150, key="foro_urls")
    texto_respuesta = st.text_area("Texto Común de la Respuesta:", height=200, key="foro_texto")

    st.caption(f"Se usará el usuario: {usuario_seleccionado.get('username', 'No definido')}")

    if st.button("🚀 Publicar en Foros", key="foro_publicar_btn"):
        urls_limpias_str = urls_foro_str # La función limpiar está dentro de publicar_en_multiples_foros

        # Validar que los datos del usuario seleccionado existan
        login_url = usuario_seleccionado.get('login_url')
        username = usuario_seleccionado.get('username')
        password = usuario_seleccionado.get('password')

        if urls_limpias_str and texto_respuesta and login_url and username and password:
            # Validar que no se estén usando los placeholders de ejemplo
            if username == 'DEFINE_USUARIO' or password == 'DEFINE_PASSWORD' or login_url == 'DEFINE_LOGIN_URL':
                st.error("Por favor, asegúrate de que la información del usuario (usuario, contraseña, URL de login) esté correctamente configurada.")
            else:
                with st.spinner("Publicando respuestas... Esto puede tardar varios minutos."):
                    publicar_en_multiples_foros(
                        urls_limpias_str, # Pasar el string original, la función lo limpia
                        texto_respuesta,
                        login_url,
                        username,
                        password
                    )
        else:
            st.warning("Por favor, completa las URLs, el texto de respuesta y asegúrate de que hay un usuario seleccionado con credenciales completas.")

    # --- Fin del Código para tu Pestaña/Sección ---
        






with tab6: #HTML-RRR

    def reemplazar_template(template, row):
        """
        Reemplaza los placeholders en el template usando los datos de una fila.
        """
        # Esta es una función que toma un 'template' (una cadena de texto con marcadores de posición) y una fila de datos ('row' de un DataFrame de pandas).
        # Su objetivo es reemplazar los marcadores de posición en el 'template' con los valores correspondientes de la 'row'.
        def repl(match):
            key = match.group(1).strip()  # Extraer el contenido dentro de {{ }}
            # Esta función interna 'repl' se utiliza como la función de reemplazo para re.sub().
            # 'match' es un objeto de coincidencia encontrado por la expresión regular.
            # 'match.group(1)' captura el texto dentro de los paréntesis en la expresión regular (es decir, el contenido dentro de {{ }}).
            # '.strip()' elimina cualquier espacio en blanco al principio o al final de la clave.
            # Intentar convertir a índice basado en letra (A -> 0, B' -> 1, ...)
            if len(key) == 1 and 'A' <= key.upper() <= 'Z':
                idx = ord(key.upper()) - ord('A')
                return str(row.iloc[idx]) if 0 <= idx < len(row) else match.group(0)
            # Si la 'key' tiene una sola letra y está entre 'A' y 'Z' (sin importar mayúsculas o minúsculas):
            # - Se calcula el índice numérico correspondiente a la letra (A=0, B=1, etc.) utilizando la función ord().
            # - Si el índice calculado está dentro del rango de las columnas de la 'row' (accedida con .iloc para indexación basada en posición),
            #   se devuelve el valor de esa celda convertido a una cadena.
            # - Si el índice está fuera de rango, se devuelve el marcador de posición original sin cambios ('match.group(0)').
            # Si no es una letra única, intentar usar el nombre de la columna directamente
            elif key in row.index:
                return str(row[key])
            # Si la 'key' no es una única letra, se verifica si coincide con el nombre de alguna de las columnas de la 'row' (accedida con .index).
            # Si coincide, se devuelve el valor de esa celda (accedida por el nombre de la columna) convertido a una cadena.

            else:
                return match.group(0)
            # Si la 'key' no es una letra única válida ni un nombre de columna existente, se devuelve el marcador de posición original sin cambios.

        return re.sub(r'\{\{(.*?)\}\}', repl, template)
        # La función 're.sub()' realiza la búsqueda y el reemplazo en el 'template'.
        # - r'\{\{(.*?)\}\}' es la expresión regular que busca cualquier texto entre dos pares de llaves {{ }}.
        #   - \{\{ y \}\} coinciden con las llaves literales (necesitan ser escapadas con una barra invertida).
        #   - (.*?) captura cualquier carácter ('.') cero o más veces ('*?'), de forma no codiciosa (para que coincida con el par de llaves más cercano).
        #   - Los paréntesis crean un grupo de captura que se accede como 'match.group(1)' en la función 'repl'.
        # - 'repl' es la función que se llama para cada coincidencia encontrada.
        # - 'template' es la cadena en la que se realizará la búsqueda y el reemplazo.
        # La función 'reemplazar_template' devuelve el 'template' con los marcadores de posición reemplazados por los datos de la 'row'.

    # Título de la aplicación
    st.subheader("Generador de mensajes para correo HTML - 3R's")
    st.write("Genera tu texto en html para cada una de las tres opciones, no olvides el subject")

    # Cargar el archivo de Excel
    uploaded_file = st.file_uploader("Selecciona un archivo Excel", type=["xlsx"], key="file_uploader_principal")
    # Se crea un widget para permitir al usuario cargar un archivo.
    # - "Selecciona un archivo Excel" es la etiqueta del widget.
    # - type=["xlsx"] especifica que solo se aceptarán archivos con la extensión .xlsx (archivos de Excel).
    # - key="file_uploader_principal" asigna una clave única a este widget, lo que puede ser útil para el manejo de estados en Streamlit.
    if uploaded_file:
        # Leer el archivo en un DataFrame
        df = pd.read_excel(uploaded_file)
        # Se utiliza la función 'pd.read_excel()' de pandas para leer el contenido del archivo cargado ('uploaded_file') y crear un DataFrame llamado 'df'.
        st.success("Archivo cargado exitosamente.")

        # Generar placeholders correctamente formateados: Encabezado: {{A}}
        placeholders_copiables = "\n".join(
            [f"{col_name}: {{ {chr(65 + idx)} }}" for idx, col_name in enumerate(df.columns)]
        ).replace("{ ", "{{").replace(" }", "}}")
    # Se genera una cadena de texto que contiene los placeholders disponibles basados en los nombres de las columnas del DataFrame 'df'.
    # - 'df.columns' devuelve una lista de los nombres de las columnas.
    # - 'enumerate(df.columns)' itera sobre las columnas, proporcionando tanto el índice ('idx') como el nombre de la columna ('col_name').
    # - f"{col_name}: {{ {chr(65 + idx)} }}" crea una cadena para cada columna en el formato "Nombre de la columna: { A }", donde la letra se calcula sumando el índice al valor ASCII de 'A' (65).
    # - .replace("{ ", "{{").replace(" }", "}}") reemplaza los espacios alrededor de las llaves para crear los placeholders de doble llave ({{A}}, {{B}}, etc.).
    # - "\n".join(...) une todas estas cadenas con un salto de línea entre ellas.

        # Cuadro de texto para copiar placeholders
        st.text_area("Copia y pega los placeholders disponibles:", placeholders_copiables, height=150)
        # Se crea un widget de área de texto ('st.text_area') donde se muestra la lista de placeholders generados ('placeholders_copiables').
        # - "Copia y pega los placeholders disponibles:" es la etiqueta del área de texto.
        # - 'height=150' establece la altura inicial del área de texto en píxeles.
        # Esto permite al usuario copiar fácilmente los placeholders para usarlos en los templates.
        # Verificar que las columnas necesarias existen
        required_columns_analisis = ["Total del curso (Real)", "Último acceso"]
        if not all(col in df.columns for col in required_columns_analisis):
            st.error(f"El archivo debe contener las columnas: '{required_columns_analisis[0]}' y '{required_columns_analisis[1]}'")
        # Se verifica si todas las columnas en 'required_columns_analisis' existen en el DataFrame 'df'.
        # Si alguna de las columnas requeridas no está presente, se muestra un mensaje de error al usuario.
        else:
            # Si todas las columnas requeridas están presentes, se procede a la sección de personalización de mensajes.
            st.subheader("Personalización de Mensajes")
             # Se muestra un subencabezado para indicar el inicio de la sección de personalización.
            st.subheader("Condición: Te extrañamos")
            mensaje_te_extranamos_base = st.text_input("Subject:Te extrañamos")
            # Se crea un widget de entrada de texto ('st.text_input') para que el usuario defina un texto base para los mensajes de "Te extrañamos".
            # - "Texto base 'Te extrañamos':" es la etiqueta del campo de entrada.
            # - "Te extrañamos en la plataforma" es el valor predeterminado que se mostrará en el campo.
            template_te_extranamos = st.text_area("Coloca tu HTML")
           # Se crea un widget de área de texto para que el usuario defina un template para los mensajes de "Te extrañamos".
            # - "Template 'Te extrañamos' (usa {{A}}, {{B}}, ...):" es la etiqueta del área de texto, indicando cómo usar los placeholders.
            # - "Hola {{A}}, {{mensaje_base}}." es el template predeterminado, que incluye un placeholder para el nombre (asumiendo que está en la primera columna, 'A') y otro placeholder llamado 'mensaje_base'.
            template_te_extranamos_sin_enter = template_te_extranamos.replace('\n', ' ')
            # Se crea una versión del template "Te extrañamos" donde todos los saltos de línea ('\n') se reemplazan con espacios.
            # Esto podría ser útil para procesar el template en una sola línea.
            st.subheader("Condición: Has ingresado pero sin entregas")
            mensaje_sin_entregas_base = st.text_input("Subject: Has ingresado pero sin entregas:")
            # Se crea un campo de entrada de texto para el texto base de los mensajes de "sin entregas".
            template_sin_entregas = st.text_area("HTML No hay aun entregas")
            template_sin_entregas_sin_enter = template_sin_entregas.replace('\n', ' ')
            # Se crea una versión del template "sin entregas" sin saltos de línea.
            st.subheader("Condición: Excelente continúa")
            mensaje_excelente_continua_base = st.text_input("Subject: Felicitaciones por tus entregas")
            template_excelente_continua = st.text_area("HTML Excelente continúa")
            template_excelente_continua_sin_enter = template_excelente_continua.replace('\n', ' ')

            # Checkbox para reemplazar '-' con 'Sin entrega'
            reemplazar_sin_entregas = st.checkbox("Reemplazar '-' con 'Sin entregas'")

            if st.button("Generar Resultados y Mensajes Personalizados"):
                # Se crea un botón con la etiqueta "Generar Resultados y Mensajes Personalizados".
                # Cuando se hace clic en este botón, se ejecutará el siguiente bloque de código.
                def generar_mensaje_personalizado(row):
                    if row["Último acceso"] == "Nunca":
                        template = template_te_extranamos_sin_enter
                        mensaje_base = mensaje_te_extranamos_base
                    elif row["Total del curso (Real)"] == "-" and row["Último acceso"] != "Nunca":
                        template = template_sin_entregas_sin_enter
                        mensaje_base = mensaje_sin_entregas_base
                    elif isinstance(row["Total del curso (Real)"], (int, float)) and row["Total del curso (Real)"] > 0:
                        template = template_excelente_continua_sin_enter
                        mensaje_base = mensaje_excelente_continua_base
                    else:
                        return ""

                    # Crear un diccionario temporal para pasar el mensaje base como una columna más
                    temp_row = row.to_dict()
                    temp_row['mensaje_base'] = mensaje_base
                    temp_series = pd.Series(temp_row)
                    return reemplazar_template(template, temp_series)
    # Se convierte la fila a un diccionario ('temp_row').
    # Se agrega el 'mensaje_base' al diccionario con la clave 'mensaje_base'.
    # Se convierte el diccionario temporal de nuevo a una Serie de pandas ('temp_series').
    # Finalmente, se llama a la función 'reemplazar_template' para reemplazar los placeholders en el 'template' seleccionado con los datos de la 'temp_series' (que ahora incluye el 'mensaje_base').
           

                def calcular_subject(row):
                    if row["Último acceso"] == "Nunca":
                        return "Te extrañamos en la plataforma"
                    elif row["Total del curso (Real)"] == "-" and row["Último acceso"] != "Nunca":
                        return "Has ingresado pero sin entregas"
                    elif isinstance(row["Total del curso (Real)"], (int, float)) and row["Total del curso (Real)"] > 0:
                        return "Excelente trabajo, ¡continúa!"
                    else:
                        return ""

                df["Subject"] = df.apply(calcular_subject, axis=1)
                df["html"] = df.apply(generar_mensaje_personalizado, axis=1)

                # Aplicar el reemplazo del checkbox *después* de generar el DataFrame
                if reemplazar_sin_entregas:
                    df = df.replace('-', 'Sin entrega')
                    st.info("Los valores '-' han sido reemplazados con 'Sin entrega'.")

                st.subheader("DataFrame Modificado:")
                st.dataframe(df)

                # Función para convertir a Excel y permitir la descarga
                def convertir_a_excel(df):
                    output = io.BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    df.to_excel(writer, index=False, sheet_name='Datos Procesados')
                    writer.close()
                    processed_data = output.getvalue()
                    return processed_data

                # Botón para descargar el archivo modificado
                processed_data = convertir_a_excel(df)
                st.download_button(
                    label="Descargar Excel con Resultados y Mensajes",
                    data=processed_data,
                    file_name="archivo_procesado_personalizado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")  
        # Esta función toma un DataFrame 'df' y lo convierte a un archivo Excel en memoria (usando BytesIO y xlsxwriter).
        # - 'io.BytesIO()' crea un objeto similar a un archivo pero en la memoria RAM.
        # - 'pd.ExcelWriter(...)' crea un escritor de Excel.
        # - 'df.to_excel(...)' escribe el DataFrame en la hoja 'Datos Procesados' del archivo Excel, sin incluir el índice.
        # - 'writer.close()' guarda el archivo.
    
                
with tab7:#"Lista-status"


    # Asegurar que xlsxwriter está disponible
    try:
        import xlsxwriter
    except ImportError:
        st.error("Falta la librería 'xlsxwriter'. Instálala con 'pip install xlsxwriter'.")
        # Este bloque try-except intenta importar la librería 'xlsxwriter'.
        # Si la importación falla (ImportError), significa que la librería no está instalada.
        # En ese caso, se muestra un mensaje de error al usuario en la interfaz de Streamlit,
        # indicándole cómo instalar la librería usando pip.
    # Inicializar session_state para almacenar los DataFrames
    if "df_final" not in st.session_state:
        st.session_state.df_final = None
    if "df_status" not in st.session_state:
        st.session_state.df_status = None
    # Streamlit utiliza 'st.session_state' para almacenar variables que persisten entre ejecuciones de la aplicación (por ejemplo, al interactuar con widgets).
    # Estas líneas verifican si las claves "df_final" y "df_status" existen en 'st.session_state'.
    # Si no existen, se inicializan con el valor None.
    # 'df_final' probablemente almacenará el DataFrame combinado de los archivos Excel cargados por el usuario.
    # 'df_status' probablemente almacenará el DataFrame con la información de estatus de los estudiantes extraída de una URL.
    #st.title("Une lista de estudiantes y agrega estatus")

    # Sección: Cargar y Unir Archivos Excel
    st.subheader("Fusiona lista de alumnos y agrega grupo y estatus")
    st.write("Adjunta tus archivos de excel y se fusionarán en uno solo, se agregará el status y grupo")

    uploaded_files = st.file_uploader("Selecciona uno o varios archivos Excel", type=["xlsx"], accept_multiple_files=True)
    # Se crea un widget para permitir al usuario cargar uno o varios archivos Excel.
    # - "Selecciona uno o varios archivos Excel" es la etiqueta del widget.
    # - type=["xlsx"] especifica que solo se aceptarán archivos con la extensión .xlsx.
    # - accept_multiple_files=True permite al usuario seleccionar y cargar varios archivos a la vez.
    # Los archivos cargados se almacenarán en la variable 'uploaded_files' como una lista de objetos de archivo.
    if uploaded_files:
        dataframes = []
        for i, file in enumerate(uploaded_files):
            # Se inicia un bucle para iterar sobre cada archivo cargado en la lista 'uploaded_files'.
            # 'enumerate' proporciona tanto el índice ('i') como el objeto de archivo ('file') en cada iteración.
            df = pd.read_excel(file, header=0)
            # Se lee el contenido del archivo Excel actual ('file') utilizando 'pd.read_excel()' y se crea un DataFrame llamado 'df'.
            # 'header=0' indica que la primera fila del archivo se utilizará como encabezado de las columnas.
            if i > 0:
                df.columns = dataframes[0].columns  # Asegurar coherencia de columnas
                # Si no es el primer archivo cargado (i > 0), se asignan al DataFrame actual ('df') las mismas columnas que el DataFrame del primer archivo cargado ('dataframes[0]').
                # Esto se hace para asegurar que todos los DataFrames tengan la misma estructura de columnas antes de unirlos.
            dataframes.append(df)
        
        # Unir los archivos en un solo DataFrame
        st.session_state.df_final = pd.concat(dataframes, ignore_index=True)
        # Se utiliza la función 'pd.concat()' para unir todos los DataFrames almacenados en la lista 'dataframes' en un único DataFrame.
        # 'ignore_index=True' hace que se genere un nuevo índice secuencial para el DataFrame resultante, ignorando los índices originales de los DataFrames individuales.
        # El DataFrame unido se guarda en 'st.session_state.df_final'.
        st.session_state.df_final.columns = st.session_state.df_final.columns.str.strip()
        # Se eliminan los espacios en blanco al principio y al final de los nombres de las columnas del DataFrame unido.
    # Botón para actualizar `df_final` con los datos de `df_status`
    if st.button("Actualizar Información"):
        try:
            datos_status = asyncio.run(extraer_datos_status(login_url, username, password, url_status))
            # Se llama a la función asíncrona 'extraer_datos_status' para obtener la información de estatus de los estudiantes.
            # Se asume que las variables 'login_url', 'username', 'password' y 'url_status' están definidas en otro lugar del código.
            # El resultado de esta función se guarda en 'datos_status'.
            if datos_status:
                st.session_state.df_status = pd.DataFrame(datos_status, columns=["Nombre", "Dirección de correo", "Grupo", "Último acceso"])
                 # Se crea un DataFrame llamado 'df_status' a partir de los datos extraídos, con las columnas "Nombre", "Dirección Email", "Grupo" y "Último acceso".
                st.session_state.df_status.columns = st.session_state.df_status.columns.str.strip()
            
            if st.session_state.df_final is not None and st.session_state.df_status is not None:
                # Se verifica si tanto 'df_final' (el DataFrame unido de los archivos cargados) como 'df_status' (el DataFrame de estatus) tienen datos.
                if "Dirección de correo" in st.session_state.df_final.columns and "Dirección de correo" in st.session_state.df_status.columns:
                    # Fusionar datos
                    st.session_state.df_final = st.session_state.df_final.merge(
                        st.session_state.df_status[["Dirección de correo", "Grupo", "Último acceso"]], 
                        on="Dirección de correo", 
                        how="left"
                    )
            # Se realiza una fusión (merge) entre 'st.session_state.df_final' y 'st.session_state.df_status'.
            # - Se utilizan solo las columnas "Dirección Email", "Grupo" y "Último acceso" de 'df_status'.
            # - La fusión se realiza basándose en la columna "Dirección Email" (on="Dirección Email").
            # - Se utiliza una fusión "left", lo que significa que se conservan todas las filas de 'df_final', y si hay coincidencias en "Dirección Email" en 'df_status', se añaden las columnas "Grupo" y "Último acceso" correspondientes. Si no hay coincidencia, estas nuevas columnas tendrán valores nulos (NaN).
            # El DataFrame fusionado se guarda de nuevo en 'st.session_state.df_final'
                    st.header("Ahora tienes la lista de alumnos con status y grupo")
                    st.dataframe(st.session_state.df_final)
                else:
                    st.error("No se encontró la columna 'Dirección Email' en uno de los DataFrames. Revisa los encabezados.")
            else:
                st.error("Asegúrate de haber cargado los archivos Excel antes de actualizar.")
        except Exception as e:
            st.error(f"Error al extraer status: {e}")

    # Función para convertir el DataFrame a un archivo Excel y permitir su descarga
    def convertir_a_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Datos Unificados")
        output.seek(0)
        return output
     # Esta función toma un DataFrame 'df' y lo convierte a un archivo Excel en memoria utilizando BytesIO y pandas.ExcelWriter con el motor 'xlsxwriter'.
        # - 'BytesIO()' crea un objeto similar a un archivo pero en memoria.
        # - 'pd.ExcelWriter(output, engine="xlsxwriter")' crea un escritor de Excel que escribe en el objeto 'output'.
        # - 'df.to_excel(writer, index=False, sheet_name="Datos Unificados")' escribe el DataFrame en una hoja llamada "Datos Unificados" sin incluir el índice.
        # - 'output.seek(0)' mueve el puntero del objeto BytesIO al principio para que su contenido pueda ser leído.
        # - La función devuelve el objeto BytesIO que contiene los datos del archivo Excel en memoria.

    # Botón de descarga en formato Excel
    if st.session_state.df_final is not None and not st.session_state.df_final.empty:
        excel_data = convertir_a_excel(st.session_state.df_final)
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name="Lista_Fusionada_gpo_status.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
     # Se crea un botón de descarga ('st.download_button').
        # - label="📥 Descargar Excel" es la etiqueta del botón.
        # - data=excel_data proporciona los datos del archivo Excel en memoria para la descarga.
        # - file_name="Lista_gpo_status.xlsx" es el nombre de archivo sugerido para la descarga.
        # - mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" especifica el tipo MIME del archivo Excel.
    else:
        st.warning("No hay datos para descargar. Asegúrate de haber unido los archivos correctamente.")






with tab8:  # Personalizado

    def reemplazar_template(template, row):
        def repl(match):
            key = match.group(1).strip()
            idx = ord(key.upper()) - ord('A')
            return str(row.iloc[idx]) if 0 <= idx < len(row) else match.group(0)
        return re.sub(r'\{\{(.*?)\}\}', repl, template)

    st.subheader("Creación de mensajes personalizados")

    uploaded_file = st.file_uploader("Selecciona el archivo Excel", type=["xlsx"])

    # ✅ Checkbox 1 - Para reemplazar '-' por 'Sin entrega'
    reemplazar_sin_entregas = st.checkbox("Reemplazar '-' con 'Sin entrega'")

    # ✅ Checkbox 2 - Para calcular la columna 'Calificación'
    calcular_calificacion = st.checkbox("Calcular columna 'Calificación'")  # <--- NUEVO checkbox

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)

            # Acción del primer checkbox
            if reemplazar_sin_entregas:
                df = df.replace('-', 'Sin entrega')
                st.info("Los valores '-' han sido reemplazados con 'Sin entrega'.")

            # Acción del segundo checkbox
            if calcular_calificacion:
                if 'Total del curso (Real)' in df.columns:
                    def calcular_calif(valor):
                        if valor == "-" or valor == "Sin entrega":
                            return "NP"
                        try:
                            val = float(valor)
                            if val < 5.99:
                                return 5
                            elif val % 1 == 0.5:
                                return round(val + 0.5)
                            else:
                                return round(val)
                        except:
                            return "Error"

                    df["Calificación"] = df["Total del curso (Real)"].apply(calcular_calif)
                    st.success("Columna 'Calificación' generada exitosamente.")
                else:
                    st.warning("No se encontró la columna 'Total del curso (Real)'. No se puede calcular 'Calificación'.")

            st.success("Archivo cargado exitosamente.")

            st.write("### Vista previa:")
            st.dataframe(df)

            placeholders_copiables = "\n".join(
                [f"{col_name}: {{ {chr(65 + idx)} }}" for idx, col_name in enumerate(df.columns)]
            ).replace("{ ", "{{").replace(" }", "}}")

            st.text_area("Copia y pega los placeholders:", placeholders_copiables, height=150)
            subject_text = st.text_input("Ingresa el Subject para los correos:")
            template_text = st.text_area(
                "Ingresa el texto con placeholders y conviertelo en html",
                "Hola {{A}} {{B}} te saludo con mucho gusto."
            )

            if st.button("Generar correos"):
                columnas_requeridas = ["Nombre", "Apellido(s)", "Dirección de correo"]

                if all(col in df.columns for col in columnas_requeridas):
                    df_final = df[columnas_requeridas].copy()
                    df_final["Subject"] = subject_text
                    template_sin_enter = template_text.replace('\n', ' ')
                    df_final["html"] = df.apply(lambda row: reemplazar_template(template_sin_enter, row), axis=1)

                    st.write("### Correos Generados:")
                    st.dataframe(df_final)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        df_final.to_excel(writer, index=False, sheet_name="Correos")
                    output.seek(0)

                    st.download_button(
                        label="Descargar Excel con Correos",
                        data=output,
                        file_name="Mail_Calificaciones_Personalizadas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error(f"Error: El archivo Excel debe contener las columnas: {', '.join(columnas_requeridas)}")

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    else:
        st.info("Por favor, sube un archivo Excel para continuar.")







        
with tab9:#grupos
    
    
    st.subheader("Extrae los grupos y los carga en el json configuración")
    
    if st.button("grupos2"):
        urls_a_extraer="https://urc.cdmx.gob.mx/LAD_A2_2025-1/mod/forum/view.php?id=4792"
        urls = [url.strip() for url in urls_a_extraer.split(",") if url.strip()]
        if not urls:
            st.error("Por favor, ingresa al menos una URL para extraer datos.")
        else:
            with st.spinner("Extrayendo grupos"): # utilidades/main.py
                resultados = asyncio.run(extraer_datos_de_url_espcs(login_url, username, password, urls))# utilidades/main.py
                if resultados:
                    st.write("Extracción de datos exitosa.")
                  
                    for resultado in resultados:
                        
                        if resultado["nombres"]:
                            for nombre in resultado["nombres"]:
                                st.write(f"- {nombre}")
                        else:
                            st.write("No se encontraron nombres.")
                    configuraciones = cargar_configuracion()
                    # Actualizar 'Grupos' con los nuevos datos
                    if configuraciones and resultados and resultados[0]['nombres']:
                        configuraciones[0]['Grupos'] = resultados[0]['nombres']
                        print("Grupos actualizados con éxito.")
                    else:
                        print("No se pudieron actualizar los grupos. Asegúrate de que 'resultados' contenga datos válidos.")

                    # Guardar la configuración actualizada
                    guardar_configuracion(configuraciones)
                else:
                  st.error("Error al extraer datos de las URLs.")
    
    
    st.header("Crea la base de datos de alumnos")
    uploaded_file = st.file_uploader("Sube un archivo Excel", type=["xlsx"])
    if uploaded_file is not None:
        if verificar_tipo_archivo(uploaded_file):
            cargar_datos(uploaded_file)
    
    if st.button("grupos"):
        urls_a_extraer="https://urc.cdmx.gob.mx/LAD_A2_2025-1/mod/forum/view.php?id=4792"
        urls = [url.strip() for url in urls_a_extraer.split(",") if url.strip()]
        if not urls:
            st.error("Por favor, ingresa al menos una URL para extraer datos.")
        else:
            with st.spinner("Extrayendo grupos"): # utilidades/main.py
                resultados = asyncio.run(extraer_datos_de_url_espcs(login_url, username, password, urls))# utilidades/main.py
                if resultados:
                    st.write("Extracción de datos exitosa.")
                  
                    for resultado in resultados:
                        
                        if resultado["nombres"]:
                            for nombre in resultado["nombres"]:
                                st.write(f"- {nombre}")
                        else:
                            st.write("No se encontraron nombres.")
                    configuraciones = cargar_configuracion()
                    # Actualizar 'Grupos' con los nuevos datos
                    if configuraciones and resultados and resultados[0]['nombres']:
                        configuraciones[0]['Grupos'] = resultados[0]['nombres']
                        print("Grupos actualizados con éxito.")
                    else:
                        print("No se pudieron actualizar los grupos. Asegúrate de que 'resultados' contenga datos válidos.")

                    # Guardar la configuración actualizada
                    guardar_configuracion(configuraciones)
                else:
                  st.error("Error al extraer datos de las URLs.")
                  
                  
    
    
    
    
with tab10:#Carga json
    
    import streamlit as st
    import json
    import os

    # --- Asume que estas funciones existen en otro lugar de tu código ---
    # Asegúrate de que estas funciones estén definidas e importadas correctamente
    # en tu script principal de Streamlit.

    def cargar_configuracion(archivo='configuracion.json'):
        """Carga la configuración desde un archivo JSON."""
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = json.load(f)
                    # Añadir validación extra: asegurar que es una lista
                    if isinstance(contenido, list):
                        return contenido
                    else:
                        st.error(f"Error: El archivo '{archivo}' no contiene una lista JSON.")
                        return [] # Devolver lista vacía si no es una lista
            except json.JSONDecodeError:
                st.error(f"Error: El archivo '{archivo}' no contiene un JSON válido.")
                return [] # Devolver lista vacía en caso de error de decodificación
            except Exception as e:
                st.error(f"Error inesperado al cargar el archivo '{archivo}': {e}")
                return []
        else:
            # Si el archivo no existe, podrías decidir devolver [] o None,
            # dependiendo de cómo quieras manejarlo en la app. Devolver [] es más seguro.
            st.warning(f"Advertencia: El archivo '{archivo}' no se encontró.")
            return []

    def guardar_configuracion(configuraciones, archivo='configuracion.json'):
        """Guarda la lista de configuraciones en un archivo JSON."""
        if not isinstance(configuraciones, list):
            st.error("Error interno: Se intentó guardar datos que no son una lista.")
            return False
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(configuraciones, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error al guardar en el archivo '{archivo}': {e}")
            return False
    # --- Fin de las funciones asumidas ---


    def llenar_config_tab():
        """
        Función para la pestaña de Streamlit que permite editar un bloque
        de configuración existente en 'configuracion.json' por su índice.
        """
        st.subheader("Editar Configuración JSON por Índice")
        ruta_archivo = "configuracion.json" # Ruta al archivo de configuración

        # 1. Cargar la configuración existente
        config_data = cargar_configuracion(ruta_archivo)

        # Verificar si la carga fue exitosa y si hay datos para editar
        if not config_data: # Se cubre el caso de archivo no existente, vacío, o con JSON inválido/no lista
            st.info(f"No hay bloques de configuración válidos en '{ruta_archivo}' para editar.")
            # Opcional: Añadir un botón/instrucciones para crear la configuración inicial si es necesario.
            return # Detiene la ejecución si no hay nada que editar

        # 2. Selección del índice a editar
        indices_disponibles = list(range(len(config_data)))

        # Usar st.selectbox para la selección del índice
        indice_a_editar = st.selectbox(
            "Seleccione el índice del bloque que desea editar:",
            options=indices_disponibles,
            # Intenta mantener el índice seleccionado anteriormente si existe en session_state
            index=st.session_state.get('indice_editado_previo', 0) if st.session_state.get('indice_editado_previo', 0) in indices_disponibles else 0,
            key='selector_indice_bloque', # Clave para el widget
            help="El índice corresponde a la posición del bloque en la lista del archivo JSON (empezando en 0)."
        )

        # Guardar el índice seleccionado para posible uso futuro o persistencia entre recargas
        st.session_state['indice_editado_previo'] = indice_a_editar

        st.markdown("---") # Separador visual

        # 3. Función interna para mostrar y actualizar los campos del bloque seleccionado
        #    (Esta función no necesita cambios respecto a la versión anterior)
        def mostrar_y_actualizar_campos(config_bloque, index):
            updated_config = config_bloque.copy() # Trabajar sobre una copia
            st.subheader(f"Editando Bloque Índice {index}")
            st.write("Modifique los valores necesarios:")

            for key, value in config_bloque.items():
                # Omitir claves específicas (ajusta según tus necesidades exactas)
                if key.startswith("op_") or key.startswith("Cbx_") or key.startswith("RdB_") or key == "ultimo_foro_seleccionado":
                    updated_config[key] = value # Mantener valor original
                    # st.text(f"{key}: {value}") # Opcional: mostrar como no editable
                    continue

                # Determinar el tipo de input adecuado
                field_key = f"{key}_{index}" # Clave única para el widget Streamlit
                if isinstance(value, list):
                    current_text = "\n".join(map(str, value)) if value else ""
                    user_input = st.text_area(
                        f"{key} (un elemento por línea)",
                        value=current_text,
                        height=100,
                        key=field_key
                    )
                    updated_config[key] = [line.strip() for line in user_input.split('\n') if line.strip()]
                elif isinstance(value, bool):
                    updated_config[key] = st.checkbox(key, value, key=field_key)
                elif value is None:
                    user_input = st.text_input(key, value="", placeholder="<Vacío>", key=field_key)
                    # Si el usuario no ingresa nada, se mantiene como None
                    updated_config[key] = user_input if user_input else None
                elif isinstance(value, (int, float)):
                    # Usar st.number_input para tipos numéricos
                    try:
                        if isinstance(value, int):
                            updated_config[key] = st.number_input(key, value=value, step=1, key=field_key)
                        else: # float
                            updated_config[key] = st.number_input(key, value=value, format="%.5f", key=field_key) # Ajusta el formato si es necesario
                    except Exception as e:
                        st.warning(f"No se pudo crear input numérico para {key}: {e}. Usando texto.")
                        updated_config[key] = st.text_input(key, str(value), key=field_key)

                elif isinstance(value, str):
                    # Usar text_area para strings largos, text_input para cortos?
                    # Por simplicidad, usamos text_input, ajusta si prefieres text_area para algunos.
                    updated_config[key] = st.text_input(key, value, key=field_key)
                else:
                    # Caso por defecto para otros tipos (representar como string)
                    st.text(f"{key} (Tipo no editable: {type(value).__name__}): {value}")
                    updated_config[key] = value # Mantener valor original

            return updated_config

        # 4. Mostrar los campos del bloque seleccionado y obtener los valores actualizados
        #    Acceder al bloque usando el índice seleccionado
        bloque_seleccionado = config_data[indice_a_editar]
        bloque_actualizado = mostrar_y_actualizar_campos(bloque_seleccionado, indice_a_editar)

        # 5. Actualizar el bloque correspondiente en la lista en memoria (crucial!)
        config_data[indice_a_editar] = bloque_actualizado

        st.markdown("---") # Otro separador

        # 6. Botón para guardar TODOS los bloques (incluyendo el modificado)
        if st.button(f"Guardar Cambios (Actualizar Archivo Completo)", key="save_button"):
            if guardar_configuracion(config_data, ruta_archivo):
                st.success(f"Archivo '{ruta_archivo}' actualizado exitosamente.")
                st.info(f"Se guardaron todos los bloques, incluyendo los cambios en el índice {indice_a_editar}.")
                # Opcional: Limpiar caché o forzar rerun si es necesario para reflejar cambios en otras partes de la app
                # st.cache_data.clear()
                # st.experimental_rerun()
            else:
                # El error específico ya se mostró dentro de guardar_configuracion
                st.error("Fallo al guardar el archivo de configuración.")


    # --- Cómo usarlo en tu app Streamlit ---
    # En tu script principal, donde defines las pestañas o secciones:
    #
    # tab_editar, tab_otra_cosa = st.tabs(["Editar Configuración", "Otra Pestaña"])
    #
    # with tab_editar:
    #llenar_config_tab() # Llama a esta función dentro de la pestaña deseada
    #
    # with tab_otra_cosa:
    #     st.write("Contenido de la otra pestaña...")
    
    
    # Tu contraseña secreta
    PASSWORD = "xxx"

    
    # Título
    st.title("Acceso protegido")

    # Campo para ingresar contraseña
    input_pass = st.text_input("Introduce la contraseña:", type="password")

    # Botón para verificar
    if st.button("Ingresar"):
        if input_pass == PASSWORD:
            st.success("✅ ¡Función ejecutada con éxito!")
            llenar_config_tab()
        else:
            st.error("❌ Contraseña incorrecta")
            
    
    
    
    
    
    
    
    #
with tab11: #captura de pantalla
    
    
    import streamlit as st
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
    import time
    import io
    import logging

    # --- Configuración de Logging (igual que antes) ---
    log_formatter_captura = logging.Formatter('%(asctime)s - %(levelname)s - [CapturaElemento] - %(message)s')
    logger_captura = logging.getLogger("captura_elemento_logger") # Logger diferente por claridad
    logger_captura.setLevel(logging.INFO)
    logger_captura.propagate = False
    if not logger_captura.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(log_formatter_captura)
        logger_captura.addHandler(ch)
    # --- Fin Configuración Logging ---

    # --- Función de Login y Captura de ELEMENTO ---
    def tomar_screenshot_elemento(target_url: str, login_url: str, username: str, password: str,
                                selector: str, by: By = By.CSS_SELECTOR) -> bytes | None:
        """
        Inicia sesión, navega a URL, espera un elemento específico usando un
        selector estable, toma captura SÓLO de ese elemento y devuelve bytes.
        """
        logger_captura.info(f"Iniciando captura de ELEMENTO en URL: {target_url}")
        logger_captura.info(f"Usando selector: [{by}] '{selector}'")
        driver = None
        screenshot_bytes = None

        # --- Configuración Firefox Headless (igual que antes) ---
        firefox_options = Options()
        try:
            firefox_options.binary_location = "/usr/bin/firefox-esr"
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--disable-gpu")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--window-size=1920,1080") # Tamaño ventana inicial
            firefox_options.add_argument("--start-maximized")
            firefox_options.set_preference("layout.css.devPixelsPerPx", "1.0")
            logger_captura.info("Configuración de Firefox Headless lista.")

            driver = webdriver.Firefox(options=firefox_options)
            logger_captura.info("Driver Firefox iniciado.")
            driver.set_page_load_timeout(90)

            # --- PASO 1: INICIAR SESIÓN (igual que antes) ---
            logger_captura.info(f"Navegando a la página de inicio de sesión: {login_url}")
            driver.get(login_url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "loginbtn"))).click()
            time.sleep(5)
            logger_captura.info("Inicio de sesión completado (aparentemente).")

            # --- PASO 2: NAVEGAR A LA URL OBJETIVO (igual que antes) ---
            logger_captura.info(f"Navegando a la URL objetivo: {target_url}")
            driver.get(target_url)
            logger_captura.info("Esperando carga de la página objetivo (body)...")
            WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger_captura.info("Página objetivo cargada (body presente).")

            # --- PASO 3: ENCONTRAR Y CAPTURAR EL ELEMENTO ESPECÍFICO ---
            logger_captura.info(f"Esperando a que el elemento '{selector}' esté presente...")
            try:
                # Esperar a que el elemento exista en el DOM
                elemento_canvas = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((by, selector))
                )
                logger_captura.info("Elemento canvas encontrado en el DOM.")

                # (Opcional pero recomendado para canvas) Esperar un poco a que se dibuje
                time.sleep(3) # Ajusta (2-5 segundos) si el gráfico tarda en aparecer

                # --- Tomar captura SÓLO del elemento ---
                screenshot_bytes = elemento_canvas.screenshot_as_png
                logger_captura.info(f"Captura de pantalla del ELEMENTO '{selector}' tomada exitosamente.")

            except TimeoutException:
                logger_captura.error(f"Timeout esperando el elemento '{selector}' en {target_url}")
                st.error(f"Error: No se encontró el elemento gráfico ('{selector}') en la página después de esperar.")
                return None # Asegurarse de devolver None si no se encontró
            except Exception as e_el:
                logger_captura.exception(f"Error al intentar capturar el elemento '{selector}': {e_el}")
                st.error(f"Error al capturar el elemento gráfico: {e_el}")
                return None # Asegurarse de devolver None en otros errores del elemento

        # --- Bloques except y finally (iguales que antes, adaptando mensajes si es necesario) ---
        except TimeoutException as e:
            # ... (manejo de error de login/carga de página) ...
            st.error(f"Error: Timeout durante el proceso (login o carga de '{target_url}'). Revisa logs.")
        except NoSuchElementException as e:
            # ... (manejo de error de elemento no encontrado en login) ...
            st.error("Error: No se encontró un campo necesario (login o en pág. destino). ¿Cambió la estructura?")
        except WebDriverException as e:
            # ... (manejo de error de WebDriver) ...
            st.error(f"Error del navegador al procesar la URL '{target_url}' post-login.")
        except Exception as e:
            # ... (manejo de error general) ...
            st.error(f"Ocurrió un error inesperado. Detalles: {e}")
        finally:
            if driver:
                driver.quit()
                logger_captura.info("Driver Firefox cerrado.")

        return screenshot_bytes # Devuelve los bytes del elemento o None si falló


    # --- Sección de la Interfaz de Streamlit (Modificada) ---

    st.header("Capturador de Elemento Específico (Canvas)")

    # --- Asumiendo que `usuario_seleccionado` está disponible ---
    if 'usuario_seleccionado' in locals() and isinstance(usuario_seleccionado, dict) and \
    all(k in usuario_seleccionado for k in ['login_url', 'username', 'password']):

        st.info(f"Se usarán las credenciales del usuario: **{usuario_seleccionado.get('Nombre', usuario_seleccionado['username'])}**")

        # Mantener estado en session_state
        if 'captura_elemento_target_url' not in st.session_state:
            # Puedes predefinir la URL aquí si siempre es la misma para el gráfico
            st.session_state.captura_elemento_target_url = "https://URL_DONDE_ESTA_EL_GRAFICO.com/reporte"
        if 'captura_elemento_bytes' not in st.session_state:
            st.session_state.captura_elemento_bytes = None

        # Input para la URL (si necesita ser variable)
        url_input = st.text_input(
            "URL de la página que contiene el gráfico:",
            value=st.session_state.captura_elemento_target_url,
            key="url_captura_elemento_input"
        )
        url_input = "https://www.plataforma.unrc.edu.mx/report/log/user.php?id=42661&course=367&mode=all"
        st.session_state.captura_elemento_target_url = url_input

        # Selector (podrías incluso hacerlo configurable si cambian)
        selector_css_grafico = "div.chart-area canvas" # <- Nuestro selector estable
        st.caption(f"Se intentará capturar el elemento con el selector CSS: `{selector_css_grafico}`")

        # Botones
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📊 Capturar Gráfico", key="btn_capturar_elemento"):
                if url_input and (url_input.startswith("http://") or url_input.startswith("https://")):
                    # Validar credenciales (opcional)
                    if usuario_seleccionado['username'] == 'DEFINE_USUARIO' or usuario_seleccionado['password'] == 'DEFINE_PASSWORD':
                        st.error("Credenciales no configuradas.")
                        st.session_state.captura_elemento_bytes = None
                    else:
                        with st.spinner(f"Accediendo a {url_input} y buscando gráfico..."):
                            # Llamar a la nueva función
                            imagen_bytes = tomar_screenshot_elemento(
                                target_url=url_input,
                                login_url=usuario_seleccionado['login_url'],
                                username=usuario_seleccionado['username'],
                                password=usuario_seleccionado['password'],
                                selector=selector_css_grafico, # Pasar selector estable
                                by=By.CSS_SELECTOR           # Indicar que es CSS Selector
                            )
                            st.session_state.captura_elemento_bytes = imagen_bytes
                            if imagen_bytes is None:
                                st.warning("No se pudo obtener la captura del gráfico.")

                elif url_input:
                    st.warning("URL inválida.")
                    st.session_state.captura_elemento_bytes = None
                else:
                    st.warning("Introduce la URL.")
                    st.session_state.captura_elemento_bytes = None

        with col2:
            if st.session_state.get('captura_elemento_bytes') is not None:
                if st.button("🗑️ Borrar Captura", key="btn_borrar_elemento"):
                    st.session_state.captura_elemento_bytes = None
                    st.info("Captura borrada.")
                    st.rerun()

        # Mostrar la imagen capturada del elemento
        if st.session_state.get('captura_elemento_bytes'):
            st.divider()
            st.subheader("Vista Previa del Gráfico Capturado:")
            st.image(
                st.session_state.captura_elemento_bytes,
                caption=f"Elemento capturado de: {st.session_state.captura_elemento_target_url}",
                use_column_width='auto' # Ajustar ancho automáticamente
            )
            st.caption("La imagen se muestra desde memoria y no se guarda en disco.")

    else:
        st.error("No se ha seleccionado un usuario válido con credenciales.")
        st.info("Asegúrate de que la lógica de selección de usuario se ejecute antes.")

    # --- Fin de la Sección ---
with tab12: # calificaciòn final

    import streamlit as st
    import pandas as pd
    import re
    from io import BytesIO
    import math

    # Título de la aplicación
    st.subheader("Coloca el mensaje HTML para cada tipo de mensaje NP, 5 , Excento")
    st.write("**Carga el excel ya fusionado con el status de los estudiantes** ")

    # Subida del archivo Excel
    archivo = st.file_uploader("Carga tu archivo Excel (.xlsx)", type=["xlsx"])

    if archivo:
        # Lectura del archivo en un DataFrame
        df = pd.read_excel(archivo)

        # Generar columna 'Calificación' desde 'Total del curso (Real)'
        def calcular_calificacion(valor):
            try:
                if str(valor).strip() in ["-", "Sin entrega"]:
                    return "NP"
                num = float(valor)
                if num < 5.99:
                    return "5"
                elif num % 1 == 0.5:
                    return str(math.ceil(num))
                else:
                    return str(round(num))
            except:
                return "Error"

        if "Total del curso (Real)" in df.columns:
            df["Calificación"] = df["Total del curso (Real)"].apply(calcular_calificacion)
        else:
            st.error("La columna 'Total del curso (Real)' no se encuentra en el archivo.")
            st.stop()

        # Mostrar columnas como placeholders (A, B, C, ...) y nombres reales
        st.subheader("Placeholders disponibles")
        placeholders = {}
        columnas = df.columns.tolist()
        for i, col in enumerate(columnas):
            letra = chr(65 + i)  # A, B, C, ...
            placeholders[letra] = col
        texto_placeholder = "\n".join([f"{{{{{letra}}}}} = {col}" for letra, col in placeholders.items()])
        st.text_area("Copia y pega los placeholders disponibles:", texto_placeholder, height=150)

        # Sección para ingresar los mensajes base y plantillas por condición
        st.subheader("Coloca el mensaje HTML en cada sección")

        st.markdown("### Calificación == 'NP'")
        base_np = st.text_input("Mensaje base para 'No presentó'", "No presentaste el examen final.")
        template_np = st.text_area("Template HTML para 'No presentó'", "<p>{{A}}, {{Subject}}</p>")

        st.markdown("### Calificación == '5'")
        base_reprobado = st.text_input("Mensaje base para 'Reprobado'", "Lamentablemente no aprobaste el curso.")
        template_reprobado = st.text_area("Template HTML para 'Reprobado'", "<p>{{A}}, {{Subject}}</p>")

        st.markdown("### Calificación > 6")
        base_aprobado = st.text_input("Mensaje base para 'Aprobado'", "¡Felicidades! Has aprobado el curso.")
        template_aprobado = st.text_area("Template HTML para 'Aprobado'", "<p>{{A}}, {{Subject}}</p>")

        # Ejemplos de mensajes por condición
        st.subheader("Previsualización de los mensajes a enviar")

        # Ejemplo para 'No presentó'
        st.markdown("#### :rainbow[Calificación 'NP']")
        fila_np = df[df["Calificación"] == "NP"].iloc[0].to_dict() if any(df["Calificación"] == "NP") else None
        if fila_np:
            fila_np["Subject"] = base_np
            html_np = re.sub(r"\{\{(.*?)\}\}", lambda match: str(fila_np.get(match.group(1), "-")), template_np.replace("\n", " "))
            st.components.v1.html(html_np, height=400, scrolling=True)
        else:
            st.info("No hay ningún registro con calificación 'NP' para mostrar un ejemplo.")

        # Ejemplo para 'Reprobado'
        st.markdown("#### :rainbow[Calificación '5']")
        fila_reprobado = df[df["Calificación"] == "5"].iloc[0].to_dict() if any(df["Calificación"] == "5") else None
        if fila_reprobado:
            fila_reprobado["Subject"] = base_reprobado
            html_reprobado = re.sub(r"\{\{(.*?)\}\}", lambda match: str(fila_reprobado.get(match.group(1), "-")), template_reprobado.replace("\n", " "))
            st.components.v1.html(html_reprobado, height=400, scrolling=True)
        else:
            st.info("No hay ningún registro con calificación '5' para mostrar un ejemplo.")

        # Ejemplo para 'Aprobado'
        st.markdown("#### :rainbow[Calificación aprobatoria]")
        calificaciones_numericas = pd.to_numeric(df["Calificación"], errors='coerce')
        df_aprobados = df[calificaciones_numericas > 6].dropna(subset=['Calificación'])
        fila_aprobado = df_aprobados.iloc[0].to_dict() if not df_aprobados.empty else None

        if fila_aprobado:
            fila_aprobado["Subject"] = base_aprobado
            html_aprobado = re.sub(r"\{\{(.*?)\}\}", lambda match: str(fila_aprobado.get(match.group(1), "-")), template_aprobado.replace("\n", " "))
            st.components.v1.html(html_aprobado, height=400, scrolling=True)
        else:
            st.info("No hay ningún registro con calificación numérica mayor a 6 para mostrar un ejemplo.")

        # Botón para generar resultado
        if st.button("Generar Resultado"):
            resultados = []
            for idx, fila in df.iterrows():
                calificacion = str(fila["Calificación"]).strip()
                mensaje_base = ""
                template = ""

                # Evaluar condiciones
                if calificacion == "NP":
                    mensaje_base = base_np
                    template = template_np
                elif calificacion == "5":
                    mensaje_base = base_reprobado
                    template = template_reprobado
                else:
                    try:
                        calif_num = float(calificacion)
                        if calif_num >= 6:
                            mensaje_base = base_aprobado
                            template = template_aprobado
                        else:
                            mensaje_base = base_reprobado
                            template = template_reprobado
                    except:
                        mensaje_base = "Calificación no reconocida"
                        template = "<p>Error: {{A}}, calificación no válida.</p>"

                # Reemplazar saltos de línea
                template = template.replace("\n", " ")

                # Diccionario por fila
                fila_dict = fila.to_dict()
                fila_dict["Subject"] = mensaje_base  # Subject contiene el mensaje base

                # Reemplazo de placeholders
                def reemplazo(match):
                    key = match.group(1)
                    if len(key) == 1 and key in placeholders:
                        col_name = placeholders[key]
                        return str(fila.get(col_name, "-"))
                    return str(fila_dict.get(key, "-"))

                mensaje_html = re.sub(r"\{\{(.*?)\}\}", reemplazo, template)

                resultados.append({
                    **fila_dict,
                    "html": mensaje_html
                })

            # DataFrame final
            df_final = pd.DataFrame(resultados)

            # Mostrar resultado
            st.subheader("Resultado")
            st.dataframe(df_final)

            # Descargar como Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Mensajes')
            output.seek(0)
            st.download_button("Descargar Excel con mensajes", data=output, file_name="Mail_Calificaciones_Finales.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
