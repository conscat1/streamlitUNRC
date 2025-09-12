# utilidades/extraccion_datos.py
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re
DASHES_RE = re.compile(r'^\s*[-–—−]\s*$')  # acepta -, –, —, − con/ sin espacios

def extraer_datos_spec(html_content):
    """Extrae los textos de las opciones de un select HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    select_group = soup.find('select', {'name': 'group'})  # Busca el select por el nombre 'group'

    if not select_group:
        return []

    opciones = []
    for option in select_group.find_all('option'):
        opciones.append(option.text.strip())

    return opciones

def extraer_datos_articulos(html_content):
    """Extrae datos de artículos HTML y devuelve una lista de diccionarios con la información."""
    soup = BeautifulSoup(html_content, 'html.parser')
    articulos = soup.find_all('article')
    resultados = []

    if not articulos:
        return resultados  # Retorna una lista vacía.

    # Autor de referencia (si existe)
    primer_articulo = articulos[0]
    div_nombre_primero = primer_articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
    autor_referencia = (div_nombre_primero.find('a').get_text(strip=True)
                        if div_nombre_primero and div_nombre_primero.find('a') else None)

    for articulo in articulos:
        div_nombre = articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
        autor_actual = (div_nombre.find('a').get_text(strip=True)
                        if div_nombre and div_nombre.find('a') else None)

        # omite artículos del mismo autor que el primero (si eso es lo que querías)
        if autor_referencia and autor_actual == autor_referencia:
            continue

        # ---- detección de "sin calificación" robusta ----
        rc = articulo.find('span', class_='ratingcount')
        txt = rc.get_text(strip=True) if rc else ''
        if not DASHES_RE.match(txt.replace('\u00a0', ' ')):  # &nbsp; -> espacio normal
            continue

        # ---- ventana de tiempo ----
        tiempo = articulo.find('time')
        fecha_txt = tiempo.get_text(strip=True) if tiempo else None

        autor_txt = (div_nombre.find('a').get_text(strip=True)
                    if div_nombre and div_nombre.find('a') else None)

        if autor_txt and fecha_txt:
            nombre = f"{autor_txt}-{fecha_txt}"          # usa " - " si prefieres con espacios
        elif autor_txt:
            nombre = autor_txt
        elif div_nombre:
            # Fallback MUY conservador: si no hay <a>, limpia "por " o un "de" pegado (deDIEGO...)
            raw = div_nombre.get_text(separator=' ', strip=True)
            raw = re.sub(r'^por\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'^de(?=[A-ZÁÉÍÓÚÑ])', '', raw)  # solo si viene pegado a mayúscula: deDIEGO
            nombre = raw or "Nombre no encontrado"
        else:
            nombre = "Nombre no encontrado"
        resultados.append({"nombre": nombre, "dentro_de_tiempo": dentro_de_tiempo})

    return resultados


def extraer_otros_datos(html_content, selector):
    """Extrae datos utilizando un selector CSS."""
    soup = BeautifulSoup(html_content, 'html.parser')
    elementos = soup.select(selector)
    return [elemento.text.strip() for elemento in elementos]

def extraer_datos_filas(html_content):#extra las filas pero de las actividades autènticas
    """
    Extrae el texto de las etiquetas <th> y <td> dentro de cada <tr>.

    Args:
        html_content: El código HTML del cual extraer la información.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    filas = soup.find_all('tr')
    datos = []  # Inicializamos una lista vacía para almacenar los datos
    for fila in filas:
        th = fila.find('th')
        td = fila.find('td')
        if th and td:
            datos.append([th.text.strip(), td.text.strip()])  # Agregamos los datos como una lista dentro de la lista 'datos'
    return datos
            
def extraer_datos_tabla(html_content):
    """
    Extrae el nombre de la etiqueta <label> y el contenido de las celdas
    "cell c2", "cell c4" y "cell c5" de la misma fila de la tabla.

    Args:
    html_content: El código HTML del cual extraer la información.

    Returns:
    Una lista de tuplas, donde cada tupla contiene:
    - El nombre extraído de la etiqueta <label>.
    - El contenido de la celda "cell c2".
    - El contenido de la celda "cell c4".
    - El contenido de la celda "cell c5".
    """
    headers = ["Nombre", "Correo", "Grupo", "Último acceso"] # Definir headers aquí
    soup = BeautifulSoup(html_content, 'html.parser')
    datos_status = []
    for label in soup.find_all('label', attrs={'for': True, 'class': 'accesshide'}):
        # Extraer el nombre del label
        nombre = label.text.replace("Seleccionar ", "").replace("'", "")

        # Encontrar la fila de la tabla (<tr>) a la que pertenece el label
        fila_tabla = label.find_parent('tr')

        # Extraer el contenido de las celdas
        celda_c2 = fila_tabla.find('td', class_='cell c2').text.strip()
        celda_c4 = fila_tabla.find('td', class_='cell c4').text.strip()
        celda_c5 = fila_tabla.find('td', class_='cell c5').text.strip()

        datos_status.append((nombre, celda_c2, celda_c4, celda_c5))

    return datos_status, headers