# Ecossistema GitHub atual — referência para adaptação IT-Tools

Observação: 21/10/2026, conta `ofelipepeixoto`. Inspeção somente leitura pelo conector GitHub. Nenhum repositório foi alterado por esta revisão.

## Cobertura e contagem

- **66 repositórios acessíveis de propriedade da conta: 50 públicos e 16 privados.** Listagem filtrada por owner, page_size=100; offset 0 retornou 66 e offset 100 retornou vazio. Não equivale a inventário de todas as organizações ou contas do usuário.
- Os 66 registros, IDs, visibilidade e branches estão em `ecosystem-inventory.json` (material privado de trabalho). Para publicação, usar `ecosystem-public-inventory.json`: 50 nomes públicos e somente contagem agregada dos privados.
- 50 endpoints públicos de metadados foram tentados: 49 respostas interpretadas e uma resposta indisponível para `magicui`. Metadados de `magicui` da listagem continuam confirmando existência/visibilidade/ID, mas fork/language/description não foram enriquecidos por essa tentativa.
- `language: null` no GitHub **não prova ausência de código**. Algumas `main` são bootstrap e a implementação está em PRs abertas; essa distinção foi verificada abaixo.
- Não há `it-tools` nem um pacote geral de utilitários de desenvolvimento identificado na listagem atual. Ausência de nome/descrição não prova ausência de funções utilitárias internas.

## Repositórios relacionados inspecionados

| Repositório | Estado e evidência atual | Sobreposição com IT-Tools | Decisão para a adaptação |
| --- | --- | --- | --- |
| `security-workbench` | `main` cf906efd01c832632f96eafac6555d55f4e39ff9; README, árvore e `workbench/core.py` lidos. Python stdlib + SQLite local; interface Next/TS hospedada separada com D1. | Inventário, hashes e revisão humana já pertencem ao scanner. | Novo utilitário pode produzir transformação verificável; não substituir scanner, confirmar achado ou escrever no SQLite/D1. Integração futura por contrato, não conectada. |
| `radar-integration-hub` | `main` d7084bdf63fcea9cf13ad1c5b3254c828b2cb6e2; README, árvore e `src/hub.mjs` lidos. Node22; ação CRM GET estrita, identidade de tenant confiável, cota e idempotência. | Governança de chamadas externas e transporte já têm destino. | Evitar outro gateway. Não estender a allowlist nem criar MCP remoto só para funções puras. |
| `radar-evidence-kit` | `main` 22d3cae88f1a43f55f75d880bbe6b46d5582d0ba; README, árvore e `src/radar_evidence/canonical.py` lidos. Python stdlib; JSON limitado, sem floats, SHA/SQLite e citação sob revisão. | Canonicalização/hash/proveniência existem com semântica própria. | Não chamar um formatter genérico de compatível com Evidence Kit ou RFC8785. Compartilhar biblioteca só após aprovação e testes de contrato; sem cópia silenciosa. |
| `radar-code-atlas` | `main` 3f12c652e840208f5c73f1499734d9382f2e4204 contém somente README. PR#2, branch `feat/snapshot-engine`, SHA 1e46971259df852c695eb7c3798e6c9c68db198a, README lido. | Consulta de código, snapshots e citações já têm um produto. | Não duplicar parsing de repositórios ou grafo. Novo utilitário restringe-se a arquivos/valores fornecidos. |
| `capital-web3-advisor` | `main` c412fa3b89b79fd86a85cc1f7996fd1c40e90eb8 é fundação. PR#17 SHA 8368ebf9254875f6166a3b0d46354ae495cbfe54 inclui evolução do portal; `capital_web3/risk.py` lido nesse SHA. | Decimal, timestamps e cálculos financeiros são domínio existente. | Não acrescentar decisão de investimento, carteira, assinatura ou cálculo DeFi no utilitário geral. Sua licença pública não concede automaticamente reutilização permissiva. |
| `camaleao-marketing-copilot` | `main` 816a9762cf82e893e5e1232adc058a2fc73c0409 é README bootstrap. PR#2 `feat/offline-chatgpt`, SHA a0fd402e7a937d7924b1cba6d616b43ff4525ea8; README e contrato lidos. | Padrão ChatGPT + arquivos + relatório determinístico já validado como desenho. | Reaproveitar padrão conceitual de instruções em PT-BR e declarar execução; não duplicar SEO/GSC/mídia. |
| `vibe-coding-toolkit` | `main` 790a895304e0c08b70a5b215c9d334f1c86b816c; README lido. Fork, documentação de contexto/orquestração/revisão. | Práticas de engenharia, não produto de transformação de dados. | Referência de documentação e revisão, sem instalar ferramentas extras por obrigação. |
| Projeto privado de workflows n8n | README `main` lido; inventário de workflows manuais, validação Python e testes Node; importação/execução separadas. | Orquestração já tem repositório; não há necessidade de mais um conjunto de automações nesta etapa. | Manter n8n desconectado. Sua identidade e detalhes operacionais não devem entrar no relatório público por padrão. |

