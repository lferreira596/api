import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta

DB_NAME = "delivery.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS pedidos")

    cursor.execute("""
    CREATE TABLE pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        cidade TEXT,
        bairro TEXT,
        produto TEXT,
        categoria TEXT,
        data_pedido DATE,
        valor_total REAL,
        tempo_entrega INTEGER,
        quantidade INTEGER,
        custo_unitario REAL,
        forma_pagamento TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_sample_data(n=3000):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    faker = Faker("pt_BR")

    produtos = [
        ("Pizza Calabresa", "Pizza", 34.00, 16.00),
        ("Pizza Marguerita", "Pizza", 36.00, 18.00),
        ("Pizza Portuguesa", "Pizza", 38.00, 20.00),
        ("Hambúrguer Duplo", "Lanche", 45.00, 15.00),
        ("Combo Burguer + Refri", "Lanche", 55.00, 18.00),
        ("Coca-Cola 2L", "Bebida", 10.00, 4.00),
        ("Pizza Quatro Queijos", "Pizza", 36.00, 18.00),
        ("Esfirra de Carne", "Lanche", 28.00, 12.00),
        ("Água com Gás", "Bebida", 5.00, 1.50),
        ("Suco Natural", "Bebida", 12.00, 3.00)
    ]

    cidades_bairros = {
        "São Paulo": ["Moema", "Pinheiros", "Vila Mariana", "Tatuapé", "Itaim Bibi"],
        "Rio de Janeiro": ["Copacabana", "Barra", "Tijuca", "Leblon", "Botafogo"],
        "Belo Horizonte": ["Savassi", "Centro", "Pampulha", "Funcionários", "Serra"]
    }

    pagamentos = ["Cartão", "Pix", "Dinheiro"]
    base_date = datetime.strptime("2024-02-01", "%Y-%m-%d")

    for _ in range(n):
        cliente = faker.name()
        cidade = random.choice(list(cidades_bairros.keys()))
        bairro = random.choice(cidades_bairros[cidade])
        produto, categoria, preco, custo = random.choice(produtos)
        quantidade = random.randint(1, 5)
        valor_total = round(preco * quantidade, 2)
        tempo_entrega = random.randint(20, 80)
        data_pedido = base_date + timedelta(days=random.randint(0, 89))
        forma_pagamento = random.choice(pagamentos)

        cursor.execute("""
            INSERT INTO pedidos (cliente, cidade, bairro, produto, categoria, data_pedido,
                                 valor_total, tempo_entrega, quantidade, custo_unitario, forma_pagamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente, cidade, bairro, produto, categoria, data_pedido.strftime("%Y-%m-%d"),
            valor_total, tempo_entrega, quantidade, custo, forma_pagamento
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    insert_sample_data()
    print("✅ Banco 'delivery.db' com 3.000 pedidos criado com sucesso!")
