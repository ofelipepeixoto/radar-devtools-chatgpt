# Revisão de segurança e correção — IT-Tools

Data: 2026-10-21. Origem: `CorentinTh/it-tools`, commit `d505845f918e946ec300af7b36efc107e2f66e9e`. Revisão local, sem acesso ao site publicado, credenciais, contas, operações ou tráfego externo nos ensaios. Código upstream permaneceu intacto. O instalador/testes/build são responsabilidade de outra etapa; estes resultados não são a suíte completa upstream.

## Licença e adoção

`LICENSE` contém GNU GPL versão 3; `package.json` declara `GNU GPLv3`. Reutilização de código/derivações deve preservar autoria, licença e obrigações de distribuição do código correspondente. Não relabelar partes copiadas como MIT autoral. Uma implementação independente dos comportamentos gerais pode evitar incorporar código GPL; não é parecer jurídico. Os patches candidatos abaixo são derivados e acompanham cópia integral da GPL.

Recomendação principal: C — EXTRACT (padrões de catálogo, organização por ferramenta e operações locais), com implementação própria pequena para ChatGPT. Não transportar geração de seeds/chaves/segredos, criptografia legada ou execução arbitrária de regex para a conversa. Manter catálogo amplo como referência, não alegar cobertura de todas as ferramentas.

## Método e evidência executada

`node research/security-reproduce.mjs`: oito comportamentos reproduzidos com dados sintéticos. Harness lê arquivos reais e usa `node:module.stripTypeScriptTypes` (Node 24.19.0, API experimental) e `node:vm`; remove somente imports/exports/tipos. O teste SVG extrai o corpo real de `computed()` e injeta refs sintéticas. Não equivale a teste de navegador ou compilação Vue.

`node --test research/security-candidates.test.mjs`: **9 testes aprovados, 0 falhas** sobre dois serviços candidatos. Logs: `security-reproduce-results.json`, `security-candidates-results.txt`. Originais não foram corrigidos nem publicados.

## Achados confirmados

### IT-01 — Tokens usam PRNG não criptográfico

- Status: [CODE VERIFIED], [TEST VERIFIED]. Severidade: média condicional (alta consequência se a saída for adotada como credencial; nenhuma quebra de conta demonstrada).
- Ativo: `src/tools/token-generator/token-generator.service.ts:1,23-30`; `src/utils/random.ts:1,8-11`.
- Evidência: `createToken` repete e embaralha alfabeto por `Math.random`, usado em cada passo. Ao substituir `Math.random` por fonte sintética constante, chamadas produzem mesma saída. Isso demonstra dependência da fonte; não demonstra previsibilidade prática de um browser real.
- Condições: operador usa ferramenta como gerador de token/senha em vez de dados de exemplo. Índice inclui palavra `password`; não há aviso de ausência de CSPRNG na tela.
- Impacto: falsa expectativa sobre força de credenciais. Alfabeto padrão ainda omite `N` e `n` (`ABCDEFGHIJKLMOPQRSTUVWXYZ` / `abcdefghijklmopqrstuvwxyz`), defeito funcional menor, confirmado sem inferir redução material isolada de segurança.
- Correção: Web Crypto `crypto.getRandomValues`, amostragem sem viés e limites numéricos validados; ou rotular somente dados sintéticos. Para a adaptação ChatGPT, excluir geração de segredos.
- Validação/risco residual: não foi executado ataque a credencial. Fonte constante é harness controlado. Patch de token não incluído.

### IT-02 — CSV não preserva aspas, quebras de linha e cabeçalhos

- Status: [CODE VERIFIED], [TEST VERIFIED]. Severidade: média para integridade de dados, sem prova de execução remota.
- Ativo: `src/tools/json-to-csv/json-to-csv.service.ts:20-26,34`.
- Evidência: `"` vira `\"`, enquanto CSV precisa duplicar aspas em campo entre aspas. Cabeçalho `a,b` é emitido como duas colunas e só há um valor na linha seguinte. Novas linhas são convertidas para sequência literal `\n`, alterando dados.
- Condições: JSON contém aspas, vírgula em chave ou CR/LF. Afeta saída copiada/exportada.
- Impacto: corrupção de colunas/conteúdo em importação de planilhas e automações.
- Correção: serializar cabeçalhos e valores pela mesma função; envolver células com vírgulas/aspas/CR/LF; duplicar aspas; preservar quebras no campo.
- Validação: patch candidato em `upstream-candidates/upstream-correctness.patch`; cinco testes CSV positivos/negativos aprovados.
- Risco residual: patch altera saída antiga com escapes; exige revisão de compatibilidade e testes upstream. Não neutraliza fórmulas automaticamente.

### IT-03 — Fórmulas preservadas na saída CSV

- Status: saída [TEST VERIFIED]; execução em planilha [NOT VERIFIED]. Severidade: baixa condicional / decisão de modo de exportação.
- Ativo: mesmo serializador, sem modo spreadsheet-safe.
- Evidência inofensiva: `{sample:'=1+1'}` gera célula `=1+1` sem neutralização. Não se abriu Excel/LibreOffice e não se executou comando.
- Condições: dados não confiáveis são exportados e abertos como planilha com avaliação de fórmulas. CSV de uso geral pode legitimamente preservar fórmulas; ausência de sanitização não prova falha universal.
- Impacto: fórmulas inesperadas na estação do consumidor; sem alegação de exfiltração ou RCE demonstrada.
- Correção: modo explicitamente orientado a planilhas neutralizando prefixos de fórmula em cabeçalhos e células; documentar perda intencional de fidelidade e manter modo de dados bruto separado.
- Risco residual: comportamento varia por planilha; patch de correção CSV acima não trata este item.

