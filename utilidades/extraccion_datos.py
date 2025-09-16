# utilidades/extraccion_datos.py
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone, time
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
    horas_ventana: int = 36,                 # UMBRAL 2 → rojo (>=)
    horas_ventana_1: int = 24,               # UMBRAL 1 → naranja (>=)
    omitir_mismo_autor_que_el_primero: bool = True,
    aceptar_vacio_como_guion: bool = False,  # True si el "-" lo pinta el front y llega vacío
    separador: str = " - ",
    ventana_lunes_a_viernes: bool = True,   # True: ignora fines de semana en el conteo
    local_utc_offset_hours: int = -6         # Hora local si el datetime no trae tz / para convertir desde UTC
):
    """
    Reglas de tiempo y color:
    - Si ventana_lunes_a_viernes = False → horas NATURALES (incluyen fines de semana).
    - Si ventana_lunes_a_viernes = True  → horas NATURALES SOLO en días laborales (L–V, 24h/día).
      * Si la publicación fue sábado/domingo, el conteo inicia el lunes a la MISMA hora local.

    Colores:
    - 'rojo'    si horas_ref >= horas_ventana        (p.ej., 36)
    - 'naranja' si NO rojo y horas_ref >= horas_ventana_1 (p.ej., 24)
    - 'default' en caso contrario

    'dentro_de_tiempo' se mantiene por compatibilidad (usa el umbral "grande").
    """

    # ------------------------ Helpers de zona horaria (LOCAL) ------------------------
    def _tz_local():
        return timezone(timedelta(hours=local_utc_offset_hours))

    def parse_to_local(dt_str: str) -> datetime | None:
        """
        Convierte la cadena ISO a datetime en zona local:
        - Si termina con 'Z' (UTC) o trae offset → convierte a LOCAL.
        - Si no trae tz → asume LOCAL.
        """
        if not dt_str:
            return None
        s = dt_str.strip()
        try:
            if s.endswith('Z'):
                dt = datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(_tz_local())
            else:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=_tz_local())
                else:
                    dt = dt.astimezone(_tz_local())
            return dt
        except Exception:
            return None

    # Si cae en finde, mover al LUNES MISMA HORA (en LOCAL)
    def mover_a_lunes_misma_hora_local(dt_local: datetime) -> datetime:
        if dt_local.weekday() < 5:
            return dt_local
        dias_a_lunes = (7 - dt_local.weekday()) % 7
        if dias_a_lunes == 0:
            dias_a_lunes = 1
        nuevo_dia = (dt_local + timedelta(days=dias_a_lunes)).date()
        return datetime.combine(nuevo_dia, dt_local.timetz())

    # Segundos "hábiles" L–V (24h/día) entre dos datetimes LOCAL,
    # arrancando el conteo el lunes MISMA HORA si inicio fue finde
    def segundos_habiles_local(inicio_local: datetime, fin_local: datetime) -> float:
        if fin_local <= inicio_local:
            return 0.0
        cur = mover_a_lunes_misma_hora_local(inicio_local)
        if fin_local <= cur:
            return 0.0

        total = 0.0
        while cur < fin_local:
            # fin del día actual (medianoche local)
            siguiente_dia = datetime.combine(
                (cur + timedelta(days=1)).date(),
                time(0, 0, 0, tzinfo=cur.tzinfo)
            )
            tramo_fin = min(fin_local, siguiente_dia)
            if cur.weekday() < 5:  # 0..4 = L–V
                total += (tramo_fin - cur).total_seconds()
            cur = tramo_fin
        return total

    # ------------------------ Parse HTML ------------------------
    soup = BeautifulSoup(html_content, 'html.parser')
    articulos = soup.find_all('article')
    resultados = []
    if not articulos:
        return resultados

    # Autor de referencia (si existe) para omitir duplicados si lo deseas
    primer_articulo = articulos[0]
    div_nombre_primero = primer_articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
    autor_referencia = (div_nombre_primero.find('a').get_text(strip=True)
                        if div_nombre_primero and div_nombre_primero.find('a') else None)

    # Hora "ahora" en LOCAL (clave para coherencia con días L–V)
    ahora_local = datetime.now(_tz_local())

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

        # --- tiempos y estado ---
        dentro_de_tiempo = True
        estado = "default"
        horas_ref = None
        horas_naturales = None
        horas_habiles = None

        tiempo = articulo.find('time')
        fecha_txt = tiempo.get_text(strip=True) if tiempo else None
        dt_attr = tiempo.get('datetime') if tiempo else None

        if dt_attr:
            fecha_local = parse_to_local(dt_attr)
            if fecha_local:
                # NATURALES: diferencia local directa
                horas_naturales = (ahora_local - fecha_local).total_seconds() / 3600.0

                # HÁBILES L–V: arrancando lunes MISMA HORA si finde
                horas_habiles = segundos_habiles_local(fecha_local, ahora_local) / 3600.0

                # Selección según flag
                horas_ref = horas_habiles if ventana_lunes_a_viernes else horas_naturales

                # Compatibilidad: dentro_de_tiempo con el umbral grande
                # (si quieres que 36h exactas ya NO estén "dentro", cambia <= por <)
                dentro_de_tiempo = (horas_ref is None) or (horas_ref <= float(horas_ventana))

                # Colores (umbral inclusivo, como pediste: "han pasado 24/36 horas")
                if horas_ref is not None:
                    if horas_ref >= float(horas_ventana):
                        estado = "rojo"
                    elif horas_ref >= float(horas_ventana_1):
                        estado = "naranja"
                    else:
                        estado = "default"

        # --- construcción del nombre SIN "de" pegado ---
        autor_txt = (div_nombre.find('a').get_text(strip=True)
                     if div_nombre and div_nombre.find('a') else None)

        if autor_txt and fecha_txt:
            nombre = f"{autor_txt}{separador}{fecha_txt}"
        elif autor_txt:
            nombre = autor_txt
        elif div_nombre:
            raw = div_nombre.get_text(separator=' ', strip=True)
            raw = re.sub(r'^\s*por\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'^\s*de(?=[A-ZÁÉÍÓÚÑ])', '', raw)
            nombre = raw or "Nombre no encontrado"
        else:
            nombre = "Nombre no encontrado"

        resultados.append({
            "nombre": nombre,
            "dentro_de_tiempo": dentro_de_tiempo,  # retrocompatible
            "estado": estado,                       # 'default' | 'naranja' | 'rojo'
            "horas_referencia": horas_ref,          # la usada para colorear (depende del flag)
            "horas_naturales": horas_naturales,
            "horas_habiles": horas_habiles
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