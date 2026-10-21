# IT-Tools — qualidade, arquitetura e verificações

Data: 2026-10-21 (UTC; mesma data em São Paulo). Origem: `CorentinTh/it-tools`, commit `d505845f918e946ec300af7b36efc107e2f66e9e`, obtido por clone raso de `main`. Nenhuma alteração de código upstream foi publicada.

## Inventário verificado em código

- Licença: **GNU GPL v3**, confirmada em `LICENSE`, `package.json` e README. Não é MIT. O texto GNU contém instruções genéricas de aplicação; não interpretar esse exemplo como declaração de copyright do autor.
- SPA Vue 3.3.4, TypeScript 5.2.2, Vite 4.4.9, Pinia 2.0.34, Vue Router 4.1.6, Naive UI 2.35.0 e UnoCSS 0.65.1. Dependências exatas acima derivam do lock instalado.
- `src/main.ts` monta app, roteador, store, i18n, UI e service worker. `src/tools/index.ts` registra **86 ferramentas em 10 categorias**, com componentes Vue e serviços puros em vários casos. Rotas derivadas do catálogo; componentes principais carregados por importações dinâmicas nos respectivos índices.
- PWA/service worker gerado pelo Vite; frontend estático sem backend próprio, contas de usuário ou persistência multi-tenant. Preferências e algumas entradas são gravadas em `localStorage` via VueUse; determinados parâmetros passam pela URL via `useRouteQuery`. Isso impede afirmar que toda entrada é efêmera.
- Plugin Plausible existe, mas **desabilitado por padrão** em `src/config.ts`. Ativação depende de configuração de build. Não foi comprovado envio de conteúdo de entradas para analytics.
- **67 dependências diretas runtime + 43 de desenvolvimento** no manifesto. O audit percorreu 1.354 entradas contando dependências transitivas e opcionais (a soma dos campos metadata não precisa representar pacotes únicos).
- **33 arquivos unitários** (`*.test.ts`) e **26 arquivos E2E** (`*.e2e.spec.ts`). Outros nomes de teste/configuração explicam a diferença para buscas amplas por `test|spec`.

## Ambiente e instalação

- Ambiente efetivamente utilizado: Linux/POSIX, Node `v24.19.0`, npm `11.9.0`, pnpm disponível `11.25.0`; projeto declara `pnpm@9.11.0` e CI usa Node 20.
- Comando inicial: `npx --yes pnpm@9.11.0 install --frozen-lockfile --ignore-scripts` (log `upstream-install.log`). Download inicialmente lento; também foi experimentado o pnpm já instalado.
- Comando efetivamente confirmado ao final: `pnpm install --frozen-lockfile --ignore-scripts --config.manage-package-manager-versions=false` (log `upstream-install-pnpm11.log`), código 0. Lockfile preservado. Scripts de instalação de dependências não foram executados. A opção CLI não prefixada por `--config.` foi rejeitada antes de instalar e corrigida; isso não é defeito do upstream.
- Instalar com scripts desabilitados reduz efeitos de supply chain; não equivale à homologação integral dos scripts de instalação upstream. Node 20/Windows/macOS não foram executados neste ambiente.

## Verificações realizadas

| Comando | Resultado e evidência |
| --- | --- |
| `./node_modules/.bin/vitest run --environment jsdom --threads false` | **138 testes aprovados, 33 arquivos**, código 0; `upstream-unit.log`. Sem testes ignorados reportados. 2,56s nessa execução, sem pretensão de benchmark. |
| `./node_modules/.bin/eslint src --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --ignore-path .gitignore` | Código 0, **0 erros e 3 warnings** de ordenação UnoCSS; `upstream-lint.log`. |
| `./node_modules/.bin/vue-tsc --noEmit -p tsconfig.vitest.json --composite false` | Código 0; aviso de depreciação `fs.Stats` do Node24; `upstream-typecheck.log`. |
| `pnpm run build` | **Código 0**, build aprovado, 55,69s nesta execução; `upstream-build.log`. Saída `dist` de 14 MiB, com 232 arquivos JS. |
| `./node_modules/.bin/playwright test --list` | Código 0: **183 testes em 26 arquivos** listados, sem abrir navegador ou executar E2E; `upstream-e2e-list.log`. |
| `pnpm audit --json --config.manage-package-manager-versions=false` | Código 1 por correspondências de advisories; `upstream-audit.json` e resumo em `upstream-audit-summary.json`. |

