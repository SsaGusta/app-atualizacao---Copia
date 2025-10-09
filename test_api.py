#!/usr/bin/env python3
"""
Teste da API de reconhecimento de gestos
"""

import requests
import json
from gesture_manager import GestureManager

def test_api():
    # Obter landmarks do gesto A salvo
    print("🧪 Testando API de reconhecimento...")
    
    gm = GestureManager()
    gesture_a = gm.get_gesture('A')
    
    if gesture_a:
        landmarks = gesture_a['landmarks']
        print(f"✅ Gesto A encontrado com {len(landmarks)} landmarks")
        
        # Testar API de reconhecimento
        url = 'http://127.0.0.1:5000/api/recognize_gesture'
        data = {'landmarks': landmarks}
        
        try:
            print("📡 Enviando requisição para API...")
            response = requests.post(url, json=data, timeout=10)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Resposta da API:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if result.get('success') and result.get('result'):
                    detected_letter = result['result']['letter']
                    similarity = result['result']['similarity']
                    print(f"🎯 Letra detectada: {detected_letter}")
                    print(f"📈 Similaridade: {similarity:.3f}")
                    
                    if detected_letter == 'A':
                        print("✅ TESTE PASSOU - API reconheceu corretamente!")
                    else:
                        print(f"❌ TESTE FALHOU - Esperado 'A', obtido '{detected_letter}'")
                else:
                    print("❌ TESTE FALHOU - API não reconheceu nenhuma letra")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Erro: Não foi possível conectar ao servidor. Certifique-se de que está rodando.")
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
    else:
        print("❌ Gesto A não encontrado no banco de dados")

if __name__ == "__main__":
    test_api()