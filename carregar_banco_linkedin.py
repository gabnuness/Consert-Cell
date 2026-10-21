"""
Script para carregar modelo de dados genérico e profissional
perfeito para prints, apresentações e postagens no LinkedIn.
"""
import os
import secrets
from datetime import date, timedelta
from app import app, db, bcrypt
from models import (
    AdminUser, Colaborador, Fornecedor, Dispositivo,
    OrdemAssistencia, Vale, Acessorio, EntradaAcessorio, SaidaAcessorio
)

def popular_dados_linkedin():
    with app.app_context():
        print("Limpando dados anteriores...")
        SaidaAcessorio.query.delete()
        EntradaAcessorio.query.delete()
        Vale.query.delete()
        OrdemAssistencia.query.delete()
        Dispositivo.query.delete()
        Acessorio.query.delete()
        Colaborador.query.delete()
        Fornecedor.query.delete()

        # Garante o Admin do Gabriel
        admin = AdminUser.query.first()
        if not admin:
            admin = AdminUser(
                email="admin@disfonte.com.br",
                nome="Gabriel Nunes (Admin TI)",
                senha_hash=bcrypt.generate_password_hash("admin123").decode("utf-8"),
                token_api=secrets.token_hex(24),
                ativo=True
            )
            db.session.add(admin)
        else:
            admin.nome = "Gabriel Nunes (Admin TI)"
            admin.email = "admin@disfonte.com.br"
            admin.senha_hash = bcrypt.generate_password_hash("admin123").decode("utf-8")
        
        db.session.commit()
        print("Admin preservado.")

        # ========================================================
        # 1. FORNECEDORES & ASSISTÊNCIAS TÉCNICAS HOMOLOGADAS
        # ========================================================
        f1 = Fornecedor(
            nome="TechFix Soluções Corporativas",
            tipo="assistencia",
            contato="(11) 98765-4321 • comercial@techfix.com.br",
            cnpj="14.285.912/0001-44",
            observacoes="Assistência técnica autorizada e especializada em coletores industriais e tablets."
        )
        f2 = Fornecedor(
            nome="MegaCell Centro Técnico",
            tipo="assistencia",
            contato="(11) 91234-5678 • suporte@megacell.com.br",
            cnpj="28.491.034/0001-89",
            observacoes="Laboratório avançado com certificação Samsung e Motorola. Prazo médio: 3 dias úteis."
        )
        f3 = Fornecedor(
            nome="Alfa Supply Acessórios & Peças",
            tipo="loja",
            contato="(11) 3322-1100 • vendas@alfasupply.com.br",
            cnpj="45.678.910/0001-22",
            observacoes="Distribuidora atacadista de capas de proteção militar, películas e fontes turbo."
        )
        db.session.add_all([f1, f2, f3])
        db.session.flush()

        # ========================================================
        # 2. COLABORADORES (SETORES OPERACIONAIS AMBEV DISFONTE)
        # ========================================================
        c_gabriel = Colaborador(nome="Gabriel Nunes", setor="TI & Infraestrutura", matricula="TI-0101")
        c_rodrigo = Colaborador(nome="Rodrigo Vasconcelos", setor="Logística & Armazém", matricula="LOG-0204")
        c_mariana = Colaborador(nome="Mariana Albuquerque", setor="Vendas Externas (Rotas)", matricula="VND-0312")
        c_lucas = Colaborador(nome="Lucas Mendonça", setor="Frota & Distribuição", matricula="FRT-0118")
        c_camila = Colaborador(nome="Camila Fernandes", setor="Trade Marketing", matricula="MKT-0405")
        c_felipe = Colaborador(nome="Felipe Andrade", setor="Supervisão Comercial", matricula="VND-0102")
        c_amanda = Colaborador(nome="Amanda Nogueira", setor="Recursos Humanos", matricula="RH-0201")
        c_thiago = Colaborador(nome="Thiago Martins", setor="Expedição & WMS", matricula="LOG-0322")

        db.session.add_all([
            c_gabriel, c_rodrigo, c_mariana, c_lucas,
            c_camila, c_felipe, c_amanda, c_thiago
        ])
        db.session.flush()

        # ========================================================
        # 3. DISPOSITIVOS (SMARTPHONES, TABLETS & COLETORES ZEBRA)
        # ========================================================
        hoje = date.today()

        d1 = Dispositivo(
            tipo="celular", marca="Samsung", modelo="Galaxy A55 5G",
            imei="354892019827361", patrimonio="PAT-AMB-0412",
            data_aquisicao=hoje - timedelta(days=280), valor_aquisicao=1450.0,
            colaborador_id=c_mariana.id, status="em_uso",
            observacoes="Aparelho padrão do time de vendas externas. Inclui capa anti-impacto corporativa."
        )

        d2 = Dispositivo(
            tipo="celular", marca="Motorola", modelo="Edge 50 Fusion",
            imei="867512049182903", patrimonio="PAT-AMB-0418",
            data_aquisicao=hoje - timedelta(days=190), valor_aquisicao=1890.0,
            colaborador_id=c_felipe.id, status="em_uso",
            observacoes="Utilizado para supervisão comercial e conferência de PDVs em tempo real."
        )

        d3 = Dispositivo(
            tipo="tablet", marca="Zebra", modelo="Coletor TC26 Industrial",
            serial="ZBR-24A99812", patrimonio="COL-WMS-018",
            data_aquisicao=hoje - timedelta(days=420), valor_aquisicao=3200.0,
            colaborador_id=c_rodrigo.id, status="na_assistencia",
            observacoes="Coletor industrial de armazém com leitor de código de barras 2D e NFC."
        )

        d4 = Dispositivo(
            tipo="tablet", marca="Samsung", modelo="Galaxy Tab Active 4 Pro",
            serial="R52N80918AB", patrimonio="TAB-FROTA-03",
            data_aquisicao=hoje - timedelta(days=310), valor_aquisicao=2650.0,
            colaborador_id=c_lucas.id, status="em_uso",
            observacoes="Tablet reforçado com suporte veicular acoplado ao caminhão de distribuição."
        )

        d5 = Dispositivo(
            tipo="celular", marca="Samsung", modelo="Galaxy A15 4G",
            imei="358291054921049", patrimonio="PAT-AMB-0499",
            data_aquisicao=hoje - timedelta(days=95), valor_aquisicao=890.0,
            colaborador_id=c_camila.id, status="na_assistencia",
            observacoes="Aparelho do trade marketing para registro fotográfico de gôndolas e displays."
        )

        d6 = Dispositivo(
            tipo="tablet", marca="Samsung", modelo="Galaxy Tab S9 FE",
            serial="R58M10293CD", patrimonio="TAB-GER-01",
            data_aquisicao=hoje - timedelta(days=150), valor_aquisicao=2300.0,
            colaborador_id=None, status="em_estoque",
            observacoes="Aparelho reserva de alta performance preparado para auditorias e inventários."
        )

        d7 = Dispositivo(
            tipo="celular", marca="Motorola", modelo="Moto G84 5G",
            imei="351982049182312", patrimonio="PAT-AMB-0388",
            data_aquisicao=hoje - timedelta(days=365), valor_aquisicao=1150.0,
            colaborador_id=c_thiago.id, status="em_uso",
            observacoes="Comunicação rápida e controle de romaneios na expedição de mercadorias."
        )

        db.session.add_all([d1, d2, d3, d4, d5, d6, d7])
        db.session.flush()

        # ========================================================
        # 4. ORDENS DE SERVIÇO (HISTÓRICO RICO E GERENCIAL)
        # ========================================================
        # OS 1: Em Reparo Atual (Coletor Zebra na TechFix)
        os1 = OrdemAssistencia(
            dispositivo_id=d3.id, fornecedor_id=f1.id, colaborador_id=c_rodrigo.id,
            data_envio=hoje - timedelta(days=5),
            defeito="Leitor de código 2D com falha intermitente após impacto na esteira.",
            status="em_reparo", valor_orcado=420.0,
            observacoes="Prioridade alta devido ao fechamento do inventário mensal de estoque."
        )

        # OS 2: Em Análise Atual (Galaxy A15 do Trade Marketing)
        os2 = OrdemAssistencia(
            dispositivo_id=d5.id, fornecedor_id=f2.id, colaborador_id=c_camila.id,
            data_envio=hoje - timedelta(days=3),
            defeito="Aparelho reiniciando sozinho e não reconhece carregamento rápido.",
            status="em_analise", valor_orcado=160.0,
            observacoes="Enviado com cabo de teste. Verificando possível oxidação na porta USB-C."
        )

        # OS 3: Concluída recente com Garantia Ativa (Galaxy A55 da Mariana)
        os3 = OrdemAssistencia(
            dispositivo_id=d1.id, fornecedor_id=f2.id, colaborador_id=c_mariana.id,
            data_envio=hoje - timedelta(days=45), data_retorno=hoje - timedelta(days=38),
            defeito="Display sem imagem após pressão no bolso / touch travado.",
            status="devolvido", valor_orcado=380.0, valor_final=380.0,
            causa="mau_uso", responsavel_custo="misto",
            valor_empresa=200.0, valor_colaborador=180.0,
            garantia_ate=hoje + timedelta(days=52),
            laudo="Substituição completa do display frontal OLED original e aplicação de nova película 3D.",
            observacoes="Acordo operacional: 50% subsidiado pela Ambev e 50% via vale corporativo."
        )

        # OS 4: Manutenção de 3 meses atrás (Tablet Active do Lucas)
        os4 = OrdemAssistencia(
            dispositivo_id=d4.id, fornecedor_id=f1.id, colaborador_id=c_lucas.id,
            data_envio=hoje - timedelta(days=110), data_retorno=hoje - timedelta(days=102),
            defeito="Bateria com autonomia reduzida e conector veicular frouxo.",
            status="devolvido", valor_orcado=290.0, valor_final=290.0,
            causa="desgaste_natural", responsavel_custo="empresa",
            valor_empresa=290.0, valor_colaborador=0.0,
            garantia_ate=hoje - timedelta(days=12),
            laudo="Substituição da célula de bateria e troca do conector magnético de encaixe no caminhão."
        )

        # OS 5: Manutenção Antiga de 5 meses atrás (Moto G84 do Thiago)
        os5 = OrdemAssistencia(
            dispositivo_id=d7.id, fornecedor_id=f2.id, colaborador_id=c_thiago.id,
            data_envio=hoje - timedelta(days=165), data_retorno=hoje - timedelta(days=158),
            defeito="Microfone e alto-falante chiando após acúmulo de poeira no armazém.",
            status="devolvido", valor_orcado=140.0, valor_final=140.0,
            causa="desgaste_natural", responsavel_custo="empresa",
            valor_empresa=140.0, valor_colaborador=0.0,
            garantia_ate=hoje - timedelta(days=68),
            laudo="Limpeza ultrassônica das membranas acústicas e substituição dos filtros antipoeira."
        )

        db.session.add_all([os1, os2, os3, os4, os5])
        db.session.flush()

        # ========================================================
        # 5. VALES DE RH (DESCONTO EM FOLHA / COMPARTILHAMENTO)
        # ========================================================
        v1 = Vale(
            ordem_id=os3.id,
            colaborador_id=c_mariana.id,
            valor=180.0,
            data_emissao=hoje - timedelta(days=38),
            status="pendente",
            motivo=f"Reparo OS #{os3.id} (Mau Uso / Tela)",
            observacoes="Aguardando fechamento da folha de pagamento pelo RH Disfonte."
        )

        v2 = Vale(
            ordem_id=None,
            colaborador_id=c_rodrigo.id,
            valor=45.0,
            data_emissao=hoje - timedelta(days=20),
            status="pendente",
            motivo="Reposição de Carregador Rápido (Perda em trânsito)",
            observacoes="Colaborador solicitou novo acessório com desconto parcelado."
        )

        v3 = Vale(
            ordem_id=None,
            colaborador_id=c_thiago.id,
            valor=85.0,
            data_emissao=hoje - timedelta(days=65),
            status="descontado",
            motivo="Reparo de case de proteção danificado",
            observacoes="Descontado na folha do mês anterior (Folha Ref. 09/2026)."
        )

        db.session.add_all([v1, v2, v3])
        db.session.flush()

        # ========================================================
        # 6. ACESSÓRIOS & ESTOQUE DE EQUIPAMENTOS
        # ========================================================
        a1 = Acessorio(
            nome="Película Vidro 3D Galaxy A55 5G",
            categoria="Pelicula", compatibilidade="Samsung Galaxy A55",
            estoque_atual=14, estoque_minimo=5, custo_medio=9.50
        )
        a2 = Acessorio(
            nome="Capa Anti-Impacto Militar Moto Edge 50",
            categoria="Capa", compatibilidade="Motorola Edge 50 Fusion",
            estoque_atual=8, estoque_minimo=4, custo_medio=18.00
        )
        a3 = Acessorio(
            nome="Case Emborrachado com Alça Zebra TC26",
            categoria="Capa", compatibilidade="Zebra TC21 / TC26",
            estoque_atual=2, estoque_minimo=5, custo_medio=55.00
        )
        a4 = Acessorio(
            nome="Cabo USB-C Reforçado em Nylon 1.5m",
            categoria="Cabo", compatibilidade="Universal Tipo-C",
            estoque_atual=19, estoque_minimo=8, custo_medio=14.00
        )
        a5 = Acessorio(
            nome="Carregador Veicular Turbo 30W (Frota)",
            categoria="Carregador", compatibilidade="Caminhões & Veículos 12V/24V",
            estoque_atual=3, estoque_minimo=6, custo_medio=38.00
        )
        a6 = Acessorio(
            nome="Carregador de Parede 25W Anatel",
            categoria="Carregador", compatibilidade="Universal Tipo-C",
            estoque_atual=11, estoque_minimo=5, custo_medio=32.00
        )

        db.session.add_all([a1, a2, a3, a4, a5, a6])
        db.session.flush()

        # ========================================================
        # 7. HISTÓRICO DE ENTRADAS & SAÍDAS DE ESTOQUE
        # ========================================================
        e1 = EntradaAcessorio(
            acessorio_id=a1.id, quantidade=20, custo_unitario=9.50,
            fornecedor_id=f3.id, nota_fiscal="NF-89211", data=hoje - timedelta(days=60)
        )
        e2 = EntradaAcessorio(
            acessorio_id=a4.id, quantidade=25, custo_unitario=14.00,
            fornecedor_id=f3.id, nota_fiscal="NF-89450", data=hoje - timedelta(days=40)
        )
        e3 = EntradaAcessorio(
            acessorio_id=a5.id, quantidade=10, custo_unitario=38.00,
            fornecedor_id=f3.id, nota_fiscal="NF-89912", data=hoje - timedelta(days=25)
        )
        db.session.add_all([e1, e2, e3])

        s1 = SaidaAcessorio(
            acessorio_id=a1.id, quantidade=1, colaborador_id=c_mariana.id,
            dispositivo_id=d1.id, motivo="novo", data=hoje - timedelta(days=38),
            custo_no_momento=9.50, gerou_vale=False
        )
        s2 = SaidaAcessorio(
            acessorio_id=a5.id, quantidade=1, colaborador_id=c_lucas.id,
            dispositivo_id=d4.id, motivo="novo", data=hoje - timedelta(days=15),
            custo_no_momento=38.00, gerou_vale=False
        )
        s3 = SaidaAcessorio(
            acessorio_id=a6.id, quantidade=1, colaborador_id=c_rodrigo.id,
            dispositivo_id=d3.id, motivo="perda", data=hoje - timedelta(days=20),
            custo_no_momento=32.00, gerou_vale=True
        )
        db.session.add_all([s1, s2, s3])

        db.session.commit()
        print("\n=== MODELO DE DADOS GENÉRICO / LINKEDIN CARREGADO COM SUCESSO! ===")
        print("Métricas:")
        print(f" - Colaboradores: {Colaborador.query.count()}")
        print(f" - Fornecedores: {Fornecedor.query.count()}")
        print(f" - Dispositivos: {Dispositivo.query.count()} (Smartphones, Coletores Zebra e Tablets)")
        print(f" - Ordens de Serviço: {OrdemAssistencia.query.count()} (2 ativas, 3 históricas com garantias e laudos)")
        print(f" - Vales RH: {Vale.query.count()} (2 pendentes, 1 descontado)")
        print(f" - Acessórios em Estoque: {Acessorio.query.count()} itens com alertas de reposição")

if __name__ == '__main__':
    popular_dados_linkedin()
