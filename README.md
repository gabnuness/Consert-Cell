# Consert Cell 📱🔧

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Flask-3.0%2B-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License MIT" />
</p>

> **Consert Cell** é um sistema completo e simplificado para gestão de assistência técnica de dispositivos móveis (smartphones e tablets corporativos), controle de estoque de acessórios e cálculo automático de custos e vales para desconto em folha (RH/DP).

---

## 🌟 Principais Recursos

- **Segurança & Autenticação Administrativa:**
  - Sistema de login com proteção de rotas (`Flask-Login` e senhas criptografadas com `Bcrypt`).
  - **API REST JSON Integrada:** Autenticação via `POST /api/auth/login`, endpoints protegidos via `Bearer Token` (`GET /api/auth/me`), atualização de perfil e geração de novos tokens.
  - Modal administrativo para gerenciamento de credenciais (e-mail, nome, senha e chave de API) e limpeza operacional (*Zerar Banco*).

- **Gestão de Dispositivos & Equipamentos:**
  - Cadastro de celulares, tablets e coletores industriais com suporte a IMEI, número de série e número de patrimônio.
  - Vínculo com colaboradores e setores da empresa.
  - **Índice de Inviabilidade ("Aparelho Bomba"):** Alerta automático quando o somatório de manutenções ultrapassa 50% do valor de aquisição do aparelho.
  - **Função de Exclusão Segura:** Exclusão com confirmação e opção de limpeza de vínculos/histórico.

- **Ordens de Serviço (OS) com Edição e Desfazer:**
  - Ciclo de vida completo: *Enviado → Em análise → Orçamento aprovado → Em reparo → Pronto → Devolvido / Sem conserto*.
  - **Edição Completa de OS:** Permite editar dados de qualquer OS (técnico, fornecedor, datas, orçamento, laudo e valores).
  - **Desfazer Conclusão:** Reabre ordens finalizadas por engano, retornando o aparelho para manutenção e revertendo automaticamente vales de RH gerados.
  - **Exclusão de OS:** Cancelamento definitivo com liberação do aparelho e cancelamento de vales.
  - **Contador Dinâmico de SLA:** Alertas visuais para aparelhos parados há mais de 7 dias (alerta) e mais de 15 dias (crítico).
  - **Alerta de Reincidência e Garantia:** Alerta automático para aparelhos que apresentem defeito em menos de 90 dias após o retorno.

- **Cálculo de Custos e Vales (RH / Departamento Pessoal):**
  - Separação automatizada entre **Custo da Empresa** e **Valor a Descontar do Colaborador**.
  - Geração automática de **Vales** de desconto em folha em casos de mau uso ou perda de acessórios.
  - Painel com acompanhamento de status: *Pendente → Emitido → Descontado → Cancelado*.

- **Controle de Estoque de Acessórios:**
  - Gerenciamento de películas, capas, carregadores e cabos.
  - **Custo Médio Ponderado:** Recalculado automaticamente a cada nova compra.
  - Alerta imediato de reposição quando o saldo atinge o estoque mínimo.
  - Exclusão e controle de saídas rastreáveis.

- **Alternância de Bancos (Produção Real vs. LinkedIn / Demo):**
  - Scripts inclusos para backup online seguro (`consertcell_PRODUCAO_REAL.db`), restauração com 1 clique (`restaurar_banco_real.py`) e carga de modelo genérico para apresentações (`carregar_banco_linkedin.py`).

- **Exportação e Relatórios:**
  - Exportação em **Excel (.xlsx)** consolidado com abas formatadas para Ordens de Serviço, Dispositivos, Vales e Estoque.

---

## 🛠️ Tecnologias Utilizadas

- **Back-end:** Python 3.10+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, OpenPyXL.
- **Banco de Dados:** SQLite (arquivo local, com backup online nativo).
- **Front-end:** HTML5 semântico, Vanilla CSS customizado (design system com paleta Ambev Disfonte Slate/Cobalt), Bootstrap 5.3, Bootstrap Icons e Chart.js.

---

## 📁 Estrutura do Projeto

```text
Consert Cell/
├── app.py                  # Rotas principais, regras de negócio e exportação Excel
├── models.py               # Modelos SQLAlchemy e cálculos de regras de negócio
├── requirements.txt        # Dependências de produção
├── requirements-dev.txt    # Dependências de desenvolvimento e testes
├── iniciar.bat             # Inicializador automático para Windows (1 clique)
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore              # Arquivos e pastas ignorados pelo Git
├── static/
│   └── css/
│       └── style.css       # Design tokens, tipografia e estilos da interface
└── templates/
    ├── base.html           # Layout base responsivo e navegação
    ├── index.html          # Dashboard com KPIs, gráficos e alertas
    ├── dispositivos.html   # Listagem, busca e cadastro de aparelhos
    ├── historico_dispositivo.html # Linha do tempo individual do aparelho
    ├── ordens.html         # Gestão de OS, laudos e divisão de custos
    ├── vales.html          # Painel de controle de vales para o RH
    ├── acessorios.html     # Estoque e saídas de acessórios
    └── cadastros.html      # Cadastros rápidos de colaboradores e fornecedores
```

---

## 🚀 Como Executar

### 1. Clonar o Repositório
```bash
git clone https://github.com/gabnuness/Consert-Cell.git
cd Consert-Cell
```

### 2. Executar no Windows (Modo Rápido)
Basta dar um duplo clique no arquivo:
```text
iniciar.bat
```
O script configurará o ambiente virtual `.venv`, instalará os pacotes e abrirá o navegador em `http://127.0.0.1:5000`.

### 3. Execução Manual

1. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/macOS:
   source venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicie o servidor:**
   ```bash
   python app.py
   ```
   Acesse no seu navegador: `http://127.0.0.1:5000`

---

## 👤 Autor

Desenvolvido por **Gabriel Nunes**  
- GitHub: [@gabnuness](https://github.com/gabnuness)  
- LinkedIn / Contato: [gabnunes.developer@gmail.com](mailto:gabnunes.developer@gmail.com)

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).
