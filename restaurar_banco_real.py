"""
Script para restaurar o banco de dados real de produção.
Restaura os dados originais a partir de backups_banco/consertcell_PRODUCAO_REAL.db
e garante a integridade da tabela admin_users para autenticação contínua.
"""
import os
import shutil
import sqlite3

backup_source = os.path.abspath('backups_banco/consertcell_PRODUCAO_REAL.db')
target_db = os.path.abspath('instance/consertcell.db')

if not os.path.exists(backup_source):
    print(f"ERRO: Arquivo de backup não encontrado em: {backup_source}")
    exit(1)

# Se já houver um admin configurado atualmente, preserva para não perder alterações de senha/perfil
admin_atual = None
if os.path.exists(target_db):
    try:
        con_curr = sqlite3.connect(target_db)
        cur_curr = con_curr.cursor()
        t_exists = cur_curr.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='admin_users'").fetchone()
        if t_exists:
            admin_atual = cur_curr.execute("SELECT email, nome, senha_hash, token_api, lembrar_token, ultimo_login, ativo FROM admin_users LIMIT 1").fetchone()
        con_curr.close()
    except Exception:
        pass

print(f"-> Restaurando banco real a partir de: {backup_source}")
os.makedirs(os.path.dirname(target_db), exist_ok=True)
shutil.copy2(backup_source, target_db)
print(f"-> Arquivo copiado com sucesso para: {target_db} ({os.path.getsize(target_db)} bytes)")

# Executa db.create_all() via app Flask para garantir que a tabela admin_users exista no banco restaurado
from app import app, db, garantir_usuario_admin
with app.app_context():
    db.create_all()
    if admin_atual:
        from models import AdminUser
        existente = AdminUser.query.first()
        if not existente:
            novo = AdminUser(
                email=admin_atual[0],
                nome=admin_atual[1],
                senha_hash=admin_atual[2],
                token_api=admin_atual[3],
                lembrar_token=admin_atual[4],
                ativo=bool(admin_atual[6])
            )
            db.session.add(novo)
            db.session.commit()
            print(f"-> Usuário Admin restaurado: {novo.email} ({novo.nome})")
        else:
            print(f"-> Usuário Admin confirmado: {existente.email}")
    else:
        garantir_usuario_admin()

# Exibe conferência completa de tabelas e registros
con = sqlite3.connect(target_db)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if not r[0].startswith('sqlite_')]
print("\n" + "="*50)
print("  BASE DE DADOS ORIGINAL DE PRODUÇÃO RESTAURADA")
print("="*50)
for t in sorted(tables):
    c = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f" • {t.ljust(22)}: {c} registros")
con.close()

print("="*50)
print("Status: Pronto para uso operacional na Ambev Disfonte!")
print("="*50 + "\n")
