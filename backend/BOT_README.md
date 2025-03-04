# LinkedIn Bot System

Este sistema permite gerenciar bots automatizados que aplicam a vagas de emprego no LinkedIn. A arquitetura utiliza Kubernetes para orquestrar os pods que executam os bots, permitindo escalabilidade, isolamento e monitoramento eficiente.

## Arquitetura

O sistema é composto por:

1. **Backend API**: Aplicação FastAPI que gerencia bots, sessões e integrações
2. **Pods Kubernetes**: Contêineres isolados que executam os bots para cada sessão
3. **Banco de Dados**: PostgreSQL para dados relacionais e MongoDB para configurações detalhadas
4. **Monitoramento**: Sistema de logging e notificações sobre eventos dos bots

### Fluxo de Funcionamento

1. Usuário configura preferências de busca de emprego, currículo e credenciais do LinkedIn
2. Usuário inicia uma sessão de bot através da API
3. Backend cria recursos Kubernetes (Pod, ConfigMap, Secret, Service)
4. Bot executa no pod e se comunica com o backend via webhooks
5. Backend monitora status do pod e atualiza o banco de dados
6. Usuário pode pausar, retomar ou parar o bot conforme necessário
7. Após concluir, o bot envia relatório e o backend limpa os recursos Kubernetes

## Configuração do Ambiente

### Pré-requisitos

- Kubernetes cluster configurado
- Acesso ao registry de imagens Docker (para a imagem do bot)
- PostgreSQL e MongoDB
- Python 3.9+

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente:

```bash
# Kubernetes
KUBERNETES_IN_CLUSTER=false  # true se rodando dentro do cluster
BOT_IMAGE=ghcr.io/linkedin-bot:latest  # imagem do bot

# Webhook
WEBHOOK_TOKEN=seu_token_secreto
WEBHOOK_URI=http://api-service:8000/api/v1/webhooks/bot

# API
SERVER_HOST=http://localhost:8000
```

### Service Account Kubernetes

Crie uma service account com permissões para gerenciar pods:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: bot-sa
  namespace: bot-jobs
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: bot-role
  namespace: bot-jobs
rules:
- apiGroups: [""]
  resources: ["pods", "configmaps", "secrets", "services"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: bot-role-binding
  namespace: bot-jobs
subjects:
- kind: ServiceAccount
  name: bot-sa
  namespace: bot-jobs
roleRef:
  kind: Role
  name: bot-role
  apiGroup: rbac.authorization.k8s.io
```

## Executando o Sistema

### Instalação de Dependências

```bash
cd backend
poetry install
```

### Configuração do Banco de Dados

Execute as migrações do banco de dados:

```bash
alembic upgrade head
```

### Inicialização do Backend

```bash
uvicorn app.main:app --reload
```

## API de Gerenciamento de Bots

### Criação de Sessão

```http
POST /api/v1/bot/sessions/
Content-Type: application/json

{
  "bot_config_id": "uuid-da-configuracao",
  "applies_limit": 50,
  "time_limit": 3600
}
```

### Controle de Sessão

```http
POST /api/v1/bot/sessions/{session_id}/stop
POST /api/v1/bot/sessions/{session_id}/pause
POST /api/v1/bot/sessions/{session_id}/resume
```

### Monitoramento de Status

```http
GET /api/v1/bot/sessions/{session_id}
GET /api/v1/bot/sessions/{session_id}/events
GET /api/v1/bot/sessions/{session_id}/applies
```

## Webhook API

Os bots se comunicam com o backend através de webhooks:

```http
POST /api/v1/webhooks/bot/{session_id}
X-API-Key: {api_key}
Content-Type: application/json

{
  "event_type": "apply_started",
  "data": {
    "job_id": "12345",
    "job_title": "Software Engineer",
    "company_name": "Example Inc",
    "job_url": "https://www.linkedin.com/jobs/view/12345"
  }
}
```

## Monitoramento e Manutenção

### Verificação de Status

```bash
kubectl get pods -n bot-jobs
kubectl logs -n bot-jobs {pod-name}
```

### Endpoints de Administração

```http
POST /api/v1/webhooks/status-update  # Atualiza status de todos os bots
```

## Solução de Problemas

### Pod não inicia

Verifique os logs do pod:

```bash
kubectl describe pod -n bot-jobs {pod-name}
kubectl logs -n bot-jobs {pod-name}
```

### Bot falha durante execução

1. Verifique os logs do pod
2. Verifique os eventos do bot na API
3. Verifique as credenciais do LinkedIn

### Recursos não são limpos

Execute manualmente a limpeza:

```bash
kubectl delete pod,configmap,secret,service -n bot-jobs -l session-id={session_id}
```

## Desenvolvimento do Bot

A imagem Docker do bot deve:

1. Aceitar as variáveis de ambiente especificadas
2. Implementar um endpoint HTTP para receber comandos
3. Enviar eventos para o webhook do backend
4. Gerenciar o ciclo de vida da sessão de aplicação

### Exemplo de Dockerfile para o Bot

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py"]
``` 