# Instalação e Uso do Sistema de Banco de Dados - Libras

## 📋 Pré-requisitos

Para usar o sistema de banco de dados completo, você precisa instalar:

```bash
pip install matplotlib
```

## 🗄️ Funcionalidades Implementadas

### 1. **Banco de Dados SQLite**
- ✅ Armazenamento automático de sessões de jogo
- ✅ Histórico de palavras praticadas
- ✅ Tempos individuais por letra
- ✅ Estatísticas de performance por letra
- ✅ Sistema de usuários (expandível para login)

### 2. **Relatórios Detalhados**
- ✅ Estatísticas gerais (precisão, tempo, sessões)
- ✅ Performance por letra (melhores e piores)
- ✅ Histórico das últimas sessões
- ✅ Palavras mais praticadas
- ✅ Gráficos de progresso (matplotlib)

### 3. **Interface Integrada**
- ✅ Botão "📊 Ver Relatórios" na interface principal
- ✅ Janela com abas organizadas
- ✅ Geração de gráficos PNG
- ✅ Estatísticas em tempo real

## 🚀 Como Usar

### Iniciar o Aplicativo
```bash
python final.py
```

### Funcionalidades do Banco
1. **Automático**: Todas as sessões são salvas automaticamente
2. **Relatórios**: Clique em "📊 Ver Relatórios" para ver estatísticas
3. **Gráficos**: Use "📊 Gerar Gráficos" na janela de relatórios

## 📊 Estrutura do Banco

### Tabelas Criadas:
- `users` - Usuários do sistema
- `game_sessions` - Sessões de jogo
- `practiced_words` - Palavras praticadas
- `letter_times` - Tempos por letra
- `letter_stats` - Estatísticas acumuladas

### Arquivo do Banco:
- **Nome**: `libras_stats.db`
- **Localização**: Pasta do aplicativo
- **Tamanho**: ~36KB (vazio)

## 📈 Relatórios Disponíveis

### Aba 1: Estatísticas Gerais
- Resumo dos últimos 30 dias
- Palavras mais praticadas
- Progresso diário

### Aba 2: Performance por Letra
- Precisão e tempo médio por letra
- Letras que precisam de prática
- Melhores performances

### Aba 3: Histórico
- Últimas 10 sessões
- Detalhes de modo e dificuldade

## 🎯 Benefícios

1. **Acompanhamento de Progresso**
   - Veja sua evolução ao longo do tempo
   - Identifique pontos de melhoria

2. **Motivação**
   - Compare performances
   - Veja estatísticas de melhoria

3. **Personalização**
   - Foco nas letras mais difíceis
   - Histórico personalizado

## 🔧 Solução de Problemas

### Se não conseguir ver relatórios:
1. Instale matplotlib: `pip install matplotlib`
2. Verifique se o arquivo `database.py` existe
3. Verifique se o arquivo `reports.py` existe

### Se houver erro no banco:
1. Delete o arquivo `libras_stats.db`
2. Reinicie o aplicativo
3. O banco será recriado automaticamente

## 📱 Expansões Futuras

- [ ] Sistema de login com múltiplos usuários
- [ ] Backup automático na nuvem
- [ ] Comparação entre usuários
- [ ] Metas e conquistas
- [ ] Exportação de dados

## 🎉 Conclusão

O sistema está totalmente funcional e integrado! Todas as suas práticas serão automaticamente salvas e você poderá acompanhar seu progresso através dos relatórios detalhados.