import flet as ft
import os
import asyncio
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from typing import Optional, Callable, List
from datetime import datetime

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


# ============================================================================
# CONFIGURATION CLASS - Centralized API Configuration
# ============================================================================
class AppConfig:
    """Centralized configuration for API endpoints and app settings"""
    
    def __init__(self):
        self.watsonx_api_key = os.getenv("WATSONX_API_KEY")
        self.watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
        self.watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.api_endpoint = os.getenv("API_ENDPOINT", "http://localhost:8000")
        
    def is_watsonx_configured(self) -> bool:
        """Check if watsonx.ai is properly configured"""
        return bool(self.watsonx_api_key and self.watsonx_project_id)
    
    def is_auth_configured(self) -> bool:
        """Check if JWT authentication is configured"""
        return bool(self.jwt_secret)


# ============================================================================
# COMPONENT CLASSES - Modular Reactive Architecture
# ============================================================================

class LoadingIndicator(ft.Container):
    """Reusable loading indicator component with animation"""
    
    def __init__(self, message: str = "Cargando..."):
        self.message = message
        super().__init__(
            content=self._build_content(),
            padding=ft.padding.all(20),
            alignment=ft.alignment.center,
        )
        
    def _build_content(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=40,
                        height=40,
                        stroke_width=4,
                        color=COLOR_BOTON,
                    ),
                    ft.Text(
                        self.message,
                        size=14,
                        color=COLOR_TEXTO_CHAT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=ft.padding.all(20),
            alignment=ft.alignment.center,
        )


class NotificationBanner(ft.UserControl):
    """Notification banner for user feedback"""
    
    def __init__(self, message: str, notification_type: str = "info"):
        super().__init__()
        self.message = message
        self.notification_type = notification_type
        
    def build(self):
        colors = {
            "info": "#0078D4",
            "success": "#107C10",
            "warning": "#FF8C00",
            "error": "#D13438",
        }
        
        icons = {
            "info": ft.icons.INFO_OUTLINED,
            "success": ft.icons.CHECK_CIRCLE_OUTLINED,
            "warning": ft.icons.WARNING_AMBER_OUTLINED,
            "error": ft.icons.ERROR_OUTLINE,
        }
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        icons.get(self.notification_type, ft.icons.INFO_OUTLINED),
                        color="white",
                        size=20,
                    ),
                    ft.Text(
                        self.message,
                        size=13,
                        color="white",
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=colors.get(self.notification_type, colors["info"]),
            padding=ft.padding.all(12),
            border_radius=8,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        )


class MessageBubble(ft.UserControl):
    """Enhanced message bubble component with timestamps and actions"""
    
    def __init__(self, username: str, message: str, timestamp: Optional[str] = None, 
                 is_own: bool = False, on_pin: Optional[Callable] = None):
        super().__init__()
        self.username = username
        self.message = message
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.is_own = is_own
        self.on_pin = on_pin
        
    def build(self):
        message_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"{self.username}",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_BOTON if self.is_own else COLOR_TEXTO_ALIAS,
                        ),
                        ft.Text(
                            self.timestamp,
                            size=11,
                            color="#999999",
                        ),
                    ],
                    spacing=10,
                ),
                ft.Text(
                    self.message,
                    size=13,
                    color=COLOR_TEXTO_CHAT,
                    selectable=True,
                ),
            ],
            spacing=4,
        )
        
        # Add action buttons on hover
        actions = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.PUSH_PIN_OUTLINED,
                    icon_size=16,
                    tooltip="Fijar mensaje",
                    on_click=self.on_pin,
                    icon_color="#999999",
                ),
                ft.IconButton(
                    icon=ft.icons.REPLY,
                    icon_size=16,
                    tooltip="Responder",
                    icon_color="#999999",
                ),
            ],
            spacing=0,
            visible=False,
        )
        
        container = ft.Container(
            content=ft.Row(
                controls=[message_content, actions],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            border_radius=8,
            bgcolor="transparent",
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=lambda e: self._toggle_actions(e, actions),
        )
        
        return container
    
    def _toggle_actions(self, e, actions):
        """Toggle action buttons visibility on hover"""
        actions.visible = e.data == "true"
        self.update()


class RoomButton(ft.UserControl):
    """Enhanced room button with active state and notifications"""
    
    def __init__(self, room_name: str, is_active: bool = False, 
                 unread_count: int = 0, on_click: Optional[Callable] = None):
        super().__init__()
        self.room_name = room_name
        self.is_active = is_active
        self.unread_count = unread_count
        self.on_click_handler = on_click
        
    def build(self):
        badge = None
        if self.unread_count > 0:
            badge = ft.Container(
                content=ft.Text(
                    str(self.unread_count),
                    size=11,
                    color="white",
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor="#D13438",
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
            )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.icons.TAG,
                        size=18,
                        color=COLOR_BOTON if self.is_active else "#999999",
                    ),
                    ft.Text(
                        self.room_name,
                        size=14,
                        color=COLOR_TEXTO_CHAT if self.is_active else "#CCCCCC",
                        weight=ft.FontWeight.BOLD if self.is_active else ft.FontWeight.NORMAL,
                        expand=True,
                    ),
                    badge if badge else ft.Container(),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=COLOR_ENTRADA_OSCURA if self.is_active else "transparent",
            border_radius=8,
            ink=True,
            on_click=self.on_click_handler,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )


