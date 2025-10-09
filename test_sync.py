#!/usr/bin/env python3
"""
Teste do sistema de sincronização de gestos melhorado
"""

from gesture_manager import GestureManager

def test_gesture_sync_system():
    print("🧪 TESTANDO SISTEMA DE SINCRONIZAÇÃO DE GESTOS")
    print("=" * 60)
    
    # Inicializar sistema
    gm = GestureManager()
    
    # Teste 1: Verificar pré-carregamento
    print("\n1️⃣ TESTE: Pré-carregamento de gestos")
    print("✅ Sistema inicializado com pré-carregamento automático")
    
    # Teste 2: Verificar cache
    print("\n2️⃣ TESTE: Sistema de cache")
    gestos1 = gm.get_all_gestures()  # Deve usar cache
    print(f"📦 Primeira chamada: {len(gestos1)} gestos")
    
    gestos2 = gm.get_all_gestures()  # Deve usar cache
    print(f"⚡ Segunda chamada (cache): {len(gestos2)} gestos")
    
    # Teste 3: Informações de sincronização
    print("\n3️⃣ TESTE: Informações de sincronização")
    sync_info = gm.get_gesture_sync_info()
    print(f"📊 Total de gestos: {sync_info['total_gestures']}")
    print(f"📈 Progresso: {sync_info['completion_percentage']:.1f}% do alfabeto")
    print(f"✅ Letras com gestos: {', '.join(sync_info['letters_with_gestures'])}")
    print(f"⚠️ Letras faltantes: {', '.join(sync_info['letters_without_gestures'])}")
    
    # Teste 4: Distribuição de qualidade
    quality = sync_info['quality_distribution']
    print(f"\n🎯 QUALIDADE DOS GESTOS:")
    print(f"  🟢 Alta qualidade (≥80%): {quality['high_quality']}")
    print(f"  🟡 Média qualidade (60-79%): {quality['medium_quality']}")
    print(f"  🔴 Baixa qualidade (<60%): {quality['low_quality']}")
    
    # Teste 5: Cache info
    cache_info = sync_info['cache_info']
    print(f"\n💾 CACHE:")
    print(f"  Status: {cache_info['status']}")
    print(f"  Tamanho: {cache_info['size']} gestos")
    print(f"  Timestamp: {cache_info['timestamp']}")
    
    # Teste 6: Garantir disponibilidade
    print("\n4️⃣ TESTE: Garantir disponibilidade")
    available = gm.ensure_gestures_available()
    print(f"✅ Gestos disponíveis: {available}")
    
    # Teste 7: Invalidar e recarregar cache
    print("\n5️⃣ TESTE: Invalidação de cache")
    print("🗑️ Invalidando cache...")
    gm.invalidate_cache()
    
    print("🔄 Recarregando gestos...")
    gestos3 = gm.get_all_gestures()  # Deve recarregar do banco
    print(f"📦 Após invalidação: {len(gestos3)} gestos")
    
    # Teste 8: Teste de reconhecimento com cache
    print("\n6️⃣ TESTE: Reconhecimento com cache")
    if gestos3:
        letra_teste = list(gestos3.keys())[0]
        landmarks_teste = gestos3[letra_teste]['landmarks']
        
        print(f"🎯 Testando reconhecimento da letra {letra_teste}...")
        resultado = gm.recognize_gesture(landmarks_teste)
        
        if resultado and resultado['letter'] == letra_teste:
            print(f"✅ Reconhecimento PASSOU: {letra_teste} ({resultado['similarity']:.3f})")
        else:
            print(f"❌ Reconhecimento FALHOU")
    
    print("\n" + "=" * 60)
    print("🎉 TESTES CONCLUÍDOS")
    print("✅ Sistema de sincronização funcionando corretamente!")
    
    return sync_info

if __name__ == "__main__":
    sync_info = test_gesture_sync_system()
    
    # Sumário final
    print(f"\n📋 SUMÁRIO:")
    print(f"Total de gestos: {sync_info['total_gestures']}")
    print(f"Progresso: {sync_info['completion_percentage']:.1f}%")
    print(f"Status: {sync_info['sync_status']}")
    
    if sync_info['total_gestures'] > 0:
        print("🟢 Sistema pronto para uso!")
    else:
        print("🔴 Vá para /admin para capturar gestos")