## Dependências e advisories

O audit reportou **192 registros de advisories (162 identificadores GHSA distintos)**: 6 critical, 89 high, 83 moderate, 14 low. Pela classificação `findings[].dev`, **114** têm pelo menos um caminho runtime e **78** só caminhos de desenvolvimento. Isso não comprova 192 vulnerabilidades exploráveis no site; não houve análise de alcance completa para cada transitiva. `pnpm audit --prod --json --config.manage-package-manager-versions=false` confirmou os 114 registros runtime (96 GHSA distintos): 1 critical, 51 high, 52 moderate, 10 low, em `upstream-audit-prod.json`, código 1 por achados.

Dois registros foram conferidos em fontes primárias do mantenedor em 21/10/2026:

- DOMPurify **3.0.6** está na faixa de [GHSA-mmhx-hmjr-r674](https://github.com/cure53/DOMPurify/security/advisories/GHSA-mmhx-hmjr-r674); o registro descreve falha de checagem de profundidade/prototype pollution e correção histórica na linha 3.1.3. Essa versão histórica não é uma recomendação atual de atualização; existem advisories posteriores. O frontend usa sanitização em funcionalidades HTML; reproduções específicas e condições pertencem à revisão de segurança.
- Vite **4.4.9** está na faixa de [GHSA-vg6x-rcgg-rjx6](https://github.com/vitejs/vite/security/advisories/GHSA-vg6x-rcgg-rjx6). Afeta o servidor de desenvolvimento e pode afetar uso só em localhost. A SPA estática servida por Nginx não é o servidor de desenvolvimento Vite. Atualização deve considerar o conjunto de advisories e compatibilidade, não apenas a primeira versão histórica que corrigiu esse registro.

Outras correspondências relevantes no relatório de audit incluem crypto-js4.1.1, yaml2.2.1, node-forge1.3.1, lodash4.17.21, markdown-it14.1.0. São triagem de dependências, não exploração comprovada. Os IDs, versões, severidades e caminhos estão nos JSONs; não atribuir automaticamente a severidade do pacote ao produto inteiro.

## CI, containers e confiabilidade

- `.github/workflows/ci.yml`: checkout fixado por SHA, setup-node por tag v3; executa instalação, lint, unit, tipos e build. Não inspecionei credenciais e não disparei execução externa.
- E2E CI usa três shards, Playwright e instalação de navegadores. O passo que obtém versão lê `.dependencies.playwright`, embora o manifesto tenha `@playwright/test` em devDependencies: chave de cache pode ter `null` (revisão estática, impacto funcional não testado).
- Dockerfile é multi-stage, mas usa `node:lts-alpine`, `nginx:stable-alpine`, instala pnpm sem versão e não declara usuário não-root/healthcheck. São lacunas de reprodutibilidade/hardening, não prova de incidente. Nenhuma imagem foi construída ou implantada.
- `nginx.conf` resolve rotas SPA; não configura TLS, CSP ou outros headers. Camada externa pode fornecê-los; não foi examinada a implantação pública.
- Vite sinaliza `crypto`, `path`, `tls` externalizados e `eval` em dependências no build. O aviso não equivale por si só a execução arbitrária confirmada.
- O build PWA concluiu, mas excluiu do precache `mac-address-lookup` (3,35 MB) e `text-diff` (3,16 MB), acima do limite. Logo, sucesso de build/PWA não demonstra disponibilidade offline de todas as ferramentas. Precache: 264 entradas, aproximadamente 6.070,95 KiB.
- O gerador do build acrescentou tipos a `components.d.ts`. Esse arquivo gerado foi restaurado ao conteúdo original após a verificação; fontes/lockfile permaneceram inalterados. Artefatos de build e logs são descartáveis.

## Limites da conclusão

Não foram executados E2E em navegador real, Docker, carga, produção, operações com chaves/carteiras, APIs pagas, banco ou n8n. Nenhuma credencial real foi fornecida. Os testes unitários provam os casos exercitados, sem certificar segurança absoluta. Windows e Node20 não foram homologados. Um motor pequeno para ChatGPT pode extrair padrões de catálogo/validação sem duplicar as 86 interfaces; manter frontend Vue saudável caso se adote a aplicação completa.
