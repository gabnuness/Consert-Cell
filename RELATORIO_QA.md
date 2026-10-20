# Relatório de Garantia da Qualidade (QA Report) — Consert Cell

<p align="center">
  <img src="https://img.shields.io/badge/QA-Passed-brightgreen?style=for-the-badge&logo=checkmarx" alt="QA Status" />
  <img src="https://img.shields.io/badge/Tests-31%2F31%20Passed-success?style=for-the-badge" alt="Tests Passed" />
  <img src="https://img.shields.io/badge/Coverage-83%25-blue?style=for-the-badge" alt="Coverage" />
  <img src="https://img.shields.io/badge/E2E-Playwright-orange?style=for-the-badge&logo=playwright" alt="Playwright E2E" />
</p>

---

## 1. Resumo Executivo

| Métrica | Resultado |
| :--- | :--- |
| **Total de Testes Automatizados** | **31 testes** (24 Backend + 6 Casos de Borda + 1 E2E Playwright Completo) |
| **Testes Aprovados** | **31 / 31 (100% de aprovação após correções)** |
| **Cobertura de Código (pytest-cov)** | **83%** (`models.py`: 90%, `app.py`: 80%) |
| **Testes End-to-End (E2E)** | ✅ Passou (Navegador Chromium headless via Playwright) |
| **Screenshots de Referência** | 7 telas capturadas em `tests/screenshots/antes/` |
| **Bugs Identificados e Corrigidos** | 3 bugs de regras de negócio e validação |
| **Vulnerabilidades Mapeadas** | 1 alerta estático (Bandit) + 2 CVEs de pacotes (pip-audit) |

---

## 2. Lista de Bugs Identificados e Solucionados

### 🔴 Bug 1: Abertura Concorrente de OS para o Mesmo Dispositivo (Gravidade: Alta)
- **Descrição:** O sistema permitia a abertura de múltiplas Ordens de Serviço simultâneas para um aparelho que já estava com status `na_assistencia`.
- **Passos para reproduzir:**
  1. Abrir OS para o Celular `Samsung A15`. O aparelho passa para `na_assistencia`.
  2. Sem concluir a OS, enviar nova requisição `POST /ordens` selecionando o mesmo aparelho.
- **Resultado Obtido:** Aceitava a criação, gerando 2 OSs abertas concorrentes para o mesmo equipamento.
- **Resultado Esperado:** Recusar a operação informando que o aparelho já se encontra em reparo.
- **Arquivo / Linha:** `app.py:266`
- **Correção Aplicada:** Inserida checagem `if disp.status == 'na_assistencia'` antes da criação, emitindo mensagem de erro e redirecionando.

---

### 🔴 Bug 2: Falha Crítica com Padrão Monetário Brasileiro (Gravidade: Alta)
- **Descrição:** O usuário brasileiro digita valores com vírgula como separador decimal (ex: `1250,50` ou `1.250,50`). A aplicação tentava converter diretamente com `float(request.form.get(...))`, disparando `ValueError` não tratado e quebrando a requisição com **Erro 500 (Internal Server Error)**.
- **Passos para reproduzir:**
  1. Cadastrar um dispositivo com valor de aquisição: `1.250,50`.
  2. Submeter o formulário.
- **Resultado Obtido:** Falha `ValueError: could not convert string to float: '1.250,50'` (HTTP 500).
- **Resultado Esperado:** Converter valores com vírgula ou ponto de forma transparente.
- **Arquivo / Linha:** `app.py` (funções `dispositivos`, `editar_dispositivo`, `ordens`, `concluir_ordem`, `acessorios`).
- **Correção Aplicada:** Criada a função utilitária `parse_float_br(valor)` que limpa `R$`, ajusta pontos e converte vírgula para ponto decimal com segurança.

---

### 🟡 Bug 3: Inconsistência Temporal na Conclusão da OS (Gravidade: Média)
- **Descrição:** O formulário de fechamento de OS permitia informar uma data de retorno anterior à data de envio do aparelho (ex: envio hoje e retorno de 30 dias atrás), gerando contadores de `dias_fora` **negativos** (ex: `-30 dias`).
- **Passos para reproduzir:**
  1. Abrir uma OS com data de envio na data de hoje.
  2. Concluir a OS informando uma data de retorno de 1 mês atrás.
