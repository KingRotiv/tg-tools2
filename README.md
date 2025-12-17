# **TG Tools**

Ferramenta avançada em Python para **envio, download e cópia de mídias do Telegram**, usando **Hydrogram Client** (userbot e bot), com recursos extras como:

* Upload automático de arquivos
* Download em massa por link do Telegram
* Copiar mensagens entre chats (via bot)
* Filtros por caption
* Test mode (não escreve arquivos reais)
* Pré-visualização e conversão de thumbnails
* Suporte a tópicos (forum topics)
* Tratamento automático de **FloodWait**

Ideal para automação, backup e migração de conteúdos entre grupos e canais.

---

# 📦 **Instalação via Releases (binário pronto)**

> **Não precisa ter Python instalado.**

As versões compiladas estão em:

👉 **GitHub Releases → Assets**
(Baixe o arquivo correspondente ao seu sistema operacional.)

### **Linux**

```bash
chmod +x tg-tools
./tg-tools --help
```

### **Windows**

Baixe o `tg-tools.exe` e execute:

```powershell
.\tg-tools.exe --help
```

---

# 📦 **Instalação via uv tool**

Instalar com uv tool:

```bash
uv tool install git+https://github.com/KingRotiv/tg-tools2
```

Executar:

```bash
tg-tools --help
```

---

# 📦 **Instalação via clone**

Clone o repositório:

```bash
git clone https://github.com/KingRotiv/tg-tools2.git
cd tg-tools
```

### Instalar com uv:

```bash
uv sync --extra tgcrypto --no-dev
```

### Ou com pip:

```bash
pip install -r requirements.txt
```

---

# ⚙️ **Configuração**

Antes de usar a ferramenta, configure suas credenciais:

```bash
tg-tools set session-string "xxxxxxx"
# ou gere uma nova
tg-tools --create-session-string

tg-tools set api-id "xxxxxxx"
tg-tools set api-hash "xxxxxxx"
tg-tools set bot-token "xxxxxxx"
```

Verificar status:

```bash
tg-tools --status
```

O projeto usa:

* `session-string` → userbot
* `api-id`, `api-hash`, `bot-token` → modo bot

---

# 🚀 **Uso Básico**

### **1. Upload de vídeos (userbot)**

Envia todos os vídeos da pasta atual para o chat id informado.

```bash
tg-tools upload-media . -100111111 video
```

### **2. Upload de qualquer arquivo**

Envia todos os arquivos da pasta atual para o chat id informado.

```bash
tg-tools upload-media . -100111111 document
```

### **3. Download de arquivos**

Baixa todos os arquivos do chat id informado para a pasta atual.

```bash
tg-tools download-media https://t.me/c/1000000/10 10 .
```

### **4. Download de vídeos**

Baixa todos os vídeos do chat id informado para a pasta atual.

```bash
tg-tools download-media https://t.me/c/1000000/10 10 . --media-type video
```

### **5. Copiar mensagens (bot)**

Copia 10 mensagens do chat id de origem para o chat id de destino.

```bash
tg-tools copy-messages https://t.me/c/1000000/10 10 -100111111
```

> Dica: use `-h` após cada comando para ver as opções extras.

---

# 🔒 **Avisos**

* O uso de **userbot** pode violar os termos do Telegram — use por sua conta e risco.
* Não exponha `session-string`, `api-id`, `api-hash` ou `bot-token`.
* Use apenas em ambientes pessoais/seguros.

---

# 🧪 **Testes**

Instalar dependências para desenvolvimento:

```bash
uv sync --all-extras
```

Rodar testes:

```bash
uv run pytest -vv
```