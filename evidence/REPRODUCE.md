# Reproduzir as evidências

Origem fixada: `CorentinTh/it-tools@d505845f918e946ec300af7b36efc107e2f66e9e`. Licença GPLv3. Usar cópia local descartável; não aplicar patches automaticamente. Apenas dados sintéticos. Os scripts Node abaixo usam `stripTypeScriptTypes` (experimental em Node24) e removem tipos/imports para exercitar funções; não são E2E de navegador.

Na raiz desta branch:

```bash
git clone https://github.com/CorentinTh/it-tools.git ../it-tools-upstream
git -C ../it-tools-upstream checkout d505845f918e946ec300af7b36efc107e2f66e9e
node evidence/security-reproduce.mjs ../it-tools-upstream
node --test evidence/security-candidates.test.mjs
```

Resultado observado: oito comportamentos reproduzidos e nove testes de candidatos aprovados. O timeout externo do harness interrompe uma regex sintética em200ms; não mede latência/capacidade e não deixa tarefa rodando. Não executar regex arbitrária recebida de terceiros.

Para os testes upstream, os comandos/versões e limitações estão em `docs/upstream-quality.md`. O `audit` consulta o registro de pacotes e muda com o tempo: os números em `upstream-audit-summary.json` são snapshot de21/10/2026, não garantia de estado atual. São192 registros/162 GHSA distintos, não192 explorações. Não instalar dependências com credenciais ou executar scripts de instalação sem revisar origem.

As fontes derivadas e o patch em `upstream-candidates/` preservam GPL. Eles tratam somente CSV e capturas opcionais. Não resolvem todos os achados, não foram enviados ao mantenedor nem promovidos à `main` upstream.
