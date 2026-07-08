# Gestão de Ativos de TI - v2

Sistema web para gerenciamento de ativos de TI desenvolvido em **Django**, com foco em inventário de computadores, plantas interativas, QR Codes, relatórios e controle de movimentações.

A aplicação foi criada para substituir uma versão anterior em Streamlit, oferecendo uma arquitetura mais robusta, escalável e adequada para ambientes corporativos.

---

## Principais Funcionalidades

- Dashboard com indicadores em tempo real
- Mapa interativo da planta da empresa
- Reposicionamento de computadores por Drag & Drop
- CRUD completo de computadores
- Página individual dos ativos
- Histórico automático de movimentações
- Upload e gerenciamento de plantas
- Central de QR Codes
- Relatórios em PDF
- Exportação completa para Excel
- Login e controle de permissões
- Configurações do sistema
- Integração com PostgreSQL (Supabase)

---

## Tecnologias

- Python
- Django
- PostgreSQL (Supabase)
- HTML5
- CSS3
- JavaScript
- Chart.js
- ReportLab
- OpenPyXL
- Pillow
- qrcode

---

# Módulos

## Dashboard

Painel principal contendo indicadores do inventário.

- Total de computadores
- Computadores ativos
- Equipamentos em manutenção
- Alertas
- Gráficos
- Histórico recente

---

## Mapa Interativo

Visualização gráfica da planta da empresa.

Funcionalidades:

- Planta da empresa
- Marcadores coloridos por status
- Clique para visualizar detalhes
- Drag & Drop para reposicionar ativos
- Salvamento automático das coordenadas

---

## Computadores

CRUD completo desenvolvido em Django.

- Cadastro
- Edição
- Exclusão
- Pesquisa
- Filtros
- Página individual

---

## Histórico

Todas as alterações ficam registradas automaticamente.

Exemplos:

- Cadastro
- Alteração de usuário
- Mudança de sala
- Alteração de status
- Reposicionamento
- Exclusão

---

## Plantas

Gerenciamento das plantas utilizadas pelo mapa.

- Upload
- Ativar/Desativar
- Troca automática da planta ativa

---

## QR Codes

Central de geração de QR Codes.

- QR individual
- PNG
- PDF
- ZIP
- Folha A4
- Logo da empresa

---

## Relatórios

### PDF

- Inventário Geral
- Por Setor
- Alertas
- Movimentações

### Excel

- Resumo
- Computadores
- Pendências
- Alertas
- Resumo por setor
- Movimentações

---

## Configurações

Painel administrativo do sistema.

- Dados da empresa
- Logo
- Tema
- Backup
- Sincronização com Supabase
- Logs
- Limpeza de cache

---

## Login e Permissões

Perfis de acesso:

- Administrador
- TI
- Leitura

Controle de acesso baseado em grupos do Django.

---

# Estrutura do Projeto

```text
inventario-computadores-django/
│
├── ativos/
├── config/
├── templates/
├── static/
├── media/
├── manage.py
└── requirements.txt
```

---

# Como executar

## Clonar o projeto

```bash
git clone https://github.com/IsaMoraess/inventario-computadores-django.git
```

## Criar ambiente virtual

```bash
python -m venv .venv
```

## Ativar

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

## Instalar dependências

```bash
pip install -r requirements.txt
```

## Configurar o arquivo `.env`

```env
DATABASE_URL=...
SECRET_KEY=...
DEBUG=True
APP_PUBLIC_URL=http://localhost:8000
```

## Aplicar migrações

```bash
python manage.py migrate
```

## Criar grupos padrão

```bash
python manage.py criar_grupos_padrao
```

## Executar

```bash
python manage.py runserver
```

---

# Roadmap

- [x] Dashboard
- [x] CRUD de computadores
- [x] Mapa interativo
- [x] Drag & Drop
- [x] Histórico automático
- [x] Upload de plantas
- [x] QR Codes
- [x] Relatórios PDF
- [x] Exportação Excel
- [x] Login e Permissões
- [x] Configurações do sistema
- [ ] API REST
- [ ] Notificações
- [ ] Inventário via dispositivos móveis

---

# Próximas melhorias

- API REST
- Integração com dispositivos móveis
- Inventário por leitura de QR Code
- Dashboard em tempo real com WebSockets
- Notificações automáticas
- Auditoria avançada
- Modo offline

---

# Autor

**Isabelly Moraes**

Desenvolvedora Python | Dados | Geoprocessamento

GitHub:
https://github.com/IsaMoraess
