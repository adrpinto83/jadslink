#!/usr/bin/env python3
"""
Migración: Agregar campos de tarjeta de crédito al modelo Account
"""
import sqlite3
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "hotspot.db"))

def migrate():
    """Agrega columnas de tarjeta de crédito a la tabla accounts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Lista de columnas a agregar
    columns_to_add = [
        ("card_last4", "TEXT DEFAULT ''"),
        ("card_brand", "TEXT DEFAULT ''"),
        ("card_exp_month", "TEXT DEFAULT ''"),
        ("card_exp_year", "TEXT DEFAULT ''"),
        ("cardholder_name", "TEXT DEFAULT ''"),
        ("stripe_customer_id", "TEXT DEFAULT ''"),
        ("stripe_payment_method_id", "TEXT DEFAULT ''"),
    ]

    # Verificar qué columnas ya existen
    cursor.execute("PRAGMA table_info(accounts)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Agregar solo las columnas que no existen
    for col_name, col_def in columns_to_add:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_def}")
                print(f"✓ Columna '{col_name}' agregada exitosamente")
            except sqlite3.OperationalError as e:
                print(f"✗ Error agregando columna '{col_name}': {e}")
        else:
            print(f"⊘ Columna '{col_name}' ya existe, omitiendo")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada")

if __name__ == "__main__":
    migrate()
