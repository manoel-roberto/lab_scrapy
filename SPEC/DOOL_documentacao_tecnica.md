# Documentação Técnica — Scraping do DOOL
## Diário Oficial do Estado da Bahia

---

## 1. Visão Geral

O DOOL (Diário Oficial do Estado da Bahia) é um portal público acessível sem autenticação. Os dados são organizados por edições diárias, cada uma contendo centenas de atos oficiais organizados em uma árvore hierárquica. O scraper pode operar inteiramente via requisições HTTP diretas, sem necessidade de browser headless, exceto para o passo inicial de obtenção do sumário.

---

## 2. URLs e Padrão de Acesso

### 2.1 Padrão de URL

As páginas de edição seguem o formato:

```
https://dool.egba.ba.gov.br/portal/visualizacoes/html/{ID}
```

Existe também uma URL alternativa (mais direta, confirmada via HAR):

```
https://dool.egba.ba.gov.br/ver-html/{ID}/
```

Ambas apontam para o mesmo conteúdo. Para o scraper, usar `/ver-html/{ID}/` é preferível por ser a URL real que o servidor processa (a outra usa hash routing no frontend).

### 2.2 Mapeamento de Datas para IDs

O ID numérico **não segue incremento fixo** entre dias úteis. Mapeamento já levantado:

| Data       | ID    |
|------------|-------|
| 10/04/2026 | 21731 |
| 11/04/2026 | 21742 |
| 14/04/2026 | 21749 |
| 15/04/2026 | 21756 |
| 16/04/2026 | 21764 |
| 17/04/2026 | 21772 |
| 18/04/2026 | 21782 |
| 06/05/2026 | 21850 |
| 07/05/2026 | 21858 |
| 08/05/2026 | 21865 |

**Estratégia recomendada:** não tentar adivinhar o ID. Descobrir o ID correto via calendário ou endpoint de listagem antes de acessar a edição.

---

## 3. Endpoints da API

### 3.1 Sumário da Edição

```
GET https://dool.egba.ba.gov.br/ver-html/{ID}/
```

Retorna a página HTML completa com o sumário (árvore de navegação) e os metadados da edição.

### 3.2 Conteúdo de um Ato Específico

```
GET https://dool.egba.ba.gov.br/apifront/portal/edicoes/publicacoes_ver_conteudo/{identificador}
```

O `{identificador}` vem do atributo `identificador` (ou `data-materia-id`) dos elementos `<a class="linkMateria">` no sumário.

Exemplos reais capturados:
```
GET /apifront/portal/edicoes/publicacoes_ver_conteudo/1280088  → retornou HTML
GET /apifront/portal/edicoes/publicacoes_ver_conteudo/1278650  → retornou PDF
```

### 3.3 Headers Necessários

Todas as requisições à API de conteúdo devem incluir:

```http
Accept: text/html, */*; q=0.01
X-Requested-With: XMLHttpRequest
Referer: https://dool.egba.ba.gov.br/portal/visualizacoes/html/{ID}
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36
```

O header `X-Requested-With: XMLHttpRequest` é crítico — identifica a requisição como AJAX legítima.

---

## 4. Barreira de Acesso (Modal Inicial)

Ao carregar qualquer página, um modal bloqueante é exibido. **Não é autenticação real** — é apenas um aviso informativo que pode ser dispensado sem login.

### Estrutura do modal no HTML:
```html
<div id="modal-acessolivre" class="modal show" ...>
  ...
  <button type="button" class="btn btn-primary btn-sm" data-dismiss="modal">
    CONTINUAR SEM CADASTRO
  </button>
  ...
</div>
```

### Solução para scraper com browser headless (Puppeteer/Playwright):
```javascript
// Aguardar o modal e clicar no botão
await page.waitForSelector('[data-dismiss="modal"]');
await page.click('[data-dismiss="modal"]');

// Ou forçar o dismiss via jQuery (se disponível na página)
await page.evaluate(() => $('#modal-acessolivre').modal('hide'));
```

