# 🔧 Guia de Solução de Problemas - Libras Learning

## ❌ Problema: "Erro de conexão. Tente novamente."

Este erro pode ocorrer por várias razões. Vamos resolver passo a passo:

### 1. ✅ Verificar se o servidor está rodando

**Passo 1: Abrir terminal/prompt de comando**
```bash
cd "c:\Users\Gusta\Documents\app atualizacao - Copia"
python teste_simples.py
```

**O que deve aparecer:**
```
🚀 Iniciando Libras Learning - Teste
📍 Acesse: http://127.0.0.1:5000
🔍 Para parar: Ctrl+C
* Running on http://127.0.0.1:5000
```

### 2. 🌐 Verificar acesso pelo navegador

**Teste 1: Acesso local**
- Abrir navegador
- Ir para: `http://127.0.0.1:5000`
- Deve aparecer página de teste

**Teste 2: Acesso pela rede**
- Ir para: `http://192.168.15.3:5000`
- Outras pessoas na mesma rede podem acessar

### 3. 🔍 Possíveis causas e soluções

#### 🔥 **Firewall/Antivírus bloqueando**
**Solução:**
1. Permitir Python/Flask no Firewall do Windows
2. Adicionar exceção no antivírus
3. Temporariamente desabilitar firewall para teste

#### 🌐 **Problemas de rede**
**Solução:**
1. Verificar se está conectado à internet
2. Tentar acessar: `http://localhost:5000` 
3. Verificar se porta 5000 não está em uso

#### 🔄 **Cache do navegador**
**Solução:**
1. Pressionar `Ctrl + F5` para recarregar
2. Limpar cache do navegador
3. Tentar em modo incógnito/privado
4. Tentar em outro navegador

#### 📱 **JavaScript desabilitado**
**Solução:**
1. Habilitar JavaScript no navegador
2. Verificar se não há bloqueadores de script
3. Desabilitar extensões temporariamente

#### 🚫 **Porta em uso**
**Solução:**
1. Fechar outros programas que podem usar porta 5000
2. Mudar porta no código para 5001:
   ```python
   app.run(host='0.0.0.0', port=5001, debug=True)
   ```

### 4. 🧪 Testes de diagnóstico

**Executar diagnóstico completo:**
```bash
python diagnostico.py
```

**Teste rápido de conectividade:**
```bash
# PowerShell
Test-NetConnection -ComputerName 127.0.0.1 -Port 5000

# Ou testar com:
telnet 127.0.0.1 5000
```

### 5. 🛠️ Soluções por ambiente

#### 💻 **Windows**
```bash
# Verificar porta
netstat -an | findstr :5000

# Liberar porta no firewall
netsh advfirewall firewall add rule name="Libras App" dir=in action=allow protocol=TCP localport=5000
```

#### 🌐 **Hospedagem online (Heroku, Railway, etc.)**
1. Verificar se deploy foi feito corretamente
2. Verificar logs do servidor
3. Verificar se domínio está correto
4. Verificar se HTTPS está configurado

### 6. 🔧 Reinstalação limpa

Se nada funcionar, faça uma reinstalação limpa:

```bash
# 1. Criar nova pasta
mkdir libras_novo
cd libras_novo

# 2. Copiar apenas arquivos essenciais
copy ..\app.py .
copy ..\database.py .
copy ..\palavras.py .
copy ..\requirements.txt .

# 3. Reinstalar dependências
pip install -r requirements.txt

# 4. Testar
python app.py
```

### 7. 📞 Suporte adicional

Se o problema persistir:

1. **Verificar logs:** Olhar mensagens de erro no terminal
2. **Testar em outra máquina:** Para verificar se é problema local
3. **Verificar versão Python:** `python --version` (deve ser 3.8+)
4. **Reinstalar Python:** Se necessário

### 8. 🚀 Deploy para acesso externo

Para acessar de qualquer lugar:

#### **Opção 1: ngrok (mais fácil)**
```bash
# Instalar ngrok
# Em outro terminal:
ngrok http 5000
# Copiar URL fornecida (ex: https://abc123.ngrok.io)
```

#### **Opção 2: Heroku**
```bash
# Instalar Heroku CLI
heroku create seu-app-libras
git init
git add .
git commit -m "Deploy inicial"
git push heroku main
```

#### **Opção 3: Railway**
1. Ir para https://railway.app
2. Conectar repositório GitHub
3. Deploy automático

### 9. ✅ Verificação final

Quando tudo estiver funcionando, você deve conseguir:

- [x] Acessar http://127.0.0.1:5000
- [x] Ver página inicial carregando
- [x] Fazer login com qualquer nome
- [x] Acessar página do jogo
- [x] Permitir acesso à câmera
- [x] Ver vídeo da câmera funcionando

---

## 🆘 **SOLUÇÃO RÁPIDA PARA TESTAR AGORA:**

1. **Abrir PowerShell/CMD**
2. **Executar:**
   ```bash
   cd "c:\Users\Gusta\Documents\app atualizacao - Copia"
   python teste_simples.py
   ```
3. **Abrir navegador em:** `http://127.0.0.1:5000`
4. **Se funcionar, o problema está resolvido!**

---

**💡 Dica:** O arquivo `teste_simples.py` é uma versão minimalista que sempre funciona. Use-o para verificar se o problema é de configuração ou de ambiente.