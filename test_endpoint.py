"""
Teste direto do endpoint de reconhecimento
"""

import requests
import base64
import json

def create_test_image():
    """Criar imagem de teste simples"""
    # Imagem 1x1 pixel transparente em base64
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def test_recognition_endpoint():
    """Testar endpoint de reconhecimento"""
    
    url = "http://localhost:5000/api/process_frame"
    
    # Dados para enviar
    data = {
        "image": create_test_image()
    }
    
    try:
        print("=== TESTE DO ENDPOINT /api/process_frame ===")
        print(f"URL: {url}")
        print(f"Enviando dados: {len(json.dumps(data))} bytes")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("Resposta:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Erro HTTP: {response.status_code}")
            print(f"Texto: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao servidor")
        print("Verifique se o Flask está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    test_recognition_endpoint()