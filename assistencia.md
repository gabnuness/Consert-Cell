# Sistema de Gestão de Assistência Técnica e Acessórios

**Objetivo:** controlar os dispositivos (tablets e celulares) enviados para assistência técnica e os acessórios entregues (películas, capinhas, carregadores etc.), para ter visibilidade e controle dos custos da empresa.
**Usuário:** apenas o TI (usuário único, sem necessidade de perfis de acesso complexos).

---

## 1. O que o sistema deve fazer

- Registrar cada **ordem de assistência técnica**: qual aparelho foi, quando saiu, para qual assistência, qual defeito, quanto custou e quando voltou.
- Registrar cada **saída de acessório**: o que foi entregue, para quem, quando, quantidade e custo.
- Controlar o **estoque** de acessórios (entradas por compra, saídas por entrega, alerta de estoque baixo).
- Mostrar **quanto a empresa gasta** com assistência e acessórios, por período, setor, colaborador e aparelho.
- Identificar **aparelhos problemáticos** (muitas manutenções, custo de reparo próximo ao valor do aparelho) e **colaboradores/setores com gasto recorrente**.
- Manter o **histórico completo** de cada aparelho.
- Gerar **relatórios** exportáveis (Excel/PDF) para prestação de contas.

---

## 2. Funções (módulos)

### 2.1 Cadastros
| Cadastro | Para quê |
|---|---|
| Dispositivos | Tablets e celulares da empresa |
| Colaboradores / setores | Quem usa o aparelho ou recebe o acessório |
| Fornecedores / assistências técnicas | Para onde o aparelho é enviado |
| Itens de acessório | Película, capinha, carregador, cabo, fone etc. |

### 2.2 Assistência técnica
- Abrir ordem de serviço (OS) de envio
- Atualizar status: *Enviado → Em análise → Orçamento aprovado → Em reparo → Pronto → Devolvido* (ou *Sem conserto / Baixado*)
- Registrar orçamento e custo final
- Registrar garantia do reparo (para detectar retorno pelo mesmo defeito)
- Registrar aparelho reserva emprestado enquanto o original está fora (opcional)

### 2.3 Acessórios
- Registrar entrada no estoque (compra)
- Registrar saída (entrega a colaborador, com data e motivo: novo, reposição, quebra, perda)
- Ajuste de estoque
- Alerta de estoque mínimo

### 2.4 Controle de custos
- Custo por OS, por aparelho, por colaborador, por setor, por período
- Custo médio de reparo por tipo de defeito e por assistência
- Comparativo mensal/anual

### 2.5 Relatórios e painel (dashboard)
- Gasto total do mês/ano (assistência + acessórios)
- Top 10 aparelhos que mais foram à assistência
- Top colaboradores/setores com maior consumo de acessórios
- Aparelhos atualmente fora da empresa e há quantos dias
- Acessórios com estoque baixo
- Exportação em Excel/PDF