class SearchBar(ft.UserControl):
    """Search bar component for filtering messages"""
    
    def __init__(self, on_search: Optional[Callable] = None):
        super().__init__()
        self.on_search = on_search
        
    def build(self):
        return ft.Container(
            content=ft.TextField(
                hint_text="Buscar mensajes...",
                hint_style=ft.TextStyle(color="#999999", size=13),
                text_style=ft.TextStyle(color=COLOR_TEXTO_CHAT, size=13),
                border_color="transparent",
                focused_border_color=COLOR_BOTON,
                bgcolor=COLOR_ENTRADA_OSCURA,
                prefix_icon=ft.icons.SEARCH,
                on_change=self.on_search,
                height=40,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )


class UserProfileCard(ft.UserControl):
    """User profile card with status indicator"""
    
    def __init__(self, username: str, status: str = "online"):
        super().__init__()
        self.username = username
        self.status = status
        
    def build(self):
        status_colors = {
            "online": "#107C10",
            "away": "#FF8C00",
            "offline": "#999999",
        }
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Stack(
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Text(
                                    self.username[0].upper(),
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color="white",
                                ),
                                bgcolor=COLOR_BOTON,
                                radius=20,
                            ),
                            ft.Container(
                                content=ft.Container(
                                    width=10,
                                    height=10,
                                    bgcolor=status_colors.get(self.status, "#999999"),
                                    border_radius=5,
                                    border=ft.border.all(2, COLOR_BARRA_LATERAL_CHAT),
                                ),
                                right=0,
                                bottom=0,
                            ),
                        ],
                        width=40,
                        height=40,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                self.username,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_TEXTO_CHAT,
                            ),
                            ft.Text(
                                self.status.capitalize(),
                                size=11,
                                color="#999999",
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class FletChatApp:
    """
    Enhanced Chat Application with Material Design 3
    Following IBM Front-end Architecture Guidelines:
    - Reactive Component Architecture
    - Async State Management
    - Token-based Auth Ready (JWT)
    - Centralized Configuration
    - Responsive Design (Flexbox/Grid)
    - Loading States for Async Operations
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.config = AppConfig()
        self.alias = "Usuario"
        self.current_room = "General"
        self.is_loading = False
        self.auth_token: Optional[str] = None
        
        # Component references
        self.message_list: ft.ListView
        self.message_input: ft.TextField
        self.send_button: ft.ElevatedButton
        self.notification_container: ft.Container
        self.pinned_message_text: ft.Text
        self.room_buttons: dict = {}
        
        # Setup and build
        self._setup_page()
        self._build_ui()
        
    def _setup_page(self):
        """Configure page properties with responsive design"""
        self.page.title = "IBM Chat - Secure Communication Platform"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        
        # Material Design 3 theme
        self.page.theme = ft.Theme(
            color_scheme_seed=COLOR_BOTON,
            use_material3=True,
        )
        
        self.page.bgcolor = COLOR_FONDO_CHAT
        
        # Responsive window configuration
        self.page.window.width = 1200
        self.page.window.height = 700
        self.page.window.min_width = 800
        self.page.window.min_height = 500
        
        # Keyboard shortcuts
        self.page.on_keyboard_event = self._handle_keyboard
        
    def _handle_keyboard(self, e: ft.KeyboardEvent):
        """Handle keyboard shortcuts for accessibility"""
        if e.key == "Enter" and e.ctrl:
            self._on_send_message(None)
        elif e.key == "K" and e.ctrl:
            # Focus search bar
            pass
            
    def _build_ui(self):
        """Build the main UI with modular components"""
        
        # Notification area (top)
        self.notification_container = ft.Container(
            content=ft.Column(controls=[], spacing=5),
            padding=ft.padding.all(10),
            visible=False,
        )
        
        # Main layout
        main_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.notification_container,
                    ft.Row(
                        controls=[
                            self._build_sidebar(),
                            self._build_chat_area(),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            bgcolor=COLOR_FONDO_CHAT,
            expand=True,
        )
        
        self.page.add(main_container)
        
    def _build_sidebar(self):
        """Build enhanced sidebar with user profile and room list"""
        
        # User profile section
        user_profile = ft.Container(
            content=UserProfileCard(self.alias, "online"),
            padding=ft.padding.all(10),
            bgcolor=COLOR_BARRA_LATERAL_CHAT,
        )
        
        # Search bar
        search_bar = SearchBar(on_search=self._on_search_rooms)
        
        # Room list
        rooms = ["General", "Desarrollo", "Soporte", "Anuncios", "Proyectos"]
        room_list_controls = []
        
        for room in rooms:
            is_active = room == self.current_room
            unread = 3 if room == "Desarrollo" else 0
            room_btn = RoomButton(
                room_name=room,
                is_active=is_active,
                unread_count=unread,
                on_click=lambda e, r=room: self._on_room_click(r)
            )
            self.room_buttons[room] = room_btn
            room_list_controls.append(room_btn)
        
        room_list = ft.Container(
            content=ft.ListView(
                controls=room_list_controls,
                spacing=5,
                padding=ft.padding.all(10),
            ),
            expand=True,
            bgcolor=COLOR_BARRA_LATERAL_CHAT,
        )
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ElevatedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.AUTO_AWESOME, size=18),
                                ft.Text("Resumir Chat", size=13),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor="#0078D4",
                        color=COLOR_TEXTO_CHAT,
                        width=220,
                        height=45,
                        on_click=self._on_summarize_click,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                    ft.Divider(height=1, color="#444444"),
                    ft.ElevatedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.SETTINGS, size=18),
                                ft.Text("Configuración", size=13),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor="transparent",
                        color=COLOR_TEXTO_CHAT,
                        width=220,
                        height=40,
                        on_click=self._on_settings_click,
                    ),
                    ft.ElevatedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.LOGOUT, size=18),
                                ft.Text("Salir", size=13),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor="#B00020",
                        color=COLOR_TEXTO_CHAT,
                        width=220,
                        height=40,
                        on_click=self._on_logout,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
            bgcolor=COLOR_BARRA_LATERAL_CHAT,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    user_profile,
                    ft.Divider(height=1, color="#444444"),
                    ft.Container(
                        content=ft.Text(
                            "CANALES",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color="#999999",
                        ),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    ),
                    search_bar,
                    room_list,
                    action_buttons,
                ],
                spacing=0,
            ),
            width=250,
            bgcolor=COLOR_BARRA_LATERAL_CHAT,
            expand=False,
        )
        
    def _build_chat_area(self):
        """Build enhanced chat area with header and message list"""
        
        # Chat header with room info
        chat_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.icons.TAG,
                                size=24,
                                color=COLOR_TEXTO_ALIAS,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        self.current_room,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLOR_TEXTO_CHAT,
                                    ),
                                    ft.Text(
                                        "12 miembros • 3 en línea",
                                        size=11,
                                        color="#999999",
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.SEARCH,
                                icon_size=20,
                                tooltip="Buscar en el chat",
                                icon_color="#999999",
                                on_click=self._on_search_messages,
                            ),
                            ft.IconButton(
                                icon=ft.icons.NOTIFICATIONS_OUTLINED,
                                icon_size=20,
                                tooltip="Notificaciones",
                                icon_color="#999999",
                            ),
                            ft.IconButton(
                                icon=ft.icons.INFO_OUTLINE,
                                icon_size=20,
                                tooltip="Información del canal",
                                icon_color="#999999",
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.all(15),
            bgcolor=COLOR_HEADER_CHAT,
            border=ft.border.only(bottom=ft.BorderSide(1, "#444444")),
        )
        
        # Pinned message area
        self.pinned_message_text = ft.Text(
            "(Ningún mensaje fijado)",
            size=12,
            italic=True,
            color="#AAAAAA",
        )
        
        pinned_message = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.PUSH_PIN, size=16, color="#FFA500"),
                    ft.Text(
                        "FIJADO:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#FFA500",
                    ),
                    self.pinned_message_text,
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor="#2B3A42",
            visible=True,
        )
        
        # Message list with sample messages
        self.message_list = ft.ListView(
            controls=[
                self._create_system_message("Bienvenido al canal #General"),
                MessageBubble("Usuario1", "¡Hola a todos! ¿Cómo están?", "10:30", on_pin=self._on_pin_message),
                MessageBubble("Usuario2", "Todo bien, trabajando en el nuevo proyecto", "10:32", on_pin=self._on_pin_message),
                MessageBubble(self.alias, "Excelente, ¿necesitan ayuda?", "10:35", is_own=True, on_pin=self._on_pin_message),
                self._create_system_message("Usuario3 se ha unido al canal"),
            ],
            spacing=8,
            padding=ft.padding.all(15),
            expand=True,
            auto_scroll=True,
        )
        
        messages_container = ft.Container(
            content=self.message_list,
            bgcolor=COLOR_FONDO_CHAT,
            expand=True,
        )
        
        # Enhanced input area
        input_area = self._build_input_area()
        
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
        """Build enhanced input area with formatting options"""
        
        self.message_input = ft.TextField(
            hint_text="Escribe un mensaje... (Ctrl+Enter para enviar)",
            hint_style=ft.TextStyle(color="#999999", size=14),
            text_style=ft.TextStyle(color=COLOR_TEXTO_CHAT, size=14),
            border_color="transparent",
            focused_border_color=COLOR_BOTON,
            bgcolor=COLOR_HEADER_CHAT,
            multiline=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            on_submit=self._on_send_message,
            shift_enter=True,
            content_padding=ft.padding.all(12),
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_size=24,
            bgcolor=COLOR_BOTON,
            icon_color="white",
            tooltip="Enviar mensaje (Ctrl+Enter)",
            on_click=self._on_send_message,
            width=50,
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=25),
            ),
        )
        
        # Formatting toolbar
        toolbar = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.ATTACH_FILE,
                    icon_size=20,
                    tooltip="Adjuntar archivo",
                    icon_color="#999999",
                ),
                ft.IconButton(
                    icon=ft.icons.EMOJI_EMOTIONS_OUTLINED,
                    icon_size=20,
                    tooltip="Emojis",
                    icon_color="#999999",
                ),
                ft.IconButton(
                    icon=ft.icons.GIF_BOX_OUTLINED,
                    icon_size=20,
                    tooltip="GIF",
                    icon_color="#999999",
                ),
            ],
            spacing=5,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                toolbar,
                            ],
                        ),
                        padding=ft.padding.symmetric(horizontal=15, vertical=5),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.message_input,
                                self.send_button,
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=COLOR_FONDO_CHAT,
            border=ft.border.only(top=ft.BorderSide(1, "#444444")),
        )
        
    def _create_system_message(self, message: str):
        """Create a system message"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.INFO_OUTLINE, size=14, color="#999999"),
                    ft.Text(
                        message,
                        size=12,
                        italic=True,
                        color="#999999",
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )
        
    def _show_notification(self, message: str, notification_type: str = "info"):
        """Show notification banner"""
        notification = NotificationBanner(message, notification_type)
        self.notification_container.content.controls.append(notification)
        self.notification_container.visible = True
        self.page.update()
        
        # Auto-hide after 3 seconds
        async def hide_notification():
            await asyncio.sleep(3)
            if notification in self.notification_container.content.controls:
                self.notification_container.content.controls.remove(notification)
                if not self.notification_container.content.controls:
                    self.notification_container.visible = False
                self.page.update()
        
        asyncio.create_task(hide_notification())
        
    def _on_send_message(self, e):
        """Handle message sending with validation"""
        if not self.message_input.value or not self.message_input.value.strip():
            return
            
        message_text = self.message_input.value.strip()
        
        # Check for commands
        if message_text.startswith("/"):
            self._handle_command(message_text)
            self.message_input.value = ""
            self.page.update()
            return
        
        # Add message to list
        new_message = MessageBubble(
            self.alias,
            message_text,
            datetime.now().strftime("%H:%M"),
            is_own=True,
            on_pin=self._on_pin_message
        )
        self.message_list.controls.append(new_message)
        
        # Clear input
        self.message_input.value = ""
        self.page.update()
        
        # TODO: Send to server via API
        print(f"[{self.current_room}] {self.alias}: {message_text}")
        
    def _handle_command(self, command: str):
        """Handle chat commands"""
        if command == "/help":
            help_text = """
Comandos disponibles:
/help - Mostrar esta ayuda
/clear - Limpiar mensajes
/status - Ver estado de conexión
/rooms - Listar salas disponibles
            """
            self.message_list.controls.append(
                self._create_system_message(help_text.strip())
            )
        elif command == "/clear":
            self.message_list.controls.clear()
            self._show_notification("Mensajes limpiados", "success")
        elif command == "/status":
            status = "🟢 Conectado" if self.config.is_watsonx_configured() else "🔴 Desconectado"
            self.message_list.controls.append(
                self._create_system_message(f"Estado: {status}")
            )
        elif command == "/rooms":
            rooms = ", ".join(self.room_buttons.keys())
            self.message_list.controls.append(
                self._create_system_message(f"Salas: {rooms}")
            )
        else:
            self._show_notification(f"Comando desconocido: {command}", "warning")
            
    def _on_room_click(self, room_name: str):
        """Handle room selection"""
        if room_name == self.current_room:
            return
            
        # Update active state
        for room, button in self.room_buttons.items():
            button.is_active = (room == room_name)
            button.update()
        
        self.current_room = room_name
        self._show_notification(f"Cambiado a #{room_name}", "info")
        
        # TODO: Load room messages from server
        print(f"Switched to room: {room_name}")
        
    def _on_pin_message(self, e):
        """Handle message pinning"""
        self.pinned_message_text.value = "Este es un mensaje fijado de ejemplo"
        self.pinned_message_text.italic = False
        self._show_notification("Mensaje fijado", "success")
        self.page.update()
        
    def _on_search_rooms(self, e):
        """Handle room search"""
        search_term = e.control.value.lower()
        for room, button in self.room_buttons.items():
            button.visible = search_term in room.lower()
            button.update()
            
    def _on_search_messages(self, e):
        """Handle message search"""
        self._show_notification("Función de búsqueda en desarrollo", "info")
        
    def _on_settings_click(self, e):
        """Handle settings button click"""
        self._show_notification("Configuración en desarrollo", "info")
        
    async def _on_summarize_click(self, e):
        """Handle chat summarization with loading state"""
        if not self.config.is_watsonx_configured():
            self._show_notification(
                "❌ Configura WATSONX_API_KEY y WATSONX_PROJECT_ID en .env",
                "error"
            )
            return
        
        # Extract message history
        history = []
        for control in self.message_list.controls:
            if isinstance(control, MessageBubble):
                history.append(f"{control.username}: {control.message}")
        
        if not history:
            self._show_notification("No hay mensajes para resumir", "warning")
            return
        
        # Show loading indicator
        loading = LoadingIndicator("Generando resumen con IBM watsonx.ai...")
        self.message_list.controls.append(loading)
        self.page.update()
        
        try:
            # Generate summary
            summary = await self._summarize_chat(history)
            
            # Remove loading indicator
            self.message_list.controls.remove(loading)
            
            # Add summary message
            summary_container = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.icons.AUTO_AWESOME, size=18, color="#00FF7F"),
                                ft.Text(
                                    "RESUMEN IA (IBM watsonx.ai)",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color="#00FF7F",
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Text(
                            summary,
                            size=13,
                            color=COLOR_TEXTO_CHAT,
                            selectable=True,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(15),
                bgcolor="#1E3A2F",
                border_radius=8,
                border=ft.border.all(1, "#00FF7F"),
            )
            self.message_list.controls.append(summary_container)
            self._show_notification("Resumen generado exitosamente", "success")
            
        except Exception as e:
            self.message_list.controls.remove(loading)
            self._show_notification(f"Error al generar resumen: {str(e)}", "error")
        
        self.page.update()
        
    async def _summarize_chat(self, history: List[str]) -> str:
        """Generate chat summary using IBM watsonx.ai"""
        try:
            credentials = {
                "url": self.config.watsonx_url,
                "apikey": self.config.watsonx_api_key
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
                project_id=self.config.watsonx_project_id,
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
            raise Exception(f"Error en watsonx.ai: {str(e)}")
            
    async def _on_logout(self, e):
        """Handle logout"""
        self._show_notification("Cerrando sesión...", "info")
        await asyncio.sleep(1)
        await self.page.window.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main(page: ft.Page):
    """Main application entry point"""
    app = FletChatApp(page)


if __name__ == "__main__":
    ft.app(target=main)

# Made with Bob - Enhanced UI/UX following IBM Front-end Architecture
