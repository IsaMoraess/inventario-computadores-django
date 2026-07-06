# Gestão de Ativos de TI - v2

Sistema web para gerenciamento de computadores, inventário de ativos e plantas interativas, desenvolvido em Django.

A aplicação permite controlar computadores, usuários, salas, movimentações, QR Codes, relatórios e mapas interativos em uma única plataforma.

---

## Demonstração

### Dashboard

> Estatísticas em tempo real do inventário.

- Total de computadores
- Computadores ativos
- Alertas
- Gráficos
- Histórico de movimentações

---

### Mapa Interativo

- Planta da empresa
- Marcadores coloridos por status
- Clique para visualizar o computador
- Reposicionamento por arrastar e soltar
- Salvamento automático no banco

---

### Computadores

CRUD completo sem utilizar o Django Admin.

- Cadastro
- Edição
- Exclusão
- Pesquisa
- Filtros
- Página individual

---

### Histórico Automático

Todas as alterações são registradas automaticamente.

Exemplos:

- Cadastro
- Alteração de usuário
- Mudança de sala
- Alteração de status
- Reposicionamento
- Exclusão

---

### Plantas

Gerenciamento completo das plantas.

- Upload
- Ativar/desativar
- Troca automática da planta do mapa

---

### QR Codes

Central completa para geração de QR Codes.

- PNG
- PDF
- ZIP
- Folha A4
- Logo da empresa
- QR individual

---

### Relatórios

Geração de relatórios profissionais.

PDF

- Inventário geral
- Por setor
- Alertas
- Movimentações

Excel

- Resumo
- Computadores
- Pendências
- Alertas
- Resumo por setor
- Movimentações

---

### Configurações

Painel administrativo próprio.

- Nome da empresa
- Logo
- Cores
- Tema
- Backup
- Logs
- Exportações
- Limpeza de cache
- Sincronização com banco

---

### Login e Permissões

Perfis de acesso.

- Administrador
- TI
- Leitura

Controle de permissões em todas as telas.

---

## Tecnologias

- Python
- Django
- PostgreSQL (Supabase)
- HTML
- CSS
- JavaScript
- Chart.js
- ReportLab
- OpenPyXL
- Pillow
- qrcode

---

## Funcionalidades

- Dashboard
- Inventário
- CRUD completo
- Mapa interativo
- Drag and Drop
- QR Codes
- Histórico automático
- Relatórios PDF
- Relatórios Excel
- Login
- Permissões
- Backup
- Configurações
- Logs
- Responsivo

---

## Estrutura

```
inventario-computadores-django/

ativos/
config/
templates/
static/
media/
manage.py
```

---

## Como executar

Clone o projeto

```bash
git clone https://github.com/IsaMoraess/inventario-computadores-django.git
```

Crie o ambiente virtual

```bash
python -m venv .venv
```

Ative

Windows

```bash
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

Instale as dependências

```bash
pip install -r requirements.txt
```

Configure o arquivo `.env`

```env
DATABASE_URL=...
SECRET_KEY=...
DEBUG=True
APP_PUBLIC_URL=http://localhost:8000
```

Migrações

```bash
python manage.py migrate
```

Criar grupos

```bash
python manage.py criar_grupos_padrao
```

Executar

```bash
python manage.py runserver
```

---

## Roadmap

- [x] Dashboard
- [x] CRUD de computadores
- [x] Mapa interativo
- [x] Drag & Drop
- [x] Histórico automático
- [x] Plantas
- [x] QR Codes
- [x] Relatórios PDF
- [x] Relatórios Excel
- [x] Login
- [x] Permissões
- [x] Configurações
- [ ] API REST
- [ ] Notificações
- [ ] Inventário por dispositivos móveis

---

## Autor

**Isabelly Moraes**

GitHub:
https://github.com/IsaMoraess
