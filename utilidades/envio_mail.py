#utilidades/envio_mail.py
#modificado el 22 de frebrero 
#cuenta con modificaciones sobre separar el código 
#Sirve como plataformar para realizar las otras operaciones
import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import re

# ... el resto del código ...

def enviar_correos(uploaded_file,remitente,contrasena):
    """
    Gestiona la carga de archivos Excel y el envío de correos electrónicos.
    """
    # Parámetros de retardo
    correos_por_lote = 30
    tiempo_espera = 30  # segundos
    # Configuración de credenciales
    #remitente = "amaya.constantino493@rcastellanos.cdmx.gob.mx"
    #contraseña = "qnvb nyoz efmz kjly"
    contraseña = contrasena
    # Expresión regular para validar correos electrónicos (versión mejorada)
    patron_correo = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df)  # Mostrar el DataFramea

            if st.button("Enviar correos"):
                correos_enviados = 0
                num_filas = len(df)

                mensaje_envio = st.empty()  # Placeholder para mensajes

                for i in range(num_filas):
                    row = df.iloc[i]
                    destinatario = row['Dirección Email']
                    asunto = row['Subject']
                    html = row['html']

                    # Validaciones
                    if pd.isna(destinatario) or not destinatario or destinatario is None:
                        mensaje_envio.error(f"Destinatario vacío o inválido en la fila {i + 2}. Se saltará este correo.")
                        continue

                    if not re.match(patron_correo, destinatario):
                        mensaje_envio.error(f"Dirección de correo inválida: {destinatario} en la fila {i+2}")
                        continue

                    if pd.isna(asunto) or not asunto or asunto is None:
                        mensaje_envio.error(f"Asunto vacío o inválido en la fila {i + 2}. Se saltará este correo.")
                        continue

                    if pd.isna(html) or not html or html is None:
                        html=""
                        print(f"Advertencia: Celda vacía para {destinatario}. Se enviará un correo sin contenido HTML.")
                    else:
                        html = str(html)


                    mensaje_envio.info(f"Enviando correo a: {destinatario}")

                    mensaje = MIMEMultipart()
                    mensaje["From"] = remitente
                    mensaje["To"] = destinatario
                    mensaje["Subject"] = asunto
                    mensaje.attach(MIMEText(html, "html"))

                    try:
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                            servidor.login(remitente, contraseña)
                            servidor.sendmail(remitente, destinatario, mensaje.as_string())
                        print(f"Correo electrónico enviado a {destinatario}")
                        correos_enviados += 1
                    except Exception as e:
                        mensaje_envio.error(f"Error al enviar correo a {destinatario}: {e}")
                        continue  # Saltar al siguiente correo

                    if correos_enviados % correos_por_lote == 0:
                        mensaje_envio.info("Pausa: esperando...")
                        print(f"Se han enviado {correos_por_lote} correos. Esperando {tiempo_espera} segundos...")

                        cuenta_regresiva_placeholder = st.empty()

                        for j in range(tiempo_espera, 0, -1):
                            cuenta_regresiva_placeholder.write(f"Tiempo restante: {j} segundos")
                            time.sleep(1)

                        cuenta_regresiva_placeholder.empty()
                        mensaje_envio.info("Reanudando envío...")
                        print("Reanudando el envío de correos...")

                mensaje_envio.success("Envío completado.")
                print("Todos los correos electrónicos han sido enviados.")

        except Exception as e:
            st.error(f"Error al procesar el archivo o enviar correos: {e}")