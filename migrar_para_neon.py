"""
Copia o banco LOCAL (SQLite) para o Postgres (Neon): cabos, projetos e seções de projeto.

Uso (PowerShell):
    $env:DATABASE_URL = "postgresql://usuario:senha@host/neondb?sslmode=require"
    python migrar_para_neon.py                 # origem padrão: ./bk_lt.db
    python migrar_para_neon.py outro.db        # outra origem
    python migrar_para_neon.py --so-testar     # só testa a conexão e mostra as contagens

- Cria as tabelas no destino se não existirem.
- Idempotente: cabos por 'codigo' (atualiza), projetos por (nome, numero, revisao); seções são substituídas.
- Não grava a senha em nenhum arquivo.
"""
import os
import sys
from pathlib import Path

import sqlalchemy as sa

import db


def contagens(eng):
    with eng.connect() as c:
        return {t.name: c.execute(sa.select(sa.func.count()).select_from(t)).scalar_one() for t in (db.cabos, db.projetos, db.projeto_secoes)}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    destino = db.get_engine()
    if destino.dialect.name == "sqlite":
        sys.exit("DATABASE_URL não aponta para Postgres. Defina DATABASE_URL antes de rodar.")
    print("Destino:", db.descricao_banco(), contagens(destino))
    if "--so-testar" in sys.argv:
        return
    origem_arq = Path(args[0]) if args else Path(__file__).resolve().parent / "bk_lt.db"
    if not origem_arq.exists():
        sys.exit(f"Origem não encontrada: {origem_arq}")
    origem = sa.create_engine(f"sqlite:///{origem_arq}", future=True)
    print("Origem :", origem_arq.name, contagens(origem))
    with origem.connect() as o, destino.begin() as d:
        # cabos (por código)
        for r in o.execute(sa.select(db.cabos)).mappings():
            row = {k: v for k, v in r.items() if k != "id"}
            ex = d.execute(sa.select(db.cabos.c.id).where(db.cabos.c.codigo == row["codigo"])).first()
            if ex:
                d.execute(sa.update(db.cabos).where(db.cabos.c.id == ex[0]).values(**row))
            else:
                d.execute(sa.insert(db.cabos).values(**row))
        # projetos + seções
        for p in o.execute(sa.select(db.projetos)).mappings():
            row = {k: v for k, v in p.items() if k != "id"}
            cond = sa.and_(db.projetos.c.nome == row["nome"], db.projetos.c.numero == row["numero"], db.projetos.c.revisao == row["revisao"])
            ex = d.execute(sa.select(db.projetos.c.id).where(cond)).first()
            if ex:
                pid = ex[0]
                d.execute(sa.update(db.projetos).where(db.projetos.c.id == pid).values(**row))
            else:
                pid = d.execute(sa.insert(db.projetos).values(**row)).inserted_primary_key[0]
            d.execute(sa.delete(db.projeto_secoes).where(db.projeto_secoes.c.projeto_id == pid))
            for s in o.execute(sa.select(db.projeto_secoes).where(db.projeto_secoes.c.projeto_id == p["id"])).mappings():
                d.execute(sa.insert(db.projeto_secoes).values(projeto_id=pid, secao=s["secao"], dados=s["dados"], atualizado_em=s["atualizado_em"]))
    print("Migração concluída:", contagens(destino))


if __name__ == "__main__":
    main()
