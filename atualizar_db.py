import sqlite3
import os

print("🕵️  Iniciando busca profunda pelo banco de dados correto...")

banco_encontrado = False

# Percorre todas as pastas e subpastas do projeto
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".db") or file.endswith(".sqlite"):
            caminho_completo = os.path.join(root, file)
            
            # Ignora arquivos de ambiente virtual e do python
            # (CORRIGIDO AQUI: "caminho_completo")
            if "venv" in caminho_completo or "pythoncore" in caminho_completo:
                continue

            print(f"\n📂 Analisando arquivo: {caminho_completo}")
            
            try:
                conn = sqlite3.connect(caminho_completo)
                cursor = conn.cursor()
                
                # Verifica se a tabela 'produto' existe neste arquivo
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produto';")
                if cursor.fetchone():
                    print(f"   ✅ Tabela 'produto' ENCONTRADA neste arquivo!")
                    print("   🛠️  Atualizando...")
                    
                    try:
                        cursor.execute("ALTER TABLE produto ADD COLUMN link_mapa VARCHAR(500)")
                        conn.commit()
                        print("   🚀 SUCESSO! Coluna 'link_mapa' adicionada.")
                        banco_encontrado = True
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print("   ⚠️  AVISO: A coluna 'link_mapa' já existia aqui. Tudo certo.")
                            banco_encontrado = True
                        else:
                            print(f"   ❌ Erro ao alterar tabela: {e}")
                else:
                    print(f"   ❌ Este arquivo não é o correto (não tem a tabela de produtos).")
                
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️  Não consegui ler este arquivo: {e}")

print("\n" + "="*50)
if banco_encontrado:
    print("🎉 PRONTO! O banco de dados foi atualizado. Pode rodar o site!")
else:
    print("😱 ERRO: Não achei nenhum banco com a tabela 'produto'.")