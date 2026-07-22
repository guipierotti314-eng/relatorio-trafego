# Dashboard de mídia paga

Dashboard Streamlit para consolidar, filtrar e comparar campanhas de Meta Ads e Google
Ads. O aplicativo carrega automaticamente `dados/base_atual.xlsx` e oferece indicadores,
gráficos, tabelas interativas e downloads nos modos claro e escuro.

## Funcionalidades

- Validação amigável de abas, colunas e valores inválidos.
- Conversão de números e datas no padrão brasileiro.
- Classificação independente por segmento (`0 km` ou `Seminovos`) e tipo de ação (`Evento` ou `Regular`).
- Período direto entre duas datas, sempre visível, e filtros avançados recolhíveis.
- Alternância persistente entre os modos claro e escuro.
- Comparação com o mesmo intervalo do mês anterior.
- Indicadores ponderados: CPC, custo por resultado, CTR, CPM e frequência.
- Visão geral, desempenho por praça, categorias, tipos de resultado e evolução semanal.
- Tabelas AgGrid com busca, filtros, ordenação e paginação.
- Downloads CSV e XLSX que respeitam o recorte selecionado.

Resultados de categorias incompatíveis nunca são somados quando o filtro está em `Todos`.
O alcance é identificado como somado e pode conter sobreposição entre campanhas.

Conversas e mensagens são classificadas como `Engajamento`. O filtro de resultado oferece
apenas Engajamento, Cliques, Alcance e Cadastro; tipos não reconhecidos permanecem somente
nos totais gerais.

`Evento` não é um segmento exclusivo: uma campanha pode ser simultaneamente `0 km`,
`Evento` e `Cadastro`. Os filtros de segmento, ação e resultado atuam apenas nas respectivas
colunas e só formam uma interseção quando o usuário seleciona mais de uma dimensão.

## Planilha de entrada

A fonte compartilhada deve ser versionada em `dados/base_atual.xlsx`. Para atualizar o
dashboard, substitua esse arquivo mantendo o mesmo nome, faça commit e push. O caminho é
resolvido a partir da raiz do projeto e funciona independentemente do diretório atual.

O XLSX deve conter as abas abaixo. Abas adicionais são permitidas.

### `dados-face`

`Nome da Página`, `Nome da campanha`, `Tipo de resultado`, `Resultados`, `Alcance`,
`Impressões`, `Custo por resultado`, `Cliques (todos)`, `Valor usado (BRL)`,
`Início dos relatórios`, `Término dos relatórios` e `Semana`.

### `dados-google`

`Marca`, `Campanha`, `Tipo de campanha`, `Cliques`, `Impr.`, `Custo`, `CPC`, `Início`,
`Fim` e `Semana`.

Datas usam dia primeiro. Valores como `1.738`, `241,99` e `2.472,58` são interpretados
como 1738, 241.99 e 2472.58. O alcance do Google permanece nulo, pois não existe na fonte.
Erros impeditivos da base são apresentados por uma mensagem pública segura. Registros sem marca ou praça
permanecem nos totais gerais, mas não criam categorias artificiais nos filtros e gráficos.

Durante a normalização, `marca_original` preserva o valor recebido e `marca` recebe o nome
canônico usado no dashboard. Os aliases consolidam Chery, Geração Omoda Jaecoo, Hyundai
HMB, Yamaha e Geração Seminovos sem substituições parciais.

## Períodos

O intervalo padrão começa no primeiro dia do mês da data mais recente e termina na última
data disponível. Uma linha é incluída quando seu intervalo intersecta a seleção. Como os
valores da fonte já são agregados, a linha inteira é considerada e não há rateio proporcional.
Datas inexistentes no mês comparativo são ajustadas ao último dia válido e informadas.

A evolução respeita o texto e as datas das semanas existentes na planilha. As datas de
início definem a ordem cronológica; semanas de meses diferentes recebem chaves internas
distintas, embora o eixo preserve rótulos simples como `1 a 8` e `9 a 16`.

## Instalação

Requer Python 3.11 ou superior.

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Prompt de Comando do Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Testes:

```bash
pytest
```

## Configuração das regras

- Aliases de praça e sua prioridade: `PLACE_ALIASES` em `src/config.py`. Coloque padrões
  específicos antes dos genéricos.
- Aliases exatos de marca: `BRAND_ALIASES` em `src/config.py`.
- Tokens de cor dos modos claro e escuro: `THEME_COLORS` em `src/config.py`.
- Campanhas e tipos de resultado: funções puras em `src/classifiers.py`.
- Colunas obrigatórias: `REQUIRED_COLUMNS` em `src/config.py`.

Ao alterar uma regra, adicione ou ajuste o teste correspondente em `tests/`.

## Estrutura

```text
dashboard_midias/
├── app.py
├── assets/styles.css
├── dados/
│   ├── base_atual.xlsx
│   └── README.md
├── src/
│   ├── data_loader.py, validators.py, normalization.py, classifiers.py
│   ├── filters.py, comparisons.py, metrics.py, formatters.py, exports.py
│   └── views/
├── tests/
├── requirements.txt
└── README.md
```

## GitHub

```bash
git init
git add .
git commit -m "Implementa dashboard de mídia paga"
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Versione `dados/base_atual.xlsx`, pois essa é a fonte compartilhada do dashboard. Não
versione credenciais, `.venv` ou `.streamlit/secrets.toml`.

## Publicação

No Streamlit Community Cloud, envie este diretório a um repositório GitHub, crie um app e
selecione `app.py` como arquivo de entrada. `requirements.txt` deve permanecer no mesmo
diretório do entrypoint. Escolha uma versão de Python compatível (3.11+) nas configurações.
Confirme também que `dados/base_atual.xlsx` aparece no repositório publicado.

Em outro serviço Linux que execute Python, use:

```bash
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```
