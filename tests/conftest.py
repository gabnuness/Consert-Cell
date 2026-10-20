import pytest
from datetime import date, timedelta
from app import app as flask_app
from models import db, Colaborador, Fornecedor, Dispositivo, Acessorio, OrdemAssistencia, Vale

@pytest.fixture
def app():
    """Cria uma instância isolada da aplicação para testes com SQLite em memória."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Cliente HTTP de teste para fazer requisições GET e POST."""
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

# Fixtures utilitárias de modelos pré-populados
@pytest.fixture
def colab_padrao(app):
    c = Colaborador(nome="Carlos Logística", setor="Logística", matricula="LOG01")
    db.session.add(c)
    db.session.commit()
    return c

@pytest.fixture
def assistencia_padrao(app):
    f = Fornecedor(nome="MegaCell Reparos", tipo="assistencia", contato="11999998888", cnpj="12.345.678/0001-90")
    db.session.add(f)
    db.session.commit()
    return f

@pytest.fixture
def loja_padrao(app):
    f = Fornecedor(nome="Distribuidora Alfa", tipo="loja", contato="1133334444", cnpj="98.765.432/0001-10")
    db.session.add(f)
    db.session.commit()
    return f

@pytest.fixture
def celular_padrao(app, colab_padrao):
    d = Dispositivo(
        tipo="celular",
        marca="Samsung",
        modelo="Galaxy A15",
        imei="123456789012345",
        patrimonio="PAT-001",
        data_aquisicao=date.today() - timedelta(days=180),
        valor_aquisicao=1000.0,
        colaborador_id=colab_padrao.id,
        status="em_uso"
    )
    db.session.add(d)
    db.session.commit()
    return d

@pytest.fixture
def tablet_padrao(app, colab_padrao):
    d = Dispositivo(
        tipo="tablet",
        marca="Samsung",
        modelo="Galaxy Tab A9",
        serial="SN-TAB-9988",
        patrimonio="PAT-TAB-01",
        data_aquisicao=date.today() - timedelta(days=90),
        valor_aquisicao=1500.0,
        colaborador_id=colab_padrao.id,
        status="em_uso"
    )
    db.session.add(d)
    db.session.commit()
    return d

@pytest.fixture
def acessorio_padrao(app):
    a = Acessorio(
        nome="Película Vidro A15",
        categoria="Pelicula",
        compatibilidade="Galaxy A15",
        estoque_atual=10,
        estoque_minimo=5,
        custo_medio=10.0
    )
    db.session.add(a)
    db.session.commit()
    return a
