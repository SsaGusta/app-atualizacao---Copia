# 🚀 GUIA DE DEPLOY - RAILWAY COM POSTGRESQL

## ❌ **PROBLEMA IDENTIFICADO**

O Railway usa **sistema de arquivos efêmero**:
- ✅ **Local**: Bancos SQLite funcionam perfeitamente
- ❌ **Railway**: Arquivos `.db` são perdidos a cada restart/redeploy
- 🔄 **Resultado**: Dados salvos desaparecem

## ✅ **SOLUÇÃO: POSTGRESQL**

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
```

### **Passo 3: Atualizar Código**

✅ **Arquivos já criados:**
- `database_postgres.py` - Database híbrido
- `gesture_manager_hybrid.py` - Gesture manager híbrido  
- `app_hybrid.py` - App que detecta ambiente automaticamente
- `requirements.txt` - Atualizado com psycopg2

### **Passo 4: Deploy**

1. **Substituir app.py**
   ```bash
   mv app.py app_sqlite.py
   mv app_hybrid.py app.py
   ```

2. **Substituir gesture_manager.py**
   ```bash
   mv gesture_manager.py gesture_manager_sqlite.py
   mv gesture_manager_hybrid.py gesture_manager.py
   ```

3. **Substituir database.py**
   ```bash
   mv database.py database_sqlite.py
   mv database_postgres.py database.py
   ```

4. **Commit e Push**
   ```bash
   git add .
   git commit -m "Add PostgreSQL support for Railway deploy"
   git push
   ```

### **Passo 5: Verificar Deploy**

1. **Logs do Railway**
   - Verifique se aparece: `🚀 Usando PostgreSQL (Produção)`
   - Sem erros de conexão

2. **Testar Funcionalidades**
   - Capturar gestos no admin
   - Jogar no modo Desafio
   - Verificar se dados persistem após restart

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