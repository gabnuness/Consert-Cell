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
