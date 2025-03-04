import logging
import uuid
from typing import Any

import yaml
from fastapi import HTTPException, status
from odmantic.session import AIOSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bot import (
    BotConfiguration,
    BotConfigurationCreate,
    LinkedInCredentials,
    LinkedInCredentialsCreate,
)
from app.models.crud import config as config_crud
from app.core.security import decrypt_password, encrypt_password

logger = logging.getLogger(__name__)


class BotConfigService:
    """
    Serviço para gerenciar configurações do bot e credenciais do LinkedIn.
    """

    def __init__(self, db: AsyncSession, nosql_db: AIOSession):
        """
        Inicializa o serviço com sessões para ambos os bancos de dados.

        Args:
            db: Sessão do PostgreSQL (SQLAlchemy/SQLModel)
            nosql_db: Sessão do MongoDB (odmantic)
        """
        self.db = db
        self.nosql_db = nosql_db

    async def convert_config_to_yaml(
        self, subscription_id: uuid.UUID
    ) -> tuple[str, str]:
        """
        Recupera a configuração e currículo existentes e converte para YAML.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Tuple[config_yaml, resume_yaml]

        Raises:
            HTTPException: Se não encontrar configuração ou currículo
        """
        # Busca config
        config = config_crud.get_config(
            session=self.nosql_db,
            subscription_id=str(subscription_id),
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Config not found for subscription {subscription_id}",
            )

        # Busca currículo
        resume = await config_crud.get_resume_async(
            session=self.nosql_db,
            subscription_id=str(subscription_id),
        )

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found for subscription {subscription_id}",
            )

        # Converter para YAML
        config_dict = config.model_dump(exclude={"id", "subscription_id", "user_id"})
        resume_dict = resume.model_dump(exclude={"id", "subscription_id", "user_id"})

        # Ajuste para tornar os dados mais compatíveis com o bot
        config_dict = self._sanitize_dict_for_yaml(config_dict)
        resume_dict = self._sanitize_dict_for_yaml(resume_dict)

        config_yaml = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
        resume_yaml = yaml.dump(resume_dict, default_flow_style=False, sort_keys=False)

        return config_yaml, resume_yaml

    def _sanitize_dict_for_yaml(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitiza um dicionário para ser convertido para YAML.
        Remove valores None e sanitiza listas e dicionários aninhados.

        Args:
            data: Dicionário a ser sanitizado

        Returns:
            Dicionário sanitizado
        """
        result = {}

        for key, value in data.items():
            # Pular valores None
            if value is None:
                continue

            # Processar dicionários aninhados
            if isinstance(value, dict):
                sanitized = self._sanitize_dict_for_yaml(value)
                if sanitized:  # Só adiciona se não estiver vazio
                    result[key] = sanitized

            # Processar listas
            elif isinstance(value, list):
                if value:  # Só adiciona se a lista não estiver vazia
                    sanitized_list = []
                    for item in value:
                        if isinstance(item, dict):
                            sanitized_item = self._sanitize_dict_for_yaml(item)
                            if sanitized_item:  # Só adiciona se não estiver vazio
                                sanitized_list.append(sanitized_item)
                        else:
                            sanitized_list.append(item)

                    if sanitized_list:  # Só adiciona se a lista não estiver vazia
                        result[key] = sanitized_list
            else:
                result[key] = value

        return result

    async def get_linkedin_credentials(
        self, subscription_id: uuid.UUID
    ) -> LinkedInCredentials | None:
        """
        Obtém as credenciais do LinkedIn para uma assinatura.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Credenciais do LinkedIn ou None se não encontradas
        """
        result = await self.db.execute(
            select(LinkedInCredentials).where(
                LinkedInCredentials.subscription_id == subscription_id
            )
        )
        credentials = result.scalars().first()

        # Descriptografa a senha, se necessário
        if credentials and credentials.password:
            try:
                credentials.password = decrypt_password(credentials.password)
            except Exception as e:
                # Log the error, but return credentials with encrypted password
                logger.error(f"Error decrypting password: {str(e)}")

        return credentials

    async def create_or_update_linkedin_credentials(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        credentials: LinkedInCredentialsCreate,
    ) -> LinkedInCredentials:
        """
        Cria ou atualiza as credenciais do LinkedIn para uma assinatura.

        Args:
            user_id: ID do usuário
            subscription_id: ID da assinatura
            credentials: Dados das credenciais

        Returns:
            Credenciais criadas ou atualizadas

        Raises:
            HTTPException: Se a assinatura não existir ou não pertencer ao usuário
        """
        # Verificar se a assinatura existe e pertence ao usuário
        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
            )

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this subscription",
            )

        # Criptografar a senha
        encrypted_password = encrypt_password(credentials.password)

        # Verificar se já existem credenciais
        existing = await self.get_linkedin_credentials(subscription_id)

        if existing:
            # Atualizar credenciais existentes
            existing.email = credentials.email
            existing.password = encrypted_password
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)

            # Retornar com senha descriptografada para uso imediato
            existing.password = credentials.password
            return existing

        # Criar novas credenciais
        new_credentials = LinkedInCredentials(
            subscription_id=subscription_id,
            user_id=user_id,
            email=credentials.email,
            password=encrypted_password,
        )

        self.db.add(new_credentials)
        await self.db.commit()
        await self.db.refresh(new_credentials)

        # Retornar com senha descriptografada para uso imediato
        new_credentials.password = credentials.password
        return new_credentials

    async def get_bot_configuration(
        self, subscription_id: uuid.UUID
    ) -> BotConfiguration | None:
        """
        Obtém a configuração do bot para uma assinatura.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Configuração do bot ou None se não encontrada
        """
        result = await self.db.execute(
            select(BotConfiguration).where(
                BotConfiguration.subscription_id == subscription_id
            )
        )
        return result.scalars().first()

    async def create_or_update_bot_configuration(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        config: BotConfigurationCreate,
    ) -> BotConfiguration:
        """
        Cria ou atualiza a configuração do bot para uma assinatura.

        Args:
            user_id: ID do usuário
            subscription_id: ID da assinatura
            config: Dados da configuração

        Returns:
            Configuração criada ou atualizada

        Raises:
            HTTPException: Se a assinatura não existir ou não pertencer ao usuário
        """
        # Verificar se a assinatura existe e pertence ao usuário
        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
            )

        if subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this subscription",
            )

        # Verificar se já existe configuração
        existing = await self.get_bot_configuration(subscription_id)

        if existing:
            # Atualizar configuração existente
            existing.style_choice = config.style_choice
            if config.user_agent:
                existing.user_agent = config.user_agent
            if config.sec_ch_ua:
                existing.sec_ch_ua = config.sec_ch_ua
            if config.sec_ch_ua_platform:
                existing.sec_ch_ua_platform = config.sec_ch_ua_platform

            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Criar nova configuração
        new_config = BotConfiguration(
            subscription_id=subscription_id,
            user_id=user_id,
            style_choice=config.style_choice,
            user_agent=config.user_agent
            or BotConfiguration.__fields__["user_agent"].default,
            sec_ch_ua=config.sec_ch_ua
            or BotConfiguration.__fields__["sec_ch_ua"].default,
            sec_ch_ua_platform=config.sec_ch_ua_platform
            or BotConfiguration.__fields__["sec_ch_ua_platform"].default,
        )

        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)

        return new_config

    async def _get_subscription(self, subscription_id: uuid.UUID):
        """
        Método auxiliar para obter uma assinatura.

        Args:
            subscription_id: ID da assinatura

        Returns:
            Assinatura ou None se não encontrada
        """
        from app.models.core import Subscription

        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalars().first()
