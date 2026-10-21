# Contrato 1.0 — Radar DevTools

Núcleo Python 3.11+, somente biblioteca padrão. As operações são locais e determinísticas; não fazem rede, executam código da entrada ou consultam serviços. Este contrato cobre funções puras e o CLI de arquivos; não define um serviço multiusuário ou endpoint MCP.

## Envelope e limites

Arquivo JSON UTF-8, até **256 KiB**, com exatamente:

```json
{
  "schema_version": "1.0",
  "operation": "json.format",
  "arguments": {"text": "{\"ficticio\":true}", "indent": 2}
}
```

`operation` pertence à tabela abaixo. `arguments` exige exatamente as chaves da operação; campos ausentes/adicionais são recusados. Textos têm limite de **64 KiB em UTF-8 por argumento**. JSON analisado aceita no máximo profundidade **32** e **10.000 nós**; cada literal numérico tem até **128 caracteres**. Chaves duplicadas, NaN/Infinity, Unicode inválido (inclusive surrogates isolados em chaves/valores) e sintaxe JSON inválida são recusados. A saída serializada tem teto de **1 MiB**; exceder o limite gera erro, sem retornar resultado truncado.

## Operações permitidas

| `operation` | `arguments` exatos | Semântica |
| --- | --- | --- |
| `json.format` | `text`: JSON em string; `indent`: inteiro 2 ou 4 | Formata a estrutura com números tratados por Decimal, sem conversão binária para float. Preserva ordem das propriedades analisadas; não promete preservar bytes, escapes ou representação lexical numérica. |
| `json.diff` | `before`, `after`: JSON em strings | Compara objetos por chave e arrays por posição. Retorna `equal` e `changes` com `kind` added/removed/changed, `path` em JSON Pointer e valores em `before_json`/`after_json` quando aplicáveis. Até 200 alterações; não é JSON Patch nem aplica mudanças. Números de mesmo valor, como 1 e 1.0, comparam iguais. |
| `base64.encode` | `text`: string | Texto UTF-8 para Base64 padrão canônico. Não é criptografia. |
| `base64.decode` | `text`: string | Base64 padrão canônico, com padding quando necessário e sem espaços; saída precisa ser UTF-8 válido. Não aceita dados binários arbitrários. |
| `url.inspect` | `url`: string | URL absoluta HTTP/HTTPS, sem usuário/senha, espaços, controles ou barra invertida; separa scheme, host, port, path, query e fragment. Valida sintaxe e informa `network_accessed: false`; não resolve DNS nem certifica segurança/propriedade do host. |
| `url.encode` | `text`: string | Percent encoding UTF-8 de um componente, mantendo caracteres não reservados RFC 3986; espaço vira `%20`. Não usar para codificar uma URL inteira como se preservasse seus separadores. |
| `url.decode` | `text`: string | Decodifica percentuais UTF-8; rejeita escapes incompletos/inválidos. `+` permanece `+`, sem a regra de formulário `application/x-www-form-urlencoded`. |
| `hash.sha256` | `text`: string | SHA-256 dos bytes UTF-8 exatos; retorna `hex` e `encoding`. Não normaliza Unicode ou quebras de linha. |
| `uuid.inspect` | `value`: string | Exige forma canônica hifenizada em minúsculas e variante RFC 4122 reconhecida pelo runtime; informa valor, versão e variante. Formato válido não garante unicidade ou autenticidade. |
| `network.cidr` | `value`: string | IPv4/IPv6 com prefixo e sem bits de host ativos (`strict=True`). Informa rede, versão, prefixo, primeiro/último endereço e contagem total como string; não enumera hosts nem usa rede. |
| `time.convert` | `value`: string | `YYYY-MM-DDTHH:MM:SS`, fração opcional de 1–6 dígitos e fuso obrigatório `Z` ou `±HH:MM`. Retorna UTC e microssegundos Unix como string. Não interpreta nome de região, horário de verão ou calendário de mercado. |

CIDR de documentação: `192.0.2.0/24` é válido; `192.0.2.1/24` é recusado. Data fictícia: `2026-10-21T12:00:00-03:00`. URL de exemplo: `https://example.invalid/teste`; sua inacessibilidade não muda o parsing local.

## API Python

```python
from radar_devtools import ToolError, execute_request, parse_request

try:
    request = parse_request(raw_bytes)
    report = execute_request(request)
except ToolError as error:
    print(error.code, error.message)
```

`parse_request(raw: bytes)` verifica tamanho, UTF-8 e JSON estrito. `execute_request(request: dict)` valida envelope, lista fixa de operações e argumentos antes de calcular. Para chamadas diretas da API, `indent` precisa ser `int` 2 ou 4; `bool` não é aceito. Não substituir a fronteira de bytes por um parser permissivo em adapters futuros.

O resultado do núcleo contém `schema_version`, `operation`, `result` e `limitations`. **O CLI acrescenta** `input_sha256`, calculado sobre os bytes exatos do arquivo de entrada, e `engine_version`. Consumidores da API que precisem desses metadados devem registrar a origem dos bytes e a versão confiável por conta própria, sem atribuir hash a uma representação reconstruída como se fosse o arquivo original.

## CLI e arquivos

```sh
mkdir -p outputs
python3 -m radar_devtools examples/json-format.json --output outputs/json-format.result.json
```

Executar da raiz do pacote, com Python 3.11+ e POSIX com `O_NOFOLLOW`/`O_DIRECTORY`. Pais de entrada/saída devem existir. Somente entrada regular; links simbólicos finais ou nos pais percorridos são recusados, assim como componentes `..`. A saída é criada exclusivamente (`O_EXCL`), com modo inicial `0600`, sujeito a umask mais restritivo; arquivos existentes não são sobrescritos. Não há confinamento geral do filesystem: o operador pode escolher caminhos acessíveis e deve usar diretório isolado confiável.

Sucesso: código 0, arquivo JSON novo e resumo no stdout. Erro: código 2 e JSON com `status`, `code`, `message` no stderr, sem inserir o conteúdo enviado na mensagem. Uma falha de escrita ou interrupção pode deixar arquivo parcial; confira-o e escolha outro nome na retomada. Não há atualização transacional de arquivos ou recuperação automática.

## Evidência e privacidade

O resultado pode conter integralmente texto, URLs e valores transformados; **não é anonimização**. Os exemplos são sintéticos. Não usar credenciais reais, senhas, seeds, chaves privadas, extratos ou dados pessoais neste piloto. Não há JWT, geração de segredos, assinatura, recomendação financeira, autorização humana ou execução externa.

Hash não autentica origem, identidade ou verdade. JSON formatado não é canonicalização RFC 8785, assinatura ou recibo do Evidence Kit. A versão do contrato não certifica equivalência ao catálogo IT-Tools. Testes locais e CI cobrem o código e os casos realmente executados; homologação dentro de uma conta ChatGPT exige evidência própria.
