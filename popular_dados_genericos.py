"""
Script para popular base de dados genérica e anônima para testes de pentest,
demonstrações, homologação e trabalhos acadêmicos de segurança da informação.
Nenhum dado real de pessoas, CPFs ou empresas reais é utilizado.
"""

import os
import sys
from datetime import date, timedelta

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app, db, bcrypt
from models import (
    AdminUser, Colaborador, Fornecedor, Dispositivo,
    OrdemAssistencia, Vale, Acessorio, EntradaAcessorio, SaidaAcessorio
)

def gerar_base_generica():
    with app.app_context():
        print("-> Limpando base atual...")
        SaidaAcessorio.query.delete()
        EntradaAcessorio.query.delete()
        Vale.query.delete()
        OrdemAssistencia.query.delete()
        Dispositivo.query.delete()
        Acessorio.query.delete()
        Colaborador.query.delete()
        Fornecedor.query.delete()

        # ========================================================
        # 1. ADMIN USER PARA PENTEST
        # ========================================================
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@pentest.local').strip().lower()
        admin_senha = os.environ.get('ADMIN_SENHA', 'admin123')
        admin_nome = os.environ.get('ADMIN_NOME', 'Administrador Pentest (TI)')

        admin = AdminUser.query.first()
        token_pentest = "a1b2c3d4e5f6789012345678"
        if not admin:
            admin = AdminUser(
                email=admin_email,
                nome=admin_nome,
                senha_hash=bcrypt.generate_password_hash(admin_senha).decode('utf-8'),
                token_api=token_pentest,
                ativo=True
            )
            db.session.add(admin)
        else:
            admin.email = admin_email
            admin.nome = admin_nome
            admin.senha_hash = bcrypt.generate_password_hash(admin_senha).decode('utf-8')
            admin.token_api = token_pentest
            admin.ativo = True

        db.session.commit()
        print(f"[OK] Usuário Admin configurado: {admin.email} (senha: {admin_senha})")

        # ========================================================
        # 2. FORNECEDORES & ASSISTÊNCIAS TÉCNICAS
        # ========================================================
        f1 = Fornecedor(
            nome="TechFix Laboratório de Reparos",
            tipo="assistencia",
            contato="(11) 98765-4321 • suporte@techfix.local",
            cnpj="12.345.678/0001-90",
            observacoes="Assistência técnica especializada em smartphones e coletores industriais."
        )
        f2 = Fornecedor(
            nome="MegaCell Soluções Móveis",
            tipo="assistencia",
            contato="(11) 91234-5678 • contato@megacell.local",
            cnpj="98.765.432/0001-10",
            observacoes="Laboratório de solda BGA e troca de telas autorizada. Prazo médio: 2 a 4 dias úteis."
        )
        f3 = Fornecedor(
            nome="Global Supply Peças & Acessórios",
            tipo="loja",
            contato="(11) 3322-1100 • vendas@globalsupply.local",
            cnpj="55.444.333/0001-22",
            observacoes="Distribuidora de cabos, carregadores certificados, capas e películas."
        )
        db.session.add_all([f1, f2, f3])
        db.session.flush()

        # ========================================================
        # 3. COLABORADORES FICTÍCIOS
        # ========================================================
        colabs = [
            Colaborador(nome="CARLOS EDUARDO SILVA", setor="TI", matricula="TEC-101"),
            Colaborador(nome="MARIANA BEATRIZ COSTA", setor="Comercial", matricula="COM-201"),
            Colaborador(nome="LUCAS MENDES OLIVEIRA", setor="Logística", matricula="LOG-301"),
            Colaborador(nome="FERNANDA SANTOS ROCHA", setor="Comercial", matricula="COM-202"),
            Colaborador(nome="RODRIGO ALVES PEREIRA", setor="Operações", matricula="OPE-401"),
            Colaborador(nome="JULIANA SOUZA LIMA", setor="Recursos Humanos", matricula="RH-501"),
            Colaborador(nome="BRUNO HENRIQUE CASTRO", setor="Comercial", matricula="COM-203"),
            Colaborador(nome="CAMILA VASCONCELOS DIAS", setor="Financeiro", matricula="FIN-601"),
            Colaborador(nome="FELIPE AUGUSTO NOGUEIRA", setor="Logística", matricula="LOG-302"),
            Colaborador(nome="BEATRIZ MARTINS VIEIRA", setor="Comercial", matricula="COM-204"),
            Colaborador(nome="GABRIEL NUNES (TESTER)", setor="TI", matricula="TEC-102"),
            Colaborador(nome="THIAGO BARBOSA CARDOSO", setor="Operações", matricula="OPE-402"),
            Colaborador(nome="VANESSA APARECIDA LIMA", setor="Comercial", matricula="COM-205"),
            Colaborador(nome="RAFAEL HENRIQUE ALMEIDA", setor="Logística", matricula="LOG-303"),
            Colaborador(nome="PATRICIA HELENA DUARTE", setor="Comercial", matricula="COM-206"),
        ]
        db.session.add_all(colabs)
        db.session.flush()

        # Mapas rápidos para vincular IDs
        c_carlos = colabs[0]
        c_mariana = colabs[1]
        c_lucas = colabs[2]
        c_fernanda = colabs[3]
        c_rodrigo = colabs[4]
        c_thiago = colabs[11]
        c_gabriel = colabs[10]

        # ========================================================
        # 4. DISPOSITIVOS FICTÍCIOS
        # ========================================================
        hoje = date.today()
        dispositivos = [
            Dispositivo(
                tipo="celular", marca="Samsung", modelo="Galaxy A55 5G",
                imei="354892019827361", patrimonio="PAT-NEX-0101",
                data_aquisicao=hoje - timedelta(days=220), valor_aquisicao=1450.0,
                colaborador_id=c_carlos.id, status="em_uso"
            ),
            Dispositivo(
                tipo="celular", marca="Samsung", modelo="Galaxy A35 5G",
                imei="359871028374652", patrimonio="PAT-NEX-0102",
                data_aquisicao=hoje - timedelta(days=180), valor_aquisicao=1250.0,
                colaborador_id=c_mariana.id, status="em_uso"
            ),
            Dispositivo(
                tipo="celular", marca="Motorola", modelo="Edge 50 Fusion",
                imei="351284920182736", patrimonio="PAT-NEX-0103",
                data_aquisicao=hoje - timedelta(days=120), valor_aquisicao=1690.0,
                colaborador_id=c_lucas.id, status="em_uso"
            ),
            Dispositivo(
                tipo="celular", marca="Samsung", modelo="Galaxy A15",
                imei="356291048273615", patrimonio="PAT-NEX-0104",
                data_aquisicao=hoje - timedelta(days=90), valor_aquisicao=890.0,
                colaborador_id=c_fernanda.id, status="em_manutencao"
            ),
            Dispositivo(
                tipo="tablet", marca="Samsung", modelo="Galaxy Tab S9 FE",
                serial="SN-TAB-NEX-0201", patrimonio="PAT-TAB-0201",
                data_aquisicao=hoje - timedelta(days=150), valor_aquisicao=2300.0,
                colaborador_id=c_rodrigo.id, status="em_uso"
            ),
            Dispositivo(
                tipo="outro", marca="Zebra", modelo="TC26 Coletor Industrial",
                serial="SN-ZEB-NEX-0301", patrimonio="PAT-ZEB-0301",
                data_aquisicao=hoje - timedelta(days=300), valor_aquisicao=3800.0,
                colaborador_id=c_thiago.id, status="em_uso"
            ),
            Dispositivo(
                tipo="outro", marca="Zebra", modelo="TC21 Coletor Industrial",
                serial="SN-ZEB-NEX-0302", patrimonio="PAT-ZEB-0302",
                data_aquisicao=hoje - timedelta(days=320), valor_aquisicao=3500.0,
                colaborador_id=None, status="em_manutencao"
            ),
            Dispositivo(
                tipo="celular", marca="Samsung", modelo="Galaxy S23 FE",
                imei="357892019482716", patrimonio="PAT-NEX-0105",
                data_aquisicao=hoje - timedelta(days=60), valor_aquisicao=2600.0,
                colaborador_id=c_gabriel.id, status="em_uso"
            ),
            Dispositivo(
                tipo="celular", marca="Motorola", modelo="Moto G84",
                imei="359281740291823", patrimonio="PAT-NEX-0106",
                data_aquisicao=hoje - timedelta(days=45), valor_aquisicao=1100.0,
                colaborador_id=None, status="estoque"
            ),
            Dispositivo(
                tipo="tablet", marca="Lenovo", modelo="Tab M11",
                serial="SN-TAB-NEX-0202", patrimonio="PAT-TAB-0202",
                data_aquisicao=hoje - timedelta(days=30), valor_aquisicao=1200.0,
                colaborador_id=None, status="estoque"
            ),
            Dispositivo(
                tipo="celular", marca="Apple", modelo="iPhone 13",
                imei="352819048291029", patrimonio="PAT-NEX-0107",
                data_aquisicao=hoje - timedelta(days=400), valor_aquisicao=4200.0,
                colaborador_id=None, status="baixado"
            )
        ]
        db.session.add_all(dispositivos)
        db.session.flush()

        d_a55 = dispositivos[0]
        d_a15 = dispositivos[3]
        d_zeb_tc21 = dispositivos[6]
        d_iphone13 = dispositivos[10]

        # ========================================================
        # 5. ORDENS DE SERVIÇO (OS)
        # ========================================================
        # OS 1: Samsung A15 na assistência (Mau uso / Tela trincada)
        os1 = OrdemAssistencia(
            dispositivo_id=d_a15.id,
            fornecedor_id=f1.id,
            colaborador_id=c_fernanda.id,
            data_envio=hoje - timedelta(days=4),
            defeito="Tela frontal trincada após queda acidental no cliente. Touch inoperante.",
            status="em_reparo",
            valor_orcado=380.0,
            valor_final=0.0,
            is_particular=False,
            causa="mau_uso",
            responsavel_custo="colaborador",
            valor_empresa=0.0,
            valor_colaborador=380.0,
            observacoes="Colaboradora assinou ciência do vale em folha. Orçamento aprovado."
        )

        # OS 2: Zebra TC21 Devolvido/Concluído com Garantia ativa (Desgaste)
        os2 = OrdemAssistencia(
            dispositivo_id=d_zeb_tc21.id,
            fornecedor_id=f1.id,
            colaborador_id=c_thiago.id,
            data_envio=hoje - timedelta(days=28),
            data_retorno=hoje - timedelta(days=12),
            defeito="Gatilho de leitura travando e falha intermitente no leitor 2D.",
            status="devolvido",
            valor_orcado=220.0,
            valor_final=220.0,
            is_particular=False,
            causa="desgaste_natural",
            responsavel_custo="empresa",
            valor_empresa=220.0,
            valor_colaborador=0.0,
            garantia_ate=hoje + timedelta(days=78),
            laudo="Troca do trigger switch e calibração do sensor laser. Garantia de 90 dias.",
            observacoes="Equipamento testado e liberado para operação."
        )

        # OS 3: Samsung A55 Concluído com Divisão de Custos
        os3 = OrdemAssistencia(
            dispositivo_id=d_a55.id,
            fornecedor_id=f2.id,
            colaborador_id=c_carlos.id,
            data_envio=hoje - timedelta(days=44),
            data_retorno=hoje - timedelta(days=35),
            defeito="Tampa traseira quebrou e conector de carga Tipo-C com folga.",
            status="devolvido",
            valor_orcado=300.0,
            valor_final=300.0,
            is_particular=False,
            causa="outro",
            responsavel_custo="misto",
            valor_empresa=150.0,
            valor_colaborador=150.0,
            garantia_ate=hoje + timedelta(days=45),
            laudo="Substituição da subplaca de carga e painel traseiro original.",
            observacoes="Acordo operacional: empresa arcou com conector e colaborador com tampa traseira."
        )

        # OS 4: iPhone 13 Baixado (Perda Total / Sem conserto)
        os4 = OrdemAssistencia(
            dispositivo_id=d_iphone13.id,
            fornecedor_id=f2.id,
            colaborador_id=None,
            data_envio=hoje - timedelta(days=88),
            data_retorno=hoje - timedelta(days=80),
            defeito="Aparelho caiu em líquido e não liga mais. Superaquecimento na linha primária.",
            status="sem_conserto",
            valor_orcado=0.0,
            valor_final=0.0,
            is_particular=False,
            causa="acidente_queda",
            responsavel_custo="empresa",
            laudo="Curto severo no SoC e oxidação profunda nas camadas da placa lógica. Sem conserto viável.",
            observacoes="Sem viabilidade técnica. Equipamento baixado do inventário."
        )

        # OS 5: APARELHO PARTICULAR - iPhone 12 da Mariana (Concluído com Desconto em Folha)
        os5 = OrdemAssistencia(
            dispositivo_id=None,
            fornecedor_id=f2.id,
            colaborador_id=c_mariana.id,
            data_envio=hoje - timedelta(days=19),
            data_retorno=hoje - timedelta(days=10),
            defeito="Troca de módulo frontal completo. Aparelho pessoal trazido pela colaboradora.",
            status="devolvido",
            valor_orcado=450.0,
            valor_final=450.0,
            is_particular=True,
            aparelho_particular="iPhone 12 Particular (Mariana Costa)",
            causa="mau_uso",
            responsavel_custo="colaborador",
            valor_empresa=0.0,
            valor_colaborador=450.0,
            garantia_ate=hoje + timedelta(days=80),
            laudo="Substituição de display OLED e restauração de True Tone. Garantia de 90 dias.",
            observacoes="Aparelho particular consertado via convênio corporativo com desconto integral em folha."
        )

        # OS 6: APARELHO PARTICULAR - Xiaomi Redmi do Lucas (Em Reparo)
        os6 = OrdemAssistencia(
            dispositivo_id=None,
            fornecedor_id=f1.id,
            colaborador_id=c_lucas.id,
            data_envio=hoje - timedelta(days=2),
            defeito="Não carrega nem reconhece no PC. Aparelho pessoal com defeito no conector.",
            status="em_reparo",
            valor_orcado=180.0,
            valor_final=0.0,
            is_particular=True,
            aparelho_particular="Xiaomi Redmi Note 12 Particular (Lucas Mendes)",
            causa="mau_uso",
            responsavel_custo="colaborador",
            valor_empresa=0.0,
            valor_colaborador=180.0,
            observacoes="Aparelho particular em reparo. Desconto aprovado para a próxima folha."
        )

        db.session.add_all([os1, os2, os3, os4, os5, os6])
        db.session.flush()

        # ========================================================
        # 6. VALES DE COLABORADOR (DESCONTO EM FOLHA)
        # ========================================================
        v1 = Vale(
            ordem_id=os1.id,
            colaborador_id=c_fernanda.id,
            valor=380.0,
            data_emissao=hoje - timedelta(days=4),
            status="pendente",
            motivo=f"Reparo OS #{os1.id} (Mau Uso / Tela A15)",
            observacoes="Aguardando fechamento da folha de pagamento."
        )

        v2 = Vale(
            ordem_id=os3.id,
            colaborador_id=c_carlos.id,
            valor=150.0,
            data_emissao=hoje - timedelta(days=44),
            status="descontado",
            motivo=f"Reparo OS #{os3.id} (Divisão 50% Tampa Traseira)",
            observacoes="Descontado na folha de pagamento do mês anterior."
        )

        v3 = Vale(
            ordem_id=os5.id,
            colaborador_id=c_mariana.id,
            valor=450.0,
            data_emissao=hoje - timedelta(days=19),
            status="pendente",
            motivo=f"Reparo OS #{os5.id} - Aparelho Particular (iPhone 12)",
            observacoes="Convênio de desconto parcelado em 2x na folha."
        )

        v4 = Vale(
            ordem_id=None,
            colaborador_id=c_rodrigo.id,
            valor=65.0,
            data_emissao=hoje - timedelta(days=15),
            status="descontado",
            motivo="Reposição de Carregador Rápido (Perda em campo)",
            observacoes="Descontado na folha ref. mês passado."
        )

        db.session.add_all([v1, v2, v3, v4])
        db.session.flush()

        # ========================================================
        # 7. ACESSÓRIOS & ESTOQUE
        # ========================================================
        a1 = Acessorio(
            nome="Película Vidro 3D Galaxy A55 5G",
            categoria="Pelicula", compatibilidade="Samsung Galaxy A55",
            estoque_atual=16, estoque_minimo=5, custo_medio=9.50
        )
        a2 = Acessorio(
            nome="Capa Anti-Impacto Reforçada Galaxy A55",
            categoria="Capa", compatibilidade="Samsung Galaxy A55",
            estoque_atual=8, estoque_minimo=4, custo_medio=18.00
        )
        a3 = Acessorio(
            nome="Cabo USB-C Reforçado em Nylon 1.5m",
            categoria="Cabo", compatibilidade="Universal USB Tipo-C",
            estoque_atual=24, estoque_minimo=8, custo_medio=14.00
        )
        a4 = Acessorio(
            nome="Carregador Turbo de Parede 25W",
            categoria="Carregador", compatibilidade="Universal USB Tipo-C",
            estoque_atual=2, estoque_minimo=6, custo_medio=32.00 # Alerta de estoque baixo!
        )
        a5 = Acessorio(
            nome="Capa Emborrachada Zebra TC26 com Alça",
            categoria="Capa", compatibilidade="Zebra TC21 / TC26",
            estoque_atual=4, estoque_minimo=3, custo_medio=55.00
        )
        a6 = Acessorio(
            nome="Carregador Veicular Rápido 30W",
            categoria="Carregador", compatibilidade="Veículos 12V/24V",
            estoque_atual=7, estoque_minimo=5, custo_medio=38.00
        )

        db.session.add_all([a1, a2, a3, a4, a5, a6])
        db.session.flush()

        # ========================================================
        # 8. ENTRADAS & SAÍDAS DE ESTOQUE
        # ========================================================
        e1 = EntradaAcessorio(
            acessorio_id=a1.id, quantidade=20, custo_unitario=9.50,
            fornecedor_id=f3.id, nota_fiscal="NF-77881", data=hoje - timedelta(days=40)
        )
        e2 = EntradaAcessorio(
            acessorio_id=a3.id, quantidade=30, custo_unitario=14.00,
            fornecedor_id=f3.id, nota_fiscal="NF-77895", data=hoje - timedelta(days=30)
        )
        e3 = EntradaAcessorio(
            acessorio_id=a4.id, quantidade=5, custo_unitario=32.00,
            fornecedor_id=f3.id, nota_fiscal="NF-78012", data=hoje - timedelta(days=20)
        )
        db.session.add_all([e1, e2, e3])

        s1 = SaidaAcessorio(
            acessorio_id=a1.id, quantidade=1, colaborador_id=c_carlos.id,
            dispositivo_id=d_a55.id, motivo="novo", data=hoje - timedelta(days=25),
            custo_no_momento=9.50, gerou_vale=False
        )
        s2 = SaidaAcessorio(
            acessorio_id=a3.id, quantidade=1, colaborador_id=c_mariana.id,
            dispositivo_id=None, motivo="novo", data=hoje - timedelta(days=18),
            custo_no_momento=14.00, gerou_vale=False
        )
        s3 = SaidaAcessorio(
            acessorio_id=a4.id, quantidade=1, colaborador_id=c_rodrigo.id,
            dispositivo_id=None, motivo="perda", data=hoje - timedelta(days=15),
            custo_no_momento=32.00, gerou_vale=True
        )
        db.session.add_all([s1, s2, s3])

        db.session.commit()

        print("\n" + "=" * 60)
        print("  BASE DE DADOS GENÉRICA DE PENTEST CARREGADA COM SUCESSO!")
        print("=" * 60)
        print(f" • Colaboradores Fictícios   : {Colaborador.query.count()} (Comercial, TI, Logística, etc.)")
        print(f" • Fornecedores Homologados : {Fornecedor.query.count()} (TechFix, MegaCell, Global Supply)")
        print(f" • Dispositivos             : {Dispositivo.query.count()} (Smartphones, Coletores Zebra, Tablets)")
        print(f" • Ordens de Serviço        : {OrdemAssistencia.query.count()} (Empresa & Aparelhos Particulares)")
        print(f" • Vales em Folha (RH)      : {Vale.query.count()} (Pendentes e Descontados)")
        print(f" • Acessórios em Estoque    : {Acessorio.query.count()} (com alerta de reposição ativo)")
        print(f" • Usuário Admin Pentest    : {admin.email} (senha: {admin_senha})")
        print(f" • Token API Bearer Pentest : {token_pentest}")
        print("=" * 60 + "\n")

if __name__ == '__main__':
    gerar_base_generica()
