import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from models import (
    db, Colaborador, Fornecedor, Dispositivo, OrdemAssistencia,
    Vale, Acessorio, EntradaAcessorio, SaidaAcessorio
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'consert-cell-chave-dev-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///consertcell.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ==========================================
# FILTROS JINJA CUSTOMIZADOS
# ==========================================
@app.template_filter('moeda')
def formato_moeda(valor):
    try:
        val = float(valor or 0.0)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

@app.template_filter('data_br')
def formato_data(val_data):
    if not val_data:
        return "-"
    if isinstance(val_data, str):
        try:
            val_data = datetime.strptime(val_data, '%Y-%m-%d').date()
        except ValueError:
            return val_data
    return val_data.strftime('%d/%m/%Y')

@app.context_processor
def injetar_globais():
    return {'hoje': date.today().strftime('%Y-%m-%d')}

def parse_float_br(valor):
    """Converte valores monetários em formato brasileiro ('1.250,50' ou '1250,50') ou internacional ('1250.50') para float com segurança."""
    if not valor:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).replace('R$', '').strip()
    if not texto:
        return 0.0
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except (ValueError, TypeError):
        return 0.0


# ==========================================
# ROTA 1: DASHBOARD
# ==========================================
@app.route('/')
def index():
    # Métricas principais
    aparelhos_na_assistencia = OrdemAssistencia.query.filter(
        OrdemAssistencia.status.notin_(['devolvido', 'sem_conserto'])
    ).all()
    
    total_na_assistencia = len(aparelhos_na_assistencia)

    # Ordens atrasadas (> 7 dias e > 15 dias)
    os_atrasadas_criticas = [os for os in aparelhos_na_assistencia if os.dias_fora >= 15]
    os_atrasadas_alerta = [os for os in aparelhos_na_assistencia if 7 <= os.dias_fora < 15]

    # Vales pendentes ou emitidos
    vales_abertos = Vale.query.filter(Vale.status.in_(['pendente', 'emitido'])).all()
    total_vales_valor = sum(v.valor for v in vales_abertos)
    total_vales_qtd = len(vales_abertos)

    # Estoque crítico
    acessorios = Acessorio.query.all()
    itens_baixo_estoque = [a for a in acessorios if a.is_estoque_baixo]
    valor_total_estoque = sum(a.valor_total_estoque for a in acessorios)

    # Gastos do Mês Atual (Empresa)
    primeiro_dia_mes = date.today().replace(day=1)
    ordens_mes = OrdemAssistencia.query.filter(
        OrdemAssistencia.data_envio >= primeiro_dia_mes
    ).all()
    
    gasto_mes_empresa = sum(o.valor_empresa for o in ordens_mes if o.valor_empresa)
    gasto_mes_total = sum((o.valor_final or o.valor_orcado or 0) for o in ordens_mes)

    # Aparelhos com custo crítico (> 50% de manutenção)
    dispositivos = Dispositivo.query.filter(Dispositivo.status != 'baixado').all()
    aparelhos_criticos = [d for d in dispositivos if d.is_alerta_bomba]

    # Lista recente de OS em andamento
    os_recentes = OrdemAssistencia.query.order_by(OrdemAssistencia.id.desc()).limit(8).all()

    # Dados para gráfico de gastos dos últimos 6 meses
    dados_meses = []
    labels_meses = []
    hoje = date.today()
    for i in range(5, -1, -1):
        # Mês aproximado
        mes_ref = (hoje.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        nome_mes = mes_ref.strftime('%b/%y').capitalize()
        labels_meses.append(nome_mes)
        
        # Gastos desse mês
        fim_mes = (mes_ref + timedelta(days=32)).replace(day=1)
        os_do_mes = OrdemAssistencia.query.filter(
            OrdemAssistencia.data_envio >= mes_ref,
            OrdemAssistencia.data_envio < fim_mes
        ).all()
        gasto = sum(o.valor_empresa for o in os_do_mes if o.valor_empresa)
        dados_meses.append(round(gasto, 2))

    return render_template(
        'index.html',
        total_na_assistencia=total_na_assistencia,
        os_atrasadas_criticas=os_atrasadas_criticas,
        os_atrasadas_alerta=os_atrasadas_alerta,
        total_vales_valor=total_vales_valor,
        total_vales_qtd=total_vales_qtd,
        itens_baixo_estoque=itens_baixo_estoque,
        valor_total_estoque=valor_total_estoque,
        gasto_mes_empresa=gasto_mes_empresa,
        gasto_mes_total=gasto_mes_total,
        aparelhos_criticos=aparelhos_criticos,
        os_recentes=os_recentes,
        chart_labels=labels_meses,
        chart_values=dados_meses
    )


# ==========================================
# ROTA 2: DISPOSITIVOS
# ==========================================
@app.route('/dispositivos', methods=['GET', 'POST'])
def dispositivos():
    if request.method == 'POST':
        tipo = request.form.get('tipo', 'celular')
        marca = request.form.get('marca', '').strip()
        modelo = request.form.get('modelo', '').strip()
        imei = request.form.get('imei', '').strip() or None
        serial = request.form.get('serial', '').strip() or None
        patrimonio = request.form.get('patrimonio', '').strip() or None
        data_aquisicao_str = request.form.get('data_aquisicao')
        data_aquisicao = datetime.strptime(data_aquisicao_str, '%Y-%m-%d').date() if data_aquisicao_str else None
        valor_aquisicao = parse_float_br(request.form.get('valor_aquisicao'))
        colaborador_id = request.form.get('colaborador_id') or None
        status = request.form.get('status', 'em_uso')
        observacoes = request.form.get('observacoes', '').strip()

        # Validação básica de IMEI único se informado
        if imei:
            existente = Dispositivo.query.filter_by(imei=imei).first()
            if existente:
                flash(f"Já existe um dispositivo com o IMEI {imei} cadastrado!", "danger")
                return redirect(url_for('dispositivos'))

        novo_disp = Dispositivo(
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            imei=imei,
            serial=serial,
            patrimonio=patrimonio,
            data_aquisicao=data_aquisicao,
            valor_aquisicao=valor_aquisicao,
            colaborador_id=colaborador_id,
            status=status,
            observacoes=observacoes
        )
        db.session.add(novo_disp)
        db.session.commit()
        flash(f"Dispositivo {marca} {modelo} cadastrado com sucesso!", "success")
        return redirect(url_for('dispositivos'))

    busca = request.args.get('busca', '').strip()
    filtro_status = request.args.get('status', '').strip()
    filtro_tipo = request.args.get('tipo', '').strip()

    query = Dispositivo.query
    if busca:
        query = query.filter(
            (Dispositivo.marca.ilike(f"%{busca}%")) |
            (Dispositivo.modelo.ilike(f"%{busca}%")) |
            (Dispositivo.imei.ilike(f"%{busca}%")) |
            (Dispositivo.serial.ilike(f"%{busca}%")) |
            (Dispositivo.patrimonio.ilike(f"%{busca}%"))
        )
    if filtro_status:
        query = query.filter_by(status=filtro_status)
    if filtro_tipo:
        query = query.filter_by(tipo=filtro_tipo)

    lista_dispositivos = query.order_by(Dispositivo.id.desc()).all()
    colaboradores = Colaborador.query.filter_by(ativo=True).order_by(Colaborador.nome).all()

    return render_template(
        'dispositivos.html',
        dispositivos=lista_dispositivos,
        colaboradores=colaboradores,
        busca=busca,
        filtro_status=filtro_status,
        filtro_tipo=filtro_tipo
    )


@app.route('/dispositivos/<int:id>/editar', methods=['POST'])
def editar_dispositivo(id):
    disp = Dispositivo.query.get_or_404(id)
    disp.tipo = request.form.get('tipo', disp.tipo)
    disp.marca = request.form.get('marca', disp.marca).strip()
    disp.modelo = request.form.get('modelo', disp.modelo).strip()
    disp.imei = request.form.get('imei', '').strip() or None
    disp.serial = request.form.get('serial', '').strip() or None
    disp.patrimonio = request.form.get('patrimonio', '').strip() or None
    
    data_aquisicao_str = request.form.get('data_aquisicao')
    if data_aquisicao_str:
        disp.data_aquisicao = datetime.strptime(data_aquisicao_str, '%Y-%m-%d').date()
    
    disp.valor_aquisicao = parse_float_br(request.form.get('valor_aquisicao'))
    disp.colaborador_id = request.form.get('colaborador_id') or None
    disp.status = request.form.get('status', disp.status)
    disp.observacoes = request.form.get('observacoes', '').strip()

    db.session.commit()
    flash(f"Dispositivo #{disp.id} atualizado com sucesso!", "success")
    return redirect(url_for('dispositivos'))


@app.route('/dispositivos/<int:id>/historico')
def historico_dispositivo(id):
    disp = Dispositivo.query.get_or_404(id)
    ordens = OrdemAssistencia.query.filter_by(dispositivo_id=disp.id).order_by(OrdemAssistencia.data_envio.desc()).all()
    saidas = SaidaAcessorio.query.filter_by(dispositivo_id=disp.id).order_by(SaidaAcessorio.data.desc()).all()
    return render_template('historico_dispositivo.html', disp=disp, ordens=ordens, saidas=saidas)


# ==========================================
# ROTA 3: ORDENS DE ASSISTÊNCIA
# ==========================================
@app.route('/ordens', methods=['GET', 'POST'])
def ordens():
    if request.method == 'POST':
        dispositivo_id = request.form.get('dispositivo_id')
        fornecedor_id = request.form.get('fornecedor_id')
        data_envio_str = request.form.get('data_envio')
        data_envio = datetime.strptime(data_envio_str, '%Y-%m-%d').date() if data_envio_str else date.today()
        defeito = request.form.get('defeito', '').strip()
        valor_orcado = parse_float_br(request.form.get('valor_orcado'))
        observacoes = request.form.get('observacoes', '').strip()

        disp = Dispositivo.query.get_or_404(dispositivo_id)
        colaborador_id = disp.colaborador_id

        if disp.status == 'na_assistencia':
            flash(f"O dispositivo {disp.marca} {disp.modelo} ({disp.identificador}) já está na assistência técnica com uma OS em aberto!", "danger")
            return redirect(url_for('ordens'))

        # Verificar se o aparelho teve OS devolvida nos últimos 90 dias
        data_limite_garantia = date.today() - timedelta(days=90)
        os_recente = OrdemAssistencia.query.filter(
            OrdemAssistencia.dispositivo_id == disp.id,
            OrdemAssistencia.status == 'devolvido',
            OrdemAssistencia.data_retorno >= data_limite_garantia
        ).first()

        nova_os = OrdemAssistencia(
            dispositivo_id=disp.id,
            fornecedor_id=fornecedor_id,
            colaborador_id=colaborador_id,
            data_envio=data_envio,
            defeito=defeito,
            valor_orcado=valor_orcado,
            status='enviado',
            observacoes=observacoes
        )

        # Atualiza status do aparelho
        disp.status = 'na_assistencia'

        db.session.add(nova_os)
        db.session.commit()

        if os_recente:
            flash(
                f"OS #{nova_os.id} aberta com sucesso! ATENÇÃO: Este aparelho retornou de reparo em "
                f"{os_recente.data_retorno.strftime('%d/%m/%Y')} (há menos de 90 dias). Verifique se está na garantia da assistência!",
                "warning"
            )
        else:
            flash(f"Ordem de Serviço #{nova_os.id} aberta com sucesso!", "success")
        return redirect(url_for('ordens'))

    filtro_status = request.args.get('status', '').strip()
    query = OrdemAssistencia.query
    if filtro_status:
        query = query.filter_by(status=filtro_status)

    lista_ordens = query.order_by(OrdemAssistencia.id.desc()).all()
    dispositivos_disponiveis = Dispositivo.query.filter(Dispositivo.status != 'baixado').all()
    fornecedores = Fornecedor.query.filter_by(tipo='assistencia').all()
    if not fornecedores:
        fornecedores = Fornecedor.query.all()
    colaboradores = Colaborador.query.filter_by(ativo=True).all()

    return render_template(
        'ordens.html',
        ordens=lista_ordens,
        dispositivos=dispositivos_disponiveis,
        fornecedores=fornecedores,
        colaboradores=colaboradores,
        filtro_status=filtro_status
    )


@app.route('/ordens/<int:id>/atualizar-status', methods=['POST'])
def atualizar_status_ordem(id):
    os_obj = OrdemAssistencia.query.get_or_404(id)
    novo_status = request.form.get('status')
    valor_orcado = request.form.get('valor_orcado')
    if valor_orcado:
        os_obj.valor_orcado = parse_float_br(valor_orcado)
    
    os_obj.status = novo_status
    db.session.commit()
    flash(f"Status da OS #{os_obj.id} atualizado para {novo_status}!", "info")
    return redirect(url_for('ordens'))


@app.route('/ordens/<int:id>/concluir', methods=['POST'])
def concluir_ordem(id):
    os_obj = OrdemAssistencia.query.get_or_404(id)
    
    status_final = request.form.get('status_final', 'devolvido') # 'devolvido' ou 'sem_conserto'
    data_retorno_str = request.form.get('data_retorno')
    data_retorno = datetime.strptime(data_retorno_str, '%Y-%m-%d').date() if data_retorno_str else date.today()
    
    if data_retorno < os_obj.data_envio:
        flash("A data de retorno não pode ser anterior à data de envio do aparelho!", "danger")
        return redirect(url_for('ordens'))

    valor_final = parse_float_br(request.form.get('valor_final'))
    causa = request.form.get('causa', 'desgaste_natural')
    laudo = request.form.get('laudo', '').strip()
    responsavel_custo = request.form.get('responsavel_custo', 'empresa')
    
    garantia_dias = int(request.form.get('garantia_dias') or 90)
    garantia_ate = data_retorno + timedelta(days=garantia_dias)

    # Divisão de custos
    if responsavel_custo == 'empresa':
        valor_empresa = valor_final
        valor_colaborador = 0.0
    elif responsavel_custo == 'colaborador':
        valor_empresa = 0.0
        valor_colaborador = valor_final
    else:  # misto
        valor_colaborador = parse_float_br(request.form.get('valor_colaborador'))
        valor_empresa = max(0.0, valor_final - valor_colaborador)

    os_obj.status = status_final
    os_obj.data_retorno = data_retorno
    os_obj.valor_final = valor_final
    os_obj.causa = causa
    os_obj.laudo = laudo
    os_obj.responsavel_custo = responsavel_custo
    os_obj.valor_empresa = valor_empresa
    os_obj.valor_colaborador = valor_colaborador
    os_obj.garantia_ate = garantia_ate

    # Atualiza o dispositivo
    disp = os_obj.dispositivo
    if status_final == 'sem_conserto':
        disp.status = 'baixado'
    else:
        disp.status = 'em_uso' if disp.colaborador_id else 'em_estoque'

    # Se houve valor para o colaborador, gera Vale automaticamente!
    if valor_colaborador > 0 and os_obj.colaborador_id:
        # Verifica se já não existe vale vinculado a esta OS
        vale_existente = Vale.query.filter_by(ordem_id=os_obj.id).first()
        if not vale_existente:
            novo_vale = Vale(
                ordem_id=os_obj.id,
                colaborador_id=os_obj.colaborador_id,
                valor=valor_colaborador,
                data_emissao=data_retorno,
                status='pendente',
                motivo=f"Reparo OS #{os_obj.id} ({causa.replace('_', ' ').title()})",
                observacoes=f"Gerado automaticamente pelo fechamento da OS #{os_obj.id}. Laudo: {laudo}"
            )
            db.session.add(novo_vale)
            flash(f"OS #{os_obj.id} finalizada! Vale de R$ {valor_colaborador:,.2f} gerado para o colaborador.", "warning")
    else:
        flash(f"OS #{os_obj.id} finalizada com sucesso! Custo da empresa: R$ {valor_empresa:,.2f}.", "success")

    db.session.commit()
    return redirect(url_for('ordens'))


# ==========================================
# ROTA 4: VALES (RH / DP)
# ==========================================
@app.route('/vales')
def vales():
    filtro_status = request.args.get('status', '').strip()
    query = Vale.query
    if filtro_status:
        query = query.filter_by(status=filtro_status)
    
    lista_vales = query.order_by(Vale.id.desc()).all()
    total_pendente = sum(v.valor for v in lista_vales if v.status == 'pendente')
    total_emitido = sum(v.valor for v in lista_vales if v.status == 'emitido')
    total_descontado = sum(v.valor for v in lista_vales if v.status == 'descontado')

    return render_template(
        'vales.html',
        vales=lista_vales,
        filtro_status=filtro_status,
        total_pendente=total_pendente,
        total_emitido=total_emitido,
        total_descontado=total_descontado
    )


@app.route('/vales/<int:id>/status', methods=['POST'])
def alterar_status_vale(id):
    vale_obj = Vale.query.get_or_404(id)
    novo_status = request.form.get('status')
    vale_obj.status = novo_status
    db.session.commit()
    flash(f"Vale #{vale_obj.id} atualizado para status '{novo_status}'!", "success")
    return redirect(url_for('vales'))


# ==========================================
# ROTA 5: ACESSÓRIOS & ESTOQUE
# ==========================================
@app.route('/acessorios', methods=['GET', 'POST'])
def acessorios():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        categoria = request.form.get('categoria', 'Geral')
        compatibilidade = request.form.get('compatibilidade', '').strip()
        estoque_minimo = int(request.form.get('estoque_minimo') or 5)
        estoque_inicial = int(request.form.get('estoque_inicial') or 0)
        custo_inicial = parse_float_br(request.form.get('custo_inicial'))

        novo_acess = Acessorio(
            nome=nome,
            categoria=categoria,
            compatibilidade=compatibilidade,
            estoque_atual=estoque_inicial,
            estoque_minimo=estoque_minimo,
            custo_medio=custo_inicial
        )
        db.session.add(novo_acess)
        db.session.commit()
        flash(f"Acessório '{nome}' cadastrado com sucesso!", "success")
        return redirect(url_for('acessorios'))

    itens = Acessorio.query.order_by(Acessorio.nome).all()
    fornecedores = Fornecedor.query.all()
    colaboradores = Colaborador.query.filter_by(ativo=True).order_by(Colaborador.nome).all()
    dispositivos = Dispositivo.query.filter(Dispositivo.status != 'baixado').all()
    ultimas_saidas = SaidaAcessorio.query.order_by(SaidaAcessorio.id.desc()).limit(10).all()

    return render_template(
        'acessorios.html',
        acessorios=itens,
        fornecedores=fornecedores,
        colaboradores=colaboradores,
        dispositivos=dispositivos,
        ultimas_saidas=ultimas_saidas
    )


@app.route('/acessorios/entrada', methods=['POST'])
def entrada_acessorio():
    acessorio_id = request.form.get('acessorio_id')
    quantidade = int(request.form.get('quantidade') or 0)
    custo_unitario = parse_float_br(request.form.get('custo_unitario'))
    fornecedor_id = request.form.get('fornecedor_id') or None
    nota_fiscal = request.form.get('nota_fiscal', '').strip()
    data_str = request.form.get('data')
    data_entrada = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else date.today()

    acess = Acessorio.query.get_or_404(acessorio_id)
    
    # Recalcula custo médio ponderado
    custo_total_antigo = acess.estoque_atual * acess.custo_medio
    custo_total_novo = quantidade * custo_unitario
    novo_estoque = acess.estoque_atual + quantidade

    if novo_estoque > 0:
        acess.custo_medio = round((custo_total_antigo + custo_total_novo) / novo_estoque, 2)
    acess.estoque_atual = novo_estoque

    entrada = EntradaAcessorio(
        acessorio_id=acess.id,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        fornecedor_id=fornecedor_id,
        nota_fiscal=nota_fiscal,
        data=data_entrada
    )
    db.session.add(entrada)
    db.session.commit()
    flash(f"Entrada de {quantidade}x {acess.nome} registrada! Estoque atual: {acess.estoque_atual}.", "success")
    return redirect(url_for('acessorios'))


@app.route('/acessorios/saida', methods=['POST'])
def saida_acessorio():
    acessorio_id = request.form.get('acessorio_id')
    quantidade = int(request.form.get('quantidade') or 1)
    colaborador_id = request.form.get('colaborador_id')
    dispositivo_id = request.form.get('dispositivo_id') or None
    motivo = request.form.get('motivo', 'novo') # 'novo', 'reposicao', 'quebra', 'perda'
    gerar_vale = request.form.get('gerar_vale') == 'sim'

    acess = Acessorio.query.get_or_404(acessorio_id)
    if acess.estoque_atual < quantidade:
        flash(f"Estoque insuficiente! Saldo atual: {acess.estoque_atual}, solicitado: {quantidade}.", "danger")
        return redirect(url_for('acessorios'))

    acess.estoque_atual -= quantidade
    custo_momento = acess.custo_medio * quantidade

    saida = SaidaAcessorio(
        acessorio_id=acess.id,
        quantidade=quantidade,
        colaborador_id=colaborador_id,
        dispositivo_id=dispositivo_id,
        motivo=motivo,
        custo_no_momento=custo_momento,
        gerou_vale=gerar_vale
    )
    db.session.add(saida)
    db.session.flush()

    if gerar_vale:
        novo_vale = Vale(
            saida_acessorio_id=saida.id,
            colaborador_id=colaborador_id,
            valor=custo_momento,
            data_emissao=date.today(),
            status='pendente',
            motivo=f"Acessório ({motivo.upper()}): {quantidade}x {acess.nome}",
            observacoes=f"Reposição por {motivo} gerou desconto para o colaborador."
        )
        db.session.add(novo_vale)
        flash(f"Saída de {quantidade}x {acess.nome} registrada e Vale de R$ {custo_momento:,.2f} criado!", "warning")
    else:
        flash(f"Saída de {quantidade}x {acess.nome} registrada com sucesso!", "success")

    db.session.commit()
    return redirect(url_for('acessorios'))


# ==========================================
# ROTA 6: CADASTROS (Colaboradores & Fornecedores)
# ==========================================
@app.route('/cadastros', methods=['GET'])
def cadastros():
    colaboradores = Colaborador.query.order_by(Colaborador.nome).all()
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    return render_template('cadastros.html', colaboradores=colaboradores, fornecedores=fornecedores)


@app.route('/cadastros/colaborador', methods=['POST'])
def salvar_colaborador():
    nome = request.form.get('nome', '').strip()
    setor = request.form.get('setor', '').strip()
    matricula = request.form.get('matricula', '').strip() or None

    if not nome or not setor:
        flash("Nome e Setor são obrigatórios!", "danger")
        return redirect(url_for('cadastros'))

    colab = Colaborador(nome=nome, setor=setor, matricula=matricula)
    db.session.add(colab)
    db.session.commit()
    flash(f"Colaborador {nome} adicionado com sucesso!", "success")
    return redirect(url_for('cadastros'))


@app.route('/cadastros/fornecedor', methods=['POST'])
def salvar_fornecedor():
    nome = request.form.get('nome', '').strip()
    tipo = request.form.get('tipo', 'assistencia')
    contato = request.form.get('contato', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    observacoes = request.form.get('observacoes', '').strip()

    if not nome:
        flash("Nome do fornecedor é obrigatório!", "danger")
        return redirect(url_for('cadastros'))

    forn = Fornecedor(nome=nome, tipo=tipo, contato=contato, cnpj=cnpj, observacoes=observacoes)
    db.session.add(forn)
    db.session.commit()
    flash(f"Fornecedor {nome} cadastrado com sucesso!", "success")
    return redirect(url_for('cadastros'))


# ==========================================
# ROTA 7: EXPORTAÇÃO EXCEL
# ==========================================
@app.route('/relatorios/excel')
def exportar_excel():
    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border_thin = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )

    # 1. Aba Ordens de Serviço
    ws_os = wb.active
    ws_os.title = "Ordens de Assistência"
    colunas_os = ["ID", "Dispositivo", "Fornecedor", "Data Envio", "Defeito", "Status", "Valor Final", "Causa", "Responsável", "Custo Empresa", "Vale Colaborador", "Dias Fora"]
    ws_os.append(colunas_os)

    ordens = OrdemAssistencia.query.all()
    for o in ordens:
        disp_txt = f"{o.dispositivo.marca} {o.dispositivo.modelo} ({o.dispositivo.identificador})" if o.dispositivo else "-"
        ws_os.append([
            o.id,
            disp_txt,
            o.fornecedor.nome if o.fornecedor else "-",
            o.data_envio.strftime('%d/%m/%Y') if o.data_envio else "-",
            o.defeito,
            o.status,
            o.valor_final,
            o.causa or "-",
            o.responsavel_custo or "-",
            o.valor_empresa,
            o.valor_colaborador,
            o.dias_fora
        ])

    # 2. Aba Dispositivos
    ws_disp = wb.create_sheet(title="Dispositivos")
    colunas_disp = ["ID", "Tipo", "Marca", "Modelo", "Identificador", "Patrimônio", "Valor Compra", "Total Manutenções", "% Custo", "Colaborador", "Setor", "Status"]
    ws_disp.append(colunas_disp)
    
    dispositivos = Dispositivo.query.all()
    for d in dispositivos:
        ws_disp.append([
            d.id,
            d.tipo,
            d.marca,
            d.modelo,
            d.identificador,
            d.patrimonio or "-",
            d.valor_aquisicao,
            d.custo_total_manutencao,
            f"{d.percentual_custo_aquisicao}%",
            d.colaborador.nome if d.colaborador else "-",
            d.colaborador.setor if d.colaborador else "-",
            d.status
        ])

    # 3. Aba Vales
    ws_vales = wb.create_sheet(title="Vales a Descontar")
    colunas_vales = ["ID Vale", "Colaborador", "Setor", "Valor (R$)", "Data Emissão", "Status", "Origem/Motivo"]
    ws_vales.append(colunas_vales)
    
    vales = Vale.query.all()
    for v in vales:
        ws_vales.append([
            v.id,
            v.colaborador.nome if v.colaborador else "-",
            v.colaborador.setor if v.colaborador else "-",
            v.valor,
            v.data_emissao.strftime('%d/%m/%Y') if v.data_emissao else "-",
            v.status,
            v.motivo or "-"
        ])

    # 4. Aba Estoque
    ws_est = wb.create_sheet(title="Estoque de Acessórios")
    colunas_est = ["Item", "Categoria", "Compatibilidade", "Estoque Atual", "Estoque Mínimo", "Custo Médio", "Valor em Estoque", "Status"]
    ws_est.append(colunas_est)
    
    acessorios = Acessorio.query.all()
    for a in acessorios:
        ws_est.append([
            a.nome,
            a.categoria,
            a.compatibilidade or "-",
            a.estoque_atual,
            a.estoque_minimo,
            a.custo_medio,
            a.valor_total_estoque,
            "CRÍTICO" if a.is_estoque_baixo else "OK"
        ])

    # Estiliza todos os cabeçalhos
    for ws in [ws_os, ws_disp, ws_vales, ws_est]:
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    data_hoje = date.today().strftime('%Y%m%d')
    return send_file(
        output,
        download_name=f"ConsertCell_Relatorio_{data_hoje}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ==========================================
# SEEDER INICIAL (DADOS DE EXEMPLO)
# ==========================================
@app.route('/carregar-dados-exemplo')
def carregar_dados_exemplo():
    if Colaborador.query.first():
        flash("O banco de dados já possui registros cadastrados!", "info")
        return redirect(url_for('index'))

    # Colaboradores
    c1 = Colaborador(nome="Gabriel Nunes", setor="TI", matricula="TI01")
    c2 = Colaborador(nome="Carlos Silva", setor="Logística", matricula="LOG04")
    c3 = Colaborador(nome="Mariana Costa", setor="Vendas Externas", matricula="VND12")
    c4 = Colaborador(nome="Lucas Oliveira", setor="Operações", matricula="OP09")
    db.session.add_all([c1, c2, c3, c4])
    db.session.flush()

    # Fornecedores
    f1 = Fornecedor(nome="MegaCell Assistência Técnica", tipo="assistencia", contato="(11) 98765-4321", cnpj="12.345.678/0001-90")
    f2 = Fornecedor(nome="TechFix Reparos Rápidos", tipo="assistencia", contato="(11) 91234-5678", cnpj="98.765.432/0001-10")
    f3 = Fornecedor(nome="Distribuidora Alfa Acessórios", tipo="loja", contato="(11) 3322-1100", cnpj="45.678.910/0001-22")
    db.session.add_all([f1, f2, f3])
    db.session.flush()

    # Dispositivos
    d1 = Dispositivo(
        tipo="celular", marca="Samsung", modelo="Galaxy A15", imei="354892019283741",
        patrimonio="PAT-0101", data_aquisicao=date(2025, 3, 10), valor_aquisicao=950.0,
        colaborador_id=c2.id, status="na_assistencia"
    )
    d2 = Dispositivo(
        tipo="celular", marca="Motorola", modelo="Moto G34", imei="867512049182375",
        patrimonio="PAT-0102", data_aquisicao=date(2025, 1, 15), valor_aquisicao=850.0,
        colaborador_id=c3.id, status="em_uso"
    )
    d3 = Dispositivo(
        tipo="tablet", marca="Samsung", modelo="Galaxy Tab A9", serial="R52N80ABCDE",
        patrimonio="PAT-TAB-01", data_aquisicao=date(2024, 11, 20), valor_aquisicao=1200.0,
        colaborador_id=c4.id, status="em_uso"
    )
    db.session.add_all([d1, d2, d3])
    db.session.flush()

    # Ordens de Assistência
    os1 = OrdemAssistencia(
        dispositivo_id=d1.id, fornecedor_id=f1.id, colaborador_id=c2.id,
        data_envio=date.today() - timedelta(days=16), defeito="Tela trincada após queda",
        status="em_reparo", valor_orcado=380.0
    )
    os2 = OrdemAssistencia(
        dispositivo_id=d2.id, fornecedor_id=f2.id, colaborador_id=c3.id,
        data_envio=date.today() - timedelta(days=40), defeito="Não carrega / conector oxidado",
        status="devolvido", valor_orcado=160.0, valor_final=160.0,
        causa="desgaste_natural", responsavel_custo="empresa", valor_empresa=160.0,
        valor_colaborador=0.0, data_retorno=date.today() - timedelta(days=32),
        garantia_ate=date.today() + timedelta(days=58)
    )
    db.session.add_all([os1, os2])
    db.session.flush()

    # Acessórios
    a1 = Acessorio(nome="Película Vidro Galaxy A15", categoria="Pelicula", compatibilidade="Samsung A15", estoque_atual=2, estoque_minimo=5, custo_medio=8.50)
    a2 = Acessorio(nome="Capa Anti-Impacto Moto G34", categoria="Capa", compatibilidade="Moto G34", estoque_atual=8, estoque_minimo=4, custo_medio=12.00)
    a3 = Acessorio(nome="Carregador Rápido Tipo-C 20W", categoria="Carregador", compatibilidade="Universal Tipo-C", estoque_atual=1, estoque_minimo=3, custo_medio=35.00)
    a4 = Acessorio(nome="Cabo USB-C Reforçado 1.5m", categoria="Cabo", compatibilidade="Universal Tipo-C", estoque_atual=12, estoque_minimo=6, custo_medio=15.00)
    db.session.add_all([a1, a2, a3, a4])

    db.session.commit()
    flash("Dados de exemplo carregados com sucesso! Você já pode navegar e testar todas as funções.", "success")
    return redirect(url_for('index'))


# Cria as tabelas na inicialização
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    import webbrowser
    import threading

    def abrir_navegador():
        webbrowser.open_new('http://127.0.0.1:5000')

    # Abre o navegador automaticamente apenas na primeira carga
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.2, abrir_navegador).start()

    app.run(debug=True, port=5000)
