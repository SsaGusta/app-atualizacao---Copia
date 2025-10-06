# Libras Learning - Aplicação Web

Uma aplicação web moderna para aprendizado de Libras com reconhecimento de sinais em tempo real usando inteligência artificial.

## 📋 Características

- **Interface Web Responsiva**: Acesso através de qualquer navegador moderno
- **Reconhecimento em Tempo Real**: Usa MediaPipe e Machine Learning para reconhecer sinais
- **Diferentes Níveis**: Iniciante, intermediário, avançado e expert
- **Estatísticas Detalhadas**: Acompanhe seu progresso com gráficos e métricas
- **Sistema de Usuários**: Login simples sem necessidade de senha
- **Banco de Dados**: SQLite para armazenar estatísticas e progresso
- **Pronto para Produção**: Docker, Nginx e configurações de deploy incluídas

## 🚀 Instalação Rápida

### Usando Docker (Recomendado)

1. **Clone ou baixe o projeto**
   ```bash
   # Se for um repositório git:
   git clone <url-do-repositorio>
   cd libras-learning-web
   ```

2. **Execute com Docker**
   ```bash
   docker-compose up -d
   ```

3. **Acesse a aplicação**
   - Abra seu navegador em: http://localhost:5000

### Instalação Manual

1. **Pré-requisitos**
   - Python 3.11 ou superior
   - pip (gerenciador de pacotes Python)
   - Câmera/webcam

2. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar aplicação**
   ```bash
   python app.py
   ```

4. **Acessar**
   - Abra seu navegador em: http://localhost:5000

## 🌐 Hospedagem para Acesso Remoto

### Opção 1: Heroku (Gratuito/Pago)

1. **Criar conta no Heroku**: https://heroku.com
2. **Instalar Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli
3. **Deploy**:
   ```bash
   heroku create seu-app-libras
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

### Opção 2: DigitalOcean (Pago)

1. **Criar Droplet** com Ubuntu 22.04
2. **Instalar Docker**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose
   ```
3. **Fazer upload dos arquivos** e executar:
   ```bash
   docker-compose up -d
   ```

### Opção 3: Railway (Simples)

1. **Conta no Railway**: https://railway.app
2. **Conectar repositório GitHub**
3. **Deploy automático** ao fazer push

### Opção 4: Render (Gratuito)

1. **Conta no Render**: https://render.com
2. **Criar Web Service**
3. **Conectar repositório**
4. **Configurar**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

## 🔧 Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```env
SECRET_KEY=sua_chave_secreta_muito_forte
FLASK_ENV=production
DATABASE_URL=sqlite:///libras_stats.db
```

### Para Produção

1. **Altere a SECRET_KEY** no arquivo `.env`
2. **Configure SSL** se necessário
3. **Ajuste configurações** no `nginx.conf`
4. **Monitore logs** em produção

## 🎮 Como Usar

1. **Acesse a aplicação** no navegador
2. **Faça login** com qualquer nome de usuário
3. **Permita acesso à câmera** quando solicitado
4. **Escolha dificuldade** e clique em "Iniciar"
5. **Pratique os sinais** das letras mostradas
6. **Acompanhe estatísticas** na aba de relatórios

## 📱 Compatibilidade

### Navegadores Suportados
- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

### Dispositivos
- Desktop (Windows, Mac, Linux)
- Tablets (iPad, Android)
- Smartphones (com limitações de tela)

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
libras-learning-web/
├── app.py                 # Aplicação Flask principal
├── database.py            # Sistema de banco de dados
├── palavras.py           # Listas de palavras por dificuldade
├── reports.py            # Sistema de relatórios
├── templates/            # Templates HTML
├── static/              # CSS, JS, imagens
├── requirements.txt     # Dependências Python
├── Dockerfile          # Container Docker
├── docker-compose.yml  # Orquestração Docker
└── README.md          # Esta documentação
```

### Executar em Desenvolvimento
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Adicionar Novas Funcionalidades

1. **Backend**: Modifique `app.py` para novas rotas
2. **Frontend**: Adicione templates em `templates/`
3. **Estilos**: Modifique `static/css/style.css`
4. **JavaScript**: Adicione em `static/js/`

## 📊 Banco de Dados

A aplicação usa SQLite por padrão. Estrutura das tabelas:

- `users`: Usuários do sistema
- `game_sessions`: Sessões de jogo
- `practiced_words`: Palavras praticadas
- `letter_times`: Tempos por letra
- `letter_stats`: Estatísticas por letra

## 🔒 Segurança

### Recomendações de Produção

1. **Use HTTPS** sempre
2. **Configure firewall** adequadamente
3. **Mantenha dependências** atualizadas
4. **Monitore logs** regularmente
5. **Backup do banco** periodicamente

### Rate Limiting

O Nginx está configurado com rate limiting:
- 10 requisições por segundo por IP
- Burst de até 20 requisições

## 🐛 Troubleshooting

### Problemas Comuns

1. **Câmera não funciona**
   - Verifique permissões do navegador
   - Teste em HTTPS (obrigatório para câmera)
   - Verifique se outro app não está usando a câmera

2. **Erro de dependências**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Performance baixa**
   - Reduza resolução da câmera
   - Ajuste FPS no código
   - Use servidor com mais recursos

4. **Banco de dados locked**
   ```bash
   rm libras_stats.db
   # Reinicie a aplicação
   ```

## 📈 Performance

### Otimizações Implementadas

- **Processamento assíncrono** de frames
- **Rate limiting** de requisições
- **Cache de recursos** estáticos
- **Compressão gzip** via Nginx
- **Modelo ML otimizado** com menos estimadores

### Monitoramento

Logs disponíveis em:
- `/var/log/nginx/` (Nginx)
- Console da aplicação (Flask)
- `docker-compose logs` (Docker)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é open source e está disponível sob a licença MIT.

## 🆘 Suporte

Para dúvidas e problemas:

1. Verifique a seção de **Troubleshooting**
2. Consulte os **logs da aplicação**
3. Abra uma **issue** no repositório
4. Entre em **contato** com a equipe de desenvolvimento

---

**Desenvolvido com ❤️ para auxiliar no aprendizado de Libras**