#utilidades/obtener_contenido.py
import aiohttp
from typing import Optional

async def fetch_url(session: aiohttp.ClientSession, url: str) -> Optional[str]:
            """Obtiene el contenido de una URL de forma asíncrona."""
            try:
                print(f"Intentando obtener contenido de: {url}")
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Error al obtener la URL {url}. Status: {response.status}")
                        return None
                    return await response.text()
            except Exception as e:
                print(f"Error al obtener {url}: {str(e)}")
                return None