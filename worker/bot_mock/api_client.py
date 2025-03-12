#!/usr/bin/env python3
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import os
import uuid

import requests
import backoff
import yaml

from logger import setup_logger

logger = setup_logger("api_client")


class APIClient:
    """Cliente para comunicação com o backend."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Inicializa o cliente API.
        
        Args:
            base_url: URL base do backend
            api_key: Token de autenticação
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"api-key": api_key}
        self.config_yaml = None
        self.resume_yaml = None
    
    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, ConnectionError),
        max_tries=5,
        jitter=backoff.full_jitter
    )
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Faz uma requisição HTTP com retry exponencial.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo
            data: Dados para enviar (opcional)
            
        Returns:
            Dict com a resposta da API ou erro
        """
        url = f"{self.base_url}/api/v1/bot-webhook{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição {method} {endpoint}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Resposta do erro: {e.response.text}")
            raise
    
    def get_config(self) -> Tuple[str, str]:
        """
        Obtém as configurações e currículo do usuário.
        
        Returns:
            Tupla com as configurações e currículo em formato YAML
        """
        logger.info("Obtendo configurações do usuário")
        try:
            response = self._make_request("GET", "/config")
            
            if "user_config" not in response or "user_resume" not in response:
                logger.error(f"Resposta da API incompleta: {response}")
                raise ValueError("Resposta da API não contém os campos esperados")
            
            # Log do tamanho dos YAMLs para debug
            user_config = response["user_config"]
            user_resume = response["user_resume"]
            
            logger.info(f"Recebido user_config com {len(user_config)} caracteres")
            logger.info(f"Recebido user_resume com {len(user_resume)} caracteres")
            
            # Salvar as configurações em arquivo para debug
            configs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
            os.makedirs(configs_dir, exist_ok=True)
            
            config_path = os.path.join(configs_dir, "user_config.yaml")
            with open(config_path, "w") as f:
                f.write(user_config)
            logger.info(f"Configuração salva em {config_path}")
            
            resume_path = os.path.join(configs_dir, "user_resume.yaml")
            with open(resume_path, "w") as f:
                f.write(user_resume)
            logger.info(f"Currículo salvo em {resume_path}")
            
            # Verificar se os YAMLs são válidos sem atribuir o resultado
            try:
                # Apenas verificar se o parsing funciona
                yaml.safe_load(user_config)
                yaml.safe_load(user_resume)
                logger.info("Configurações obtidas e validadas com sucesso")
            except yaml.YAMLError as e:
                logger.error(f"YAML inválido recebido da API: {e}")
                # Não levantamos exceção aqui para permitir que o bot continue
                # O processamento real do YAML acontecerá no bot_session.py
            
            return user_config, user_resume
            
        except Exception as e:
            logger.error(f"Erro ao obter configurações: {e}")
            # Retornar YAMLs vazios mas válidos em caso de erro
            return "{}", "{}"
    
    def register_apply(self, apply_data: Dict) -> Dict:
        """
        Registra uma aplicação para vaga.
        
        Args:
            apply_data: Dados da aplicação
            
        Returns:
            Dict com a resposta da API
        """
        logger.info(f"Registrando aplicação: {apply_data}")
        return self._make_request("POST", "/apply", apply_data)
    
    def create_event(self, event_type: str, message: str, severity: str = "info", details: Optional[Dict] = None) -> Dict:
        """
        Cria um evento no backend.
        
        Args:
            event_type: Tipo do evento
            message: Mensagem do evento
            severity: Severidade do evento (info, warning, error)
            details: Detalhes adicionais
            
        Returns:
            Dict com a resposta da API
        """
        event_data = {
            "type": event_type,
            "message": message,
            "severity": severity,
            "details": details or {}
        }
        logger.info(f"Criando evento: {event_data}")
        return self._make_request("POST", "/events", event_data)
    
    def request_user_action(self, action_type: str, description: str, input_field: Optional[str] = None) -> Dict:
        """
        Solicita uma ação do usuário.
        
        Args:
            action_type: Tipo da ação (PROVIDE_2FA, SOLVE_CAPTCHA, ANSWER_QUESTION)
            description: Descrição da ação para o usuário
            input_field: Campo para entrada do usuário (opcional)
            
        Returns:
            Dict com a resposta da API contendo o ID da ação
        """
        # Convert action_type to lowercase as expected by the API
        # (API expects 'provide_2fa' but our enum uses 'PROVIDE_2FA')
        lowercase_action_type = action_type.lower()
        
        action_data = {
            "action_type": lowercase_action_type,
            "description": description,
            "input_field": input_field
        }
        logger.info(f"Solicitando ação do usuário: {action_data}")
        return self._make_request("POST", "/user-actions", action_data) 