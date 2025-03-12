#!/usr/bin/env python3
import time
import random
import threading
import uuid
import json
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Tuple

from faker import Faker
import yaml

from logger import setup_logger
from models import BotApplyStatus, UserActionType  # Import both from models

logger = setup_logger("bot_session")
faker = Faker()


class BotStatus(Enum):
    """Estados possíveis do bot."""
    STARTING = "starting"
    RUNNING = "running" 
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPING = "stopping"


class ApplyStatus(Enum):
    """Estados possíveis de uma aplicação."""
    SUCCESS = "success"
    FAILED = "failed"


class JobInfo:
    """Informações simuladas de uma vaga."""
    
    def __init__(self):
        """Gera uma vaga simulada com dados aleatórios."""
        self.id = str(uuid.uuid4())
        self.title = faker.job()
        self.company = faker.company()
        self.url = f"https://linkedin.com/jobs/view/{faker.numerify('########')}"
        self.location = faker.city()
        self.description = faker.paragraph(nb_sentences=5)
        self.posted_at = faker.date_time_between(start_date="-30d", end_date="now")
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte a vaga para dicionário."""
        return {
            "job_id": self.id,
            "job_title": self.title,
            "job_url": self.url,
            "company_name": self.company,
            "location": self.location,
            "description": self.description,
            "posted_at": self.posted_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class BotSession:
    """Sessão do bot que simula o comportamento do bot real."""
    
    def __init__(self, config, api_client):
        """
        Inicializa a sessão do bot.
        
        Args:
            config: Configurações do bot
            api_client: Cliente para comunicação com o backend
        """
        self.config = config
        self.api_client = api_client
        self.status = BotStatus.STARTING
        
        # Contador de aplicações
        self.total_applied = 0
        self.total_success = 0
        self.total_failed = 0
        
        # Flag para controle de pausas
        self.paused = threading.Event()
        self.should_stop = threading.Event()
        
        # Flag para aguardar ação do usuário
        self.waiting_for_action = threading.Event()
        self.current_action_id = None
        self.action_response = None
        
        # Configurações lidas do YAML
        self.user_config = None
        self.user_resume = None
    
    def run(self) -> None:
        """Executa o bot simulado."""
        try:
            # Enviar evento de início
            self._change_status(BotStatus.STARTING)
            self.api_client.create_event(
                "starting",
                "Iniciando o bot de aplicação",
                "info",
                {"bot_id": self.config.BOT_ID}
            )
            
            # Obter as configurações do usuário
            logger.info("Obtendo configurações e currículo do usuário")
            try:
                config_yaml, resume_yaml = self.api_client.get_config()
                
                # Carregar configurações
                try:
                    self.user_config = yaml.safe_load(config_yaml)
                    logger.info("Configuração do usuário carregada com sucesso")
                except yaml.YAMLError as e:
                    logger.error(f"Erro ao carregar configuração YAML: {e}")
                    self.user_config = {}
                
                try:
                    self.user_resume = yaml.safe_load(resume_yaml)
                    logger.info("Currículo do usuário carregado com sucesso")
                except yaml.YAMLError as e:
                    logger.error(f"Erro ao carregar currículo YAML: {e}")
                    self.user_resume = {}
                
                # Verificar se temos configurações mínimas necessárias
                if not self.user_config:
                    logger.warning("Configuração do usuário está vazia ou inválida")
                
            except Exception as e:
                logger.error(f"Falha ao obter configurações do usuário: {e}")
                self.user_config = {}
                self.user_resume = {}
            
            # Simular login no LinkedIn
            logger.info("Realizando login no LinkedIn")
            self._simulate_login()
            
            # Mudando para status executando
            self._change_status(BotStatus.RUNNING)
            self.api_client.create_event(
                "running",
                "Bot iniciado com sucesso e executando",
                "info",
                {"status": "running", "bot_version": "1.0.0"}
            )
            
            # Simular navegação e aplicações
            self._simulate_job_search_and_apply()
            
            # Finalizar o bot
            self._finalize_bot()
            
        except Exception as e:
            logger.error(f"Erro durante a execução do bot: {e}", exc_info=True)
            self._handle_failure(str(e))
    
    def _change_status(self, new_status: BotStatus) -> None:
        """
        Altera o status do bot.
        
        Args:
            new_status: Novo status do bot
        """
        logger.info(f"Alterando status de {self.status.value} para {new_status.value}")
        self.status = new_status
        
        # Configurar eventos relacionados ao status
        if new_status == BotStatus.PAUSED:
            self.paused.set()
        elif new_status == BotStatus.RUNNING:
            self.paused.clear()
        elif new_status == BotStatus.WAITING:
            self.waiting_for_action.set()
        elif new_status == BotStatus.STOPPING or new_status == BotStatus.COMPLETED or new_status == BotStatus.FAILED:
            self.should_stop.set()
            self.paused.clear()  # Desbloquear threads pausadas para que possam terminar
            self.waiting_for_action.set()  # Desbloquear threads esperando ação
    
    def _simulate_login(self) -> None:
        """Simula o processo de login no LinkedIn."""
        # Evento de navegação até a página de login
        self.api_client.create_event(
            "navigating",
            "Navegando para a página de login do LinkedIn",
            "info",
            {"url": "https://www.linkedin.com/login"}
        )
        
        # Atraso para simular carregamento da página
        time.sleep(2)
        
        # Decidir aleatoriamente se vamos precisar de 2FA (30% de chance)
        needs_2fa = random.random() < 0.3
        
        if needs_2fa:
            # Solicitar código 2FA
            logger.info("Código 2FA solicitado pelo LinkedIn")
            self._change_status(BotStatus.WAITING)
            
            # Enviar evento de espera
            self.api_client.create_event(
                "waiting",
                "Aguardando código de verificação 2FA",
                "info",
                {"reason": "2FA required"}
            )
            
            # Solicitar ação do usuário
            response = self.api_client.request_user_action(
                UserActionType.PROVIDE_2FA.value,
                "Por favor, forneça o código de verificação em dois fatores do LinkedIn",
                "2fa_code"
            )
            
            # Armazenar o ID da ação atual
            self.current_action_id = response["id"]
            
            # Aguardar a resposta do usuário
            logger.info(f"Aguardando resposta do usuário para ação {self.current_action_id}")
            self.waiting_for_action.wait(timeout=300)  # Timeout de 5 minutos
            
            if not self.action_response:
                logger.warning("Tempo limite excedido para ação do usuário")
                self._handle_failure("Tempo limite excedido para código 2FA")
                return
            
            # Resetar as flags
            self.waiting_for_action.clear()
            code = self.action_response.get("input", "")
            logger.info(f"Código 2FA recebido: {code}")
            self.action_response = None
            self.current_action_id = None
            
            # Simulando validação do código
            time.sleep(2)
            
            # Evento de login bem-sucedido com 2FA
            self.api_client.create_event(
                "logged_in",
                "Login no LinkedIn realizado com sucesso usando 2FA",
                "info"
            )
        else:
            # Evento de preenchimento de credenciais
            self.api_client.create_event(
                "login",
                "Preenchendo credenciais de login",
                "info"
            )
            
            # Atraso para simular o preenchimento
            time.sleep(1)
            
            # Evento de submissão de formulário
            self.api_client.create_event(
                "form_submit",
                "Enviando formulário de login",
                "info"
            )
            
            # Atraso para simular o processamento do login
            time.sleep(2)
            
            # Evento de login bem-sucedido
            self.api_client.create_event(
                "logged_in",
                "Login no LinkedIn realizado com sucesso",
                "info"
            )
    
    def _simulate_job_search_and_apply(self) -> None:
        """Simula a busca e aplicação para vagas."""
        # Simular navegação para página de busca
        self.api_client.create_event(
            "navigating",
            "Navegando para a página de busca de vagas",
            "info",
            {"url": "https://www.linkedin.com/jobs/"}
        )
        
        # Atraso para simular carregamento da página
        time.sleep(2)
        
        # Simular pesquisa com os termos do usuário
        # Verificar se user_config existe e fornecer defaults se necessário
        if self.user_config is None:
            logger.warning("Configuração do usuário não está disponível, usando valores padrão")
            positions = ["Software Developer"]
            locations = ["Remote"]
            company_blacklist = []
            title_blacklist = []
        else:
            logger.info(f"Usando configuração do usuário: {type(self.user_config)}")
            try:
                positions = self.user_config.get("positions", ["Software Developer"])
                # Validar positions
                if not positions or not isinstance(positions, list):
                    logger.warning(f"Configuração de posições inválida: {positions}, usando padrão")
                    positions = ["Software Developer"]
                logger.info(f"Posições configuradas: {positions}")
                
                locations = self.user_config.get("locations", ["Remote"])
                # Validar locations
                if not locations or not isinstance(locations, list):
                    logger.warning(f"Configuração de localizações inválida: {locations}, usando padrão")
                    locations = ["Remote"]
                logger.info(f"Localizações configuradas: {locations}")
                
                company_blacklist = self.user_config.get("company_blacklist", [])
                # Validar company_blacklist
                if company_blacklist is None or not isinstance(company_blacklist, list):
                    logger.warning(f"Lista negra de empresas inválida: {company_blacklist}, usando lista vazia")
                    company_blacklist = []
                logger.info(f"Lista negra de empresas: {company_blacklist}")
                
                title_blacklist = self.user_config.get("title_blacklist", [])
                # Validar title_blacklist
                if title_blacklist is None or not isinstance(title_blacklist, list):
                    logger.warning(f"Lista negra de títulos inválida: {title_blacklist}, usando lista vazia")
                    title_blacklist = []
                logger.info(f"Lista negra de títulos: {title_blacklist}")
            except Exception as e:
                logger.error(f"Erro ao processar configuração do usuário: {e}")
                positions = ["Software Developer"]
                locations = ["Remote"]
                company_blacklist = []
                title_blacklist = []
        
        # Assegurar que temos ao menos um valor em cada lista para random.choice
        if not positions:
            positions = ["Software Developer"]
        if not locations:
            locations = ["Remote"]
            
        search_query = f"{random.choice(positions)} em {random.choice(locations)}"
        
        self.api_client.create_event(
            "search_started",
            f"Iniciando busca por: {search_query}",
            "info",
            {"query": search_query}
        )
        
        # Atraso para simular a busca
        time.sleep(3)
        
        # Entrar no loop de aplicações até atingir o limite ou receber comando para parar
        while (self.total_applied < self.config.APPLY_LIMIT and not self.should_stop.is_set()):
            # Verificar se o bot está pausado
            if self.paused.is_set():
                logger.info("Bot está pausado, aguardando comando para continuar")
                self.paused.wait()  # Aguardar até que o bot seja despausado
                if self.should_stop.is_set():
                    break
                
            try:
                # Gerar tempo de espera entre 10 e 60 segundos
                wait_time = random.randint(10, 60)
                logger.info(f"Aguardando {wait_time} segundos antes da próxima aplicação")
                
                # Aguardar, checando a cada segundo se o bot deve parar
                for _ in range(wait_time):
                    if self.should_stop.is_set() or self.paused.is_set():
                        break
                    time.sleep(1)
                
                if self.should_stop.is_set():
                    break
                    
                if self.paused.is_set():
                    continue
                
                # Simular encontrar uma vaga
                job = JobInfo()
                
                self.api_client.create_event(
                    "job_found",
                    f"Vaga encontrada: {job.title} na {job.company}",
                    "info",
                    job.to_dict()
                )
                
                # Atraso para simular a abertura da vaga
                time.sleep(2)
                
                # Verificar se a empresa está na lista negra
                try:
                    if company_blacklist is None:
                        company_blacklist = []
                        logger.warning("company_blacklist é None, usando lista vazia")
                    
                    if any(blacklisted.lower() in job.company.lower() for blacklisted in company_blacklist):
                        logger.info(f"Empresa {job.company} está na lista negra, pulando")
                        self.api_client.create_event(
                            "job_skipped",
                            f"Vaga pulada: empresa {job.company} está na lista negra",
                            "info",
                            {"reason": "blacklisted_company"}
                        )
                        continue
                except Exception as e:
                    logger.error(f"Erro ao verificar lista negra de empresas: {e}")
                
                # Verificar se o título está na lista negra
                try:
                    if title_blacklist is None:
                        title_blacklist = []
                        logger.warning("title_blacklist é None, usando lista vazia")
                        
                    if any(blacklisted.lower() in job.title.lower() for blacklisted in title_blacklist):
                        logger.info(f"Título {job.title} está na lista negra, pulando")
                        self.api_client.create_event(
                            "job_skipped",
                            f"Vaga pulada: título {job.title} está na lista negra",
                            "info",
                            {"reason": "blacklisted_title"}
                        )
                        continue
                except Exception as e:
                    logger.error(f"Erro ao verificar lista negra de títulos: {e}")
                
                # Simular clique no botão de aplicar
                self.api_client.create_event(
                    "apply_started",
                    f"Iniciando aplicação para: {job.title} na {job.company}",
                    "info",
                    job.to_dict()
                )
                
                # Decidir aleatoriamente se vamos precisar resolver um CAPTCHA (15% de chance)
                needs_captcha = random.random() < 0.15
                
                if needs_captcha:
                    # Solicitar resolução de CAPTCHA
                    logger.info("CAPTCHA detectado no processo de aplicação")
                    self._change_status(BotStatus.WAITING)
                    
                    # Enviar evento de espera
                    self.api_client.create_event(
                        "waiting",
                        "CAPTCHA detectado no processo de aplicação",
                        "info",
                        {"reason": "captcha_detected"}
                    )
                    
                    # Solicitar ação do usuário
                    response = self.api_client.request_user_action(
                        UserActionType.SOLVE_CAPTCHA.value,
                        "Por favor, resolva o CAPTCHA para continuar com a aplicação",
                        "captcha_solution"
                    )
                    
                    # Armazenar o ID da ação atual
                    self.current_action_id = response["id"]
                    
                    # Aguardar a resposta do usuário
                    logger.info(f"Aguardando resolução do CAPTCHA pelo usuário para ação {self.current_action_id}")
                    self.waiting_for_action.wait(timeout=300)  # Timeout de 5 minutos
                    
                    if not self.action_response:
                        logger.warning("Tempo limite excedido para resolução do CAPTCHA")
                        self._handle_failure("Tempo limite excedido para resolução do CAPTCHA")
                        return
                    
                    # Resetar as flags
                    self.waiting_for_action.clear()
                    captcha_solution = self.action_response.get("input", "")
                    logger.info(f"CAPTCHA resolvido: {captcha_solution}")
                    self.action_response = None
                    self.current_action_id = None
                    
                    # Voltar ao status RUNNING
                    self._change_status(BotStatus.RUNNING)
                    self.api_client.create_event(
                        "running",
                        "Continuando a aplicação após resolução do CAPTCHA",
                        "info"
                    )
                
                # Simular preenchimento do formulário
                self.api_client.create_event(
                    "form_filling",
                    "Preenchendo formulário de aplicação",
                    "info"
                )
                
                # Atraso para simular o preenchimento
                time.sleep(random.uniform(3, 8))
                
                # 10% de chance de falha na aplicação
                will_fail = random.random() < 0.1
                
                # Registrar aplicação
                apply_start_time = datetime.now(timezone.utc)
                apply_duration = random.randint(15, 120)  # Duração em segundos
                
                try:
                    if will_fail:
                        # Falha aleatória na aplicação
                        failure_reasons = [
                            "Erro no formulário de aplicação",
                            "Problemas de conexão",
                            "Aplicação já realizada anteriormente",
                            "Vaga não está mais disponível",
                            "Perfil incompatível com os requisitos",
                        ]
                        failed_reason = random.choice(failure_reasons)
                        
                        # Registrar a falha
                        apply_data = {
                            "status": BotApplyStatus.FAILED.value,
                            "total_time": apply_duration,
                            "job_title": job.title,
                            "job_url": job.url,
                            "company_name": job.company,
                            "failed_reason": failed_reason
                        }
                        
                        response = self.api_client.register_apply(apply_data)
                        logger.info(f"Aplicação falha registrada: {response}")
                        
                        # Incrementar contadores
                        self.total_applied += 1
                        self.total_failed += 1
                        
                        # Enviar evento de falha
                        self.api_client.create_event(
                            "apply_failed",
                            f"Falha na aplicação: {failed_reason}",
                            "warning",
                            {"job_title": job.title, "company": job.company, "reason": failed_reason}
                        )
                    else:
                        # Aplicação bem-sucedida
                        apply_data = {
                            "status": BotApplyStatus.SUCCESS.value,
                            "total_time": apply_duration,
                            "job_title": job.title,
                            "job_url": job.url,
                            "company_name": job.company
                        }
                        
                        response = self.api_client.register_apply(apply_data)
                        logger.info(f"Aplicação bem-sucedida registrada: {response}")
                        
                        # Incrementar contadores
                        self.total_applied += 1
                        self.total_success += 1
                        
                        # Enviar evento de sucesso
                        self.api_client.create_event(
                            "apply_success",
                            f"Aplicação enviada com sucesso para: {job.title} na {job.company}",
                            "info",
                            {"job_title": job.title, "company": job.company}
                        )
                    
                    # Atualizar o progresso
                    self.api_client.create_event(
                        "progress_update",
                        f"Progresso: {self.total_applied}/{self.config.APPLY_LIMIT} aplicações completadas",
                        "info",
                        {
                            "total_applied": self.total_applied,
                            "total_success": self.total_success,
                            "total_failed": self.total_failed,
                            "apply_limit": self.config.APPLY_LIMIT,
                            "progress_percentage": round(self.total_applied / self.config.APPLY_LIMIT * 100, 1)
                        }
                    )
                except Exception as e:
                    logger.error(f"Erro ao registrar aplicação: {e}", exc_info=True)
                    self.api_client.create_event(
                        "error",
                        f"Erro ao registrar aplicação: {e}",
                        "error",
                        {"error_details": str(e)}
                    )
                
                # Verificar se atingimos o limite
                if self.total_applied >= self.config.APPLY_LIMIT:
                    logger.info(f"Limite de aplicações atingido ({self.config.APPLY_LIMIT})")
                    self._change_status(BotStatus.STOPPING)
                    self.api_client.create_event(
                        "stopping",
                        f"Limite de aplicações atingido: {self.config.APPLY_LIMIT}",
                        "info",
                        {"apply_limit": self.config.APPLY_LIMIT}
                    )
            except Exception as e:
                logger.error(f"Erro durante a aplicação: {e}", exc_info=True)
                
                # Reportar erro como evento
                self.api_client.create_event(
                    "error",
                    f"Erro durante a aplicação: {str(e)}",
                    "error",
                    {"error_details": str(e)}
                )
                
                # Continuar tentando
                continue
    
    def _finalize_bot(self) -> None:
        """Finaliza o bot e envia os eventos de conclusão."""
        # Verificar o status para decidir como finalizar
        if self.status == BotStatus.STOPPING:
            # Finalizar como completo
            self._change_status(BotStatus.COMPLETED)
            
            success_rate = 0 if self.total_applied == 0 else round(self.total_success / self.total_applied * 100, 1)
            
            # Evento de conclusão
            self.api_client.create_event(
                "completed",
                f"Bot concluído com sucesso. Aplicações: {self.total_applied}, Taxa de sucesso: {success_rate}%",
                "info",
                {
                    "total_applies": self.total_applied,
                    "successful_applies": self.total_success,
                    "failed_applies": self.total_failed,
                    "success_rate": f"{success_rate}%"
                }
            )
            
            logger.info(f"Bot concluído com sucesso. Aplicações: {self.total_applied}, Taxa de sucesso: {success_rate}%")
        elif self.status == BotStatus.FAILED:
            # Já enviamos o evento de falha no _handle_failure
            logger.info("Bot finalizado com status de falha.")
    
    def _handle_failure(self, reason: str) -> None:
        """
        Trata uma falha fatal do bot.
        
        Args:
            reason: Motivo da falha
        """
        logger.error(f"Falha fatal do bot: {reason}")
        
        # Mudar o status para falha
        self._change_status(BotStatus.FAILED)
        
        # Enviar evento de falha
        self.api_client.create_event(
            "failed",
            f"Falha do bot: {reason}",
            "error",
            {"reason": reason}
        )
    
    def resolve_user_action(self, action_id: str, data: Dict[str, Any]) -> None:
        """
        Resolve uma ação do usuário.
        
        Args:
            action_id: ID da ação
            data: Dados da resposta do usuário
        """
        if self.current_action_id == action_id:
            logger.info(f"Ação do usuário resolvida: {action_id}")
            self.action_response = data
            
            # Desbloquear a thread que está esperando
            self.waiting_for_action.set()
            
            # Enviar evento de continuação
            self.api_client.create_event(
                "user_action_completed",
                f"Ação do usuário #{action_id} foi concluída",
                "info",
                {"action_id": action_id}
            )
            
            # Voltar ao status executando
            self._change_status(BotStatus.RUNNING)
        else:
            logger.warning(f"Recebida resposta para ação {action_id}, mas a ação atual é {self.current_action_id}") 