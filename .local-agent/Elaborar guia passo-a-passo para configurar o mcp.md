<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Elaborar guia passo-a-passo para configurar o mcp server do docker MCP_DOCKER no agente de IA Hermes que está dentro de um conteiner no docker, veja o dockerfile e o compose.

Você já tem quase tudo pronto na imagem para o Hermes; falta só instalar o servidor MCP de Docker e registrá‑lo no `config.yaml` do Hermes, levando em conta que ele está rodando dentro do container.[^1][^2][^3]

***

## 1. Entender o cenário atual

- Sua imagem é baseada em `python:3.11-slim`, instala o `uv` via `pip` e depois instala o Hermes Agent pelo script oficial (`curl ... hermes-agent/main/scripts/install.sh | bash`).[^2][^4]
- O serviço `agents` no `docker-compose-2.yml` usa `working_dir: /workspaces` e monta seu projeto Windows em `/workspaces`, com `extra_hosts` para `host.docker.internal`. Isso facilita falar com serviços na máquina host a partir do container.[^1]

Esses detalhes importam porque:

- o Hermes vai ler sua configuração em `~/.hermes/config.yaml` dentro do container;[^5][^3]
- o servidor MCP de Docker (`docker-mcp` ou equivalente) precisa conseguir se conectar ao Docker Engine (via socket ou HTTP), o que pode envolver montar o socket da máquina host no container.[^6]

***

## 2. Verificar pré‑requisitos do `docker-mcp`

O projeto `docker-mcp` (servidor MCP para gerenciar Docker/Compose) exige Python 3.12+, `uv` e Docker Desktop/Engine disponíveis.[^6]

- Como sua imagem hoje é `python:3.11-slim`, vale considerar trocar a base para `python:3.12-slim` no Dockerfile para ficar estritamente compatível com o requisito do `docker-mcp`.[^2][^6]
- Se você não puder mudar a base agora, pode tentar rodar o `docker-mcp` mesmo assim, mas tenha em mente que qualquer erro estranho pode ser devido à versão do Python não suportada.[^6]

***

## 3. Ajustar o `docker-compose-2.yml` (acesso ao Docker)

O servidor MCP de Docker normalmente conversa com o Docker via o socket padrão `/var/run/docker.sock` ou via `DOCKER_HOST` para um endpoint remoto.[^6]

Dentro do seu `docker-compose-2.yml`, adicione (se ainda não existir) o volume do socket para o serviço `agents`:

```yaml
services:
  agents:
    build:
      context: .
    working_dir: /workspaces
    volumes:
      - "C:/Users/julio.chaves/PycharmProjects/IDE-IDT/INSS/MBA-INSS:/workspaces"
      - "/var/run/docker.sock:/var/run/docker.sock"  # acesso ao Docker da máquina host
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

- Isso permite que qualquer processo dentro do container (incluindo o `docker-mcp`) fale com o Docker Engine da máquina host através do socket.[^6]

Recrie o container:

```bash
docker compose -f docker-compose-2.yml build agents
docker compose -f docker-compose-2.yml up -d agents
```


***

## 4. Entrar no container do Hermes

Com o serviço no ar:

```bash
docker compose -f docker-compose-2.yml exec agents bash
```

Dentro do container:

1. Confirme que o Hermes está instalado:

```bash
hermes --version
```

2. Confirme que o `uv` está disponível (foi instalado no Dockerfile):[^2]

```bash
uv --version
```


O Hermes já vem com suporte a MCP incluído se você usou o instalador padrão; caso contrário, a doc recomenda:

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```


***

## 5. Instalar o servidor MCP de Docker no container

### Opção A – usando `uvx` (modo “quickstart”)

O README do `docker-mcp` exemplifica o uso em clientes MCP (como Claude) via `uvx docker-mcp`, isto é, chamando diretamente o executável via `uvx`.[^6]

Dentro do container, teste:

```bash
uvx docker-mcp --help
```

Se funcionar, significa que o `docker-mcp` pode ser baixado e rodado sob demanda pelo `uvx` (sem clone manual). Nesse caso você nem precisa instalar nada “fixo”: o Hermes chamará `uvx docker-mcp` sempre que precisar.[^6]

### Opção B – clonar o repositório (mais estável)

