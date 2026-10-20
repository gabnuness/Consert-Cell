import pytest
from sqlalchemy.exc import IntegrityError
from models import db, Colaborador, Dispositivo, OrdemAssistencia, Acessorio, SaidaAcessorio

def test_exclusao_colaborador_com_dispositivo_vinculado(app, colab_padrao, celular_padrao):
    """
    Verifica a política de integridade ao tentar excluir um colaborador
    que possui dispositivos ou histórico associado.
    """
    with app.app_context():
        colab = Colaborador.query.get(colab_padrao.id)
        # O colaborador possui 1 dispositivo vinculado
        assert len(colab.dispositivos) == 1

        # Testar se a exclusão desassocia ou se é impedida
        db.session.delete(colab)
        try:
            db.session.commit()
            # Se permitir a exclusão, o dispositivo não pode sumir silenciosamente!
            disp = Dispositivo.query.get(celular_padrao.id)
            assert disp is not None
        except IntegrityError:
            # Se houver trava de integridade referencial, o rollback garante a consistência
            db.session.rollback()

def test_exclusao_acessorio_com_historico_de_saidas(app, acessorio_padrao, colab_padrao):
    """
    Verifica se a exclusão de um acessório que já teve movimentações registradas
    não corrompe o histórico contábil de saídas.
    """
    with app.app_context():
        saida = SaidaAcessorio(
            acessorio_id=acessorio_padrao.id,
            quantidade=2,
            colaborador_id=colab_padrao.id,
            motivo='novo',
            custo_no_momento=20.0
        )
        db.session.add(saida)
        db.session.commit()
        saida_id = saida.id

        # Tenta excluir o acessório pai
        acess = Acessorio.query.get(acessorio_padrao.id)
        db.session.delete(acess)
        try:
            db.session.commit()
            # Se apagou o pai, verifica o filho
            saida_existente = SaidaAcessorio.query.get(saida_id)
            assert saida_existente is not None
        except IntegrityError:
            db.session.rollback()
