# 🚀 Guia de Deploy - Aplicação Libras Web

## 📋 Opções de Hospedagem

### 1. 🆓 **Railway** (Recomendado - Fácil e Gratuito)
- ✅ Deploy automático via GitHub
- ✅ 500h gratuitas por mês
- ✅ Suporte a Python/Flask
- ✅ Banco de dados incluído

### 2. 🆓 **Render** 
- ✅ 750h gratuitas por mês
- ✅ Deploy via GitHub
- ✅ SSL automático

### 3. 🆓 **Heroku** (Com limitações)
- ✅ Deploy via Git
- ✅ Addons disponíveis
- ⚠️ Limitações no plano gratuito

### 4. 💰 **DigitalOcean App Platform**
- ✅ Mais recursos
- ✅ Fácil escalabilidade
- 💰 A partir de $5/mês

---

## 🚀 Deploy no Railway (Recomendado)

### Passo 1: Preparar o Repositório Git
```bash
# Se não tem git inicializado
git init
git add .
git commit -m "Initial commit - Libras Web App"

# Criar repositório no GitHub (através da interface web)
# Depois conectar:
git remote add origin https://github.com/SEU_USUARIO/libras-web-app.git
git push -u origin main
```

### Passo 2: Deploy no Railway
1. Acesse: https://railway.app/
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha seu repositório
6. Railway detectará automaticamente que é uma aplicação Python

### Passo 3: Configurar Variáveis de Ambiente
No painel do Railway, vá em Variables e adicione:
```
FLASK_ENV=production
PORT=5000
```

---

## 🚀 Deploy no Render

### Passo 1: Criar conta e conectar GitHub
1. Acesse: https://render.com/
2. Faça login com GitHub
3. Clique em "New +" → "Web Service"
4. Conecte seu repositório

### Passo 2: Configurar o serviço
- **Name**: libras-web-app
- **Branch**: main
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

---

## 🚀 Deploy no Heroku

### Passo 1: Instalar Heroku CLI
```bash
# Download em: https://devcenter.heroku.com/articles/heroku-cli
```

### Passo 2: Deploy
```bash
# Login no Heroku
heroku login

# Criar aplicação
heroku create seu-app-libras

# Deploy
git push heroku main

# Abrir aplicação
heroku open
```

---

## 🐳 Deploy com Docker (Avançado)

### Para VPS (DigitalOcean, AWS, etc.)
```bash
# Build da imagem
docker build -t libras-web-app .

# Executar
docker run -p 80:5000 libras-web-app
```

### Com docker-compose
```bash
docker-compose up -d
```

---

## ⚙️ Configurações de Produção

### 1. Variáveis de Ambiente (.env)
```env
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_super_segura_aqui
DATABASE_URL=sqlite:///libras_stats.db
```

### 2. Domínio Personalizado
- Railway: Vá em Settings → Domains
- Render: Vá em Settings → Custom Domains
- Adicione seu domínio (ex: libras.seusite.com)

### 3. SSL/HTTPS
- ✅ Automático no Railway e Render
- ✅ Certificado gratuito

---

## 🔧 Troubleshooting

### Erro de Port
Se der erro de porta, certifique-se que o app.py use a variável PORT:
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

### Erro de Dependências
Verifique se o requirements.txt está atualizado:
```bash
pip freeze > requirements.txt
```

### Vídeos não carregam
Certifique-se que a pasta Videos/ está no repositório:
```bash
git add Videos/
git commit -m "Add demo videos"
```

---

## 📊 Monitoramento

### Logs
- Railway: Aba "Deployments" → Ver logs
- Render: Aba "Logs"
- Heroku: `heroku logs --tail`

### Performance
- Railway: Metrics automáticos
- Render: Analytics integrado

---

## 🎯 Próximos Passos

1. ✅ **Escolher plataforma** (Railway recomendado)
2. ✅ **Criar repositório Git**
3. ✅ **Fazer deploy**
4. ✅ **Configurar domínio** (opcional)
5. ✅ **Testar aplicação**

---

## 🆘 Suporte

Se precisar de ajuda:
1. Verifique os logs da plataforma
2. Teste localmente primeiro
3. Consulte a documentação da plataforma escolhida

**Sua aplicação estará acessível 24/7 na internet! 🌐**