### Observação importante:
Para acessar o **sumário** (passo 1 do fluxo), é necessário carregar a página no browser headless e dispensar o modal. Para os **conteúdos dos atos** (passo 2), as requisições diretas à API **não passam pelo modal** — ele é puramente frontend.

---

## 5. Estrutura do Sumário (Árvore de Navegação)

### 5.1 Hierarquia

O sumário é uma árvore `<ul id="tree">` com até 4 níveis de profundidade:

```
Seção Principal (ex: EXECUTIVO)
  └── Subseção (ex: DECRETOS NUMERADOS)
        └── Sub-subseção (ex: Diretoria Geral)
              └── Ato individual (ex: #1184693 - Dec24535)
```

Exemplos reais da hierarquia:
- `EXECUTIVO > LEIS > #1184927`
- `EXECUTIVO > DECRETOS NUMERADOS > #1184693 - Dec24535`
- `EXECUTIVO > SECRETARIA DA EDUCAÇÃO > Universidade do Estado da Bahia – UNEB > Portarias > #1184399`
- `LICITAÇÕES > AVISOS DE LICITAÇÃO > SECRETARIA DA SAÚDE > Pregão Eletrônico > #1184369`
- `MUNICÍPIOS > PREFEITURAS > CAETITÉ > Atos Pub-BA > #1184286`

### 5.2 Estrutura HTML dos Atos

Cada ato individual é um elemento `<a class="linkMateria">`:

```html
<a class="linkMateria"
   identificador="1279851"
   pagina="1"
   data-id="1285670"
   data-protocolo="1184693"
   data-materia-id="1279851">
  #1184693 - Dec24535
</a>
```

### 5.3 Atributos Relevantes

| Atributo | Descrição | Uso |
|---|---|---|
| `identificador` | ID interno da matéria | Usado na URL da API de conteúdo |
| `data-materia-id` | Igual ao `identificador` | Redundante, confirma o valor |
| `data-protocolo` | Número do protocolo oficial | Aparece no título do ato (ex: `#1184693`) |
| `data-id` | ID da publicação no sistema | Referência interna adicional |
| `pagina` | Página física no documento | Útil para localizar no PDF; vazio em licitações |

### 5.4 Observação sobre o atributo `pagina`

Atos do tipo Executivo e similares têm o atributo `pagina` preenchido (ex: `pagina="1"`, `pagina="14"`). Atos de Licitações e alguns outros têm `pagina=""` (vazio). Isso indica que esses atos não têm posição fixa no PDF da edição.

### 5.5 Extração do Sumário

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_da_pagina, "html.parser")
links = soup.select("div.sumario a.linkMateria")

for link in links:
    ato = {
        "identificador": link.get("identificador"),
        "data_id": link.get("data-id"),
        "data_protocolo": link.get("data-protocolo"),
        "pagina": link.get("pagina"),
        "titulo": link.get_text(strip=True),
        # hierarquia: percorrer os <span class="folder"> ancestrais
    }
```

---

## 6. Metadados da Edição

O número da edição e a data ficam no seguinte trecho HTML:

```html
<div class="text-center">
  Diário Oficial do Estado da Bahia do dia 08/05/2026 | <strong>Edição 24390</strong>
  <div class="dropdown-edicoes">Edição Principal</div>
</div>
```

### Extração:
```python
import re

div = soup.select_one("div.text-center")
texto = div.get_text()

