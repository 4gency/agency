#!/usr/bin/env python3
import os
import sys
import time
import random
import logging
import uuid
import threading
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from waitress import serve
import requests
import yaml
import backoff

from config import Config
from logger import setup_logger
from bot_session import BotSession
from api_client import APIClient

# Configurar logger
logger = setup_logger("bot_mock")

def validate_env_vars() -> bool:
    """Valida as variáveis de ambiente necessárias."""
    required_vars = [
        "API_PORT",
        "LINKEDIN_EMAIL",
        "LINKEDIN_PASSWORD",
        "APPLY_LIMIT",
        "STYLE_CHOICE",
        "SEC_CH_UA",
        "SEC_CH_UA_PLATFORM",
        "USER_AGENT",
        "BACKEND_TOKEN",
        "BACKEND_URL",
        "BOT_ID"
    ]

    for var in required_vars:
        if not os.environ.get(var):
            logger.error(f"Variável de ambiente {var} não definida")
            return False

    # Validar style choice
    valid_styles = [
        "Cloyola Grey",
        "Modern Blue",
        "Modern Grey",
        "Default",
        "Clean Blue"
    ]
    style = os.environ.get("STYLE_CHOICE")
    if style not in valid_styles:
        logger.error(f"STYLE_CHOICE deve ser um dos seguintes: {', '.join(valid_styles)}")
        return False

    # Validar valor do APPLY_LIMIT
    try:
        apply_limit = int(os.environ.get("APPLY_LIMIT", "0"))
        if apply_limit <= 0:
            logger.error("APPLY_LIMIT deve ser um número maior que zero")
            return False
    except ValueError:
        logger.error("APPLY_LIMIT deve ser um número válido")
        return False

    # Validar que a porta é um número
    try:
        port = int(os.environ.get("API_PORT", "0"))
        if port <= 0 or port > 65535:
            logger.error("API_PORT deve ser um número válido entre 1 e 65535")
            return False
    except ValueError:
        logger.error("API_PORT deve ser um número válido")
        return False

    return True

def create_app():
    """Cria a aplicação Flask."""
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

    @app.route('/action/<action_id>', methods=['POST'])
    def handle_action(action_id):
        """Endpoint para receber resposta de ações do usuário."""
        try:
            data = request.json
            logger.info(f"Recebida resposta para ação {action_id}: {data}")
            
            # Notificar o bot para continuar o processo
            if hasattr(app, 'bot_session'):
                app.bot_session.resolve_user_action(action_id, data)
                return jsonify({"status": "success", "message": "Ação processada com sucesso"})
            else:
                return jsonify({"status": "error", "message": "Bot não está inicializado"}), 500
        except Exception as e:
            logger.error(f"Erro ao processar ação do usuário: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return app

def start_api_server(app, port):
    """Inicia o servidor API."""
    logger.info(f"Iniciando API na porta {port}")
    serve(app, host='0.0.0.0', port=port)

def main():
    """Função principal do bot."""
    # Verificar variáveis de ambiente
    if not validate_env_vars():
        logger.error("Falha na validação das variáveis de ambiente. Encerrando.")
        sys.exit(1)
    
    # Carregar configuração
    config = Config()
    
    # Inicializar cliente API
    api_client = APIClient(config.BACKEND_URL, config.BACKEND_TOKEN)
    
    # Criar a sessão do bot
    bot = BotSession(config, api_client)
    
    # Inicializar aplicação Flask
    app = create_app()
    app.bot_session = bot
    
    # Iniciar o servidor API em uma thread separada
    api_thread = threading.Thread(target=start_api_server, args=(app, config.API_PORT), daemon=True)
    api_thread.start()
    
    try:
        # Iniciar o bot
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar o bot: {e}")
    finally:
        logger.info("Encerrando bot")
        sys.exit(0)

if __name__ == "__main__":
    main() 