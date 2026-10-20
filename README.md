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

- **Gestão de Dispositivos:**
  - Cadastro de celulares e tablets com suporte a IMEI, número de série e número de patrimônio.
  - Vínculo direto com colaboradores e setores da empresa.
  - **Índice de Inviabilidade ("Aparelho Bomba"):** Alerta automático quando o somatório de manutenções ultrapassa 50% do valor de aquisição do aparelho, recomendando substituição.
  - Histórico e linha do tempo completa por dispositivo.

- **Ordens de Serviço (OS):**
  - Acompanhamento do ciclo de vida: *Enviado → Em análise → Orçamento aprovado → Em reparo → Pronto → Devolvido / Baixado*.
  - **Contador Dinâmico de SLA:** Alertas visuais para aparelhos parados há mais de 7 dias (atenção) e mais de 15 dias (crítico).
  - **Alerta de Reincidência e Garantia:** Alerta automático caso um aparelho dê defeito dentro de 90 dias após o último retorno da assistência técnica.
  - **Classificação de Causa e Laudo Técnico:** Classificação entre desgaste natural, defeito de fabricação, mau uso ou queda.

- **Cálculo de Custos e Vales (RH / Departamento Pessoal):**
  - Separação automatizada entre **Custo da Empresa** e **Valor a Descontar do Colaborador**.
  - Se a causa for *Mau Uso* ou *Perda*, o sistema gera automaticamente um **Vale** pendente de desconto em folha de pagamento.
  - Painel dedicado com status dos vales: *Pendente → Emitido → Descontado → Cancelado*.

- **Controle de Estoque de Acessórios:**
  - Gerenciamento de películas, capas, carregadores e cabos.
  - **Custo Médio Ponderado:** Recalculado automaticamente a cada nova compra.
  - Alerta imediato de reposição quando o saldo atinge o estoque mínimo.
  - Saídas com motivos rastreáveis (*Novo, Reposição, Quebra ou Perda com opção de vale*).

- **Exportação e Relatórios:**
  - Exportação em **Excel (.xlsx)** consolidado com um clique, contendo abas formatadas para Ordens de Serviço, Dispositivos, Vales e Estoque.

---

## 🛠️ Tecnologias Utilizadas

- **Back-end:** Python 3.10+, Flask 3.0, Flask-SQLAlchemy, OpenPyXL.
- **Banco de Dados:** SQLite (arquivo único local, de fácil backup e sem necessidade de servidor dedicado).
- **Front-end:** HTML5 semântico, Vanilla CSS customizado (design system com paleta Slate/Indigo), Bootstrap 5.3, Bootstrap Icons e Chart.js.

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
