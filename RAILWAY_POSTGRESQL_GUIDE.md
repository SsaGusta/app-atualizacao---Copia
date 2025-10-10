# 🚀 GUIA DE DEPLOY - RAILWAY COM POSTGRESQL

## ❌ **PROBLEMA IDENTIFICADO**

O Railway usa **sistema de arquivos efêmero** + problemas de build:
- ✅ **Local**: Bancos SQLite funcionam perfeitamente
- ❌ **Railway**: Arquivos `.db` são perdidos a cada restart/redeploy
- ⚠️ **Build Error**: Python 3.12 sem distutils causa falhas
- 🔄 **Resultado**: Dados salvos desaparecem + deploy falha

## ✅ **SOLUÇÃO: POSTGRESQL + BUILD FIX**

### **Passo 1: Configurar PostgreSQL no Railway**

1. **Acesse o Railway Dashboard**
   - Entre em https://railway.app
   - Vá para seu projeto

2. **Adicionar PostgreSQL**
   ```
   New → Database → Add PostgreSQL
   ```

3. **Obter URL de Conexão**
   - Vá na aba PostgreSQL criada
   - Copie a `DATABASE_URL` das variáveis

### **Passo 2: Configurar Variáveis de Ambiente**

No Railway, adicione:
```
DATABASE_URL=postgresql://user:password@host:port/database
RAILWAY_ENVIRONMENT=production
PYTHON_VERSION=3.11.6
```

### **Passo 3: Fix de Build - Requirements Simplificado**

⚠️ **PROBLEMA**: scikit-learn + numpy causam erro de build no Railway  
✅ **SOLUÇÃO**: Deploy em 2 fases

**Fase 1 - Deploy Básico (Funcional):**
```
# requirements.txt (atual - apenas essenciais)
Flask==2.3.3
Flask-Session==0.5.0
Flask-CORS==4.0.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
psycopg2-binary==2.9.7
```

**Fase 2 - ML Opcional (se necessário):**
```
# requirements_full.txt (com ML)
+ scikit-learn==1.3.0
+ joblib==1.3.2
+ numpy==1.24.3
+ Pillow==10.0.0
```

### **Passo 4: Deploy Imediato**

✅ **Status atual**: App funcional sem ML
- ✅ Reconhecimento tradicional de gestos
- ✅ PostgreSQL para persistência
- ✅ Todos os jogos funcionando
- ⏸️ ML desabilitado temporariamente

**Deploy agora:**
```bash
git add .
git commit -m "Fix Railway build - PostgreSQL + simplified requirements"
git push
```

### **Passo 5: Verificar Deploy**

1. **Logs do Railway**
   - ✅ Build successful
   - ✅ `🚀 Usando PostgreSQL (Produção)`
   - ⚠️ `Aviso: Sistema de ML não disponível`

2. **Testar Funcionalidades**
   - ✅ Capturar gestos no admin
   - ✅ Jogar no modo Desafio
   - ✅ Verificar se dados persistem após restart

## 🔄 **COMO FUNCIONA**

### **Detecção Automática de Ambiente:**
```python
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL')

if IS_PRODUCTION:
    # 🚀 PostgreSQL (Railway)
    from database_postgres import LibrasPostgresDatabase as LibrasDatabase
else:
    # 🏠 SQLite (Local)
    from database import LibrasDatabase
```

### **Compatibilidade Total:**
- **Local**: Continua usando SQLite (sem mudanças)
- **Railway**: Automaticamente usa PostgreSQL
- **API**: Mesma interface, zero mudanças no frontend

## 🎯 **VANTAGENS DA SOLUÇÃO**

✅ **Persistência**: Dados nunca mais serão perdidos  
✅ **Performance**: PostgreSQL é mais rápido que SQLite  
✅ **Escalabilidade**: Suporta mais usuários simultâneos  
✅ **Backup**: Railway faz backup automático  
✅ **Zero Breaking Changes**: Frontend continua igual  

## 🛠 **TROUBLESHOOTING**

### **Erro: "DATABASE_URL not found"**
```bash
# Verificar variáveis no Railway
echo $DATABASE_URL
```

### **Erro: "psycopg2 not found"**
```bash
# Verificar requirements.txt
grep psycopg2 requirements.txt
```

### **Erro: "Connection refused"**
- Verificar se PostgreSQL está ativo no Railway
- Verificar se URL está correta

### **Migração de Dados (se necessário)**
```python
# Script para migrar dados SQLite → PostgreSQL
python migrate_data.py
```

## 📊 **MONITORAMENTO**

### **Verificar Status:**
```python
# No console do Railway ou logs
print("🚀 PostgreSQL ativo" if IS_PRODUCTION else "🏠 SQLite local")
```

### **Verificar Dados:**
```sql
-- No PostgreSQL (Railway)
SELECT COUNT(*) FROM gestures;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM challenge_results;
```

## 🎉 **RESULTADO FINAL**

- ✅ **Local**: Desenvolvimento com SQLite (rápido)
- ✅ **Railway**: Produção com PostgreSQL (persistente)
- ✅ **Dados**: Nunca mais perdidos
- ✅ **Performance**: Melhorada significativamente
- ✅ **Zero Downtime**: Deploy sem interrupção