"""
Teste Final do Sistema LIBRAS
"""

import requests
import json
import os

def test_server_status():
    """Testar se o servidor está funcionando"""
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_recognition_endpoint():
    """Testar endpoint de reconhecimento"""
    try:
        # Teste com imagem vazia
        response = requests.post(
            "http://localhost:5000/api/process_frame",
            json={"image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('success') == False and 'mão' in data.get('error', '').lower()
        return False
    except:
        return False

def test_static_files():
    """Testar se arquivos estáticos estão acessíveis"""
    files_to_test = [
        "/static/js/camera.js",
        "/static/css/style.css"
    ]
    
    results = {}
    for file_path in files_to_test:
        try:
            response = requests.get(f"http://localhost:5000{file_path}", timeout=5)
            results[file_path] = response.status_code == 200
        except:
            results[file_path] = False
    
    return results

def check_files():
    """Verificar se arquivos importantes existem"""
    files = [
        "dados_libras.csv",
        "libras_model.pkl", 
        "libras_model_alt.pkl",
        "static/js/camera.js",
        "templates/game.html"
    ]
    
    results = {}
    for file_path in files:
        results[file_path] = os.path.exists(file_path)
    
    return results

def main():
    print("=== TESTE FINAL DO SISTEMA LIBRAS ===")
    
    # 1. Verificar arquivos
    print("\n1. Verificando arquivos...")
    file_results = check_files()
    for file_path, exists in file_results.items():
        status = "✓" if exists else "✗"
        print(f"   {status} {file_path}")
    
    # 2. Testar servidor
    print("\n2. Testando servidor...")
    if test_server_status():
        print("   ✓ Servidor Flask respondendo")
    else:
        print("   ✗ Servidor Flask não está respondendo")
        return
    
    # 3. Testar endpoint
    print("\n3. Testando endpoint de reconhecimento...")
    if test_recognition_endpoint():
        print("   ✓ Endpoint /api/process_frame funcionando")
    else:
        print("   ✗ Problema no endpoint /api/process_frame")
    
    # 4. Testar arquivos estáticos
    print("\n4. Testando arquivos estáticos...")
    static_results = test_static_files()
    for file_path, accessible in static_results.items():
        status = "✓" if accessible else "✗"
        print(f"   {status} {file_path}")
    
    print("\n=== INSTRUÇÕES DE USO ===")
    print("1. Acesse: http://localhost:5000")
    print("2. Clique em 'Iniciar Jogo' > 'Modo Normal'")
    print("3. Permita acesso à câmera")
    print("4. Clique em 'Testar Reconhecimento' para testar manualmente")
    print("5. Posicione sua mão fazendo uma letra LIBRAS")
    print("6. Verifique se aparece a letra reconhecida e o método usado")
    
    print("\n=== MELHORIAS IMPLEMENTADAS ===")
    print("✓ Sistema híbrido: MediaPipe + OpenCV")
    print("✓ Teste manual independente do jogo")
    print("✓ Feedback visual melhorado")
    print("✓ Logs detalhados com método usado")
    print("✓ Compatibilidade com hospedagem")

if __name__ == "__main__":
    main()