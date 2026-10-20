import pytest
from datetime import date, timedelta
from models import db, OrdemAssistencia, Dispositivo, Vale

def test_abrir_ordem_servico_atualiza_status_dispositivo(client, app, celular_padrao, assistencia_padrao):
    """Ao abrir OS, o status do dispositivo deve mudar obrigatoriamente para 'na_assistencia'."""
    assert celular_padrao.status == 'em_uso'
    
    res = client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'data_envio': date.today().strftime('%Y-%m-%d'),
        'defeito': 'Não liga após molhar',
        'valor_orcado': '250.00'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        disp = Dispositivo.query.get(celular_padrao.id)
        assert disp.status == 'na_assistencia'
        os_aberta = OrdemAssistencia.query.filter_by(dispositivo_id=disp.id).first()
        assert os_aberta is not None
        assert os_aberta.status == 'enviado'
        assert os_aberta.valor_orcado == 250.0
        assert os_aberta.is_aberta is True

def test_concluir_ordem_mau_uso_gera_vale_colaborador(client, app, celular_padrao, assistencia_padrao, colab_padrao):
    """
    Fechamento de OS com causa 'mau_uso':
    - Deve gerar um registro de Vale para o colaborador
    - O valor do vale deve ser igual a valor_colaborador
    - O status do dispositivo deve voltar para 'em_uso'
    - valor_empresa + valor_colaborador deve somar o valor_final
    """
    # 1. Abre a OS
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Tela quebrada por queda',
        'valor_orcado': '300.00'
    })

    with app.app_context():
        os_obj = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first()
        os_id = os_obj.id

    # 2. Conclui com Mau Uso e 100% de custo ao colaborador
    res = client.post(f'/ordens/{os_id}/concluir', data={
        'status_final': 'devolvido',
        'data_retorno': date.today().strftime('%Y-%m-%d'),
        'valor_final': '350.00',
        'causa': 'mau_uso',
        'laudo': 'Troca de display danificado por impacto',
        'responsavel_custo': 'colaborador',
        'valor_colaborador': '350.00',
        'garantia_dias': '90'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        os_fechada = OrdemAssistencia.query.get(os_id)
        assert os_fechada.status == 'devolvido'
        assert os_fechada.valor_final == 350.0
        assert os_fechada.valor_colaborador == 350.0
        assert os_fechada.valor_empresa == 0.0
        assert (os_fechada.valor_empresa + os_fechada.valor_colaborador) == os_fechada.valor_final

        # Aparelho voltou a ficar em uso
        disp = Dispositivo.query.get(celular_padrao.id)
        assert disp.status == 'em_uso'

        # Vale foi gerado automaticamente!
        vale = Vale.query.filter_by(ordem_id=os_id).first()
        assert vale is not None
        assert vale.colaborador_id == colab_padrao.id
        assert vale.valor == 350.0
        assert vale.status == 'pendente'

def test_concluir_ordem_desgaste_custo_empresa(client, app, celular_padrao, assistencia_padrao):
    """Fechamento por desgaste natural não gera vale e fica 100% com a empresa."""
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Bateria estufada'
    })

    with app.app_context():
        os_obj = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first()
        os_id = os_obj.id

    client.post(f'/ordens/{os_id}/concluir', data={
        'status_final': 'devolvido',
        'valor_final': '180.00',
        'causa': 'desgaste_natural',
        'responsavel_custo': 'empresa',
        'garantia_dias': '90'
    })

    with app.app_context():
        os_fechada = OrdemAssistencia.query.get(os_id)
        assert os_fechada.valor_empresa == 180.0
        assert os_fechada.valor_colaborador == 0.0
        # Nenhum vale gerado
        assert Vale.query.filter_by(ordem_id=os_id).first() is None

def test_divisao_mista_de_custos_os(client, app, celular_padrao, assistencia_padrao, colab_padrao):
    """Testa divisão parcial de custo: R$ 300 empresa, R$ 200 colaborador em conserto de R$ 500."""
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Troca de tampa traseira e bateria'
    })

    with app.app_context():
        os_id = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first().id

    client.post(f'/ordens/{os_id}/concluir', data={
        'status_final': 'devolvido',
        'valor_final': '500.00',
        'causa': 'misto',
        'responsavel_custo': 'misto',
        'valor_colaborador': '200.00',
        'garantia_dias': '90'
    })

    with app.app_context():
        os_fechada = OrdemAssistencia.query.get(os_id)
        assert os_fechada.valor_final == 500.0
        assert os_fechada.valor_colaborador == 200.0
        assert os_fechada.valor_empresa == 300.0
        assert (os_fechada.valor_empresa + os_fechada.valor_colaborador) == os_fechada.valor_final

        vale = Vale.query.filter_by(ordem_id=os_id).first()
        assert vale is not None
        assert vale.valor == 200.0

def test_concluir_ordem_sem_conserto_baixa_aparelho(client, app, celular_padrao, assistencia_padrao):
    """Se a OS for finalizada como 'sem_conserto', o status do dispositivo passa para 'baixado'."""
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Placa mãe queimada'
    })

    with app.app_context():
        os_id = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).first().id

    client.post(f'/ordens/{os_id}/concluir', data={
        'status_final': 'sem_conserto',
        'valor_final': '0.00',
        'causa': 'defeito_fabricacao',
        'responsavel_custo': 'empresa'
    })

    with app.app_context():
        disp = Dispositivo.query.get(celular_padrao.id)
        assert disp.status == 'baixado'

def test_transicao_status_do_vale(client, app, colab_padrao):
    """Testa ciclo de vida do vale: pendente -> emitido -> descontado -> cancelado."""
    with app.app_context():
        vale = Vale(
            colaborador_id=colab_padrao.id,
            valor=150.0,
            status='pendente',
            motivo='Teste Vale'
        )
        db.session.add(vale)
        db.session.commit()
        vale_id = vale.id

    # Muda para emitido
    client.post(f'/vales/{vale_id}/status', data={'status': 'emitido'})
    with app.app_context():
        assert Vale.query.get(vale_id).status == 'emitido'

    # Muda para descontado
    client.post(f'/vales/{vale_id}/status', data={'status': 'descontado'})
    with app.app_context():
        assert Vale.query.get(vale_id).status == 'descontado'

def test_tentativa_abrir_segunda_os_para_aparelho_ja_na_assistencia(client, app, celular_padrao, assistencia_padrao):
    """
    REGRA DE NEGÓCIO CRÍTICA:
    Um aparelho que já está na assistência técnica (com status 'na_assistencia')
    NÃO deveria permitir a abertura de uma segunda OS em paralelo.
    """
    # 1. Abre a primeira OS
    client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Primeiro defeito'
    })

    # 2. Tenta abrir a segunda OS para o MESMO aparelho sem concluir a primeira
    res = client.post('/ordens', data={
        'dispositivo_id': str(celular_padrao.id),
        'fornecedor_id': str(assistencia_padrao.id),
        'defeito': 'Segundo defeito concomitante'
    }, follow_redirects=True)

    with app.app_context():
        total_os = OrdemAssistencia.query.filter_by(dispositivo_id=celular_padrao.id).count()
        # Se total_os for 2, significa que o sistema permitiu OS duplicada simultânea!
        assert total_os == 1, "VULNERABILIDADE / BUG: Sistema permitiu abrir duas OS concorrentes para o mesmo aparelho!"