Se preferir deixar o código local (ou se `uvx` não estiver disponível), faça:

```bash
cd /opt
git clone https://github.com/QuantGeekDev/docker-mcp.git
cd docker-mcp
uv sync  # ou instrução equivalente do README do projeto
```

O próprio README mostra uma configuração típica de cliente MCP chamando o servidor via `uv --directory <path> run docker-mcp`:[^6]

```json
"docker-mcp": {
  "command": "uv",
  "args": [
    "--directory",
    "<path-to-docker-mcp>",
    "run",
    "docker-mcp"
  ]
}
```

Você vai reaproveitar exatamente essa forma no Hermes.

***

## 6. Registrar o servidor MCP_DOCKER no Hermes

O Hermes lê as definições de MCP em `~/.hermes/config.yaml`, na chave `mcp_servers`.[^3][^5]
Você pode:

- ou editar o YAML manualmente;
- ou usar o comando interativo `hermes mcp add`, que já faz a detecção de ferramentas e grava o `config.yaml` para você.[^7][^3]


### 6.1. Usando `hermes mcp add` (recomendado)

Dentro do container:

#### Se usar `uvx` (Opção A):

```bash
hermes mcp add docker-mcp --command uvx --args docker-mcp
```

- `docker-mcp` aqui é o nome lógico do servidor dentro do Hermes (pode ser `MCP_DOCKER` se quiser, mas vou usar `docker-mcp` por simetria com o projeto).[^3][^7]
- `--command uvx --args docker-mcp` diz ao Hermes que este é um servidor MCP de stdio executado localmente via `uvx docker-mcp`.[^3][^6]

O fluxo será:

1. O Hermes pergunta se precisa de autenticação HTTP; no caso do `docker-mcp` local, normalmente não precisa, então pode escolher “não”.[^7][^3]
2. Ele tenta conectar ao servidor, listar as ferramentas MCP expostas e mostra uma lista interativa para você escolher quais ferramentas expor (whitelist).[^8][^7][^3]
3. Ao final, grava a entrada em `~/.hermes/config.yaml` sob `mcp_servers.docker-mcp`.

#### Se usar repositório clonado (Opção B)

Assumindo que você clonou em `/opt/docker-mcp`:

```bash
hermes mcp add docker-mcp \
  --command uv \
  --args --directory \
  --args /opt/docker-mcp \
  --args run \
  --args docker-mcp
```

Isso produz no `config.yaml` algo equivalente a:[^7][^3]

```yaml
mcp_servers:
  docker-mcp:
    command: "uv"
    args: ["--directory", "/opt/docker-mcp", "run", "docker-mcp"]
    enabled: true
    tools:
      include:
        - <lista_de_tools_que_você_marcou>
```


### 6.2. Editando `~/.hermes/config.yaml` manualmente (alternativa)

Se preferir, você pode abrir o arquivo de configuração diretamente (ele é criado automaticamente no primeiro uso do Hermes):[^5][^3]

```bash
vim ~/.hermes/config.yaml
```

E adicionar algo como (Opção A – `uvx`):

```yaml
mcp_servers:
  docker-mcp:
    command: "uvx"
    args: ["docker-mcp"]
    enabled: true
    # tools:  # opcional – whitelist explícita se quiser limitar
    #   include: [list_containers, list_images]
```

Ou (Opção B – repositório clonado):

```yaml
mcp_servers:
  docker-mcp:
    command: "uv"
    args: ["--directory", "/opt/docker-mcp", "run", "docker-mcp"]
    enabled: true
```

Depois de alterar manualmente, rode:

```bash
hermes mcp test docker-mcp
```

para garantir que o Hermes consegue conectar e listar as ferramentas.[^3][^7]

***

## 7. Testar o servidor MCP_DOCKER com o Hermes

Ainda dentro do container:

1. Teste direto o servidor MCP:

```bash
hermes mcp test docker-mcp
```

    - Se estiver tudo certo, o comando mostra o tipo de transporte (`stdio → uvx docker-mcp` ou `stdio → uv ...`), o tempo de conexão e o número de ferramentas descobertas.[^7][^3]
2. Inicie uma sessão de chat do Hermes:

```bash
hermes chat
```

