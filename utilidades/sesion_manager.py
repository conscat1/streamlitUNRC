# utilidades/sesion_manager.py
import aiohttp
from .sesion import login_to_site

class SesionManager:
    def __init__(self):
        self.session = None

    async def iniciar_sesion(self, login_url, username, password):
        """Inicia sesión y crea una sesión autenticada."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            login_exitoso = await login_to_site(self.session, login_url, username, password)
            if not login_exitoso:
                await self.session.close()
                self.session = None
        return self.session is not None

    async def obtener_sesion(self):
        """Devuelve la sesión si está autenticada, None en caso contrario."""
        return self.session

    async def cerrar_sesion(self):
        """Cierra la sesión."""
        if self.session:
            await self.session.close()
            self.session = None