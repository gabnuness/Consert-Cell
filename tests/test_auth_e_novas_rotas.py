import pytest
from app import app as flask_app, bcrypt
from models import db, AdminUser, Colaborador, Dispositivo, Fornecedor, Acessorio, OrdemAssistencia
from datetime import date

def test_modelo_admin_e_hash(app):
    """Testa criação do admin, hash de senha Bcrypt e validação de dicionário."""
    with app.app_context():
        user = AdminUser(
            email="ti.teste@disfonte.com.br",
            nome="Admin Teste",
            senha_hash=bcrypt.generate_password_hash("SenhaForte123!").decode("utf-8"),
            token_api="token_super_secreto_123"
        )
        db.session.add(user)
        db.session.commit()

        buscado = AdminUser.query.filter_by(email="ti.teste@disfonte.com.br").first()
        assert buscado is not None
        assert buscado.nome == "Admin Teste"
        assert bcrypt.check_password_hash(buscado.senha_hash, "SenhaForte123!") is True
        assert bcrypt.check_password_hash(buscado.senha_hash, "SenhaErrada") is False
        assert buscado.to_dict()["email"] == "ti.teste@disfonte.com.br"

def test_api_rest_login_e_bearer_token(client, app):
    """Testa autenticação via API REST (JSON) e validação de token Bearer."""
    with app.app_context():
        user = AdminUser(
            email="api.admin@disfonte.com.br",
            nome="Admin API",
            senha_hash=bcrypt.generate_password_hash("TokenPass123").decode("utf-8"),
            token_api="token_teste_bearer_abc"
        )
        db.session.add(user)
        db.session.commit()

    # Tentativa com senha errada
    resp_erro = client.post("/api/auth/login", json={
        "email": "api.admin@disfonte.com.br",
        "senha": "senha_incorreta"
    })
    assert resp_erro.status_code == 401
    assert resp_erro.get_json()["success"] is False

    # Login com sucesso
    resp_ok = client.post("/api/auth/login", json={
        "email": "api.admin@disfonte.com.br",
        "senha": "TokenPass123"
    })
    assert resp_ok.status_code == 200
    dados = resp_ok.get_json()
    assert dados["success"] is True
    assert "token" in dados

    # Consulta /api/auth/me com Bearer token
    token = dados["token"]
    resp_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.status_code == 200
    assert resp_me.get_json()["user"]["email"] == "api.admin@disfonte.com.br"

    # Encerra sessão para testar chamada sem token/sessão
    client.post("/api/auth/logout")
    resp_sem_token = client.get("/api/auth/me")
    assert resp_sem_token.status_code == 401

def test_edicao_e_desfazer_ordem_servico(client, app, celular_padrao, assistencia_padrao):
    """Testa abertura, edição de dados e estorno/desfazer conclusão de OS."""
    # 1. Abrir OS
    resp_abrir = client.post("/ordens", data={
        "dispositivo_id": str(celular_padrao.id),
        "fornecedor_id": str(assistencia_padrao.id),
        "defeito": "Tela trincada original",
        "data_envio": date.today().strftime("%Y-%m-%d"),
        "valor_orcado": "200.00"
    }, follow_redirects=True)
    assert resp_abrir.status_code == 200

    os_criada = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first()
    assert os_criada is not None

    # 2. Editar OS
    resp_edit = client.post(f"/ordens/{os_criada.id}/editar", data={
        "fornecedor_id": str(assistencia_padrao.id),
        "defeito": "Tela trincada e conector oxidado",
        "laudo_tecnico": "Necessária troca de display e flex",
        "valor_orcado": "350.00",
        "observacoes": "Aguardando aprovação de orçamento"
    }, follow_redirects=True)
    assert resp_edit.status_code == 200

    os_editada = db.session.get(OrdemAssistencia, os_criada.id)
    assert "conector oxidado" in os_editada.defeito
    assert os_editada.valor_orcado == 350.00

    # 3. Concluir OS
    resp_conc = client.post(f"/ordens/{os_criada.id}/concluir", data={
        "data_retorno": date.today().strftime("%Y-%m-%d"),
        "valor_final": "350.00",
        "causa": "desgaste_natural",
        "laudo_tecnico": "Troca de display realizada com sucesso",
        "acao_dispositivo": "em_uso"
    }, follow_redirects=True)
    assert resp_conc.status_code == 200

    os_concluida = db.session.get(OrdemAssistencia, os_criada.id)
    assert os_concluida.status == "devolvido"
    assert os_concluida.is_aberta is False

    # 4. Desfazer Conclusão
    resp_desfazer = client.post(f"/ordens/{os_criada.id}/desfazer-conclusao", follow_redirects=True)
    assert resp_desfazer.status_code == 200

    os_reaberta = db.session.get(OrdemAssistencia, os_criada.id)
    assert os_reaberta.status == "em_reparo"
    assert os_reaberta.data_retorno is None
    assert os_reaberta.is_aberta is True


