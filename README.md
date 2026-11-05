# Plataforma_UnB_FCTE

Projeto desenvolvido para a disciplina de Orientação a Objetos, com o objetivo de simular uma plataforma acadêmica semelhante ao SIGAA, exclusiva da UnB — campus FCTE (Faculdade de Ciências e Tecnologias em Engenharia). A proposta é reunir funcionalidades acadêmicas e serviços próprios da unidade em um único sistema, facilitando o acesso dos discentes a informações e recursos da universidade.

Os diagramas de classes e de casos de uso estão em [docs/diagramas.md](docs/diagramas.md), e as relações entre classes (herança, polimorfismo, composição, agregação, associação e dependência) em [docs/relacoes_oo.md](docs/relacoes_oo.md).

##  Estrutura do Projeto

```text
unb_fcte_plataforma_discente/
├── code_py/                                        # Código-fonte Python
│   ├── banco.py                                    # Conexão e esquema SQLite (sistema.db)
│   ├── biblioteca.py                               # Módulo da biblioteca (reservas, empréstimos, multas)
│   ├── cardapio.py                                 # Extrator de PDF do RU (pdfplumber)
│   ├── consultas_publicas.py                       # Consultas abertas (RU, Cursos, Calendário)
│   ├── exemplos.py                                 # Povoamento com dados de teste
│   ├── horarios.py                                 # Tradutor de códigos de horário do SIGAA
│   ├── interface.py                                # Interface principal do terminal
│   ├── login.py                                    # Autenticação e hash PBKDF2
│   ├── organizacoes.py                             # Mural de oportunidades e entidades
│   ├── paginas.py                                  # Menus por perfil (Discente, Docente, Admin)
│   ├── system.py                                   # Web scraper de turmas do SIGAA
│   ├── turmas.py                                   # Matrículas, menções e cálculo de MP/IRA
│   └── user.py                                     # Classes de usuário e validações (CPF, E-mail)
├── data/                                           # Arquivos de dados (.json e .csv)
│   ├── acervo_biblioteca.json                      # Acervo inicial da biblioteca
│   ├── acervo_biblioteca_modelo.csv                # Modelo para importação em lote
│   ├── calendario_academico.json                   # Calendário acadêmico UnB
│   └── cardapio_extraido.json                      # Cardápio do RU estruturado
├── tests/                                          # Suíte de testes unitários (unittest)
├── requirements.txt                                # Dependências externas (pdfplumber)
└── README.md                                       # Documentação do projeto
```

---

## Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o sistema
```bash
python -m code_py.interface
```

### 3. Povoar com dados de teste (Opcional)
```bash
python -m code_py.exemplos
```

**Credenciais padrão para testes:**
* **Admin**: `admin@exemplo.unb.br` | Senha: `admin12345`
* **Discente**: `aluno@exemplo.unb.br` | Senha: `aluno12345`
* **Docente**: `professor@exemplo.unb.br` | Senha: `professor12345`

---

##  Executar Testes Automatizados

```bash
python -m unittest discover -s tests
```
