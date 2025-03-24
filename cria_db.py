import sqlite3

DB_NAME = "delivery.db"

def create_database():
    """Cria o banco de dados SQLite e a tabela de pedidos de delivery."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            cidade TEXT NOT NULL,
            bairro TEXT NOT NULL,
            produto TEXT NOT NULL,
            valor_total REAL NOT NULL,
            tempo_entrega INTEGER NOT NULL,
            data_pedido TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_sample_data():
    """Insere alguns registros de pedidos no banco de dados."""
    pedidos = [
        ("João Silva", "São Paulo", "Moema", "Pizza Margherita", 42.90, 35, "2024-03-01"),
        ("Maria Oliveira", "São Paulo", "Pinheiros", "Hambúrguer Duplo", 38.50, 28, "2024-03-02"),
        ("Carlos Souza", "Rio de Janeiro", "Copacabana", "Sushi Combo", 65.00, 40, "2024-03-01"),
        ("Ana Martins", "Belo Horizonte", "Savassi", "Esfirra de Carne", 22.00, 20, "2024-03-03"),
        ("Pedro Santos", "São Paulo", "Vila Mariana", "Pizza Calabresa", 48.00, 30, "2024-03-02")
    ]
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.executemany('''
        INSERT INTO pedidos (cliente_nome, cidade, bairro, produto, valor_total, tempo_entrega, data_pedido)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', pedidos)
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    create_database()
    insert_sample_data()
    print("Banco de dados e registros de pedidos de delivery criados com sucesso!")
