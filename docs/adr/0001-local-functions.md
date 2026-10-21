# ADR 0001 — Funções locais para uso no ChatGPT

Status: adotada para o experimento inicial. Data: 21/10/2026. Responsável pelo produto: Carlos Felipe.

## Problema e decisão

O IT-Tools reúne utilitários numa aplicação web. A necessidade deste recorte é realizar transformações pequenas, conferir o resultado e explicá-lo em português no ChatGPT, com arquivos e execução observáveis.

Criar um motor Python autoral com biblioteca padrão e operações explicitamente permitidas, contrato estrito, CLI de arquivo novo e instruções para o ChatGPT. Começar por JSON, Base64, URL, hash, UUID, CIDR e datas. Python executa o cálculo; o assistente explica a saída e seus limites. Dados do exemplo são sintéticos.

## Alternativas e consequências

| Alternativa | Avaliação |
| --- | --- |
| Usar a UI upstream para todas as tarefas | Continua útil para seu catálogo amplo. Não oferece por si só o contrato de arquivo e a transparência de execução deste recorte no ChatGPT. |
| Copiar/migrar toda a aplicação Vue | Amplia escopo e manutenção sem demanda comprovada; não adotada nesta etapa. |
| LLM calcular cada transformação | Reduz reprodutibilidade de tarefas exatas; reservado à explicação, sem chamada paga implementada. |
| Novo servidor MCP/API e n8n | Desnecessário para funções puras locais e acrescenta autenticação, rede e operação. Reavaliar apenas se houver consumidor real e benefício mensurável. |

Não adicionar banco, RAG, embeddings, GPU, autenticação ou frontend para cumprir uma lista de tecnologias. Preservar fronteiras dos projetos atuais: Workbench analisa repositórios; Code Atlas consulta código; Evidence Kit fornece sua própria semântica de evidência; Integration Hub governa chamadas externas; Capital mantém cálculos de domínio financeiro. Nenhum deles foi integrado ou alterado por este recorte.

## Critérios de avanço e revisão

Primeiro marco: exemplos fictícios, testes de resultados e recusas, preservação da entrada, relatório novo e documentação compatível com o código. Uma segunda pessoa/sessão deve homologar o uso no ChatGPT antes de afirmar instalação ou integração na conta. Utilidade e tempo economizado precisam ser medidos, sem ROI presumido.

Código e auditoria seguem em propostas independentes e revisáveis no GitHub; abertura/estado de PR, CI e merge exigem observação real. Não há merge ou implantação implícitos por esta decisão. Uma integração futura requer contrato versionado, identidade e limites no serviço, testes negativos e autorização para o efeito externo.

## Origem e licença

Referência conceitual: CorentinTh/it-tools, revisão `d505845f918e946ec300af7b36efc107e2f66e9e`, GPL-3.0. Não foram copiados fontes Vue ou assets. O código original desta adaptação é distribuído sob GPL-3.0-only, copyright 2026 Carlos Felipe. Referenciar um projeto não transfere autoria nem garante equivalência de comportamento; veja [ATTRIBUTION.md](../../ATTRIBUTION.md).