def test_rate_limit_web_login(client, app):
    """Testa bloqueio de força bruta na interface Web após 5 tentativas falhas (HTTP 429)."""
    with app.app_context():
        user = AdminUser(
            email="brute.force@disfonte.com.br",
            nome="Admin Teste Forca Bruta",
            senha_hash=bcrypt.generate_password_hash("Correta123!").decode("utf-8")
        )
        db.session.add(user)
        db.session.commit()

    # 5 tentativas com senha errada: devem retornar 401
    for i in range(1, 6):
        resp = client.post("/login", data={
            "email": "brute.force@disfonte.com.br",
            "senha": f"senha_errada_{i}"
        })
        if i < 5:
            assert resp.status_code == 401
            assert f"Tentativas restantes antes do bloqueio: {5 - i}" in resp.get_data(as_text=True)
        else:
            # Na 5ª falha o limite de 5 é atingido e o bloqueio é ativado
            assert resp.status_code == 429
            assert "bloqueado por segurança" in resp.get_data(as_text=True).lower()

    # 6ª tentativa imediata: é rejeitada preventivamente com 429
    resp_bloqueado = client.post("/login", data={
        "email": "brute.force@disfonte.com.br",
        "senha": "qualquer_coisa"
    })
    assert resp_bloqueado.status_code == 429
    assert "Bloqueio de segurança ativo" in resp_bloqueado.get_data(as_text=True)


def test_rate_limit_api_login(client, app):
    """Testa bloqueio de força bruta na API REST após 5 falhas, verificando Retry-After e JSON."""
    with app.app_context():
        user = AdminUser(
            email="api.brute@disfonte.com.br",
            nome="API Brute Target",
            senha_hash=bcrypt.generate_password_hash("SenhaCerta999").decode("utf-8"),
            token_api="token_valido_999"
        )
        db.session.add(user)
        db.session.commit()

    # 5 falhas consecutivas via JSON
    for i in range(1, 6):
        resp = client.post("/api/auth/login", json={
            "email": "api.brute@disfonte.com.br",
            "senha": f"errada_{i}"
        })
        if i < 5:
            assert resp.status_code == 401
            data = resp.get_json()
            assert data["attempts_left"] == 5 - i
        else:
            assert resp.status_code == 429
            data = resp.get_json()
            assert data["error"] == "rate_limit_exceeded"
            assert "Retry-After" in resp.headers

    # Tentativa bloqueada
    resp_block = client.post("/api/auth/login", json={
        "email": "api.brute@disfonte.com.br",
        "senha": "SenhaCerta999"
    })
    assert resp_block.status_code == 429
    assert resp_block.get_json()["error"] == "rate_limit_exceeded"


def test_reset_rate_limit_apos_sucesso(client, app):
    """Testa que login com sucesso limpa o histórico de falhas e reseta a contagem."""
    with app.app_context():
        user = AdminUser(
            email="reset.rate@disfonte.com.br",
            nome="Admin Reset",
            senha_hash=bcrypt.generate_password_hash("SenhaForte!").decode("utf-8")
        )
        db.session.add(user)
        db.session.commit()

    # 3 falhas
    for _ in range(3):
        resp = client.post("/api/auth/login", json={
            "email": "reset.rate@disfonte.com.br",
            "senha": "senha_errada"
        })
        assert resp.status_code == 401

    # Login bem-sucedido
    resp_ok = client.post("/api/auth/login", json={
        "email": "reset.rate@disfonte.com.br",
        "senha": "SenhaForte!"
    })
    assert resp_ok.status_code == 200

    # Próxima falha deve ter voltado para 4 tentativas restantes (5 - 1)
    resp_nova_falha = client.post("/api/auth/login", json={
        "email": "reset.rate@disfonte.com.br",
        "senha": "outra_errada"
    })
    assert resp_nova_falha.status_code == 401
    assert resp_nova_falha.get_json()["attempts_left"] == 4


def test_defesa_timing_attack_email_inexistente(client, app):
    """Testa que usuário inexistente recebe a mesma mensagem genérica e não gera vazamento de informação."""
    resp = client.post("/api/auth/login", json={
        "email": "email_que_nao_existe@disfonte.com.br",
        "senha": "qualquer_coisa"
    })
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False
    assert "Credenciais inválidas" in data["message"]


def test_cabecalhos_seguranca_http(client):
    """Verifica se os cabeçalhos de segurança HTTP recomendados contra pentest estão ativos."""
    resp = client.get("/login")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

