import pytest
from datetime import date, timedelta
from models import db, Colaborador, Fornecedor, Dispositivo, OrdemAssistencia, Acessorio

def test_ids_inexistentes_retornam_404_sem_erro_500(client):
    """Garante que IDs inexistentes em rotas parametrizadas retornem 404 (Not Found) e nunca 500."""
    rotas_get_404 = [
        '/dispositivos/99999/historico',
    ]
    for r in rotas_get_404:
        res = client.get(r)
        assert res.status_code == 404, f"Rota {r} deveria retornar 404, retornou {res.status_code}"

    rotas_post_404 = [
        ('/dispositivos/99999/editar', {'tipo': 'celular'}),
        ('/ordens/99999/atualizar-status', {'status': 'pronto'}),
        ('/ordens/99999/concluir', {'status_final': 'devolvido'}),
        ('/vales/99999/status', {'status': 'descontado'}),
    ]
    for r, dados in rotas_post_404:
        res = client.post(r, data=dados)
        assert res.status_code == 404, f"Rota {r} deveria retornar 404, retornou {res.status_code}"

def test_injecao_sql_e_xss_protegidos(client, app, celular_padrao):
    """
    Testa payload de SQL Injection e XSS nos campos de texto.
    O sistema deve escapar tags HTML e parametrizar queries SQL.
    """
    payload_xss = "<script>alert('hack')</script>"
    payload_sqli = "'; DROP TABLE colaboradores; --"

    res = client.post('/cadastros/colaborador', data={
        'nome': payload_sqli,
        'setor': payload_xss,
        'matricula': 'MAT-SEC'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        colab = Colaborador.query.filter_by(matricula='MAT-SEC').first()
        assert colab is not None
        assert colab.nome == payload_sqli
        
    res_tela = client.get('/cadastros')
    assert b"<script>alert('hack')</script>" not in res_tela.data
    assert b"&lt;script&gt;alert(&#39;hack&#39;)&lt;/script&gt;" in res_tela.data or b"&lt;script&gt;" in res_tela.data

def test_campos_apenas_espacos_em_branco_recusados(client, app):
    """Strings compostas apenas de espaços '   ' devem ser tratadas como vazias e recusadas."""
    res = client.post('/cadastros/colaborador', data={
        'nome': '     ',
        'setor': '     '
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        assert Colaborador.query.count() == 0

def test_suporte_a_acentuacao_e_emojis(client, app):
    """Garante suporte completo a UTF-8 (acentuação em português, ç e emojis)."""
    nome_com_emoji = "João da Silva Conceição 📱🚀"
    res = client.post('/cadastros/colaborador', data={
        'nome': nome_com_emoji,
        'setor': 'Operações & Logística'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        colab = Colaborador.query.filter_by(nome=nome_com_emoji).first()
        assert colab is not None
        assert colab.nome == nome_com_emoji

def test_conversao_valor_monetario_padrao_brasileiro_com_virgula(client, app, colab_padrao):
    """
    CASO DE BORDA CRÍTICO:
    No Brasil, o usuário digita valores com vírgula (ex: '1250,50' ou '1.250,50').
    O sistema converte com sucesso para float sem estourar Erro 500.
    """
    res = client.post('/dispositivos', data={
        'tipo': 'celular',
        'marca': 'Xiaomi',
        'modelo': 'Redmi Note 13',
        'imei': '112233445566778',
        'valor_aquisicao': '1.250,50',  # Padrão brasileiro com ponto e vírgula
        'colaborador_id': str(colab_padrao.id)
    }, follow_redirects=True)
    
    assert res.status_code == 200
    with app.app_context():
        disp = Dispositivo.query.filter_by(imei='112233445566778').first()
        assert disp is not None
        assert disp.valor_aquisicao == 1250.50

def test_datas_fora_de_ordem_retorno_anterior_a_envio(client, app, celular_padrao, assistencia_padrao):
    """
    CASO DE BORDA LÓGICO:
    A data de retorno de uma OS não pode ser anterior à data de envio do aparelho.
    O sistema deve recusar com mensagem explicativa.
    """
    # Abre a OS com envio hoje
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'data_envio': date.today().strftime('%Y-%m-%d'),
        'defeito': 'Teste data invertida'
    })

    with app.app_context():
        os_id = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first().id

    # Tenta concluir com data de retorno de 30 dias atrás (anterior ao envio)
    data_passada = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    res = client.post(f'/ordens/{os_id}/concluir', data={
        'status_final': 'devolvido',
        'data_retorno': data_passada,
        'valor_final': '100.00'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert (b"anterior" in res.data or b"data de retorno" in res.data or b"envio" in res.data)

    with app.app_context():
        os_obj = OrdemAssistencia.query.get(os_id)
        # Permanece com status original (não devolvido com data inválida)
        assert os_obj.status == 'enviado'
