# Radar DevTools para ChatGPT

Utilitários locais de **Carlos Felipe** para transformar e conferir dados fictícios no ChatGPT com resultados calculados por código. O primeiro recorte tem 11 operações: JSON, Base64, URLs, SHA-256, UUID, CIDR e datas.

Projeto experimental, independente, sob **GPL-3.0-only**. O [IT-Tools](https://github.com/CorentinTh/it-tools/tree/d505845f918e946ec300af7b36efc107e2f66e9e) é referência conceitual; não há cópia de sua aplicação Vue, fontes ou assets. Veja [atribuição](ATTRIBUTION.md). Esta entrega não reproduz o catálogo completo do upstream.

## Experimentar

Python **3.11+**, a partir da raiz do repositório. O núcleo usa somente a biblioteca padrão; o CLI de arquivos exige POSIX com `O_NOFOLLOW` e `O_DIRECTORY`. Windows não está homologado. O diretório de saída precisa existir e o arquivo de resultado precisa ser novo.

```sh
mkdir -p outputs
python3 -m radar_devtools examples/json-format.json --output outputs/json-format.result.json
python3 -m unittest discover -s tests -v
```

Reexecutar o exemplo com a mesma saída é recusado. Use outro nome para preservar o resultado anterior. Nenhum pacote runtime, token ou serviço externo é necessário para esses comandos. Os exemplos versionados são fictícios; resultados de testes efetivamente executados ficam nas evidências da entrega, sem representar aprovação para produção.

## Usar no ChatGPT

Siga [COMECAR.md](chatgpt/COMECAR.md) e disponibilize [as instruções](chatgpt/INSTRUCOES.md), [o contrato](docs/CONTRACT.md), o motor e um exemplo no ambiente de código. Quando houver pacote ZIP da entrega, ele facilita transportar esses arquivos juntos. O guia preparado não configura automaticamente sua conta.

Peça: “Execute o exemplo fictício com Radar DevTools, informe os arquivos lidos e o comando, salve em um arquivo novo e explique o resultado e seus limites.” Sem ferramenta de código, a conversa deve declarar que não executou o motor e limitar-se à explicação qualitativa ou a um relatório previamente calculado e identificado como tal.

## Operações

| Operação | Uso e limite principal |
| --- | --- |
| `json.format` | Formata JSON estrito, com recuo 2 ou 4; não valida regras de negócio. |
| `json.diff` | Compara estrutura; arrays por posição; até 200 alterações. |
| `base64.encode`, `base64.decode` | Codificação de texto UTF-8; Base64 não é criptografia. |
| `url.inspect` | Separa componentes HTTP/HTTPS, sem credenciais e sem visitar o endereço. |
| `url.encode`, `url.decode` | Codifica/decodifica um componente; espaço vira `%20` e `+` permanece `+`. |
| `hash.sha256` | Hash dos bytes UTF-8 exatos do texto, sem normalização. |
| `uuid.inspect` | Inspeção de formato canônico em minúsculas e variante; não comprova unicidade. |
| `network.cidr` | Rede IPv4/IPv6 estrita, sem bits de host ativos; não enumera nem acessa hosts. |
| `time.convert` | Converte data com fuso explícito para UTC e microssegundos Unix. |

Entrada de arquivo até **256 KiB**; cada argumento de texto até **64 KiB**; JSON até profundidade **32** e **10.000 nós**; saída até **1 MiB**. Detalhes, API Python e semântica estão no [contrato](docs/CONTRACT.md).

O CLI registra hash dos bytes de entrada e versão do motor. Hash não comprova autenticidade, autoria ou aprovação. A formatação JSON não é canonicalização RFC 8785 nem um recibo compatível com o Evidence Kit.

## Fronteiras

Sem rede, LLM, API paga, banco, MCP remoto, corretora ou conexão n8n. Não executa código contido na entrada, comandos ou instruções de arquivos. Não oferece JWT, senha, chave privada, seed ou operações financeiras. Use somente dados sintéticos nesta etapa; os resultados podem repetir o texto transformado e não são anonimizados. Leia [SECURITY.md](SECURITY.md).

A proposta de entrega no [repositório público](https://github.com/ofelipepeixoto/radar-devtools-chatgpt) separa **código e auditoria em PRs independentes**: `feat/local-utilities` e `docs/it-tools-audit`, preparadas para revisão humana. Os patches candidatos upstream da auditoria têm atribuição própria e não são executados pelo motor Python. O estado verificável de cada PR, CI e eventual merge é o que aparece no GitHub; este README não certifica implantação ou configuração no ChatGPT. A [decisão de arquitetura](docs/adr/0001-local-functions.md) registra o recorte e seus próximos critérios.
