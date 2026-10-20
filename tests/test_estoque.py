import pytest
from models import db, Acessorio, EntradaAcessorio, SaidaAcessorio, Vale

def test_entrada_estoque_soma_e_recalcula_custo_medio_ponderado(client, app, acessorio_padrao, loja_padrao):
    """
    Testa a fórmula de média móvel ponderada:
    - Saldo inicial: 10 un a R$ 10,00 (Total = R$ 100,00)
    - Nova compra: 10 un a R$ 20,00 (Total = R$ 200,00)
    - Novo estoque: 20 un
    - Novo custo médio: (100 + 200) / 20 = R$ 15,00
    """
    res = client.post('/acessorios/entrada', data={
        'acessorio_id': str(acessorio_padrao.id),
        'quantidade': '10',
        'custo_unitario': '20.00',
        'fornecedor_id': str(loja_padrao.id),
        'nota_fiscal': 'NF-10020'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        item = Acessorio.query.get(acessorio_padrao.id)
        assert item.estoque_atual == 20
        assert item.custo_medio == 15.0
        assert item.valor_total_estoque == 300.0

def test_saida_estoque_subtrai_corretamente(client, app, acessorio_padrao, colab_padrao):
    """Testa saída regular de estoque (entrega ao colaborador)."""
    saldo_anterior = acessorio_padrao.estoque_atual  # 10
    res = client.post('/acessorios/saida', data={
        'acessorio_id': str(acessorio_padrao.id),
        'quantidade': '3',
        'colaborador_id': str(colab_padrao.id),
        'motivo': 'novo'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        item = Acessorio.query.get(acessorio_padrao.id)
        assert item.estoque_atual == 7
        assert item.custo_medio == 10.0  # Custo médio unitário não se altera na saída
        saida = SaidaAcessorio.query.filter_by(acessorio_id=item.id).first()
        assert saida is not None
        assert saida.quantidade == 3
        assert saida.custo_no_momento == 30.0  # 3 * 10.0

def test_saida_maior_que_estoque_recusada_sem_ficar_negativo(client, app, acessorio_padrao, colab_padrao):
    """Garante que o sistema recusa saídas quando o saldo solicitado for maior que o disponível."""
    saldo_disponivel = acessorio_padrao.estoque_atual  # 10
    
    res = client.post('/acessorios/saida', data={
        'acessorio_id': str(acessorio_padrao.id),
        'quantidade': '15',  # Pedindo 15 de 10 disponíveis
        'colaborador_id': str(colab_padrao.id),
        'motivo': 'novo'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert (b"insuficiente" in res.data.lower() or 
            b"saldo" in res.data.lower() or 
            b"estoque" in res.data.lower())

    with app.app_context():
        item = Acessorio.query.get(acessorio_padrao.id)
        assert item.estoque_atual == 10  # Saldo inalterado
        assert item.estoque_atual >= 0   # Nunca negativo

def test_alerta_estoque_minimo(client, app, acessorio_padrao, colab_padrao):
    """
    Testa o gatilho de alerta de estoque crítico:
    - Estoque inicial: 10, Mínimo: 5
    - Baixa de 6 itens -> Saldo 4 (abaixo do mínimo)
    - `is_estoque_baixo` deve ser True.
    """
    client.post('/acessorios/saida', data={
        'acessorio_id': str(acessorio_padrao.id),
        'quantidade': '6',
        'colaborador_id': str(colab_padrao.id),
        'motivo': 'reposicao'
    })

    with app.app_context():
        item = Acessorio.query.get(acessorio_padrao.id)
        assert item.estoque_atual == 4
        assert item.estoque_minimo == 5
        assert item.is_estoque_baixo is True

def test_saida_acessorio_perda_gera_vale_colaborador(client, app, acessorio_padrao, colab_padrao):
    """Testa saída por perda que gera cobrança em Vale para o colaborador."""
    res = client.post('/acessorios/saida', data={
        'acessorio_id': str(acessorio_padrao.id),
        'quantidade': '2',
        'colaborador_id': str(colab_padrao.id),
        'motivo': 'perda',
        'gerar_vale': 'sim'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        saida = SaidaAcessorio.query.filter_by(motivo='perda').first()
        assert saida is not None
        assert saida.gerou_vale is True
        assert saida.custo_no_momento == 20.0  # 2 * R$ 10,00

        vale = Vale.query.filter_by(saida_acessorio_id=saida.id).first()
        assert vale is not None
        assert vale.colaborador_id == colab_padrao.id
        assert vale.valor == 20.0
        assert vale.status == 'pendente'
