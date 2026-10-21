# Revisão independente — Radar DevTools ChatGPT

Data: 2026-10-21. Escopo: `radar-devtools-chatgpt/radar_devtools/`, adaptador CLI, contrato e instruções ChatGPT. Revisão por agente separado do implementador. Nenhuma alteração ao motor/CLI/documentação por este revisor; somente `tests/test_independent.py` acrescentado no repositório. Dados sintéticos, sem rede ou conta externa.

## Resultado

**21 testes independentes aprovados, 0 falhas**, incluindo dois subprocessos reais do CLI. Comando executado da raiz: `python3 -m unittest discover -s tests -p test_independent.py -v`. Log: `research/adaptation-independent-tests.txt`. Snapshot dos arquivos revisados: `research/adaptation-review-sha256.json`. Esses 21 testes não incluem a contagem da suíte principal e não substituem homologação numa conta ChatGPT.

Os testes percorrem as 11 operações pelo envelope de bytes, duplicidade de chaves após decodificação, números de expoente elevado sem expansão, preservação de decimais, diferença entre null/bool/arrays, texto que contém markup/instruções tratado como dado, UTF-8 e byte NUL no conteúdo, Base64, semântica de `+` no percent encoding, URLs inválidas sem eco, datas anteriores ao Unix epoch e fusos, IPv4/IPv6 `/0` sem enumerar hosts e formas UUID não canônicas. CLI é exercitado por subprocesso e chamada direta: hash da entrada exata, modo 0600, preservação da entrada, diretórios/links simbólicos nos pais, caminhos inválidos e ausência de saída em erro de validação.

## Pontos encontrados e resolvidos pelo integrador

1. **Fuso com minuto fora de 00–59**: inspeção inicial mostrava delegação a `datetime.fromisoformat`, que pode normalizar alguns offsets inválidos. Integrador adicionou checagem de componentes; regressões para +00:60, -00:99 e +23:99 passaram. Resultado final é recusa estruturada.
2. **Surrogates isolados no JSON interno**: eram preservados como escapes por `render_json`; não causavam execução ou quebra de UTF-8 de saída, mas não atendiam à política escolhida de Unicode interoperável. Integrador passou a verificar chaves e folhas textuais. Regressões em `json.format`/`json.diff` recusam pares inválidos com erro sem eco; par UTF-16 válido de 🚀 continua funcionando.
3. **NUL/Unicode inválido em caminho na API direta do CLI**: `os.open` podia lançar ValueError fora do tratamento. Integrador adicionou validação do caminho antes de abrir. Testes agora observam retorno 2 com erro JSON sem payload. Argumento NUL não pode chegar por argv de processo normal; era robustez da função Python, não falha de acesso remoto.

## Fronteiras e contraprovas

- Núcleo importa biblioteca padrão de parsing/cálculo; análise AST dos três módulos de domínio não encontrou adaptadores de rede, subprocessos ou chamadas de `eval`/`exec`/`compile`/`__import__`. Isso é inspeção estática e teste de fronteira, não prova formal contra todo fluxo possível.
- URL pode preservar `%FF` em path e formas numéricas de hostname; `url.inspect` não decodifica o path nem o visita, e contrato declara ausência de DNS/garantia de segurança. Não tratar parsing como filtro SSRF ou prova de autorização.
- CLI recusa symlinks nos componentes percorridos usando descritores POSIX/O_NOFOLLOW; não é sandbox geral de filesystem. Operador escolhe caminhos permitidos pelo processo. Contrato já explica isso.
- Uma falha de I/O/interrupção pode deixar novo arquivo parcial; nenhuma escrita é descrita como transacional. A saída existente e a entrada são preservadas por O_EXCL. Limitação documentada, sem necessidade de simular indisponibilidade de disco.
- Relatórios podem conter integralmente dados transformados. Não são anonimização; somente exemplos fictícios são apropriados para este piloto. Erros/stdout não ecoam payload nos casos verificados.
- Não há endpoint, MCP, automação ativa, integração n8n, modelo pago, instalação de plugin ou deploy. Instruções ChatGPT diferenciam leitura, execução real e fallback qualitativo.

## Documentação

Contrato e instruções correspondem às fronteiras implementadas; especificam POSIX, arquivo novo, byte hashes, limites de entrada/saída, operações permitidas e semântica dos resultados. Recomenda-se explicitar no contrato a recusa de surrogates Unicode isolados para registrar a decisão recente; isso não muda o resultado dos testes.

Conclusão: não há bloqueio remanescente identificado neste recorte após as correções acima. Apropriado para proposta experimental revisável, com homologação de uso no ChatGPT ainda pendente. Não é certificação de segurança, escala ou produção.
