import flet as ft
import os
import asyncio
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from design_constants import (
    COLOR_BOTON,
    COLOR_BOTON_HOVER,
    COLOR_ENTRADA_OSCURA,
    COLOR_BARRA_LATERAL_CHAT,
    COLOR_FONDO_CHAT,
    COLOR_HEADER_CHAT,
    COLOR_TEXTO_CHAT,
    COLOR_TEXTO_ALIAS
)

load_dotenv()


class FletChatApp:
    """
    Aplicación de Chat usando Flet con Material Design 3.
    Interfaz traducida desde CustomTkinter manteniendo la estructura visual.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.alias = ""
        
    
    async def summarize_chat(self, history: list[str]) -> str:
        """Genera un resumen del historial de chat usando IBM watsonx.ai"""
        try:
            api_key = os.getenv("WATSONX_API_KEY")
            project_id = os.getenv("WATSONX_PROJECT_ID")
            url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
            
            if not api_key or not project_id:
                return "❌ Error: Configura WATSONX_API_KEY y WATSONX_PROJECT_ID en .env"
            
            credentials = {
                "url": url,
                "apikey": api_key
            }
            
            client = APIClient(credentials)
            
            conversation_text = "\n".join(history[-20:])
            
            prompt = f"""Eres un asistente de secretaría técnica. Resume la siguiente conversación de chat empresarial.
Ignora mensajes de sistema como [ENTRÓ], [SALIÓ].
Enumera los puntos clave y decisiones importantes.
Sé breve y profesional en español.

Conversación:
{conversation_text}