data = re.search(r'(\d{2}/\d{2}/\d{4})', texto).group(1)
edicao = div.select_one("strong").get_text()  # "Edição 24390"
```

---

## 7. Tipo de Conteúdo dos Atos (HTML vs PDF)

### 7.1 O Problema

O mesmo endpoint `/publicacoes_ver_conteudo/{identificador}` pode retornar **HTML ou PDF** dependendo do ato e da data. Não há padrão fixo por período — o formato pode variar inclusive dentro de uma mesma edição.

Comportamento observado:
| Período | Formato observado |
|---|---|
| Antes de 06/05/2026 | HTML puro |
| 06/05/2026 e 07/05/2026 | PDF (com texto selecionável) |
| 08/05/2026 | HTML puro novamente |

### 7.2 Detecção via Content-Type (Confirmado via HAR)

A forma correta e confiável de detectar o formato é verificar o header `Content-Type` da resposta:

| Formato | Content-Type | Content-Disposition |
|---|---|---|
| HTML | `text/html; charset=UTF-8` | ausente |
| PDF | `application/pdf` | `inline;filename='downloaded.pdf'` |

### 7.3 Dados de Performance Observados

| Métrica | HTML | PDF |
|---|---|---|
| Tamanho da resposta | ~6 KB | ~82 KB |
| Tempo de espera (server) | ~239 ms | ~434 ms |
| Tempo de download | ~3 ms | ~60 ms |
| Tempo total | ~308 ms | ~563 ms |

PDFs são ~13x maiores e ~2x mais lentos que respostas HTML.

---

## 8. Fluxo Completo do Scraper

```
┌─────────────────────────────────────────────────┐
│ PASSO 1 — Obter o ID da edição para a data      │
│   → Via calendário do site ou tabela mapeada    │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│ PASSO 2 — Carregar a página da edição           │
│   GET /ver-html/{ID}/                           │
│   → Dispensar modal (se usar browser headless)  │
│   → Extrair metadados (data, número da edição)  │
│   → Parsear div.sumario                         │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│ PASSO 3 — Extrair todos os atos do sumário      │
│   → Selecionar todos: a.linkMateria             │
│   → Registrar: identificador, protocolo,        │
│                pagina, titulo, hierarquia       │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│ PASSO 4 — Para cada ato, buscar o conteúdo      │
│   GET /apifront/portal/edicoes/                 │
│       publicacoes_ver_conteudo/{identificador}  │
│   Headers: X-Requested-With, Referer, Accept   │
└────────────────────────┬────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Verificar          │
              │  Content-Type       │
              └──────┬──────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
   text/html              application/pdf
         │                       │
┌────────▼────────┐   ┌──────────▼──────────┐
│ Parsear HTML    │   │ Extrair texto do PDF │
│ (BeautifulSoup) │   │ (pdfplumber/pdfminer)│
└────────┬────────┘   └──────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
┌────────────────────▼────────────────────────────┐
│ PASSO 5 — Armazenar                             │
│   → Texto extraído + metadados do ato           │
│   → Hierarquia (seção > subseção > título)      │
│   → Referências (protocolo, data, edição)       │
└─────────────────────────────────────────────────┘
```

---

## 9. Implementação de Referência (Python)

```python
import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import re

BASE_URL = "https://dool.egba.ba.gov.br"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

