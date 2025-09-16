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



# --- Importaciones necesarias ---
import re
from datetime import datetime, time, timedelta
# zoneinfo es la forma moderna y recomendada para manejar zonas horarias (Python 3.9+)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bs4 import BeautifulSoup

# --- CONSTANTES ---
# Es buena práctica definir valores fijos como constantes para mayor claridad.
SEGUNDOS_POR_HORA = 3600.0
DIAS_LABORALES_POR_SEMANA = 5
SEGUNDOS_DIA_LABORAL = 24 * SEGUNDOS_POR_HORA
DASHES_RE = re.compile(r'^[\s\u00a0—-]*$')

# ==============================================================================
# 1. FUNCIONES AUXILIARES DE TIEMPO (Refactorizadas fuera de la función principal)
#    Esto mejora la legibilidad, permite pruebas y su reutilización.
# ==============================================================================

def obtener_tz_local(tz_name: str = 'America/Mexico_City') -> ZoneInfo:
    """
    Obtiene un objeto de zona horaria a partir de un nombre IANA.
    Maneja el horario de verano automáticamente.
    """
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # Si la zona horaria no es válida, regresa UTC como fallback seguro.
        return ZoneInfo('UTC')

def parse_to_local(dt_str: str, tz_local: ZoneInfo) -> datetime | None:
    """
    Convierte una cadena de fecha ISO a un objeto datetime en la zona horaria local especificada.
    """
    if not dt_str:
        return None
    try:
        # El método fromisoformat es robusto.
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        # Si no tiene zona horaria, se asume que ya estaba en hora local.
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz_local)
        # Si tiene zona horaria (ej. UTC), se convierte a la local.
        return dt.astimezone(tz_local)
    except (ValueError, TypeError):
        return None

def mover_a_lunes_siguiente(dt: datetime) -> datetime:
    """
    Si una fecha cae en fin de semana, la mueve al lunes siguiente a la misma hora.
    """
    if dt.weekday() >= 5:  # 5: Sábado, 6: Domingo
        dias_para_lunes = 7 - dt.weekday()
        return dt + timedelta(days=dias_para_lunes)
    return dt

def calcular_horas_habiles(inicio_local: datetime, fin_local: datetime) -> float:
    """
    Calcula las horas hábiles (L-V) entre dos momentos, de forma eficiente y sin bucles.
    Si la fecha de inicio es un fin de semana, el conteo empieza el lunes siguiente.
    """
    if fin_local <= inicio_local:
        return 0.0

    # 1. Ajustar la fecha de inicio si cae en fin de semana.
    cur = mover_a_lunes_siguiente(inicio_local)
    if fin_local <= cur:
        return 0.0

    total_segundos = 0

    # 2. Manejar días completos entre las fechas.
    # Se normalizan las fechas a medianoche para contar días enteros.
    dia_inicio_normalizado = datetime.combine(cur.date(), time(0), tzinfo=cur.tzinfo)
    dia_fin_normalizado = datetime.combine(fin_local.date(), time(0), tzinfo=fin_local.tzinfo)
    
    # Calcular segundos del primer día parcial (desde `cur` hasta medianoche)
    if cur.weekday() < 5:
        siguiente_medianoche = dia_inicio_normalizado + timedelta(days=1)
        total_segundos += (min(fin_local, siguiente_medianoche) - cur).total_seconds()

    # Calcular segundos de los días completos intermedios
    dias_intermedios = (dia_fin_normalizado - (dia_inicio_normalizado + timedelta(days=1))).days
    if dias_intermedios > 0:
        # np.busday_count es ideal para esto, pero para no agregar dependencias:
        dias_habiles_completos = 0
        for i in range(dias_intermedios):
            dia = (dia_inicio_normalizado + timedelta(days=i + 1))
            if dia.weekday() < 5:
                dias_habiles_completos += 1
        total_segundos += dias_habiles_completos * SEGUNDOS_DIA_LABORAL

    # Calcular segundos del último día parcial (desde medianoche hasta `fin_local`)
    # Solo si el día final es diferente al de inicio.
    if fin_local.date() > cur.date() and fin_local.weekday() < 5:
        total_segundos += (fin_local - dia_fin_normalizado).total_seconds()

    return total_segundos / SEGUNDOS_POR_HORA

# ==============================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# ==============================================================================

def extraer_datos_articulos_revisado(
    html_content: str,
    horas_ventana_rojo: int = 36,
    horas_ventana_naranja: int = 24,
    omitir_mismo_autor_que_el_primero: bool = True,
    zona_horaria: str = 'America/Mexico_City' # Parámetro flexible para la zona horaria
):
    """
    Versión refactorizada que usa manejo de zonas horarias robusto y una estructura más clara.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articulos = soup.find_all('article')
    if not articulos:
        return []

    # Se obtiene la zona horaria una sola vez.
    tz_local = obtener_tz_local(zona_horaria)
    ahora_local = datetime.now(tz_local)
    
    resultados = []
    
    autor_referencia_div = articulos[0].select_one('div.mb-3[tabindex="-1"], div.mb-3')
    autor_referencia = autor_referencia_div.find('a').get_text(strip=True) if autor_referencia_div and autor_referencia_div.find('a') else None

    for articulo in articulos:
        div_nombre = articulo.select_one('div.mb-3[tabindex="-1"], div.mb-3')
        autor_actual_a = div_nombre.find('a') if div_nombre else None
        autor_actual = autor_actual_a.get_text(strip=True) if autor_actual_a else "Autor Desconocido"

        if omitir_mismo_autor_que_el_primero and autor_referencia and autor_actual == autor_referencia:
            continue

        rating_span = articulo.find('span', class_='ratingcount')
        rating_text = rating_span.get_text(strip=True).replace('\u00a0', ' ') if rating_span else ''
        if not (DASHES_RE.match(rating_text) or rating_text == ''):
            continue

        estado = "default"
        horas_habiles = None
        
        tiempo_tag = articulo.find('time')
        dt_attr = tiempo_tag.get('datetime') if tiempo_tag else None

        if dt_attr:
            fecha_publicacion_local = parse_to_local(dt_attr, tz_local)
            
            if fecha_publicacion_local:
                # El cálculo de horas naturales es simple
                horas_naturales = (ahora_local - fecha_publicacion_local).total_seconds() / SEGUNDOS_POR_HORA
                
                # El cálculo de horas hábiles ahora usa la función optimizada.
                # Tu lógica original con el flag `ventana_lunes_a_viernes` está implícita aquí.
                # Para mantenerla explícita, podrías hacer:
                # horas_ref = calcular_horas_habiles(...) if ventana_lunes_a_viernes else horas_naturales
                
                horas_habiles = calcular_horas_habiles(fecha_publicacion_local, ahora_local)

                # Asignación de estado basada en horas hábiles
                if horas_habiles >= horas_ventana_rojo:
                    estado = "rojo"
                elif horas_habiles >= horas_ventana_naranja:
                    estado = "naranja"
        
        # Construcción del resultado
        fecha_txt = tiempo_tag.get_text(strip=True) if tiempo_tag else "Fecha Desconocida"
        nombre = f"{autor_actual} - {fecha_txt}"

        resultados.append({
            "nombre": nombre,
            "estado": estado,
            "horas_habiles_calculadas": round(horas_habiles, 2) if horas_habiles is not None else None,
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