Resumen:"""
            
            model = ModelInference(
                model_id="meta-llama/llama-3-70b-instruct",
                api_client=client,
                project_id=project_id,
                params={
                    GenParams.MAX_NEW_TOKENS: 500,
                    GenParams.TEMPERATURE: 0.7,
                    GenParams.TOP_P: 0.9
                }
            )
            
            response = model.generate_text(prompt=prompt)
            
            if isinstance(response, dict):
                return response.get("results", [{}])[0].get("generated_text", str(response))
            return str(response)
            
        except Exception as e:
            return f"❌ Error al generar resumen: {str(e)}"
        # Configuración de la página
        self._setup_page()
        
        # Componentes principales con type hints
        self.message_list: ft.ListView
        self.message_input: ft.TextField
        self.send_button: ft.ElevatedButton
        
        # Construir interfaz
        self._build_ui()
    
    def _setup_page(self):
        """Configura las propiedades básicas de la página"""
        self.page.title = "Chat Seguro - Flet Material Design 3"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        
        # Tema personalizado con Material Design 3
        self.page.theme = ft.Theme(
            color_scheme_seed=COLOR_BOTON,
            use_material3=True,
        )
        
        # Colores personalizados para tema oscuro
        self.page.bgcolor = COLOR_FONDO_CHAT
        
        # Tamaño de ventana (API moderna de Flet)
        self.page.window.width = 900
        self.page.window.height = 600
        self.page.window.min_width = 400
        self.page.window.min_height = 400
    
    def _build_ui(self):
        """Construye la interfaz principal del chat"""
        
        # Contenedor principal con tema oscuro
        main_container = ft.Container(
            content=ft.Row(
                controls=[
                    # Barra lateral izquierda (20% del ancho)
                    self._build_sidebar(),
                    
                    # Área central del chat (80% del ancho)
                    self._build_chat_area(),
                ],
                spacing=0,
                expand=True,
            ),
            bgcolor=COLOR_FONDO_CHAT,
            expand=True,
        )
        
        self.page.add(main_container)
    
    def _build_sidebar(self):
        """Construye la barra lateral con lista de salas"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Encabezado de la barra lateral
                    ft.Container(
                        content=ft.Text(
                            "Salas",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO_CHAT,
                        ),
                        padding=ft.padding.all(20),
                        bgcolor=COLOR_BARRA_LATERAL_CHAT,
                    ),
                    
                    # Lista de salas (scrollable)
                    ft.Container(
                        content=ft.ListView(
                            controls=[
                                self._create_room_button("General"),
                                self._create_room_button("Desarrollo"),
                                self._create_room_button("Soporte"),
                                self._create_room_button("Anuncios"),
                            ],
                            spacing=5,
                            padding=ft.padding.all(10),
                        ),
                        expand=True,
                        bgcolor=COLOR_BARRA_LATERAL_CHAT,
                    ),
                    
                    # Botón de salir en la parte inferior
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.ElevatedButton(
                                    "🤖 Resumir Chat",
                                    bgcolor="#0078D4",
                                    color=COLOR_TEXTO_CHAT,
                                    width=180,
                                    on_click=self._on_summarize_click,
                                ),
                                ft.ElevatedButton(
                                    "Salir",
                                    bgcolor="#B00020",
                                    color=COLOR_TEXTO_CHAT,
                                    width=180,
                                    on_click=self._on_logout,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=COLOR_BARRA_LATERAL_CHAT,
                    ),
                ],
                spacing=0,
            ),
            width=200,
            bgcolor=COLOR_BARRA_LATERAL_CHAT,
            expand=False,
        )
    
    def _create_room_button(self, room_name: str):
        """Crea un botón para una sala de chat"""
        return ft.TextButton(
            content=ft.Container(
                content=ft.Text(
                    room_name,
                    size=14,
                    color=COLOR_TEXTO_CHAT,
                ),
                padding=ft.padding.symmetric(horizontal=15, vertical=10),
            ),
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "transparent",
                    ft.ControlState.HOVERED: COLOR_ENTRADA_OSCURA,
                },
                overlay_color="transparent",
            ),
            on_click=lambda e, room=room_name: self._on_room_click(room),
        )
    
    def _build_chat_area(self):
        """Construye el área central del chat"""
        
        # Header del chat
        chat_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "#",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_ALIAS,
                    ),
                    ft.Text(
                        "General",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_CHAT,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(15),
            bgcolor=COLOR_HEADER_CHAT,
        )
        
        # Área de mensajes fijados
        pinned_message = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "📌 FIJADO:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#FFA500",
                    ),
                    ft.Text(
                        "(Ningún mensaje fijado)",
                        size=12,
                        italic=True,
                        color="#AAAAAA",
                    ),
                ],
                spacing=5,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            bgcolor="#2B3A42",
        )
        
        # ListView para mensajes (80% de la pantalla)
        self.message_list = ft.ListView(
            controls=[
                self._create_system_message("Bienvenido al chat"),
                self._create_message("Usuario1", "Hola a todos!"),
                self._create_message("Usuario2", "¿Cómo están?"),
                self._create_system_message("Usuario3 se ha unido a la sala"),
            ],
            spacing=10,
            padding=ft.padding.all(15),
            expand=True,
            auto_scroll=True,
        )
        
        # Contenedor de mensajes con scroll
        messages_container = ft.Container(
            content=self.message_list,
            bgcolor=COLOR_FONDO_CHAT,
            expand=True,
        )
        
        # Campo de entrada y botón de envío
        input_area = self._build_input_area()
        
        # Columna principal del área de chat
        return ft.Container(
            content=ft.Column(
                controls=[
                    chat_header,
                    pinned_message,
                    messages_container,
                    input_area,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=COLOR_FONDO_CHAT,
        )
    
    def _build_input_area(self):
        """Construye el área de entrada de mensajes"""
        
        # Campo de texto para escribir mensajes
        self.message_input = ft.TextField(
            hint_text="Escribe un mensaje... (/help para comandos)",
            hint_style=ft.TextStyle(color="#999999"),
            text_style=ft.TextStyle(color=COLOR_TEXTO_CHAT, size=14),
            border_color=COLOR_ENTRADA_OSCURA,
            focused_border_color=COLOR_BOTON,
            bgcolor=COLOR_HEADER_CHAT,
            multiline=False,
            max_lines=1,
            expand=True,
            on_submit=self._on_send_message,
            text_size=14,
        )
        
        # Botón de envío
        self.send_button = ft.ElevatedButton(
            "Enviar",
            bgcolor=COLOR_BOTON,
            color=COLOR_TEXTO_CHAT,
            height=50,
            on_click=self._on_send_message,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: COLOR_BOTON_HOVER,
                },
            ),
        )
        
        # Contenedor del área de entrada
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.message_input,
                    self.send_button,
                ],
                spacing=10,
            ),
            padding=ft.padding.all(15),
            bgcolor=COLOR_FONDO_CHAT,
        )
    
    def _create_message(self, username: str, message: str):
        """Crea un mensaje de usuario"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"{username}:",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_ALIAS,
                    ),
                    ft.Text(
                        message,
                        size=13,
                        color=COLOR_TEXTO_CHAT,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )
    
    def _create_system_message(self, message: str):
        """Crea un mensaje del sistema"""
        return ft.Container(
            content=ft.Text(
                f"[SISTEMA] {message}",
                size=12,
                italic=True,
                color="#999999",
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )
    
    def _on_send_message(self, e):
        """Maneja el envío de mensajes"""
        if self.message_input.value and self.message_input.value.strip():
            message_text = self.message_input.value.strip()
            
            # Agregar mensaje a la lista
            new_message = self._create_message(self.alias or "Tú", message_text)
            self.message_list.controls.append(new_message)
            
            # Limpiar campo de entrada
            self.message_input.value = ""
            
            # Actualizar la página
            self.page.update()
            
            # Aquí iría la lógica de red para enviar el mensaje
            print(f"Mensaje enviado: {message_text}")
    
    def _on_room_click(self, room_name: str):
        """Maneja el clic en una sala"""
    
    async def _on_summarize_click(self, e):
        """Maneja el clic en el botón de resumir chat"""
        history = []
        for control in self.message_list.controls:
            if isinstance(control, ft.Container) and hasattr(control, 'content'):
                content = control.content
                if isinstance(content, ft.Column) and hasattr(content, 'controls'):
                    for text_control in content.controls:
                        if isinstance(text_control, ft.Text) and text_control.value:
                            history.append(text_control.value)
        
        if not history:
            self.message_list.controls.append(
                self._create_system_message("No hay mensajes para resumir")
            )
            self.page.update()
            return
        
        self.message_list.controls.append(
            self._create_system_message("🤖 Generando resumen con IBM watsonx.ai...")
        )
        self.page.update()
        
        summary = await self.summarize_chat(history)
        
        self.message_list.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "✨ RESUMEN IA (IBM watsonx.ai)",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color="#00FF7F",
                        ),
                        ft.Text(
                            summary,
                            size=13,
                            color=COLOR_TEXTO_CHAT,
                        ),
                    ],
                    spacing=5,
                ),
                padding=ft.padding.all(15),
                bgcolor="#1E3A2F",
                border_radius=8,
            )
        )
        self.page.update()
    
    async def _on_logout(self, e):
        """Maneja el cierre de sesión"""
        print("Cerrando sesión...")
        # Aquí iría la lógica de desconexión
        await self.page.window.close()


def main(page: ft.Page):
    """Función principal de la aplicación Flet"""
    app = FletChatApp(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    ft.app(target=main)

# Made with Bob