HEADERS_API = {
    **HEADERS_BASE,
    "Accept": "text/html, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def obter_sumario(id_edicao: int) -> dict:
    """Carrega a página da edição e extrai metadados + lista de atos."""
    url = f"{BASE_URL}/ver-html/{id_edicao}/"
    headers = {
        **HEADERS_BASE,
        "Referer": BASE_URL,
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Metadados
    div_meta = soup.select_one("div.text-center")
    texto_meta = div_meta.get_text() if div_meta else ""
    data_match = re.search(r"(\d{2}/\d{2}/\d{4})", texto_meta)
    data = data_match.group(1) if data_match else None
    strong = div_meta.select_one("strong") if div_meta else None
    edicao = strong.get_text(strip=True) if strong else None

    # Atos
    atos = []
    for link in soup.select("div.sumario a.linkMateria"):
        # Hierarquia: coletar todos os <span class="folder"> ancestrais
        hierarquia = []
        for ancestor in link.parents:
            folder = ancestor.find("span", class_="folder", recursive=False)
            if folder:
                hierarquia.insert(0, folder.get_text(strip=True))

        atos.append({
            "identificador": link.get("identificador"),
            "data_id": link.get("data-id"),
            "data_protocolo": link.get("data-protocolo"),
            "pagina": link.get("pagina"),
            "titulo": link.get_text(strip=True),
            "hierarquia": hierarquia,
        })

    return {
        "id_edicao": id_edicao,
        "data": data,
        "edicao": edicao,
        "atos": atos,
    }


def obter_conteudo_ato(identificador: str, id_edicao: int) -> dict:
    """Busca o conteúdo de um ato e retorna texto extraído + tipo."""
    url = f"{BASE_URL}/apifront/portal/edicoes/publicacoes_ver_conteudo/{identificador}"
    headers = {
        **HEADERS_API,
        "Referer": f"{BASE_URL}/portal/visualizacoes/html/{id_edicao}",
    }

    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")

    if "application/pdf" in content_type:
        texto = extrair_texto_pdf(resp.content)
        formato = "pdf"
    elif "text/html" in content_type:
        texto = extrair_texto_html(resp.text)
        formato = "html"
    else:
        texto = None
        formato = "desconhecido"
        print(f"[AVISO] Formato inesperado para identificador {identificador}: {content_type}")

    return {"formato": formato, "texto": texto}


def extrair_texto_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def extrair_texto_pdf(conteudo_bytes: bytes) -> str:
    texto_paginas = []
    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_paginas.append(texto)
    return "\n".join(texto_paginas)
```

---

## 10. Recomendações de Performance e Robustez

### Concorrência
Para edições com centenas de atos, usar requisições assíncronas com limite de conexões:

```python
import asyncio
import aiohttp

async def buscar_atos_concorrente(atos, id_edicao, max_concurrent=8):
    semaforo = asyncio.Semaphore(max_concurrent)
    async with aiohttp.ClientSession() as session:
        tarefas = [
            buscar_com_semaforo(session, ato, id_edicao, semaforo)
            for ato in atos
        ]
        return await asyncio.gather(*tarefas, return_exceptions=True)
```

### Retry com backoff
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def obter_conteudo_ato_com_retry(identificador, id_edicao):
    return obter_conteudo_ato(identificador, id_edicao)
```

### Outras recomendações
- **Salvar PDFs em disco** antes de extrair texto, evitando redownload em caso de falha
- **Logar formatos desconhecidos** para investigação manual
- **Respeitar o servidor** — o DOOL roda em Apache/2.2.22 (Debian), infraestrutura governamental antiga; não exceder 8–10 requisições simultâneas
- **Adicionar delay mínimo** entre requisições sequenciais (200–500ms) como boa prática

---

## 11. Resumo dos Endpoints

| Finalidade | Método | URL |
|---|---|---|
| Página da edição (sumário) | GET | `/ver-html/{ID}/` |
| Página alternativa (hash routing) | GET | `/portal/visualizacoes/html/{ID}` |
| Conteúdo de um ato | GET | `/apifront/portal/edicoes/publicacoes_ver_conteudo/{identificador}` |

## 12. Resumo dos Headers

| Header | Valor | Obrigatório em |
|---|---|---|
| `X-Requested-With` | `XMLHttpRequest` | API de conteúdo |
| `Referer` | URL da página da edição | API de conteúdo |
| `Accept` | `text/html, */*; q=0.01` | API de conteúdo |
| `User-Agent` | String de browser real | Todas as requisições |

## 13. Resumo das Respostas da API de Conteúdo

| Formato | Content-Type | Tamanho típico | Tempo típico |
|---|---|---|---|
| HTML | `text/html; charset=UTF-8` | ~6 KB | ~300 ms |
| PDF | `application/pdf` | ~82 KB | ~560 ms |
