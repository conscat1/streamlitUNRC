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

def extraer_datos_articulos(
    html_content: str,
    horas_ventana: int = 36,
    omitir_mismo_autor_que_el_primero: bool = True,
    aceptar_vacio_como_guion: bool = False,   # pon True si el "-" se pinta con CSS/JS y te llega vacío
    separador: str = " - ",
    ventana_lunes_a_viernes: bool = True     # NUEVO: si True, solo cuenta tiempo hábil (L–V)
):
    """
    Extrae artículos sin calificación (ratingcount = '-') y devuelve lista de dicts.

    Si ventana_lunes_a_viernes=True, el cálculo de horas transcurridas entre la fecha de publicación
    y 'ahora' ignora por completo sábados y domingos (cuenta 24h por cada día L–V).
    """

    # --- helper interno: segundos hábiles (L–V) entre dos datetimes ---
    def segundos_habiles_entre(inicio: datetime, fin: datetime) -> float:
        """
        Cuenta segundos transcurridos ignorando sábados y domingos.
        Cada día hábil aporta hasta 24h (no restringe a horario laboral).
        """
        if fin <= inicio:
            return 0.0

        # Asegura TZ aware (UTC) para consistencia
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)
        if fin.tzinfo is None:
            fin = fin.replace(tzinfo=timezone.utc)

        cur = inicio
        total = 0.0
        while cur < fin:
            # Inicio del siguiente día
            siguiente_dia = (cur + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            tramo_fin = min(fin, siguiente_dia)
            # 0=lunes ... 6=domingo
            if cur.weekday() < 5:  # L–V
                total += (tramo_fin - cur).total_seconds()
            cur = tramo_fin
        return total

    soup = BeautifulSoup(html_content, 'html.parser')
    articulos = soup.find_all('article')
    resultados = []
    if not articulos:
        return resultados  # lista vacía

    # Autor de referencia (si existe) para omitir duplicados si lo deseas
    primer_articulo = articulos[0]
    div_nombre_primero = primer_articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
    autor_referencia = (div_nombre_primero.find('a').get_text(strip=True)
                        if div_nombre_primero and div_nombre_primero.find('a') else None)

    for articulo in articulos:
        div_nombre = articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
        autor_actual = (div_nombre.find('a').get_text(strip=True)
                        if div_nombre and div_nombre.find('a') else None)

        if omitir_mismo_autor_que_el_primero and autor_referencia and autor_actual == autor_referencia:
            continue

        # --- detección robusta de "sin calificación" ---
        rc = articulo.find('span', class_='ratingcount')
        txt = rc.get_text(strip=True).replace('\u00a0', ' ') if rc else ''
        sin_calificacion = bool(DASHES_RE.match(txt)) or (aceptar_vacio_como_guion and txt == '')
        if not sin_calificacion:
            continue

        # --- ventana de tiempo (con opción L–V) ---
        dentro_de_tiempo = True
        tiempo = articulo.find('time')
        fecha_txt = tiempo.get_text(strip=True) if tiempo else None
        datetime_tiempo = tiempo.get('datetime') if tiempo else None

        if datetime_tiempo:
            try:
                fecha_publicacion = datetime.fromisoformat(datetime_tiempo.replace('Z', '+00:00'))
                ahora = datetime.now(timezone.utc)

                if ventana_lunes_a_viernes:
                    segundos = segundos_habiles_entre(fecha_publicacion, ahora)
                    horas_transcurridas = segundos / 3600.0
                else:
                    horas_transcurridas = (ahora - fecha_publicacion).total_seconds() / 3600.0

                if horas_transcurridas > float(horas_ventana):
                    dentro_de_tiempo = False
            except ValueError:
                # fecha no convertible: deja dentro_de_tiempo=True por defecto
                pass

        # --- construcción del nombre SIN "de" pegado ---
        autor_txt = (div_nombre.find('a').get_text(strip=True)
                     if div_nombre and div_nombre.find('a') else None)

        if autor_txt and fecha_txt:
            nombre = f"{autor_txt}{separador}{fecha_txt}"
        elif autor_txt:
            nombre = autor_txt
        elif div_nombre:
            # Fallback conservador si no hay <a>: limpia "por " o "de" pegado a mayúscula
            raw = div_nombre.get_text(separator=' ', strip=True)
            raw = re.sub(r'^\s*por\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'^\s*de(?=[A-ZÁÉÍÓÚÑ])', '', raw)
            nombre = raw or "Nombre no encontrado"
        else:
            nombre = "Nombre no encontrado"

        resultados.append({
            "nombre": nombre,
            "dentro_de_tiempo": dentro_de_tiempo
        })

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