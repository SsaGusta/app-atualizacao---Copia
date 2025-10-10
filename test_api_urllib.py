#!/usr/bin/env python3
"""
Teste da API usando urllib em vez de requests
"""

import json
import urllib.request
import urllib.parse
from gesture_manager import GestureManager

def test_api_with_urllib():
    print("🧪 Testando API de reconhecimento com urllib...")
    
    gm = GestureManager()
    gesture_a = gm.get_gesture('A')
    
    if gesture_a:
        landmarks = gesture_a['landmarks']
        print(f"✅ Gesto A encontrado com {len(landmarks)} landmarks")
        
        # Preparar dados
        url = 'http://127.0.0.1:5000/api/recognize_gesture'
        data = {'landmarks': landmarks}
        json_data = json.dumps(data).encode('utf-8')
        
        try:
            print("📡 Enviando requisição para API...")
            
            # Criar requisição
            request = urllib.request.Request(
                url, 
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Fazer requisição
            with urllib.request.urlopen(request, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                
                print(f"📊 Status: {response.status}")
                print("✅ Resposta da API:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if result.get('success') and result.get('result'):
                    detected_letter = result['result']['letter']
                    similarity = result['result']['similarity']
                    print(f"🎯 Letra detectada: {detected_letter}")
                    print(f"📈 Similaridade: {similarity:.3f}")
                    
                    if detected_letter == 'A':
                        print("✅ TESTE PASSOU - API reconheceu corretamente!")
                        return True
                    else:
                        print(f"❌ TESTE FALHOU - Esperado 'A', obtido '{detected_letter}'")
                        return False
                else:
                    print("❌ TESTE FALHOU - API não reconheceu nenhuma letra")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False
    else:
        print("❌ Gesto A não encontrado no banco de dados")
        return False

if __name__ == "__main__":
    success = test_api_with_urllib()
    print(f"\n{'='*50}")
    print(f"RESULTADO FINAL: {'SUCESSO' if success else 'FALHOU'}")
    print(f"{'='*50}")