Os números de testes citados nesses READMEs são **declarações dos próprios projetos**, não testes executados novamente por esta revisão. Código lido comprova estruturas específicas, não todas as capacidades documentadas. PR aberta não representa merge ou implantação.

## Escopo recomendado

**C — EXTRACT / NEW REPOSITORY**, caso a auditoria upstream confirme licença e qualidade: criar pacote pequeno, autoral e determinístico de utilitários para arquivos fornecidos no ChatGPT, com nomes de operação fixos, limites, formatos explícitos e resultados reproduzíveis. Exemplos de fronteira útil: JSON estrito/formatado, Base64 UTF-8, URL parse sem rede, hash de conteúdo e comparação textual limitada. Escolher subconjunto após avaliar o upstream e não prometer equivalência às dezenas de ferramentas da UI.

O ChatGPT interpreta e explica; código executa funções exatas. Não há necessidade de LLM pago, agente, RAG, embeddings, Supabase, VPS, servidor público ou MCP remoto para essa primeira fatia. A diferenciação é contrato de entrada/saída, rastreabilidade, recusa de casos ambíguos e instruções em português. Frontend próprio só se uma jornada visual trouxer benefício comprovável; não migrar Vue saudável upstream apenas por preferência Python.

Evitar ferramentas que induzam inserção de credenciais reais: geradores de chaves/seed, assinatura, JWT com segredo, dumps, extratos e tokens. Decodificar não significa verificar assinatura/autenticidade. Hash não prova verdade, origem ou aprovação. Não transformar descrições técnicas em recomendações financeiras; Capital Web3 permanece outro domínio.

## Mapa público — 50 repositórios

Classificação abaixo é **inferência de finalidade** baseada no nome e nos metadados públicos, salvo os aprofundamentos acima. Não certifica atividade, completude, testes ou infraestrutura.

| Grupo | Repositórios públicos |
| --- | --- |
| Perfil | `ofelipepeixoto` |
| Documentos, evidência e RAG | `assistente-documental-ia`, `laboratorio-busca-rag`, `skill-revisao-de-fontes`, `avaliacao-rag-juridico`, `radar-evidence-kit`, `llm-legislativo` |
| Governança e runtime de IA | `agente-aprovacao-humana`, `radar-integration-hub`, `radar-model-router`, `radar-agent-observatory`, `automaton`, `LibreChat` |
| Segurança e código | `security-workbench`, `radar-code-atlas`, `VulnClaw`, `rea`, `reverse-skill`, `anthropic-cybersecurity-skills`, `auditoria-seguranca-supabase` |
| Marketing, conteúdo e mídia | `radar-video-studio`, `creator-lab`, `habblaud`, `VoiceStudio`, `openreply`, `MoneyPrinterTurbo`, `open-seo`, `no-ai-slop`, `camaleao-marketing-copilot`, `radar-creator-chatgpt` |
| Produtos de negócio e portais | `radar-oaas`, `hermes-leilao-rj`, `camaleao-infra-portal`, `camaleao-portal` |
| Finanças e simulação | `TradingAgents`, `capital-web3-advisor`, `radar-equity-replay-lab`, `radar-backtest-chatgpt` |
| Ciência, aprendizagem e avaliação | `scientific-agent-skills`, `awesome-harness-engineering`, `radar-classificador-colab` |
| Navegação, memória e contexto | `browser-use`, `OpenViking`, `Agent-Memory` |
| Design e ferramentas de desenvolvimento | `diagram-design`, `magicui`, `awesome-design-md`, `ui`, `react-bits`, `vibe-coding-toolkit` |

Privados: **16**, conservados somente na análise local. Não inferir produção ou serviço ativo a partir de nome/repositório. GitHub não demonstra que Sites, n8n, Supabase ou VPS estejam conectados nesta conversa.

## Fontes e reprodução

- Inventário: `github_list_repositories(owner=ofelipepeixoto,page_size=100,page_offset=0)` e offset 100 vazio.
- Metadados públicos: `GET /repos/ofelipepeixoto/{name}` por conector GitHub; observação em 21/10/2026.
- Fontes fixadas, SHA de README, proteção `main` e PRs relacionadas: `ecosystem-evidence.json`.
- READMEs completos ficam em `github-readmes/` como apoio temporário, não como conteúdo a redistribuir integralmente. O relatório deve parafrasear e usar links por SHA.
- `main` protegida foi observada em Workbench, Integration Hub e Evidence Kit; as outras `main` públicas inspecionadas retornaram `protected=false`. Não foi feita alteração de proteção e não se presume que checks de PR certifiquem a adaptação nova.
