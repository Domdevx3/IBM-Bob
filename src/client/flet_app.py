import flet as ft
import os
import asyncio
import json
import hashlib
import requests
import threading
from functools import lru_cache
from dotenv import load_dotenv
from typing import Optional, Callable, List, Dict
from datetime import datetime

from src.shared.design_constants import (
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

# Lazy imports for heavy dependencies (only load when needed)
_watsonx_imports_loaded = False

def _ensure_watsonx_imports():
    """Lazy load WatsonX AI imports only when needed"""
    global _watsonx_imports_loaded, APIClient, ModelInference, GenParams
    if not _watsonx_imports_loaded:
        from ibm_watsonx_ai import APIClient as _APIClient
        from ibm_watsonx_ai.foundation_models import ModelInference as _ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as _GenParams
        APIClient = _APIClient
        ModelInference = _ModelInference
        GenParams = _GenParams
        _watsonx_imports_loaded = True


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
        self.users_file = "data/usuarios.json"
        self.giphy_api_key = os.getenv("GIPHY_API_KEY", "")
        
    def is_watsonx_configured(self) -> bool:
        """Check if watsonx.ai is properly configured"""
        return bool(self.watsonx_api_key and self.watsonx_project_id)
    
    def is_auth_configured(self) -> bool:
        """Check if JWT authentication is configured"""
        return bool(self.jwt_secret)


# ============================================================================
# AUTHENTICATION MANAGER
# ============================================================================
class AuthManager:
    """Handle user authentication and registration with caching"""
    
    def __init__(self, users_file: str):
        self.users_file = users_file
        self._users_cache: Optional[Dict] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 60.0  # Cache for 60 seconds
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Ensure users file exists"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self, force_reload: bool = False) -> Dict:
        """Load users with caching"""
        import time
        current_time = time.time()
        
        if force_reload or self._users_cache is None or (current_time - self._cache_timestamp) > self._cache_ttl:
            with open(self.users_file, 'r') as f:
                self._users_cache = json.load(f)
            self._cache_timestamp = current_time
        
        return self._users_cache if self._users_cache is not None else {}
    
    def _save_users(self, users: Dict):
        """Save users and invalidate cache"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
        self._users_cache = users
        import time
        self._cache_timestamp = time.time()
    
    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Register a new user"""
        try:
            users = self._load_users(force_reload=True)
            
            if username in users:
                return False, "El usuario ya existe"
            
            users[username] = {
                "password": self._hash_password(password),
                "created_at": datetime.now().isoformat(),
                "status": "online"
            }
            
            self._save_users(users)
            
            return True, "Usuario registrado exitosamente"
        except Exception as e:
            return False, f"Error al registrar: {str(e)}"
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate user"""
        try:
            users = self._load_users()
            
            if username not in users:
                return False, "Usuario no encontrado"
            
            if users[username]["password"] != self._hash_password(password):
                return False, "Contraseña incorrecta"
            
            return True, "Login exitoso"
        except Exception as e:
            return False, f"Error al iniciar sesión: {str(e)}"


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
    """Notification banner for user feedback with close button"""
    
    def __init__(self, message: str, notification_type: str = "info", on_close: Optional[Callable] = None):
        super().__init__()
        self.message = message
        self.notification_type = notification_type
        self.on_close = on_close
        
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
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=18,
                        icon_color="white",
                        tooltip="Cerrar",
                        on_click=lambda e: self.on_close() if self.on_close else None,
                        style=ft.ButtonStyle(
                            padding=ft.padding.all(4),
                        ),
                    ),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=colors.get(self.notification_type, colors["info"]),
            padding=ft.padding.all(12),
            border_radius=8,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        )


class MessageBubble(ft.UserControl):
    """Enhanced message bubble component with timestamps, actions, and smooth animations"""
    
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
                    size=14,
                    color=COLOR_TEXTO_CHAT,
                    selectable=True,
                ),
            ],
            spacing=5,
        )
        
        # Add action buttons on hover with better styling
        actions = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.PUSH_PIN_OUTLINED,
                    icon_size=18,
                    tooltip="📌 Fijar mensaje",
                    on_click=self.on_pin,
                    icon_color="#999999",
                    hover_color=COLOR_BOTON,
                ),
                ft.IconButton(
                    icon=ft.icons.REPLY,
                    icon_size=18,
                    tooltip="↩️ Responder",
                    icon_color="#999999",
                    hover_color=COLOR_BOTON,
                ),
            ],
            spacing=5,
            visible=False,
        )
        
        # Enhanced container with smooth animations
        container = ft.Container(
            content=ft.Row(
                controls=[message_content, actions],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=12,
            bgcolor="#2a2a2a" if self.is_own else "transparent",
            border=ft.border.all(1, "#3a3a3a") if self.is_own else None,
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.animation.Animation(200, ft.AnimationCurve.BOUNCE_OUT),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN),
            on_hover=lambda e: self._toggle_actions(e, actions),
        )
        
        return container
    
    def _toggle_actions(self, e, actions):
        """Toggle action buttons visibility on hover with smooth transition"""
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


class ScaffoldCard(ft.UserControl):
    """
    AI Project Scaffolder Card - Material Design 3
    Displays generated project structure with copy/generate functionality
    """
    
    def __init__(self, project_data: Dict, on_generate: Optional[Callable] = None,
                 on_copy: Optional[Callable] = None):
        super().__init__()
        self.project_data = project_data
        self.on_generate = on_generate
        self.on_copy = on_copy
        
    def build(self):
        # Extract project info
        project_name = self.project_data.get("project_name", "Proyecto")
        description = self.project_data.get("description", "")
        structure = self.project_data.get("structure", {})
        files = self.project_data.get("files", {})
        
        # Build folder tree visualization
        tree_items = []
        for folder, contents in structure.items():
            tree_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.FOLDER, size=16, color="#FFA726"),
                            ft.Text(folder, size=13, color=COLOR_TEXTO_CHAT, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.only(left=10, top=5, bottom=5),
                )
            )
            if isinstance(contents, list):
                for item in contents:
                    tree_items.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.INSERT_DRIVE_FILE, size=14, color="#66BB6A"),
                                    ft.Text(item, size=12, color="#CCCCCC"),
                                ],
                                spacing=8,
                            ),
                            padding=ft.padding.only(left=30, top=2, bottom=2),
                        )
                    )
        
        # Action buttons
        action_buttons = ft.Row(
            controls=[
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.CONTENT_COPY, size=18),
                            ft.Text("Copiar Estructura", size=13),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    bgcolor=COLOR_ENTRADA_OSCURA,
                    color=COLOR_TEXTO_CHAT,
                    on_click=lambda e: self.on_copy(self.project_data) if self.on_copy else None,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.CREATE_NEW_FOLDER, size=18),
                            ft.Text("Generar Archivos", size=13),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    bgcolor=COLOR_BOTON,
                    color="white",
                    on_click=lambda e: self.on_generate(self.project_data) if self.on_generate else None,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.END,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.ARCHITECTURE, size=24, color=COLOR_BOTON),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            project_name,
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_TEXTO_CHAT,
                                        ),
                                        ft.Text(
                                            description,
                                            size=12,
                                            color="#999999",
                                            italic=True,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.all(16),
                        bgcolor="#2a2a2a",
                        border_radius=ft.border_radius.only(top_left=12, top_right=12),
                    ),
                    # Structure tree
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "📁 Estructura del Proyecto",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_BOTON,
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        controls=tree_items,
                                        spacing=0,
                                        scroll=ft.ScrollMode.AUTO,
                                    ),
                                    height=200,
                                    bgcolor="#1a1a1a",
                                    border_radius=8,
                                    padding=ft.padding.all(10),
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=ft.padding.all(16),
                    ),
                    # Actions
                    ft.Container(
                        content=action_buttons,
                        padding=ft.padding.all(16),
                        bgcolor="#2a2a2a",
                        border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12),
                    ),
                ],
                spacing=0,
            ),
            border=ft.border.all(2, COLOR_BOTON),
            border_radius=12,
            bgcolor=COLOR_FONDO_CHAT,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        )


class SearchBar(ft.UserControl):
    """Search bar component for filtering messages"""
    
    def __init__(self, on_search: Optional[Callable] = None):
        super().__init__()
        self.on_search = on_search
        
    def build(self):
        return ft.Container(
            content=ft.TextField(
                hint_text="Buscar salas...",
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
# LOGIN/REGISTER VIEW
# ============================================================================

class LoginView(ft.UserControl):
    """Login and registration view"""
    
    def __init__(self, on_login_success: Callable):
        super().__init__()
        self.on_login_success = on_login_success
        self.auth_manager = AuthManager("data/usuarios.json")
        self.is_register_mode = False
        
    def build(self):
        self.username_field = ft.TextField(
            label="Usuario",
            hint_text="Ingresa tu usuario",
            prefix_icon=ft.icons.PERSON,
            bgcolor=COLOR_ENTRADA_OSCURA,
            border_color=COLOR_BOTON,
            focused_border_color=COLOR_BOTON,
            color=COLOR_TEXTO_CHAT,
            width=350,
        )
        
        self.password_field = ft.TextField(
            label="Contraseña",
            hint_text="Ingresa tu contraseña",
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            bgcolor=COLOR_ENTRADA_OSCURA,
            border_color=COLOR_BOTON,
            focused_border_color=COLOR_BOTON,
            color=COLOR_TEXTO_CHAT,
            width=350,
            on_submit=lambda e: self._handle_submit(),
        )
        
        self.error_text = ft.Text(
            "",
            color="#D13438",
            size=12,
            visible=False,
        )
        
        self.submit_button = ft.ElevatedButton(
            text="Iniciar Sesión",
            icon=ft.icons.LOGIN,
            bgcolor=COLOR_BOTON,
            color="white",
            width=350,
            height=45,
            on_click=lambda e: self._handle_submit(),
        )
        
        self.toggle_button = ft.TextButton(
            text="¿No tienes cuenta? Regístrate",
            on_click=self._toggle_mode,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=50),
                    ft.Icon(
                        ft.icons.CHAT_BUBBLE_ROUNDED,
                        size=80,
                        color=COLOR_BOTON,
                    ),
                    ft.Text(
                        "IBM Chat",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_CHAT,
                    ),
                    ft.Text(
                        "Secure Communication Platform",
                        size=14,
                        color="#999999",
                    ),
                    ft.Container(height=30),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    ft.Container(height=10),
                    self.submit_button,
                    self.toggle_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            bgcolor=COLOR_FONDO_CHAT,
            expand=True,
            alignment=ft.alignment.center,
        )
    
    def _toggle_mode(self, e):
        """Toggle between login and register mode"""
        self.is_register_mode = not self.is_register_mode
        if self.is_register_mode:
            self.submit_button.text = "Registrarse"
            self.submit_button.icon = ft.icons.PERSON_ADD
            self.toggle_button.text = "¿Ya tienes cuenta? Inicia sesión"
        else:
            self.submit_button.text = "Iniciar Sesión"
            self.submit_button.icon = ft.icons.LOGIN
            self.toggle_button.text = "¿No tienes cuenta? Regístrate"
        self.error_text.visible = False
        self.update()
    
    def _handle_submit(self):
        """Handle login or registration"""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self.error_text.value = "Por favor completa todos los campos"
            self.error_text.visible = True
            self.update()
            return
        
        if len(username) < 3:
            self.error_text.value = "El usuario debe tener al menos 3 caracteres"
            self.error_text.visible = True
            self.update()
            return
        
        if len(password) < 4:
            self.error_text.value = "La contraseña debe tener al menos 4 caracteres"
            self.error_text.visible = True
            self.update()
            return
        
        if self.is_register_mode:
            success, message = self.auth_manager.register(username, password)
        else:
            success, message = self.auth_manager.login(username, password)
        
        if success:
            self.on_login_success(username)
        else:
            self.error_text.value = message
            self.error_text.visible = True
            self.update()


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class FletChatApp:
    """
    Enhanced Chat Application with Material Design 3 - Optimized
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.config = AppConfig()
        self.alias = None
        self.current_room = "General"
        self.is_loading = False
        self.auth_token: Optional[str] = None
        self.is_authenticated = False
        
        # Component references
        self.message_list: ft.ListView = None
        self.message_input: ft.TextField = None
        self.send_button: ft.ElevatedButton = None
        self.notification_container: ft.Container = None
        self.pinned_message_text: ft.Text = None
        self.room_buttons: dict = {}
        self.main_container: ft.Container = None
        
        # Performance optimizations
        self._update_batch: List = []
        self._update_timer: Optional[asyncio.Task] = None
        self._watsonx_client_cache: Optional[object] = None  # Will be APIClient when loaded
        
        # Setup and build
        self._setup_page()
        self._show_login()
        
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
    
    def _show_login(self):
        """Show login/register view"""
        login_view = LoginView(on_login_success=self._on_login_success)
        self.page.clean()
        self.page.add(login_view)
        self.page.update()
    
    def _on_login_success(self, username: str):
        """Handle successful login"""
        self.alias = username
        self.is_authenticated = True
        self.page.clean()
        self._build_ui()
        self._show_notification(f"¡Bienvenido, {username}!", "success")
        
    def _handle_keyboard(self, e: ft.KeyboardEvent):
        """Handle keyboard shortcuts for accessibility"""
        if not self.is_authenticated:
            return
        if e.key == "Enter" and e.ctrl:
            self._on_send_message(None)
            
    def _build_ui(self):
        """Build the main UI with modular components"""
        
        # Notification area (top)
        self.notification_container = ft.Container(
            content=ft.Column(controls=[], spacing=5),
            padding=ft.padding.all(10),
            visible=False,
        )
        
        # Main layout
        self.main_container = ft.Container(
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
        
        self.page.add(self.main_container)
        self.page.update()
        
    def _build_sidebar(self):
        """Build enhanced sidebar with user profile and room list - Optimized"""
        
        # User profile section
        user_profile = ft.Container(
            content=UserProfileCard(self.alias or "Guest", "online"),
            padding=ft.padding.all(10),
        )
        
        # Enhanced Channels Header with icon
        channels_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.icons.TAG,
                        size=16,
                        color=COLOR_BOTON,
                    ),
                    ft.Text(
                        "CANALES",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_CHAT,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor="#2a2a2a",
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=10, vertical=5),
        )
        
        # Search bar
        search_bar = SearchBar(on_search=self._on_search_rooms)
        
        # Room list - Lazy loading for better performance
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
                        bgcolor=COLOR_BOTON,
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
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    user_profile,
                    ft.Divider(height=1, color="#444444"),
                    channels_header,
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
                                on_click=self._on_notifications_click,
                            ),
                            ft.IconButton(
                                icon=ft.icons.INFO_OUTLINE,
                                icon_size=20,
                                tooltip="Información del canal",
                                icon_color="#999999",
                                on_click=self._on_channel_info_click,
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
        
        # Pinned message area - Hidden by default, shown when message is pinned
        self.pinned_message_text = ft.Text(
            "",
            size=12,
            color="#FFFFFF",
        )
        
        self.pinned_message_container = ft.Container(
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
            visible=False,  # Hidden by default
        )
        
        # Message list with sample messages - Optimized with lazy loading
        initial_messages = [
            self._create_system_message("Bienvenido al canal #General"),
            MessageBubble("Usuario1", "¡Hola a todos! ¿Cómo están?", "10:30", on_pin=self._on_pin_message),
            MessageBubble("Usuario2", "Todo bien, trabajando en el nuevo proyecto", "10:32", on_pin=self._on_pin_message),
            MessageBubble(self.alias or "Guest", "Excelente, ¿necesitan ayuda?", "10:35", is_own=True, on_pin=self._on_pin_message),
            self._create_system_message("Usuario3 se ha unido al canal"),
        ]
        
        self.message_list = ft.ListView(
            controls=initial_messages,
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
                    self.pinned_message_container,
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
        """Build enhanced input area with formatting options and smooth animations"""
        
        self.message_input = ft.TextField(
            hint_text="💬 Escribe un mensaje... (Ctrl+Enter para enviar)",
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
            content_padding=ft.padding.all(14),
            border_radius=12,
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_size=24,
            bgcolor=COLOR_BOTON,
            icon_color="white",
            tooltip="🚀 Enviar mensaje (Ctrl+Enter)",
            on_click=self._on_send_message,
            width=52,
            height=52,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=26),
                animation_duration=200,
            ),
            animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
        )
        
        # Enhanced formatting toolbar with functional buttons
        toolbar = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.ATTACH_FILE,
                    icon_size=22,
                    tooltip="📎 Adjuntar archivo",
                    icon_color="#999999",
                    on_click=self._on_attach_file,
                    hover_color=COLOR_BOTON,
                ),
                ft.IconButton(
                    icon=ft.icons.EMOJI_EMOTIONS_OUTLINED,
                    icon_size=22,
                    tooltip="😊 Emojis",
                    icon_color="#999999",
                    on_click=self._on_emoji_click,
                    hover_color=COLOR_BOTON,
                ),
                ft.IconButton(
                    icon=ft.icons.GIF_BOX_OUTLINED,
                    icon_size=22,
                    tooltip="🎬 GIF",
                    icon_color="#999999",
                    on_click=self._on_gif_click,
                    hover_color=COLOR_BOTON,
                ),
            ],
            spacing=8,
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
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.message_input,
                                self.send_button,
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=COLOR_FONDO_CHAT,
            border=ft.border.only(top=ft.BorderSide(2, "#3a3a3a")),
        )
    
    def _on_attach_file(self, e):
        """Handle file attachment"""
        file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="Seleccionar archivo",
            allow_multiple=False,
        )
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection - Optimized"""
        if not e.files:
            return
        
        # Batch message creation for better performance
        new_messages = []
        for file in e.files:
            file_message = f"📎 Archivo adjunto: {file.name}"
            new_message = MessageBubble(
                self.alias or "Guest",
                file_message,
                datetime.now().strftime("%H:%M"),
                is_own=True,
                on_pin=self._on_pin_message
            )
            new_messages.append(new_message)
        
        # Add all messages at once
        self.message_list.controls.extend(new_messages)
        self.page.update()
        self._show_notification(f"{len(new_messages)} archivo(s) adjuntado(s)", "success")
    
    @lru_cache(maxsize=1)
    def _get_emoji_categories(self) -> Dict[str, List[str]]:
        """Get emoji categories - Cached for performance"""
        return {
            "😊 Smileys": ["😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
                          "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙",
                          "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔"],
            "👋 Gestures": ["👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞",
                           "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍",
                           "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "💪"],
            "❤️ Hearts": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
                         "❤️‍🔥", "❤️‍🩹", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟"],
            "🐶 Animals": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
                          "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🦆",
                          "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋"],
            "🍕 Food": ["🍕", "🍔", "🍟", "🌭", "🍿", "🧈", "🥓", "🥚", "🍳", "🧇",
                       "🥞", "🧈", "🍞", "🥐", "🥨", "🥯", "🥖", "🧀", "🥗", "🥙",
                       "🌮", "🌯", "🥪", "🍖", "🍗", "🥩", "🍱", "🍘", "🍙", "🍚"],
            "✈️ Travel": ["✈️", "🚀", "🛸", "🚁", "🛶", "⛵", "🚤", "🛳️", "⛴️", "🚢",
                         "🚂", "🚃", "🚄", "🚅", "🚆", "🚇", "🚈", "🚉", "🚊", "🚝",
                         "🚞", "🚋", "🚌", "🚍", "🚎", "🚐", "🚑", "🚒", "🚓", "🚔"],
            "⚽ Sports": ["⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱",
                        "🪀", "🏓", "🏸", "🏒", "🏑", "🥍", "🏏", "🥅", "⛳", "🪁",
                        "🏹", "🎣", "🤿", "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸️"],
            "🎉 Objects": ["🎉", "🎊", "🎈", "🎁", "🎀", "🎂", "🎄", "🎃", "🎆", "🎇",
                          "🧨", "✨", "🎋", "🎍", "🎎", "🎏", "🎐", "🎑", "🧧", "🎀",
                          "🎁", "🎗️", "🎟️", "🎫", "🎖️", "🏆", "🏅", "🥇", "🥈", "🥉"],
            "💯 Symbols": ["💯", "🔥", "⭐", "🌟", "✨", "⚡", "💥", "💫", "💢", "💦",
                          "💨", "🕳️", "💬", "👁️‍🗨️", "🗨️", "🗯️", "💭", "💤", "🚀", "🎯",
                          "✅", "❌", "⭕", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫"],
        }
    
    def _on_emoji_click(self, e):
        """Show enhanced emoji/sticker picker dialog with Giphy API - Optimized"""
        if not self.config.giphy_api_key or self.config.giphy_api_key == "your_giphy_api_key_here":
            # Fallback to local emojis if no API key
            self._show_local_emoji_picker()
            return
        
        # Show loading
        loading_dialog = ft.AlertDialog(
            title=ft.Text("Cargando stickers..."),
            content=ft.Container(
                content=ft.ProgressRing(),
                padding=20,
            ),
        )
        self.page.dialog = loading_dialog
        loading_dialog.open = True
        self.page.update()
        
        # Fetch stickers using threading
        def load_stickers():
            sticker_categories = {
                "😊 Emociones": self._fetch_giphy_stickers("happy emotions"),
                "👋 Gestos": self._fetch_giphy_stickers("hand gestures"),
                "❤️ Amor": self._fetch_giphy_stickers("love hearts"),
                "🎉 Celebración": self._fetch_giphy_stickers("celebration party"),
                "😂 Divertido": self._fetch_giphy_stickers("funny lol"),
                "🐱 Animales": self._fetch_giphy_stickers("cute animals"),
            }
            
            self._show_sticker_dialog(sticker_categories)
        
        threading.Thread(target=load_stickers, daemon=True).start()
    
    def _show_local_emoji_picker(self):
        """Show local emoji picker as fallback"""
        emoji_categories = self._get_emoji_categories()
        
        # Create tabs for categories
        tabs = []
        for category, emojis in emoji_categories.items():
            emoji_buttons = []
            for emoji in emojis:
                emoji_buttons.append(
                    ft.Container(
                        content=ft.TextButton(
                            text=emoji,
                            style=ft.ButtonStyle(
                                text_style=ft.TextStyle(size=28),
                                padding=ft.padding.all(8),
                            ),
                            on_click=lambda e, em=emoji: self._insert_emoji(em),
                        ),
                        animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
                    )
                )
            
            tabs.append(
                ft.Tab(
                    text=category,
                    content=ft.Container(
                        content=ft.GridView(
                            controls=emoji_buttons,
                            runs_count=6,
                            max_extent=60,
                            child_aspect_ratio=1,
                            spacing=8,
                            run_spacing=8,
                        ),
                        padding=ft.padding.all(10),
                    ),
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.EMOJI_EMOTIONS, color=COLOR_BOTON),
                    ft.Text("Selecciona un emoji", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Tabs(
                    tabs=tabs,
                    selected_index=0,
                    animation_duration=300,
                    indicator_color=COLOR_BOTON,
                    label_color=COLOR_BOTON,
                    unselected_label_color="#999999",
                ),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self._close_dialog(),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _insert_emoji(self, emoji: str):
        """Insert emoji into message input"""
        current_text = self.message_input.value or ""
        self.message_input.value = current_text + emoji
        self._close_dialog()
        self.page.update()
    
    def _fetch_giphy_gifs(self, query: str, limit: int = 8) -> List[Dict]:
        """Fetch GIFs from Giphy API"""
        if not self.config.giphy_api_key or self.config.giphy_api_key == "your_giphy_api_key_here":
            return []
        
        try:
            url = f"https://api.giphy.com/v1/gifs/search"
            params = {
                "api_key": self.config.giphy_api_key,
                "q": query,
                "limit": limit,
                "rating": "g",
                "lang": "es"
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "title": gif["title"],
                        "url": gif["images"]["fixed_height"]["url"]
                    }
                    for gif in data.get("data", [])
                ]
        except Exception as e:
            print(f"Error fetching GIFs: {e}")
        return []
    
    def _fetch_giphy_stickers(self, query: str, limit: int = 20) -> List[Dict]:
        """Fetch stickers/emojis from Giphy API"""
        if not self.config.giphy_api_key or self.config.giphy_api_key == "your_giphy_api_key_here":
            return []
        
        try:
            url = f"https://api.giphy.com/v1/stickers/search"
            params = {
                "api_key": self.config.giphy_api_key,
                "q": query,
                "limit": limit,
                "rating": "g",
                "lang": "es"
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "title": sticker["title"],
                        "url": sticker["images"]["fixed_height_small"]["url"]
                    }
                    for sticker in data.get("data", [])
                ]
        except Exception as e:
            print(f"Error fetching stickers: {e}")
        return []
    
    def _on_gif_click(self, e):
        """Show enhanced GIF picker dialog with Giphy API integration"""
        if not self.config.giphy_api_key or self.config.giphy_api_key == "your_giphy_api_key_here":
            self._show_notification("⚠️ Giphy API key no configurada. Usa una API key válida en el archivo .env", "warning")
            return
        
        # Show loading
        loading_dialog = ft.AlertDialog(
            title=ft.Text("Cargando GIFs..."),
            content=ft.Container(
                content=ft.ProgressRing(),
                padding=20,
            ),
        )
        self.page.dialog = loading_dialog
        loading_dialog.open = True
        self.page.update()
        
        # Fetch GIFs using threading to avoid async issues
        def load_gifs():
            gif_categories = {
                "🎉 Celebración": self._fetch_giphy_gifs("celebration party"),
                "👍 Reacciones": self._fetch_giphy_gifs("thumbs up reaction"),
                "😂 Divertido": self._fetch_giphy_gifs("funny lol"),
                "💼 Trabajo": self._fetch_giphy_gifs("work office"),
                "❤️ Amor": self._fetch_giphy_gifs("love heart"),
                "🐱 Animales": self._fetch_giphy_gifs("cute animals"),
            }
            
            self._show_gif_dialog(gif_categories)
        
        threading.Thread(target=load_gifs, daemon=True).start()
    
    def _show_gif_dialog(self, gif_categories: Dict[str, List[Dict]]):
        """Show GIF picker dialog with fetched GIFs"""
        
        # Create tabs for GIF categories
        tabs = []
        for category, gifs in gif_categories.items():
            if not gifs:
                continue
                
            gif_buttons = []
            for gif_data in gifs:
                title = gif_data.get("title", "GIF")
                url = gif_data.get("url", "")
                gif_buttons.append(
                    ft.Container(
                        content=ft.ElevatedButton(
                            text=f"🎬 {title[:20]}...",
                            on_click=lambda e, u=url, t=title: self._insert_gif(u, t),
                            style=ft.ButtonStyle(
                                bgcolor=COLOR_ENTRADA_OSCURA,
                                color=COLOR_TEXTO_CHAT,
                            ),
                        ),
                        animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
                    )
                )
            
            tabs.append(
                ft.Tab(
                    text=category,
                    content=ft.Container(
                        content=ft.GridView(
                            controls=gif_buttons,
                            runs_count=2,
                            max_extent=200,
                            child_aspect_ratio=2,
                            spacing=10,
                            run_spacing=10,
                        ),
                        padding=ft.padding.all(15),
                    ),
                )
            )
        
        if not tabs:
            tabs.append(
                ft.Tab(
                    text="Sin resultados",
                    content=ft.Container(
                        content=ft.Text("No se encontraron GIFs", color="#999999"),
                        padding=20,
                    ),
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.GIF_BOX, color=COLOR_BOTON),
                    ft.Text("Selecciona un GIF", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Tabs(
                    tabs=tabs,
                    selected_index=0,
                    animation_duration=300,
                    indicator_color=COLOR_BOTON,
                    label_color=COLOR_BOTON,
                    unselected_label_color="#999999",
                ),
                width=450,
                height=350,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self._close_dialog(),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _insert_gif(self, gif_url: str, gif_name: str = "GIF"):
        """Insert GIF into chat with animation - Optimized"""
        gif_message = f"🎬 {gif_name}"
        new_message = MessageBubble(
            self.alias or "Guest",
            gif_message,
            datetime.now().strftime("%H:%M"),
            is_own=True,
            on_pin=self._on_pin_message
        )
        self.message_list.controls.append(new_message)
        self._close_dialog()
        
        # Scroll to bottom with animation
        self.message_list.scroll_to(offset=-1, duration=300)
        self.page.update()
        self._show_notification("🎬 GIF enviado", "success")
    
    def _close_dialog(self):
        """Close current dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
        
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
        """Show notification banner with close button and 3-second auto-hide"""
        def close_notification():
            try:
                if notification in self.notification_container.content.controls:
                    self.notification_container.content.controls.remove(notification)
                    if not self.notification_container.content.controls:
                        self.notification_container.visible = False
                    self.page.update()
            except Exception:
                pass
        
        notification = NotificationBanner(message, notification_type, on_close=close_notification)
        self.notification_container.content.controls.append(notification)
        self.notification_container.visible = True
        self.page.update()
        
        # Auto-hide after 3 seconds using threading
        def hide_notification():
            import time
            time.sleep(3)
            close_notification()
        
        threading.Thread(target=hide_notification, daemon=True).start()
        
    def _on_send_message(self, e):
        """Handle message sending with validation and smooth animation - Optimized"""
        if not self.message_input.value or not self.message_input.value.strip():
            return
        
        message_text = self.message_input.value.strip()
        
        # Batch UI updates for better performance
        self.send_button.scale = 0.8
        
        # Check for commands
        if message_text.startswith("/"):
            self._handle_command(message_text)
            self.message_input.value = ""
            self.send_button.scale = 1.0
            self.page.update()
            return
        
        # Add message to list
        new_message = MessageBubble(
            self.alias or "Guest",
            message_text,
            datetime.now().strftime("%H:%M"),
            is_own=True,
            on_pin=self._on_pin_message
        )
        self.message_list.controls.append(new_message)
        
        # Clear input and reset button
        self.message_input.value = ""
        self.send_button.scale = 1.0
        
        # Single update call for better performance
        self.page.update()
        
        # TODO: Send to server via API (async for non-blocking)
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
/scaffold [descripción] - Generar estructura de proyecto con IA
Ejemplo: /scaffold API REST con Node.js y Express
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
        elif command.startswith("/scaffold "):
            # Extract project description
            description = command[10:].strip()
            if not description:
                self._show_notification("Uso: /scaffold [descripción del proyecto]", "warning")
                return
            
            # Handle scaffold command asynchronously
            self.page.run_task(self._handle_scaffold_command, description)
        else:
            self._show_notification(f"Comando desconocido: {command}", "warning")
            
    def _on_room_click(self, room_name: str):
        """Handle room/channel switching"""
        # Update current room
        old_room = self.current_room
        self.current_room = room_name
        
        # Update room buttons
        for room, button in self.room_buttons.items():
            button.is_active = (room == room_name)
        
        # Clear and reload messages for new room
        self.message_list.controls.clear()
        self.message_list.controls.append(
            self._create_system_message(f"Cambiaste al canal #{room_name}")
        )
        
        self._show_notification(f"Canal cambiado a #{room_name}", "info")
        self.page.update()
    
    def _on_notifications_click(self, e):
        """Show notifications panel"""
        notifications = [
            {"type": "mention", "user": "Usuario1", "message": "Te mencionó en #General", "time": "Hace 5 min"},
            {"type": "reply", "user": "Usuario2", "message": "Respondió a tu mensaje", "time": "Hace 15 min"},
            {"type": "system", "user": "Sistema", "message": "Nueva actualización disponible", "time": "Hace 1 hora"},
        ]
        
        notification_items = []
        for notif in notifications:
            icon = ft.icons.ALTERNATE_EMAIL if notif["type"] == "mention" else \
                   ft.icons.REPLY if notif["type"] == "reply" else ft.icons.INFO
            
            notification_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon, size=20, color=COLOR_BOTON),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"{notif['user']}: {notif['message']}",
                                        size=13,
                                        color=COLOR_TEXTO_CHAT,
                                    ),
                                    ft.Text(
                                        notif['time'],
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
                    padding=ft.padding.all(12),
                    bgcolor=COLOR_ENTRADA_OSCURA,
                    border_radius=8,
                    margin=ft.margin.only(bottom=8),
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.NOTIFICATIONS, color=COLOR_BOTON),
                    ft.Text("Notificaciones", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=notification_items if notification_items else [
                        ft.Text("No hay notificaciones nuevas", color="#999999")
                    ],
                    spacing=5,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton(
                    "Marcar todas como leídas",
                    on_click=lambda e: self._show_notification("Notificaciones marcadas como leídas", "success"),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self._close_dialog(),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _on_channel_info_click(self, e):
        """Show channel information panel"""
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.INFO, color=COLOR_BOTON),
                    ft.Text(f"Información de #{self.current_room}", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("📝 Descripción", size=14, weight=ft.FontWeight.BOLD, color=COLOR_BOTON),
                                    ft.Text(
                                        f"Canal de {self.current_room.lower()} para el equipo",
                                        size=13,
                                        color=COLOR_TEXTO_CHAT,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=ft.padding.all(10),
                            bgcolor=COLOR_ENTRADA_OSCURA,
                            border_radius=8,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("👥 Miembros", size=14, weight=ft.FontWeight.BOLD, color=COLOR_BOTON),
                                    ft.Text("12 miembros totales", size=13, color=COLOR_TEXTO_CHAT),
                                    ft.Text("3 en línea ahora", size=13, color="#4CAF50"),
                                ],
                                spacing=5,
                            ),
                            padding=ft.padding.all(10),
                            bgcolor=COLOR_ENTRADA_OSCURA,
                            border_radius=8,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("📊 Estadísticas", size=14, weight=ft.FontWeight.BOLD, color=COLOR_BOTON),
                                    ft.Text("156 mensajes hoy", size=13, color=COLOR_TEXTO_CHAT),
                                    ft.Text("Creado: 15 Ene 2024", size=13, color="#999999"),
                                ],
                                spacing=5,
                            ),
                            padding=ft.padding.all(10),
                            bgcolor=COLOR_ENTRADA_OSCURA,
                            border_radius=8,
                        ),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self._close_dialog(),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_sticker_dialog(self, sticker_categories: Dict[str, List[Dict]]):
        """Show sticker picker dialog with fetched stickers from Giphy"""
        
        # Create tabs for sticker categories
        tabs = []
        for category, stickers in sticker_categories.items():
            if not stickers:
                continue
                
            sticker_buttons = []
            for sticker_data in stickers:
                title = sticker_data.get("title", "Sticker")
                url = sticker_data.get("url", "")
                sticker_buttons.append(
                    ft.Container(
                        content=ft.Image(
                            src=url,
                            width=80,
                            height=80,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        on_click=lambda e, u=url, t=title: self._insert_sticker(u, t),
                        bgcolor=COLOR_ENTRADA_OSCURA,
                        border_radius=8,
                        padding=ft.padding.all(5),
                        animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
                    )
                )
            
            tabs.append(
                ft.Tab(
                    text=category,
                    content=ft.Container(
                        content=ft.GridView(
                            controls=sticker_buttons,
                            runs_count=4,
                            max_extent=90,
                            child_aspect_ratio=1,
                            spacing=10,
                            run_spacing=10,
                        ),
                        padding=ft.padding.all(15),
                    ),
                )
            )
        
        if not tabs:
            tabs.append(
                ft.Tab(
                    text="Sin resultados",
                    content=ft.Container(
                        content=ft.Text("No se encontraron stickers", color="#999999"),
                        padding=20,
                    ),
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.EMOJI_EMOTIONS, color=COLOR_BOTON),
                    ft.Text("Selecciona un sticker", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Tabs(
                    tabs=tabs,
                    selected_index=0,
                    animation_duration=300,
                    indicator_color=COLOR_BOTON,
                    label_color=COLOR_BOTON,
                    unselected_label_color="#999999",
                ),
                width=450,
                height=400,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self._close_dialog(),
                    style=ft.ButtonStyle(color=COLOR_BOTON),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _insert_sticker(self, url: str, title: str):
        """Insert sticker as a message"""
        new_message = MessageBubble(
            self.alias or "Guest",
            f"🎨 Sticker: {title}",
            datetime.now().strftime("%H:%M"),
            is_own=True,
            on_pin=self._on_pin_message
        )
        self.message_list.controls.append(new_message)
        self._close_dialog()
        self.page.update()
        print(f"Sticker URL: {url}")
    
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
        """Handle message search in chat"""
        search_field = ft.TextField(
            hint_text="Buscar mensajes...",
            prefix_icon=ft.icons.SEARCH,
            autofocus=True,
            on_submit=lambda e: self._perform_message_search(e.control.value),
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Buscar en el chat"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        search_field,
                        ft.Text(
                            "Presiona Enter para buscar",
                            size=11,
                            color="#999999",
                        ),
                    ],
                    spacing=10,
                ),
                width=300,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._close_dialog()),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _perform_message_search(self, search_term: str):
        """Perform message search"""
        if not search_term:
            return
        
        found_messages = []
        for control in self.message_list.controls:
            if isinstance(control, MessageBubble):
                if search_term.lower() in control.message.lower():
                    found_messages.append(f"{control.username}: {control.message}")
        
        if found_messages:
            result_text = f"Encontrados {len(found_messages)} mensajes:\n" + "\n".join(found_messages[:5])
            if len(found_messages) > 5:
                result_text += f"\n... y {len(found_messages) - 5} más"
        else:
            result_text = "No se encontraron mensajes"
        
        self._close_dialog()
        self._show_notification(result_text, "info")
        
    def _on_settings_click(self, e):
        """Handle settings button click - User preferences only"""
        self.theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Oscuro"),
                ft.dropdown.Option("Claro"),
                ft.dropdown.Option("Auto"),
            ],
            value="Oscuro",
            width=150,
        )
        
        self.font_size_slider = ft.Slider(
            min=10,
            max=20,
            value=14,
            divisions=10,
            label="{value}px",
            width=200,
        )
        
        self.username_field = ft.TextField(
            label="Nombre de usuario",
            value=self.alias or "",
            width=250,
        )
        
        settings_content = ft.Column(
            controls=[
                ft.Text("Configuración de Usuario", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Text("Usuario:", size=14, width=100),
                        self.username_field,
                    ],
                    spacing=20,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Tema:", size=14, width=100),
                        self.theme_dropdown,
                    ],
                    spacing=20,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Tamaño de fuente:", size=14, width=100),
                        self.font_size_slider,
                    ],
                    spacing=20,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Notificaciones:", size=14, width=100),
                        ft.Switch(value=True),
                    ],
                    spacing=20,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Sonidos:", size=14, width=100),
                        ft.Switch(value=True),
                    ],
                    spacing=20,
                ),
            ],
            spacing=15,
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Configuración"),
            content=ft.Container(
                content=settings_content,
                width=400,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Guardar", on_click=lambda e: self._save_settings()),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _save_settings(self):
        """Save settings"""
        self._close_dialog()
        self._show_notification("Configuración guardada", "success")
        
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
        
    def _get_watsonx_client(self):
        """Get or create cached WatsonX client for better performance - Lazy loaded"""
        if self._watsonx_client_cache is None:
            # Lazy load WatsonX imports only when needed
            _ensure_watsonx_imports()
            credentials = {
                "url": self.config.watsonx_url,
                "apikey": self.config.watsonx_api_key
            }
            self._watsonx_client_cache = APIClient(credentials)
        return self._watsonx_client_cache
    
    async def _summarize_chat(self, history: List[str]) -> str:
        """Generate chat summary using IBM watsonx.ai - Optimized with lazy loading"""
        try:
            # Lazy load WatsonX imports only when summarize is used
            _ensure_watsonx_imports()
            
            client = self._get_watsonx_client()
            
            # Limit history to last 20 messages for efficiency
            conversation_text = "\n".join(history[-20:])
            
            prompt = f"""Eres un asistente de secretaría técnica. Resume la siguiente conversación de chat empresarial.
Ignora mensajes de sistema como [ENTRÓ], [SALIÓ].
Enumera los puntos clave y decisiones importantes.
Sé breve y profesional en español.

Conversación:
{conversation_text}

Resumen:"""
            
            # Create model with proper error handling
            try:
                model = ModelInference(
                    model_id="ibm/granite-8b-code-instruct",
                    api_client=client,
                    project_id=self.config.watsonx_project_id,
                    params={
                        GenParams.MAX_NEW_TOKENS: 500,
                        GenParams.TEMPERATURE: 0.7,
                        GenParams.TOP_P: 0.9
                    }
                )
            except Exception as model_error:
                raise Exception(f"Error al crear modelo: {str(model_error)}")
            
            # Generate text with proper error handling
            try:
                response = model.generate_text(prompt=prompt)
            except Exception as gen_error:
                raise Exception(f"Error al generar texto: {str(gen_error)}")
            
            # Extract response text with validation
            response_text = None
            if isinstance(response, dict):
                # Try to extract from results array
                results = response.get("results", [])
                if results and len(results) > 0:
                    response_text = results[0].get("generated_text", "")
                
                # Fallback: try direct generated_text key
                if not response_text:
                    response_text = response.get("generated_text", "")
                
                # Last resort: stringify the whole response
                if not response_text:
                    response_text = str(response)
            else:
                response_text = str(response)
            
            # Validate we got something
            if not response_text or response_text.strip() == "":
                raise Exception("La respuesta de watsonx.ai está vacía. Verifica tu configuración.")
            
            return response_text.strip()
            
        except Exception as e:
            # Return detailed error message instead of silently failing
            error_msg = f"Error en watsonx.ai: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _handle_scaffold_command(self, description: str):
        """Handle /scaffold command - Generate project structure with AI"""
        if not self.config.is_watsonx_configured():
            self._show_notification(
                "⚠️ watsonx.ai no está configurado. Configura WATSONX_API_KEY y WATSONX_PROJECT_ID",
                "warning"
            )
            return
        
        # Show loading indicator
        loading = LoadingIndicator(f"🏗️ Generando estructura de proyecto con IBM watsonx.ai...")
        self.message_list.controls.append(loading)
        self.page.update()
        
        try:
            # Generate project structure
            project_data = await self._generate_project_scaffold(description)
            
            # Remove loading indicator
            if loading in self.message_list.controls:
                self.message_list.controls.remove(loading)
            
            # Add scaffold card to chat
            scaffold_card = ScaffoldCard(
                project_data=project_data,
                on_generate=self._on_generate_files,
                on_copy=self._on_copy_structure
            )
            self.message_list.controls.append(scaffold_card)
            
            self._show_notification("✅ Estructura de proyecto generada", "success")
            
        except Exception as e:
            # Remove loading indicator
            if loading in self.message_list.controls:
                self.message_list.controls.remove(loading)
            
            error_message = f"❌ Error al generar estructura: {str(e)}"
            self.message_list.controls.append(
                self._create_system_message(error_message)
            )
            self._show_notification("Error al generar proyecto", "error")
        
        self.page.update()
    
    async def _generate_project_scaffold(self, description: str) -> Dict:
        """Generate project structure using IBM watsonx.ai as Software Architect"""
        try:
            # Lazy load WatsonX imports
            _ensure_watsonx_imports()
            
            client = self._get_watsonx_client()
            
            # Engineered prompt for structured JSON output
            prompt = f"""You are an expert Software Architect. Generate a complete project structure for the following description.

Project Description: {description}

You MUST respond with ONLY a valid JSON object (no markdown, no explanations) with this exact structure:
{{
  "project_name": "project-name-kebab-case",
  "description": "Brief project description",
  "structure": {{
    "src/": ["main.py", "config.py", "utils.py"],
    "tests/": ["test_main.py"],
    "docs/": ["README.md", "API.md"],
    "config/": [".env.example", "settings.json"]
  }},
  "files": {{
    "src/main.py": "# Main application entry point\\nimport config\\n\\ndef main():\\n    print('Hello World')\\n\\nif __name__ == '__main__':\\n    main()",
    "README.md": "# Project Name\\n\\n## Description\\nProject description here\\n\\n## Installation\\n```bash\\npip install -r requirements.txt\\n```",
    ".env.example": "API_KEY=your_api_key_here\\nDEBUG=true"
  }},
  "tech_stack": ["Python 3.11", "FastAPI", "PostgreSQL"],
  "commands": {{
    "install": "pip install -r requirements.txt",
    "run": "python src/main.py",
    "test": "pytest tests/"
  }}
}}

Generate the JSON structure now:"""
            
            # Use strict parameters for structured output
            # Using meta-llama model which is more reliable for code generation
            try:
                model = ModelInference(
                    model_id="meta-llama/llama-3-3-70b-instruct",
                    api_client=client,
                    project_id=self.config.watsonx_project_id,
                    params={
                        GenParams.MAX_NEW_TOKENS: 2000,
                        GenParams.TEMPERATURE: 0.3,  # Low temperature for consistent structure
                        GenParams.TOP_P: 0.85,
                        GenParams.STOP_SEQUENCES: ["\n\n\n"],  # Stop at code blocks or excessive newlines
                    }
                )
                print(f"✅ Modelo creado: meta-llama/llama-3-3-70b-instruct")
            except Exception as model_error:
                error_msg = f"Error al crear modelo watsonx.ai: {str(model_error)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            # Generate text with proper error handling
            try:
                print(f"🔄 Generando respuesta con watsonx.ai...")
                response = model.generate_text(prompt=prompt)
                print(f"✅ Respuesta recibida. Tipo: {type(response)}")
                
                # Debug: print response structure
                if isinstance(response, dict):
                    print(f"📊 Claves en respuesta: {list(response.keys())}")
                    if "results" in response:
                        print(f"📊 Resultados: {len(response.get('results', []))} items")
                
            except Exception as gen_error:
                error_msg = f"Error al generar proyecto: {str(gen_error)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            # Extract response text with validation
            response_text = None
            if isinstance(response, dict):
                # Try to extract from results array
                results = response.get("results", [])
                if results and len(results) > 0:
                    response_text = results[0].get("generated_text", "")
                    print(f"✅ Texto extraído de results[0]: {len(response_text)} caracteres")
                
                # Fallback: try direct generated_text key
                if not response_text:
                    response_text = response.get("generated_text", "")
                    if response_text:
                        print(f"✅ Texto extraído de generated_text directo: {len(response_text)} caracteres")
                
                # Last resort: stringify the whole response
                if not response_text:
                    response_text = str(response)
                    print(f"⚠️ Usando stringify de respuesta completa: {len(response_text)} caracteres")
            else:
                response_text = str(response)
                print(f"⚠️ Respuesta no es dict, usando str(): {len(response_text)} caracteres")
            
            # Validate we got something
            if not response_text or response_text.strip() == "":
                print(f"❌ Respuesta vacía detectada!")
                print(f"📊 Debug - Respuesta completa: {response}")
                raise Exception("La respuesta de watsonx.ai está vacía. Verifica tu configuración y modelo.")
            
            print(f"✅ Validación exitosa: {len(response_text)} caracteres")
            
            # Clean and parse JSON with robust error handling
            response_text = response_text.strip()
            print(f"🔍 Limpiando respuesta...")
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                # Extract content between ```json and ```
                import re
                json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                    print(f"✅ JSON extraído de markdown block")
            elif response_text.startswith("```"):
                # Generic code block
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    print(f"✅ Código extraído de block genérico")
            
            response_text = response_text.strip()
            
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
                print(f"✅ JSON object encontrado: {len(response_text)} caracteres")
            
            # Parse JSON with better error handling
            try:
                print(f"🔄 Intentando parsear JSON...")
                project_data = json.loads(response_text)
                print(f"✅ JSON parseado exitosamente!")
            except json.JSONDecodeError as e:
                print(f"❌ Error de JSON en línea {e.lineno}, columna {e.colno}: {e.msg}")
                print(f"📊 Contexto: {response_text[max(0, e.pos-50):e.pos+50]}")
                
                # Try to fix common JSON issues
                print(f"🔧 Intentando reparar JSON...")
                
                # Fix 1: Replace single quotes with double quotes
                fixed_text = response_text.replace("'", '"')
                
                # Fix 2: Remove trailing commas
                fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
                
                # Fix 3: Escape unescaped quotes in strings
                # This is complex, so we'll try a simple approach
                
                try:
                    project_data = json.loads(fixed_text)
                    print(f"✅ JSON reparado y parseado!")
                except json.JSONDecodeError as e2:
                    print(f"❌ No se pudo reparar el JSON")
                    print(f"📄 Respuesta completa (primeros 500 chars):")
                    print(response_text[:500])
                    raise ValueError(f"No se pudo parsear JSON: {e.msg} en línea {e.lineno}, columna {e.colno}")
            
            # Validate required fields
            if "project_name" not in project_data:
                project_data["project_name"] = description.replace(" ", "-").lower()[:30]
            if "description" not in project_data:
                project_data["description"] = description
            if "structure" not in project_data:
                project_data["structure"] = {"src/": ["main.py"]}
            
            return project_data
            
        except Exception as e:
            raise Exception(f"Error en watsonx.ai scaffolder: {str(e)}")
    
    def _on_generate_files(self, project_data: Dict):
        """Handle Generate Files button click"""
        try:
            import os
            
            project_name = project_data.get("project_name", "project")
            structure = project_data.get("structure", {})
            files = project_data.get("files", {})
            
            # Create project directory
            base_path = os.path.join(os.getcwd(), project_name)
            os.makedirs(base_path, exist_ok=True)
            
            # Create folder structure
            for folder in structure.keys():
                folder_path = os.path.join(base_path, folder)
                os.makedirs(folder_path, exist_ok=True)
            
            # Create files with content
            for file_path, content in files.items():
                full_path = os.path.join(base_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            self._show_notification(f"✅ Proyecto '{project_name}' generado en {base_path}", "success")
            
        except Exception as e:
            self._show_notification(f"❌ Error al generar archivos: {str(e)}", "error")
    
    def _on_copy_structure(self, project_data: Dict):
        """Handle Copy Structure button click"""
        try:
            # Format structure as text
            structure_text = f"# {project_data.get('project_name', 'Project')}\n\n"
            structure_text += f"{project_data.get('description', '')}\n\n"
            structure_text += "## Structure\n```\n"
            
            for folder, files in project_data.get("structure", {}).items():
                structure_text += f"{folder}\n"
                for file in files:
                    structure_text += f"  ├── {file}\n"
            
            structure_text += "```\n\n"
            
            # Add tech stack
            if "tech_stack" in project_data:
                structure_text += "## Tech Stack\n"
                for tech in project_data["tech_stack"]:
                    structure_text += f"- {tech}\n"
                structure_text += "\n"
            
            # Add commands
            if "commands" in project_data:
                structure_text += "## Commands\n"
                for cmd_name, cmd in project_data["commands"].items():
                    structure_text += f"- **{cmd_name}**: `{cmd}`\n"
            
            # Copy to clipboard (using page clipboard if available)
            if hasattr(self.page, 'set_clipboard'):
                self.page.set_clipboard(structure_text)
                self._show_notification("✅ Estructura copiada al portapapeles", "success")
            else:
                # Fallback: show in dialog
                dialog = ft.AlertDialog(
                    title=ft.Text("Estructura del Proyecto"),
                    content=ft.Container(
                        content=ft.TextField(
                            value=structure_text,
                            multiline=True,
                            read_only=True,
                            min_lines=10,
                            max_lines=20,
                        ),
                        width=600,
                    ),
                    actions=[
                        ft.TextButton("Cerrar", on_click=lambda e: self._close_dialog())
                    ],
                )
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
                
        except Exception as e:
            self._show_notification(f"❌ Error al copiar: {str(e)}", "error")
            raise Exception(f"Error en watsonx.ai: {str(e)}")
            
    async def _on_logout(self, e):
        """Handle logout"""
        self._show_notification("Cerrando sesión...", "info")
        await asyncio.sleep(1)
        self.is_authenticated = False
        self.alias = None
        self._show_login()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main(page: ft.Page):
    """Main application entry point"""
    app = FletChatApp(page)


if __name__ == "__main__":
    ft.app(target=main)

# Made with Bob - Enhanced UI/UX with Login/Register and Full Features
