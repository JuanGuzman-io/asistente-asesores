import sqlite3
import sys

c = sqlite3.connect(":memory:")
print("python", sys.version.split()[0], "sqlite", sqlite3.sqlite_version)
c.execute("create virtual table t using fts5(x, tokenize='unicode61 remove_diacritics 2')")
c.execute("insert into t values (?)", ("Crédito Productivo Impulso",))
print("fts5 credito ->", c.execute("select count(*) from t where t match ?", ('"credito"',)).fetchone()[0])
print("fts5 CRÉDITO ->", c.execute("select count(*) from t where t match ?", ('"CRÉDITO"',)).fetchone()[0])
