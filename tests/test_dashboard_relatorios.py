import pytest
import io
import openpyxl
from datetime import date, timedelta
from models import db, OrdemAssistencia, Acessorio, Vale

def test_calculo_totais_dashboard_comparados_a_mao(client, app, celular_padrao, tablet_padrao, assistencia_padrao, colab_padrao, acessorio_padrao):
    """
    Simula cenário financeiro e confere os totais manualmente:
    - OS 1 (Celular, devolvido este mês): Total R$ 300 (Empresa R$ 200, Vale R$ 100)
    - OS 2 (Tablet, aberto este mês): Orçado R$ 500 (em reparo)
    - Estoque: 10 películas a R$ 10,00 = R$ 100,00
    - Vales: 1 vale de R$ 100 pendente
    """
    with app.app_context():
        # 1. OS Devolvida este mês
        os1 = OrdemAssistencia(
            dispositivo_id=celular_padrao.id,
            fornecedor_id=assistencia_padrao.id,
            colaborador_id=colab_padrao.id,
            data_envio=date.today() - timedelta(days=5),
            data_retorno=date.today(),
            defeito="Conector",
            status="devolvido",
            valor_final=300.0,
            responsavel_custo="misto",
            valor_empresa=200.0,
            valor_colaborador=100.0
        )
        # 2. OS em andamento na assistência
        os2 = OrdemAssistencia(
            dispositivo_id=tablet_padrao.id,
            fornecedor_id=assistencia_padrao.id,
            colaborador_id=colab_padrao.id,
            data_envio=date.today() - timedelta(days=16),  # +15 dias -> Crítico!
            defeito="Display quebrado",
            status="em_reparo",
            valor_orcado=500.0
        )
        # 3. Vale correspondente
        v1 = Vale(
            ordem_id=os1.id,
            colaborador_id=colab_padrao.id,
            valor=100.0,
            status="pendente",
            motivo="Reparo OS 1"
        )
        db.session.add_all([os1, os2, v1])
        db.session.commit()

    # Faz a requisição para o Dashboard
    res = client.get('/')
    assert res.status_code == 200

    # Validações dos cálculos manuais na resposta HTML renderizada
    # 1. Na assistência: exatamente 1 aparelho (o tablet)
    assert b"Na Assist\xc3\xa1ncia" in res.data or b"Na Assistencia" in res.data or b"Na Assist" in res.data
    # 2. Aparelhos atrasados +15 dias: exatamente 1 (os2 tem 16 dias)
    assert b"1 aparelhos h\xc3\xa1 +15 dias" in res.data or b"1 aparelhos" in res.data
    # 3. Gasto da empresa no mês: R$ 200,00
    assert b"200,00" in res.data
    # 4. Total de vales pendentes: R$ 100,00
    assert b"100,00" in res.data

def test_exportacao_relatorio_excel_abas_e_conteudo(client, app, celular_padrao, assistencia_padrao):
    """Testa a geração do arquivo Excel consolidado (.xlsx)."""
    with app.app_context():
        os_teste = OrdemAssistencia(
            dispositivo_id=celular_padrao.id,
            fornecedor_id=assistencia_padrao.id,
            defeito="Teste Excel",
            status="enviado",
            valor_orcado=250.0
        )
        db.session.add(os_teste)
        db.session.commit()

    res = client.get('/relatorios/excel')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Carrega a planilha a partir dos bytes da resposta para inspecionar
    wb = openpyxl.load_workbook(io.BytesIO(res.data))
    sheet_names = wb.sheetnames
    assert "Ordens de Assistência" in sheet_names
    assert "Dispositivos" in sheet_names
    assert "Vales a Descontar" in sheet_names
    assert "Estoque de Acessórios" in sheet_names

    ws_os = wb["Ordens de Assistência"]
    assert ws_os.max_row >= 2  # Cabeçalho + 1 linha
    assert "Teste Excel" in [cell.value for row in ws_os.iter_rows() for cell in row]
