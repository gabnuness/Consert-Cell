import os
import time
import threading
import pytest
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from app import app as flask_app
from models import db

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "antes")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class ServerThread(threading.Thread):
    def __init__(self, app, port=5005):
        super().__init__()
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.port = port

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

@pytest.fixture(scope="module")
def live_server():
    """Sobe um servidor HTTP local isolado em porta de teste com banco temporário."""
    db_path = os.path.join(os.path.dirname(__file__), "test_playwright.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False
    })

    with flask_app.app_context():
        db.create_all()

    server = ServerThread(flask_app, port=5005)
    server.start()
    time.sleep(1)  # Aguarda subida do socket
    
    yield "http://127.0.0.1:5005"
    
    server.shutdown()
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_fluxo_completo_e2e_playwright(live_server):
    """
    Fluxo E2E 1, 2 e 3:
    1. Cadastrar Colaborador e Fornecedor -> Cadastrar Dispositivo -> Abrir OS -> Concluir com Mau Uso -> Gerar Vale.
    2. Cadastrar Acessório -> Entrada de Compra -> Saída com Vale -> Verificar Estoque.
    3. Validar números e cards no Dashboard.
    Captura screenshots em tests/screenshots/antes/.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # ----------------------------------------------------
        # TELA 1: DASHBOARD INICIAL (VAZIO)
        # ----------------------------------------------------
        page.goto(f"{live_server}/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_dashboard_inicial.png"))
        assert "Painel Geral de Controle" in page.content()

        # ----------------------------------------------------
        # FLUXO 1: CADASTROS (COLABORADOR E FORNECEDOR)
        # ----------------------------------------------------
        page.goto(f"{live_server}/cadastros")
        page.wait_for_load_state("networkidle")

        # Cadastra Colaborador
        page.fill('input[name="nome"]', 'Roberto Logística')
        page.fill('input[name="setor"]', 'Expedição')
        page.fill('input[name="matricula"]', 'EXP01')
        page.click('button:has-text("Adicionar Colaborador")')
        page.wait_for_load_state("networkidle")

        # Cadastra Fornecedor / Assistência
        page.locator('input[placeholder*="MegaCell"]').fill('TechMaster Consertos')
        page.locator('select[name="tipo"]').first.select_option('assistencia')
        page.locator('input[name="contato"]').first.fill('11988887777')
        page.click('button:has-text("Cadastrar Fornecedor")')
        page.wait_for_load_state("networkidle")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_cadastros.png"))
        assert "Roberto Logística" in page.content()
        assert "TechMaster Consertos" in page.content()

        # ----------------------------------------------------
        # FLUXO 1 (CONT.): DISPOSITIVOS
        # ----------------------------------------------------
        page.goto(f"{live_server}/dispositivos")
        page.wait_for_load_state("networkidle")

        # Abre modal de novo dispositivo
        page.click('button:has-text("Cadastrar Dispositivo")')
        page.wait_for_selector('#modalNovoDispositivo', state='visible')

        # Preenche os dados
        page.locator('#modalNovoDispositivo select[name="tipo"]').select_option('celular')
        page.locator('#modalNovoDispositivo input[name="marca"]').fill('Samsung')
        page.locator('#modalNovoDispositivo input[name="modelo"]').fill('Galaxy S23')
        page.locator('#modalNovoDispositivo input[name="imei"]').fill('351234567890123')
        page.locator('#modalNovoDispositivo input[name="patrimonio"]').fill('PAT-S23-01')
        page.locator('#modalNovoDispositivo input[name="valor_aquisicao"]').fill('2500.00')
        
        # Seleciona Roberto como responsável
        page.locator('#modalNovoDispositivo select[name="colaborador_id"]').select_option(label='Roberto Logística (Expedição)')
        page.click('#modalNovoDispositivo button:has-text("Salvar Dispositivo")')
        page.wait_for_load_state("networkidle")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_dispositivos.png"))
        assert "Galaxy S23" in page.content()
        assert "351234567890123" in page.content()

        # ----------------------------------------------------
        # FLUXO 1 (CONT.): ORDENS DE SERVIÇO & FECHAMENTO COM VALE
        # ----------------------------------------------------
        page.goto(f"{live_server}/ordens")
        page.wait_for_load_state("networkidle")

        # Abre modal de nova OS
        page.click('button:has-text("Abrir Nova OS")')
        page.wait_for_selector('#modalNovaOS', state='visible')

        page.locator('#modalNovaOS select[name="dispositivo_id"]').select_option(index=1)
        page.locator('#modalNovaOS select[name="fornecedor_id"]').select_option(index=1)
        page.locator('#modalNovaOS textarea[name="defeito"]').fill('Vidro frontal quebrado por impacto no chão')
        page.locator('#modalNovaOS input[name="valor_orcado"]').fill('450.00')
        page.click('#modalNovaOS button:has-text("Abrir Ordem de Serviço")')
        page.wait_for_load_state("networkidle")

        # Concluir a OS com Mau Uso -> Gera Vale
        page.click('button.btn-concluir')
        page.wait_for_selector('#modalConcluirOS', state='visible')

        page.locator('#modalConcluirOS select[name="causa"]').select_option('mau_uso')
        page.locator('#modalConcluirOS select[name="causa"]').dispatch_event('change')
        page.locator('#modalConcluirOS input[name="valor_final"]').fill('450.00')
        page.locator('#modalConcluirOS input[name="valor_colaborador"]').fill('450.00')
        page.locator('#modalConcluirOS textarea[name="laudo"]').fill('Substituição de display original danificado por queda')
        page.click('#modalConcluirOS button:has-text("Confirmar Conclusão")')
        page.wait_for_load_state("networkidle")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_ordens.png"))
        assert "450,00" in page.content()

        # ----------------------------------------------------
        # FLUXO 1 (FINAL): VALES (RH / DP)
        # ----------------------------------------------------
        page.goto(f"{live_server}/vales")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_vales.png"))
        assert "Roberto Logística" in page.content()
        assert "450,00" in page.content()

        # ----------------------------------------------------
        # FLUXO 2: ACESSÓRIOS & ESTOQUE
        # ----------------------------------------------------
        page.goto(f"{live_server}/acessorios")
        page.wait_for_load_state("networkidle")

        # Novo item
        page.click('button:has-text("Novo Item")')
        page.wait_for_selector('#modalNovoAcessorio', state='visible')
        page.locator('#modalNovoAcessorio input[name="nome"]').fill('Capa Anti-Impacto S23')
        page.locator('#modalNovoAcessorio select[name="categoria"]').select_option('Capa')
        page.locator('#modalNovoAcessorio input[name="estoque_minimo"]').fill('4')
        page.locator('#modalNovoAcessorio input[name="estoque_inicial"]').fill('5')
        page.locator('#modalNovoAcessorio input[name="custo_inicial"]').fill('20.00')
        page.click('#modalNovoAcessorio button:has-text("Salvar Item")')
        page.wait_for_load_state("networkidle")

        # Entrada de mais 5 itens a R$ 30,00
        page.click('button:has-text("Entrada (Compra)")')
        page.wait_for_selector('#modalEntrada', state='visible')
        page.locator('#modalEntrada select[name="acessorio_id"]').select_option(index=1)
        page.locator('#modalEntrada input[name="quantidade"]').fill('5')
        page.locator('#modalEntrada input[name="custo_unitario"]').fill('30.00')
        page.click('#modalEntrada button:has-text("Confirmar Entrada")')
        page.wait_for_load_state("networkidle")

        # Saída de 7 itens (saldo vai para 3 un, abaixo do mínimo 4)
        page.click('button:has-text("Saída (Entrega)")')
        page.wait_for_selector('#modalSaida', state='visible')
        page.locator('#modalSaida select[name="acessorio_id"]').select_option(index=1)
        page.locator('#modalSaida input[name="quantidade"]').fill('7')
        page.locator('#modalSaida select[name="colaborador_id"]').select_option(index=1)
        page.locator('#modalSaida select[name="motivo"]').select_option('quebra')
        page.click('#modalSaida button:has-text("Registrar Saída")')
        page.wait_for_load_state("networkidle")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_acessorios.png"))
        assert "3 un." in page.content()
        assert "Reposição Urgente" in page.content() or "baixo" in page.content()

        # ----------------------------------------------------
        # FLUXO 3: DASHBOARD FINAL COM DADOS INTEGRADOS
        # ----------------------------------------------------
        page.goto(f"{live_server}/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_dashboard_final.png"))
        
        # Verifica elementos principais do painel
        assert "Evolução de Gastos da Empresa" in page.content()
        assert "Painel Geral de Controle" in page.content()

        browser.close()