### IT-04 — Captura opcional válida gera erro e tela mostra “No match”

- Status: [CODE VERIFIED], [TEST VERIFIED]. Severidade: baixa (correção de utilitário).
- Ativo: `src/tools/regex-tester/regex-tester.service.ts:37-38,47-48`; Vue envolve chamada em `try/catch` e retorna `[]`.
- Evidência: `(?<a>a)?b` em `b`, flags `dg`, encontra `b` no motor nativo mas serviço lança TypeError ao acessar índices de captura ausente. A UI mascara falha como ausência de correspondência.
- Impacto: resultado incorreto silencioso para padrão válido.
- Correção: omitir capturas ausentes, testar existência de índices; garantir flag `d` no serviço.
- Validação: quatro testes no serviço candidato aprovados (grupo opcional ausente, grupo presente, flag faltante e correspondência simples).
- Risco residual: candidato não resolve consumo de CPU por padrões arbitrários.

### IT-05 — Regex arbitrária executada sincronamente sem orçamento

- Status: [CODE VERIFIED], [TEST VERIFIED] em harness local. Severidade: baixa para ferramenta local (indisponibilidade da própria aba; sem serviço remoto).
- Ativo: `regex-tester.service.ts:23,25,58`; `regex-tester.vue` usa computed síncrono e `RandExp`/renderização adicionais.
- Evidência: padrão sintético `^(a+)+$` e 28 caracteres `a` seguidos de `!` excederam limite externo de 200ms aplicado pelo harness VM; a aplicação não aplica esse limite. Ensaio encerrado pelo limite, sem deixar processo ativo.
- Impacto/condições: entrada patológica, mesmo pequena, pode bloquear thread da aba. Não é benchmark de capacidade, nem prova de ataque entre usuários.
- Correção: Worker encerrável e limite de entrada/tempo; ou motor com garantias adequadas. Não expor como ferramenta síncrona de agente ou endpoint sem isolamento.
- Risco residual: patch candidato do IT-04 não resolve este problema. Regex excluída da primeira adaptação recomendada.

### IT-06 — Texto customizado é markup no SVG exportado

- Status: [CODE VERIFIED], [TEST VERIFIED] para estrutura exportada; execução no navegador [NOT VERIFIED]. Severidade: baixa condicional.
- Ativo: `src/tools/svg-placeholder-generator/svg-placeholder-generator.vue:17-26`.
- Evidência: texto sintético `</text><rect id="audit-marker" .../><text>` cria elemento adicional no resultado SVG, em vez de aparecer literalmente como texto.
- Condições: conteúdo de terceiro é colado no campo e SVG é incorporado posteriormente num contexto que aceite markup ativo.
- Contraprova importante: preview upstream usa `<img :src="data:image/svg+xml...">`, contexto que normalmente restringe script. Não classificar como XSS automático na aplicação.
- Impacto: saída inadequada para ser considerada imagem/markup confiável.
- Correção: escape XML de texto e atributos ou criação via DOM `textContent`; restringir valores numéricos/cores antes de exportar.
- Risco residual: SVG nunca deve ser tratado como confiança implícita só por vir de gerador.

## Observações sem vulnerabilidade confirmada

- `c-markdown.vue` usa DOMPurify; `v-html` sozinho não prova XSS. Markdown-to-HTML usa markdown-it padrão (HTML bruto desabilitado). Não foi comprovada execução de script por esses caminhos.
- Dados JSON/YAML/HTML do usuário são persistidos em localStorage em algumas ferramentas (JSON viewer, YAML viewer, HTML WYSIWYG). É comportamento de privacidade: permanece no perfil do navegador, acessível a scripts da mesma origem; não é exfiltração observada. Para documentos sensíveis, preferir não persistir por padrão e oferecer apagar.
- Configuração Plausible existe; `src/config.ts` define tracker desabilitado por padrão. Não afirmar telemetria ativa no site ou envio de payload sem observar runtime publicado. URLs de regex usam parâmetros; outros parâmetros encontrados são principalmente configurações, não prova de JWT ou segredo em URL.
- JWT é decodificado com `jwt-decode`, não validado criptograficamente. UI diz “JWT to decode”; não foi achado uso desse resultado como autorização. Adaptação deve emitir `signature_verified:false` se vier a incluir decoder.
- RSA/BIP39/OTP e cifras legadas existem no catálogo. Para ChatGPT, excluir seeds, chaves privadas, senhas e assinatura em vez de transportar geração de segredos para contexto de nuvem. Não houve análise criptográfica integral.
- Nginx não define CSP e containers usam tags flutuantes/serviço padrão; são lacunas de hardening/distribuição, não demonstração de exploração. Ambiente hospedado não foi inspecionado.
- Dependências/advisories: delegados à etapa de qualidade. Não inventar CVEs a partir de versões ou nome do pacote.

## Conteúdo dos candidatos

`upstream-candidates/` contém dois serviços derivados GPL, licença completa e patch unificado. Os nove testes validam correção CSV/capturas, não CSPRNG, SVG, planilhas, navegador ou isolamento regex. Não aplicar silenciosamente ao upstream; revisão de mantenedor e regressão completa continuam necessárias.
