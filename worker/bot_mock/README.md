# LinkedIn Bot Mock

Este é um bot mock para simulação de aplicações de emprego no LinkedIn, projetado para integrar-se com o sistema de backend por meio das APIs webhook.

## Funcionalidades

- Simulação do processo de login no LinkedIn (com possibilidade de 2FA)
- Busca de vagas baseada nas configurações do usuário
- Aplicação para vagas com intervalo aleatório entre 10 e 60 segundos
- Suporte a solicitações de ação do usuário (2FA, CAPTCHA, perguntas)
- Registro de aplicações bem-sucedidas e falhas (10% de chance de falha)
- Eventos detalhados para acompanhamento do progresso
- Validação de configurações YAML
- Suporte a limitação de aplicações

## Variáveis de ambiente

```
API_PORT=8080                 # Porta para a API do bot
LINKEDIN_EMAIL=email@exemplo.com # Email do LinkedIn
LINKEDIN_PASSWORD=senha123     # Senha do LinkedIn
APPLY_LIMIT=200               # Limite de aplicações
STYLE_CHOICE=Modern Blue      # Estilo do currículo
SEC_CH_UA=...                 # Header User-Agent Client Hints
SEC_CH_UA_PLATFORM=Windows    # Plataforma do User-Agent
USER_AGENT=...                # User-Agent completo
BACKEND_TOKEN=chave_secreta   # Token para autenticação com o backend
BACKEND_URL=http://api:5000   # URL do backend
BOT_ID=1234                   # ID do bot
GOTENBERG_URL=http://gotenberg:3000 # URL do serviço Gotenberg (opcional)
```

## Estilos disponíveis

- "Cloyola Grey"
- "Modern Blue" 
- "Modern Grey"
- "Default"
- "Clean Blue"

## Executando com Docker

Para executar o bot usando Docker:

```bash
docker build -t linkedin-bot-mock .
docker run -p 8080:8080 --env-file .env linkedin-bot-mock
```

## Executando com Docker Compose

Para executar o bot usando Docker Compose:

```bash
docker-compose up -d
```

## API do Bot

O bot expõe uma API para interagir com ele:

- `GET /health` - Verifica se o bot está funcionando
- `POST /action/<action_id>` - Endpoint para receber respostas de ações do usuário

## Fluxo de Execução

1. Bot inicia e valida as variáveis de ambiente
2. Bot obtém configurações e currículo do backend
3. Bot simula login no LinkedIn (pode solicitar 2FA)
4. Bot navega para a página de busca de vagas
5. Bot inicia o loop de busca e aplicação:
   - Encontra uma vaga
   - Verifica se empresa/título está na lista negra
   - Simula o processo de aplicação (pode solicitar CAPTCHA)
   - Registra aplicação (sucesso ou falha)
   - Aguarda entre 10 e 60 segundos antes da próxima aplicação
6. Bot finaliza quando atinge o limite de aplicações

## Eventos Gerados

O bot gera diversos eventos para monitoramento:

- `starting` - Iniciando o bot
- `running` - Bot em execução
- `paused` - Bot pausado
- `waiting` - Aguardando ação do usuário
- `completed` - Bot finalizado com sucesso
- `failed` - Bot finalizado com erro
- `stopping` - Bot finalizando

Além desses, outros eventos específicos são gerados durante o processo de aplicação, como:

- `navigating` - Navegando para uma página
- `login` - Preenchendo credenciais
- `logged_in` - Login realizado com sucesso
- `search_started` - Iniciando busca por vagas
- `job_found` - Vaga encontrada
- `job_skipped` - Vaga pulada
- `apply_started` - Iniciando aplicação
- `apply_success` - Aplicação bem-sucedida
- `apply_failed` - Falha na aplicação
- `progress_update` - Atualização de progresso

## Ações do Usuário

O bot pode solicitar ações do usuário em determinados momentos:

- `PROVIDE_2FA` - Fornecer código de verificação em dois fatores
- `SOLVE_CAPTCHA` - Resolver um CAPTCHA
- `ANSWER_QUESTION` - Responder a uma pergunta personalizada

## Logs

O bot gera logs detalhados em:

- Console (colorido)
- Arquivo `logs/bot_mock.log` 