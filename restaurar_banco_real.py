"""
Script para restaurar o banco de dados real de produção.
Copia backups_banco/consertcell_PRODUCAO_REAL.db de volta para instance/consertcell.db.
"""
import os
import shutil
import sqlite3

backup_source = os.path.abspath('backups_banco/consertcell_PRODUCAO_REAL.db')
target_db = os.path.abspath('instance/consertcell.db')

if not os.path.exists(backup_source):
    print(f"ERRO: Arquivo de backup não encontrado em: {backup_source}")
    exit(1)

print(f"Restaurando banco real a partir de: {backup_source}")
shutil.copy2(backup_source, target_db)
print(f"Banco real restaurado com sucesso em: {target_db} ({os.path.getsize(target_db)} bytes)")

# Exibe conferência de registros
con = sqlite3.connect(target_db)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if not r[0].startswith('sqlite_')]
print("\nRegistros restaurados:")
for t in tables:
    c = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f" - {t}: {c}")
con.close()
print("\nPronto! O sistema está de volta com seus dados reais de produção.")
