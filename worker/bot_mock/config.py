#!/usr/bin/env python3
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Classe para armazenar as configurações do bot."""
    
    def __init__(self):
        """Inicializa as configurações a partir das variáveis de ambiente."""
        # Configurações da API
        self.API_PORT = int(os.environ.get("API_PORT", "5000"))
        
        # Credenciais do LinkedIn
        self.LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL", "")
        self.LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "")
        
        # Configurações de aplicação
        self.APPLY_LIMIT = int(os.environ.get("APPLY_LIMIT", "200"))
        self.STYLE_CHOICE = os.environ.get("STYLE_CHOICE", "Modern Blue")
        
        # Headers do navegador
        self.SEC_CH_UA = os.environ.get("SEC_CH_UA", "")
        self.SEC_CH_UA_PLATFORM = os.environ.get("SEC_CH_UA_PLATFORM", "")
        self.USER_AGENT = os.environ.get("USER_AGENT", "")
        
        # Configurações do backend
        self.BACKEND_TOKEN = os.environ.get("BACKEND_TOKEN", "")
        self.BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
        self.BOT_ID = os.environ.get("BOT_ID", "")
        
        # URL do serviço Gotenberg (opcional)
        self.GOTENBERG_URL = os.environ.get("GOTENBERG_URL", "")
        
        # Diretórios
        self.CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
        os.makedirs(self.CONFIG_DIR, exist_ok=True) 