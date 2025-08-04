#utilidades/load.py
import streamlit as st
import pandas as pd
import os

def verificar_tipo_archivo(uploaded_file):
    """Verifica si el archivo subido es un archivo Excel (.xlsx)."""
    filename, file_extension = os.path.splitext(uploaded_file.name)
    if file_extension.lower() != ".xlsx":
        st.error("Por favor, sube un archivo Excel (.xlsx).")
        return False
    return True

def cargar_datos(uploaded_file):
    """Carga y muestra el contenido de un archivo Excel."""
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df)  # Mostrar el DataFrame
        except ValueError as ve:
            st.error(f"Error de formato de archivo: {ve}")
        except FileNotFoundError as fnfe:
            st.error(f"Archivo no encontrado: {fnfe}")
        except Exception as e:
            st.error(f"Error inesperado al procesar el archivo: {e}")

