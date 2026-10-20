import pytest
from models import db, Colaborador, Fornecedor, Dispositivo

def test_criar_colaborador_sucesso(client, app):
    """Testa criação de colaborador com dados válidos."""
    res = client.post('/cadastros/colaborador', data={
        'nome': 'Mariana Vendas',
        'setor': 'Comercial',
        'matricula': 'VND05'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        colab = Colaborador.query.filter_by(nome='Mariana Vendas').first()
        assert colab is not None
        assert colab.setor == 'Comercial'
        assert colab.matricula == 'VND05'
        assert colab.ativo is True

def test_criar_colaborador_campos_obrigatorios(client, app):
    """Valida que nome e setor são obrigatórios ao criar colaborador."""
    res = client.post('/cadastros/colaborador', data={
        'nome': '',
        'setor': ''
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Nome e Setor" in res.data or b"obrigat" in res.data
    with app.app_context():
        assert Colaborador.query.count() == 0

def test_criar_fornecedor_sucesso(client, app):
    """Testa cadastro de fornecedor (assistência e loja)."""
    res = client.post('/cadastros/fornecedor', data={
        'nome': 'TechRepair Assistência',
        'tipo': 'assistencia',
        'contato': '11988887777',
        'cnpj': '00.111.222/0001-33',
        'observacoes': 'Atende aos sábados'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        forn = Fornecedor.query.filter_by(nome='TechRepair Assistência').first()
        assert forn is not None
        assert forn.tipo == 'assistencia'
        assert forn.cnpj == '00.111.222/0001-33'

def test_cadastrar_dispositivo_celular_com_imei(client, app, colab_padrao):
    """Testa cadastro de celular com IMEI e vínculo com colaborador."""
    res = client.post('/dispositivos', data={
        'tipo': 'celular',
        'marca': 'Motorola',
        'modelo': 'Moto G54',
        'imei': '865432019876543',
        'serial': '',
        'patrimonio': 'PAT-MOTO-01',
        'data_aquisicao': '2025-05-10',
        'valor_aquisicao': '900.00',
        'colaborador_id': str(colab_padrao.id),
        'status': 'em_uso',
        'observacoes': 'Novo'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        disp = Dispositivo.query.filter_by(imei='865432019876543').first()
        assert disp is not None
        assert disp.modelo == 'Moto G54'
        assert disp.colaborador_id == colab_padrao.id
        assert disp.identificador == 'IMEI: 865432019876543'

def test_cadastrar_dispositivo_imei_duplicado_recusado(client, app, celular_padrao):
    """Garante que o sistema recusa o cadastro de um dispositivo com IMEI repetido."""
    res = client.post('/dispositivos', data={
        'tipo': 'celular',
        'marca': 'Outra Marca',
        'modelo': 'Outro Modelo',
        'imei': celular_padrao.imei,  # Repetindo o mesmo IMEI
        'valor_aquisicao': '800.00'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert (b"duplicado" in res.data.lower() or 
            b"j\xc3\xa1 existe" in res.data.lower() or 
            b"ja existe" in res.data.lower() or
            b"imei" in res.data.lower())
    with app.app_context():
        # Continua existindo apenas 1 dispositivo com esse IMEI
        assert Dispositivo.query.filter_by(imei=celular_padrao.imei).count() == 1

def test_cadastrar_tablet_sem_imei_com_serial(client, app):
    """Valida o caso de uso de tablet sem IMEI (Wi-Fi), que utiliza Serial alternativo."""
    res = client.post('/dispositivos', data={
        'tipo': 'tablet',
        'marca': 'Samsung',
        'modelo': 'Galaxy Tab A9+',
        'imei': '',  # Sem IMEI
        'serial': 'R52N-TAB-WIFI',
        'patrimonio': 'PAT-TAB-02',
        'valor_aquisicao': '1400.00',
        'status': 'em_estoque'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        tablet = Dispositivo.query.filter_by(serial='R52N-TAB-WIFI').first()
        assert tablet is not None
        assert tablet.imei is None
        assert tablet.identificador == 'S/N: R52N-TAB-WIFI'

def test_editar_dispositivo(client, app, celular_padrao, colab_padrao):
    """Testa atualização dos dados de um dispositivo existente."""
    res = client.post(f'/dispositivos/{celular_padrao.id}/editar', data={
        'tipo': 'celular',
        'marca': 'Samsung Atualizada',
        'modelo': 'Galaxy A15 5G',
        'imei': celular_padrao.imei,
        'serial': 'NOVO-SERIAL',
        'patrimonio': 'PAT-001-REV',
        'valor_aquisicao': '1100.00',
        'colaborador_id': str(colab_padrao.id),
        'status': 'em_uso',
        'observacoes': 'Tela trocada em garantia'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        disp = Dispositivo.query.get(celular_padrao.id)
        assert disp.modelo == 'Galaxy A15 5G'
        assert disp.serial == 'NOVO-SERIAL'
        assert disp.valor_aquisicao == 1100.0

def test_alerta_aparelho_bomba_proporcao_reparos(app, celular_padrao, assistencia_padrao):
    """Verifica se o cálculo de percentual de manutenção ativa o alerta crítico (> 50%)."""
    from models import OrdemAssistencia
    with app.app_context():
        disp = Dispositivo.query.get(celular_padrao.id)
        disp.valor_aquisicao = 1000.0
        
        # Cria uma OS finalizada com R$ 600 em reparos (60% do valor de compra)
        os_reparo = OrdemAssistencia(
            dispositivo_id=disp.id,
            fornecedor_id=assistencia_padrao.id,
            defeito="Placa e tela",
            status="devolvido",
            valor_final=600.0,
            responsavel_custo="empresa",
            valor_empresa=600.0
        )
        db.session.add(os_reparo)
        db.session.commit()

        assert disp.custo_total_manutencao == 600.0
        assert disp.percentual_custo_aquisicao == 60.0
        assert disp.is_alerta_bomba is True
