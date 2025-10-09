#!/usr/bin/env python3
"""
Verificar estado do banco de dados de gestos
"""

from gesture_manager import GestureManager
import sqlite3

def verificar_banco():
    print('=== GESTOS NO BANCO DE DADOS ===')
    
    # Verificar gestos
    gm = GestureManager()
    gestos = gm.get_all_gestures()
    print(f'Total de gestos: {len(gestos)}')
    
    if gestos:
        print('\nGestos salvos:')
        for letra, dados in gestos.items():
            print(f'  Letra {letra}: qualidade {dados["quality"]}%, criado em {dados["created_at"]}')
    else:
        print('⚠️ Nenhum gesto encontrado no banco!')
    
    # Verificar estrutura do banco
    print('\n=== ESTRUTURA DO BANCO ===')
    conn = sqlite3.connect('gestures.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tabelas = cursor.fetchall()
    print('Tabelas:', [t[0] for t in tabelas])
    
    cursor.execute('PRAGMA table_info(gestures)')
    colunas = cursor.fetchall()
    print('\nColunas da tabela gestures:')
    for col in colunas:
        print(f'  {col[1]} ({col[2]})')
    
    # Verificar registros na tabela
    cursor.execute('SELECT COUNT(*) FROM gestures')
    total = cursor.fetchone()[0]
    print(f'\nTotal de registros na tabela: {total}')
    
    # Verificar detalhes dos registros
    cursor.execute('SELECT letter, quality, created_at FROM gestures ORDER BY letter')
    registros = cursor.fetchall()
    print('\nDetalhes dos registros:')
    for reg in registros:
        print(f'  {reg[0]}: qualidade {reg[1]}%, {reg[2]}')
    
    conn.close()

if __name__ == "__main__":
    verificar_banco()