# Configuração Gmail para Envio de Emails

## 📧 Como Configurar

### Passo 1: Habilitar Verificação em 2 Etapas

1. Acesse: https://myaccount.google.com/security
2. Clique em **"Verificação em duas etapas"**
3. Siga as instruções para habilitar (se ainda não tiver)

### Passo 2: Gerar Senha de App

1. Acesse: https://myaccount.google.com/apppasswords
2. No campo "Nome do app", digite: **WhatsApp Chatbot**
3. Clique em **"Criar"**
4. Copie a senha de 16 caracteres gerada (ex: `abcd efgh ijkl mnop`)

### Passo 3: Configurar .env

Adicione no arquivo `.env`:

```bash
# Email Configuration
GMAIL_ADDRESS=seu_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop  # Sem espaços!
```

⚠️ **IMPORTANTE**: Remova os espaços da senha de app!

## 🧪 Testar Configuração

```bash
# Teste rápido
python -m src.main

# No chat, digite:
# "Envie um email para teste@example.com com assunto 'Teste' e conteúdo 'Olá, mundo!'"
```

## 🔒 Segurança

- ✅ Use senha de app específica (não use sua senha do Gmail)
- ✅ Mantenha o `.env` no `.gitignore`
- ✅ Nunca commit suas credenciais

## ❓ Problemas Comuns

**"Authentication failed"**
- Verifique se a verificação em 2 etapas está ativa
- Confirme que está usando senha de app (não senha normal)
- Remova espaços da senha

**"Invalid email address"**
- Verifique o formato do email destinatário
- Gmail requer formato válido: `nome@dominio.com`

**"Connection refused"**
- Verifique sua conexão com internet
- Gmail SMTP usa porta 465 (SSL)