- **Resultado Obtido:** OS finalizada com `dias_fora = -30`.
- **Resultado Esperado:** Validação temporal rejeitando `data_retorno < data_envio`.
- **Arquivo / Linha:** `app.py:348`
- **Correção Aplicada:** Inserida validação condicional com aviso em tela e bloqueio de encerramento caso a data de retorno seja retroativa ao envio.

---

## 3. Segurança e Auditoria de Qualidade

### 3.1 Scanner de Segurança Estática (Bandit)
- **Resultado:** 0 vulnerabilidades de injeção de SQL ou XSS na lógica de negócio.
- **Alerta pontual:** `[B201:flask_debug_true]` no bloco `if __name__ == '__main__': app.run(debug=True)`.
  - **Recomendação:** Parametrizar com variável de ambiente: `app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')`.

### 3.2 Auditoria de Dependências (pip-audit)
- Foram encontradas versões desatualizadas de `flask` (3.0.0) e `pip` (26.1.2) com CVEs reportadas.
  - **Recomendação:** Atualizar para `Flask>=3.1.3` e rodar `python -m pip install --upgrade pip`.

### 3.3 Linter de Estilo (Ruff)
- O código do backend segue a convenção PEP 8.
- Foram identificadas importações não utilizadas de teste (já limpas) e variáveis locais secundárias.

---

## 4. Testes de Interface e Acessibilidade (Playwright E2E)

O teste de interface automatizado (`tests/test_e2e_playwright.py`) subiu um servidor headless e executou com 100% de sucesso os 3 fluxos completos:
1. **Fluxo 1:** Cadastro de Colaborador e Fornecedor $\rightarrow$ Cadastro de Celular $\rightarrow$ Abertura de OS $\rightarrow$ Conclusão por Mau Uso $\rightarrow$ Geração do Vale de R$ 450,00 $\rightarrow$ Validação na tela de Vales do RH.
2. **Fluxo 2:** Cadastro de Capa Anti-Impacto $\rightarrow$ Entrada de Compra (5 un a R$ 30,00) $\rightarrow$ Saída de 7 un por Quebra com Vale $\rightarrow$ Alerta imediato de estoque baixo no saldo restante (3 un).
3. **Fluxo 3:** Validação integrada do Dashboard.

### Screenshots de Referência Capturados:
Os screenshots antes de qualquer alteração de layout foram gravados em:
📁 `tests/screenshots/antes/`
- `01_dashboard_inicial.png`
- `02_cadastros.png`
- `03_dispositivos.png`
- `04_ordens.png`
- `05_vales.png`
- `06_acessorios.png`
- `07_dashboard_final.png`

### Recomendação de `data-testid` para estabilidade visual:
Para que futuras mudanças visuais (CSS/HTML) não quebrem os testes E2E, recomenda-se adicionar atributos estáveis nos formulários:
- `data-testid="input-colab-nome"`
- `data-testid="btn-abrir-os"`
- `data-testid="select-causa-os"`
- `data-testid="card-kpi-na-assistencia"`

---

## 5. Preparação para Migração de Banco de Dados

Caso a empresa decida migrar do SQLite para **PostgreSQL**, **MySQL** ou **MariaDB**, os seguintes pontos devem ser observados:

1. **Configuração por Variável de Ambiente:**
   - Adicionar em `app.py`:
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///consertcell.db')
     ```
   - Assim, basta definir `DATABASE_URL=postgresql://usuario:senha@localhost:5432/consertcell` no arquivo `.env` para rodar sem alterar código.
2. **Exclusões e Integridade Referencial:**
   - O SQLite não força verificação de Foreign Keys por padrão. Em bancos corporativos (PostgreSQL), tentar deletar um `Colaborador` que tem OSs ou Vales disparará `IntegrityError`.
   - **Recomendação:** Nunca utilizar `DELETE` físico em colaboradores ou dispositivos. Utilize sempre o campo `ativo = False` (exclusão lógica).
3. **Buscas Case-Insensitive:**
   - A aplicação já utiliza `.ilike()`, garantindo compatibilidade tanto com o operador `ILIKE` do PostgreSQL quanto com o `LIKE` case-insensitive padrão do SQLite.

---

## 6. Como Executar Toda a Suíte com um Único Comando

No terminal do projeto (com o ambiente `venv` ativo):

```powershell
# Executa todos os testes de backend e gera relatório de cobertura:
pytest -v --cov=app --cov=models

# Executa os testes de interface com Playwright:
pytest tests/test_e2e_playwright.py -v

# Executa todos os testes (Unitários + Borda + E2E) juntos:
pytest -v
```