3. Pergunte algo que force o uso do servidor de Docker, por exemplo:
    - “Liste os containers Docker em execução e resuma o status de cada um.”
    - “Verifique se existe um container chamado `agents` e mostre os logs recentes.”

O Hermes registra as tools de MCP com prefixo `mcp_<nome_servidor>_<nome_tool>`, por exemplo `mcp_docker_mcp_list_containers`, mas na prática você não precisa chamar o nome exato da tool; basta descrever a tarefa que o agente escolhe a ferramenta correta.[^3]

Se você editar o `config.yaml` depois (por exemplo, para ajustar `tools.include`), use `/reload-mcp` dentro da sessão do Hermes para recarregar as configurações sem reiniciar o processo:[^8][^3]

```text
/reload-mcp
```

### SEGREDO FINAL NÃO EXPLICADO

```bash
vi ~/.hermes/config.yaml

mcp_servers:
  docker-mcp:
    command: uvx
    args:
      - docker-mcp
    enabled: true
  docker-research:
    command: uvx
    args:
      - docker-mcp
      - gateway
      - run
      - --profile
      - research
    enabled: true
```
Precisa de `uvx` para rodar o `docker-mcp` localmente.


## 8. Resumo do fluxo prático

1. Ajustar `docker-compose-2.yml` para montar `/var/run/docker.sock` (para o servidor MCP falar com o Docker host).[^1][^6]
2. Subir o container `agents` e entrar via `docker compose exec agents bash`.[^1]
3. Verificar `hermes --version` e `uv --version` dentro do container.[^2][^3]
4. Instalar/validar o `docker-mcp` (via `uvx docker-mcp` ou clone + `uv run docker-mcp`).[^6]
5. Registrar o servidor no Hermes com `hermes mcp add docker-mcp --command uvx --args docker-mcp` (ou a variante com `uv --directory /opt/docker-mcp run docker-mcp`).[^7][^3][^6]
6. Testar com `hermes mcp test docker-mcp` e depois usar `hermes chat` para pedir operações em containers Docker, deixando o Hermes acionar o MCP_DOCKER automaticamente.[^3][^7]

Se você quiser, na próxima iteração posso sugerir um `Dockerfile` já ajustado para `python:3.12-slim` e com o `docker-mcp` pré-instalado, mais um `config.yaml` de exemplo pronto para copiar.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^9]</span>

<div align="center">⁂</div>

[^1]: docker-compose-2.yml

[^2]: Dockerfile

[^3]: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp

[^4]: https://hermes-agent.nousresearch.com/docs/

[^5]: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

[^6]: https://github.com/QuantGeekDev/docker-mcp

[^7]: https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/mcp_config.py

[^8]: https://hermes-agent.nousresearch.com/docs/guides/use-mcp-with-hermes

[^9]: https://composio.dev/toolkits/docker_hub/framework/hermes-agent

[^10]: https://sema4.ai/docs/build-agents/mcp/docker-mcp

[^11]: https://hexdocs.pm/hermes_mcp/home.html

[^12]: https://github.com/outsourc-e/hermes-workspace/issues/560

[^13]: https://www.youtube.com/watch?v=ZhlM4ntQBGI

[^14]: https://www.youtube.com/watch?v=-NEzssNrL8c

[^15]: https://www.reddit.com/r/docker/comments/1h6yxwf/introducing_dockermcp_a_mcp_server_for_docker/

[^16]: https://openclawlaunch.com/guides/hermes-agent-documentation

[^17]: https://github.com/NousResearch/hermes-agent/issues/8558

[^18]: https://www.reddit.com/r/hermesagent/comments/1tjhb6z/how_i_ran_3_independent_hermes_agent_from_a/

[^19]: https://www.youtube.com/watch?v=ENuDO1xIg8Q

[^20]: https://mcp.docker.com

[^21]: https://www.datacamp.com/tutorial/hermes-agent

[^22]: https://www.docker.com/blog/mcp-toolkit-mcp-servers-that-just-work/

[^23]: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/use-mcp-with-hermes.md

[^24]: https://github.com/nousresearch/hermes-agent

[^25]: https://www.youtube.com/watch?v=dXhwwxsTWj0

[^26]: https://www.youtube.com/watch?v=IMO8ooIqONM

[^27]: https://nousresearch-hermes-agent.mintlify.app/reference/configuration-options

