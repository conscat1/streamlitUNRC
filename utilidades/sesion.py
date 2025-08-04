#utilidades/sesion.py
import aiohttp
import re
async def login_to_site(session: aiohttp.ClientSession, login_url: str, username: str, password: str) -> bool:
            """Realiza el inicio de sesión en el sitio web."""
            try:
                print(f"Intentando acceder a la página de login: {login_url}")
                async with session.get(login_url) as response:
                    if response.status != 200:
                        print(f"Error al acceder a la página de login. Status: {response.status}")
                        return False

                    html = await response.text()

                    login_data = {
                        "username": username,
                        "password": password,
                        "anchor": "",
                        "logintoken": "",
                    }

                    if "logintoken" in html:
                        token_match = re.search(r'name="logintoken" value="([^"]+)"', html)
                        if token_match:
                            login_data["logintoken"] = token_match.group(1)
                            print("Token de login encontrado y agregado a los datos de login")
                        else:
                            print("No se pudo encontrar el token de login")
                            return False

                    async with session.post(login_url, data=login_data, allow_redirects=True) as login_response:
                        response_text = await login_response.text()
                        is_logged_in = not ("Invalid login" in response_text or "Acceso denegado" in response_text)

                        if is_logged_in:
                            print("Login exitoso")
                        else:
                            print("Login fallido - Credenciales incorrectas")

                        return is_logged_in
            except Exception as e:
                print(f"Error durante el login: {str(e)}")
                return False
