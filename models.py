from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# ==========================================
# MODELO DE AUTENTICAÇÃO (ADMIN ÚNICO)
# ==========================================
class AdminUser(UserMixin, db.Model):
    """Usuário administrador único do sistema TI Disfonte."""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False, default='Gabriel Nunes (Admin TI)')
    senha_hash = db.Column(db.String(256), nullable=False)
    token_api = db.Column(db.String(64), unique=True, nullable=True)
    lembrar_token = db.Column(db.String(256), nullable=True)  # para "lembrar de mim"
    ultimo_login = db.Column(db.DateTime, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'ultimo_login': self.ultimo_login.strftime('%d/%m/%Y %H:%M:%S') if self.ultimo_login else None,
            'ativo': self.ativo,
            'token_api': self.token_api
        }

    def __repr__(self):
        return f'<Admin {self.email}>'



class Colaborador(db.Model):
    __tablename__ = 'colaboradores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(50), nullable=False)
    matricula = db.Column(db.String(30), nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    dispositivos = db.relationship('Dispositivo', backref='colaborador', lazy=True)
    ordens = db.relationship('OrdemAssistencia', backref='colaborador', lazy=True)
    vales = db.relationship('Vale', backref='colaborador', lazy=True)
    saidas_acessorios = db.relationship('SaidaAcessorio', backref='colaborador', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Colaborador {self.nome} ({self.setor})>"


class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), default='assistencia')  # 'assistencia', 'loja', 'outro'
    contato = db.Column(db.String(100), nullable=True)
    cnpj = db.Column(db.String(25), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    ordens = db.relationship('OrdemAssistencia', backref='fornecedor', lazy=True)
    entradas_acessorios = db.relationship('EntradaAcessorio', backref='fornecedor', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Fornecedor {self.nome}>"


class Dispositivo(db.Model):
    __tablename__ = 'dispositivos'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), default='celular')  # 'celular', 'tablet'
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    imei = db.Column(db.String(50), unique=True, nullable=True)
    serial = db.Column(db.String(50), nullable=True)
    patrimonio = db.Column(db.String(50), nullable=True)
    data_aquisicao = db.Column(db.Date, nullable=True)
    valor_aquisicao = db.Column(db.Float, default=0.0)
    garantia_ate = db.Column(db.Date, nullable=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True)
    status = db.Column(db.String(20), default='em_uso')  # 'em_uso', 'em_estoque', 'na_assistencia', 'baixado'
    observacoes = db.Column(db.Text, nullable=True)

    ordens = db.relationship('OrdemAssistencia', backref='dispositivo', lazy=True)
    saidas_acessorios = db.relationship('SaidaAcessorio', backref='dispositivo', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def identificador(self):
        """Retorna IMEI se existir, senão Serial ou Patrimônio."""
        if self.imei:
            return f"IMEI: {self.imei}"
        if self.serial:
            return f"S/N: {self.serial}"
        if self.patrimonio:
            return f"Patrimônio: {self.patrimonio}"
        return f"ID #{self.id}"

    @property
    def custo_total_manutencao(self):
        """Soma de todos os custos de reparo já finalizados."""
        return sum(o.valor_final for o in self.ordens if o.status in ['devolvido', 'pronto'] and o.valor_final)

    @property
    def percentual_custo_aquisicao(self):
        """Percentual do custo de reparos em relação ao valor do aparelho."""
        if self.valor_aquisicao and self.valor_aquisicao > 0:
            return round((self.custo_total_manutencao / self.valor_aquisicao) * 100, 1)
        return 0.0

    @property
    def is_alerta_bomba(self):
        """Indica se os reparos já ultrapassaram 50% do valor do dispositivo."""
        return self.percentual_custo_aquisicao >= 50.0

    def __repr__(self):
        return f"<Dispositivo {self.marca} {self.modelo} - {self.identificador}>"


class OrdemAssistencia(db.Model):
    __tablename__ = 'ordens_assistencia'

    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivos.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True)
    data_envio = db.Column(db.Date, default=date.today, nullable=False)
    defeito = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='enviado') 
    # Status: 'enviado', 'em_analise', 'orcamento_aprovado', 'em_reparo', 'pronto', 'devolvido', 'sem_conserto'
    valor_orcado = db.Column(db.Float, default=0.0)
    valor_final = db.Column(db.Float, default=0.0)

    # Diagnóstico e Responsabilidade
    causa = db.Column(db.String(30), nullable=True)
    # Causas: 'defeito_fabricacao', 'desgaste_natural', 'mau_uso', 'acidente_queda', 'outro'
    laudo = db.Column(db.Text, nullable=True)
    responsavel_custo = db.Column(db.String(20), default='empresa') # 'empresa', 'colaborador', 'misto'
    valor_empresa = db.Column(db.Float, default=0.0)
    valor_colaborador = db.Column(db.Float, default=0.0)

    data_retorno = db.Column(db.Date, nullable=True)
    garantia_ate = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    # Relacionamento de Vale
    vale = db.relationship('Vale', backref='ordem', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def dias_fora(self):
        """Calcula há quantos dias o aparelho está na assistência ou quanto tempo ficou fora."""
        if not self.data_envio:
            return 0
        data_fim = self.data_retorno if self.data_retorno else date.today()
        return (data_fim - self.data_envio).days

    @property
    def is_aberta(self):
        return self.status not in ['devolvido', 'sem_conserto']

    @property
    def alerta_dias(self):
        """Retorna 'critico' se > 15 dias aberta, 'alerta' se > 7 dias, ou 'ok'."""
        if not self.is_aberta:
            return 'ok'
        dias = self.dias_fora
        if dias >= 15:
            return 'critico'
        if dias >= 7:
            return 'alerta'
        return 'ok'

    def __repr__(self):
        return f"<OS #{self.id} - Disp {self.dispositivo_id} - {self.status}>"


class Vale(db.Model):
    __tablename__ = 'vales'

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens_assistencia.id'), nullable=True)
    saida_acessorio_id = db.Column(db.Integer, db.ForeignKey('saidas_acessorio.id'), nullable=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False, default=0.0)
    data_emissao = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # 'pendente', 'emitido', 'descontado', 'cancelado'
    motivo = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Vale #{self.id} - Colab {self.colaborador_id} - R$ {self.valor}>"


class Acessorio(db.Model):
    __tablename__ = 'acessorios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), default='Geral') # 'Pelicula', 'Capa', 'Carregador', 'Cabo', 'Fone', 'Outro'
    compatibilidade = db.Column(db.String(100), nullable=True)
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=5)
    custo_medio = db.Column(db.Float, default=0.0)

    entradas = db.relationship('EntradaAcessorio', backref='acessorio', lazy=True)
    saidas = db.relationship('SaidaAcessorio', backref='acessorio', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_estoque_baixo(self):
        return self.estoque_atual <= self.estoque_minimo

    @property
    def valor_total_estoque(self):
        return round(self.estoque_atual * self.custo_medio, 2)

    def __repr__(self):
        return f"<Acessorio {self.nome} - Qtd: {self.estoque_atual}>"


class EntradaAcessorio(db.Model):
    __tablename__ = 'entradas_acessorio'

    id = db.Column(db.Integer, primary_key=True)
    acessorio_id = db.Column(db.Integer, db.ForeignKey('acessorios.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    custo_unitario = db.Column(db.Float, nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    nota_fiscal = db.Column(db.String(50), nullable=True)
    data = db.Column(db.Date, default=date.today, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SaidaAcessorio(db.Model):
    __tablename__ = 'saidas_acessorio'

    id = db.Column(db.Integer, primary_key=True)
    acessorio_id = db.Column(db.Integer, db.ForeignKey('acessorios.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivos.id'), nullable=True)
    motivo = db.Column(db.String(30), default='novo')  # 'novo', 'reposicao', 'quebra', 'perda'
    data = db.Column(db.Date, default=date.today, nullable=False)
    custo_no_momento = db.Column(db.Float, default=0.0)
    gerou_vale = db.Column(db.Boolean, default=False)

    vale = db.relationship('Vale', backref='saida_acessorio', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