### 2.6 Extras úteis
- Anexar documentos (orçamento, nota fiscal, foto do defeito)
- Alerta de OS parada há mais de X dias
- Integração futura com o [sistema de termos de responsabilidade](#) (AutomaTermos) e com o inventário de celulares

---

## 3. Dados que o sistema deve **receber** (entrada)

### Dispositivo
- Tipo (celular/tablet), marca, modelo
- IMEI / número de série
- Patrimônio/identificação interna
- Data e valor de aquisição, garantia do fabricante
- Número da linha (se houver)
- Colaborador/setor atual
- Situação (em uso, em estoque, na assistência, baixado)

### Ordem de assistência
- Dispositivo, data de envio, assistência técnica
- Defeito relatado, quem solicitou
- Valor do orçamento, aprovação (sim/não, data)
- Valor final, data de retorno, garantia do serviço
- Observações, anexos

### Acessório
- Nome/descrição, categoria, modelo compatível
- Quantidade comprada, custo unitário, fornecedor, nota fiscal, data
- Estoque mínimo desejado

### Saída de acessório
- Item, quantidade, data
- Colaborador/setor
- Dispositivo associado (opcional)
- Motivo (novo, reposição, quebra, perda)

### Cadastros de apoio
- Colaboradores: nome, setor, cargo/matrícula
- Fornecedores: nome, contato, CNPJ

---

## 4. Dados que o sistema deve **armazenar**

| Tabela | Principais campos |
|---|---|
| `dispositivos` | id, tipo, marca, modelo, imei/serial, patrimônio, data_aquisição, valor, garantia_até, colaborador_id, status |
| `colaboradores` | id, nome, setor, matrícula, ativo |
| `fornecedores` | id, nome, tipo (assistência/loja), contato, cnpj |
| `ordens_assistencia` | id, dispositivo_id, fornecedor_id, data_envio, defeito, status, valor_orcado, valor_final, aprovado_em, data_retorno, garantia_até, observações |
| `acessorios` | id, nome, categoria, compatibilidade, estoque_atual, estoque_minimo, custo_médio |
| `entradas_acessorio` | id, acessorio_id, quantidade, custo_unitário, fornecedor_id, nota_fiscal, data |
| `saidas_acessorio` | id, acessorio_id, quantidade, colaborador_id, dispositivo_id, motivo, data, custo_no_momento |
| `anexos` | id, tipo, caminho_do_arquivo, vínculo (OS/entrada) |
| `historico` (log) | id, entidade, ação, data/hora, detalhes (rastreabilidade das mudanças) |

**Informações derivadas (calculadas, não precisam ser digitadas):**
- Custo total por aparelho, colaborador e setor
- Número de manutenções por aparelho
- Dias que o aparelho ficou fora
- Valor atual do estoque de acessórios

---

## 5. Ferramentas técnicas sugeridas

### Opção A — Rápida e simples (recomendada para começar)
Como você já trabalha com Python e está desenvolvendo o AutomaTermos com Flask, vale aproveitar o mesmo conhecimento:

| Camada | Ferramenta |
|---|---|
| Linguagem | **Python** |
| Back-end web | **Flask** (ou FastAPI) |
| Banco de dados | **SQLite** (arquivo único, sem servidor, ideal para usuário único) |
| ORM | **SQLAlchemy** (+ **Alembic** para migrações) |
| Front-end | **Jinja2 + Bootstrap** (templates simples) |
| Gráficos | **Chart.js** ou **Plotly** |
| Relatórios | **pandas** + **openpyxl** (Excel) e **WeasyPrint/ReportLab** (PDF) |
| Formulários | **Flask-WTF** |

### Opção B — Mais crescimento no futuro
| Camada | Ferramenta |
|---|---|
| Banco | **PostgreSQL** ou **MariaDB** |
| Framework | **Django** (já traz painel administrativo, CRUD e autenticação prontos) |
| Deploy | **Docker** em servidor interno |

> **Dica:** o **Django Admin** entrega praticamente todo o CRUD pronto, com filtros e busca, com muito pouco código. Para uso individual, é uma ótima forma de ter o sistema funcionando rápido.

### Opção C — Sem programar (para validar a ideia)
- **Planilha** (Excel/Google Sheets) com abas ligadas por fórmulas
- **Baserow**, **NocoDB** ou **Airtable** (banco de dados visual, com formulários e dashboards)
- **Power BI / Metabase / Grafana** para os painéis, conectados ao banco ou à planilha

### Ferramentas complementares
- **Git/GitHub** para versionar o código
- **Backup** automático do arquivo `.db` (script agendado ou cópia para o NAS)
- **Leitor de código de barras / QR Code** (etiquetas por aparelho) para agilizar entrada e saída
- **Lembretes por e-mail** (`smtplib`) para OS paradas e estoque baixo

---

## 6. Sugestão de ordem de construção (MVP)

1. Cadastro de dispositivos, colaboradores e fornecedores
2. Ordem de assistência (abrir, atualizar status, registrar custo)
3. Cadastro e estoque de acessórios (entradas e saídas)
4. Dashboard de custos e relatórios em Excel
5. Alertas, anexos e etiquetas com QR Code
6. Integração com os outros sistemas (AutomaTermos / inventário de celulares)

---

## 7. Decisões tomadas

| Ponto | Decisão | Impacto no sistema |
|---|---|---|
| Identificação do aparelho | **IMEI** | Campo `imei` único e obrigatório em `dispositivos`. Tablets sem IMEI (só Wi-Fi) precisarão usar o número de série; vale prever o campo `serial` como alternativa. Celulares com dois chips têm dois IMEIs: guardar o IMEI 1 como principal. |
| Acessórios | **Com controle de estoque** | Módulo completo de entradas, saídas, ajuste e estoque mínimo (seção 2.3). |
| Responsável pelo custo | **Depende do diagnóstico**: mau uso gera **vale** para o colaborador; nos demais casos a empresa paga | Registrar o diagnóstico em cada OS, o responsável pelo custo e, quando houver vale, o valor e o status dele (ver seção 8). |
| Onde roda | **Apenas no PC do TI**, por enquanto | **SQLite** + Flask local (`127.0.0.1`) atende bem. Sem necessidade de login. Fazer **backup** periódico do arquivo `.db`. Se for para a rede no futuro, basta trocar o banco e adicionar autenticação. |

---

## 8. Ajustes decorrentes das decisões

### 8.1 Fluxo do diagnóstico e do vale
1. Aparelho volta da assistência com o **laudo/diagnóstico**.
2. TI classifica a **causa**: `defeito de fabricação/garantia`, `desgaste natural`, `mau uso`, `acidente/queda`, `outro`.
3. O sistema sugere o responsável pelo custo (mau uso → colaborador; demais → empresa), mas o TI pode alterar.
4. Se for colaborador, gera o registro de **vale** com valor, data e situação (`pendente`, `emitido`, `descontado`, `cancelado`).
5. Os relatórios separam **custo da empresa** e **valor repassado em vale**.

### 8.2 Campos a acrescentar em `ordens_assistencia`
- `causa` (lista acima)
- `laudo` (texto) e anexo do laudo
- `responsavel_custo` (`empresa` ou `colaborador`)
- `valor_empresa` e `valor_colaborador` (permite divisão parcial do custo)

### 8.3 Nova tabela `vales`
| Campo | Descrição |
|---|---|
| id | identificador |
| ordem_id | OS que originou o vale |
| colaborador_id | quem arca com o custo |
| valor | valor do vale |
| data_emissao | quando foi gerado |
| status | pendente / emitido / descontado / cancelado |
| observações | justificativa, número do documento, parcelas |

> O mesmo vale pode ser usado para **acessórios perdidos ou danificados**: em `saidas_acessorio`, o motivo `perda` ou `quebra` pode gerar vale da mesma forma.

### 8.4 Relatórios adicionais
- Total de vales por período e por situação
- Custo líquido da empresa (custo total menos valores repassados em vale)
- Vales pendentes de emissão ou desconto
- Colaboradores com reincidência de mau uso

### 8.5 Ajustes no MVP
Incluir o **diagnóstico e o vale** já na etapa 2 (ordem de assistência), pois mudam a forma de calcular o custo da empresa.
