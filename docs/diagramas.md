# Diagramas UML

## Diagrama de classes

O GitHub desenha este diagrama automaticamente (Mermaid). As funções de módulo (`login.py`, `banco.py`,
`turmas.py`, `horarios.py`) não aparecem aqui; elas funcionam como a camada de serviço.

```mermaid
classDiagram
    class User {
        <<abstract>>
        -ano_entrada
        -semestre_entrada
        -id_user
        -nome
        -cpf
        -email
        +tipo_usuario()*
        +curso_ou_area()*
        +sortear_nova_matricula()
    }
    class Discente {
        -curso
    }
    class Docente {
        -area
    }
    User <|-- Discente
    User <|-- Docente

    class Conta {
        -email
        -tipo_usuario
        -precisa_trocar_senha
        +eh_admin()
    }
    class Sessao {
        -usuario : Conta
        -perfil : User
        +iniciar(usuario, perfil)
        +encerrar()
        +autenticada()
    }
    Sessao o-- Conta
    Sessao o-- User

    class Oportunidade {
        -titulo
        -categoria
        -descricao
        -contato
        -prazo
        -encerrada
        +encerrar()
        +inscricoes_abertas()
    }
    class Matricula {
        -turma
        -nota
        +creditos()
        +mencao()
        +aprovado()
    }

    class PaginaPerfil {
        <<abstract>>
        -sessao : Sessao
        +titulo()*
        +_opcoes()*
        +executar()
    }
    PaginaPerfil <|-- PaginaDiscente
    PaginaPerfil <|-- PaginaDocente
    PaginaPerfil <|-- PaginaAdmin
    PaginaPerfil <|-- PaginaCardapio
    PaginaPerfil <|-- PaginaTurmas
    PaginaPerfil o-- Sessao

    class InterfaceFCTE {
        -sessao : Sessao
        +executar()
    }
    InterfaceFCTE *-- Sessao

    class SistemaFCTE {
        +atualizar_turmas_sigaa(conta)
        +listar_turmas(ano, semestre, filtro)
        +listar_cursos()
    }
    PaginaTurmas --> SistemaFCTE
    SistemaFCTE ..> AnalisadorTabelas
    HTMLParser <|-- AnalisadorTabelas
    HTMLParser <|-- AnalisadorViewState
```

## Diagrama de casos de uso

O GitHub não desenha PlantUML. Para ver a imagem, cole o código em <https://www.plantuml.com/plantuml>
ou use a extensão "PlantUML" do VS Code.

Todos os casos de uso estão disponíveis no menu do terminal.

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle

actor Visitante
actor "Usuário logado" as Usuario
actor Discente
actor Docente
actor Admin
actor "SIGAA" as SIGAA <<sistema>>
actor "Site do RU" as RU <<sistema>>
actor "Site da SAA" as SAA <<sistema>>

Usuario --|> Visitante
Discente --|> Usuario
Docente --|> Usuario
Admin --|> Usuario

rectangle "Plataforma UnB FCTE" {
  ' ---------- portal público ----------
  usecase "Consultar cardápio do RU" as UC_RU
  usecase "Consultar turmas do SIGAA" as UC_TURMAS
  usecase "Consultar cursos e organizações" as UC_CURSOS
  usecase "Consultar calendário acadêmico" as UC_CALENDARIO
  usecase "Consultar acervo da biblioteca" as UC_ACERVO

  ' ---------- acesso ----------
  usecase "Fazer login" as UC_LOGIN
  usecase "Trocar senha inicial" as UC_SENHA
  usecase "Completar perfil" as UC_PERFIL
  usecase "Ver meu perfil" as UC_VERPERFIL
  usecase "Reservar, renovar e devolver livros" as UC_EMPRESTIMO

  ' ---------- discente ----------
  usecase "Consultar oportunidades\n(extensão, pesquisa, estágio, monitoria)" as UC_OPS
  usecase "Demonstrar / retirar interesse" as UC_INTERESSE
  usecase "Conhecer EJs, atléticas e equipes" as UC_ENTIDADES
  usecase "Ver turmas matriculadas" as UC_MINHAS
  usecase "Consultar MP e IRA" as UC_IRA

  ' ---------- docente ----------
  usecase "Publicar oportunidade" as UC_PUBLICAR
  usecase "Editar / encerrar publicação" as UC_EDITAR
  usecase "Ver interessados" as UC_INTERESSADOS
  usecase "Ver turmas ofertadas e créditos" as UC_OFERTADAS
  usecase "Ver alunos da turma" as UC_ALUNOS
  usecase "Lançar nota" as UC_NOTA

  ' ---------- admin ----------
  usecase "Gerar acesso para um e-mail" as UC_ACESSO
  usecase "Moderar publicações\n(listar, encerrar, remover)" as UC_MODERAR
  usecase "Cadastrar entidade" as UC_CADENT
  usecase "Atualizar cardápio do RU" as UC_ATUALRU
  usecase "Atualizar turmas do SIGAA" as UC_ATUALSIGAA
  usecase "Matricular aluno em turma" as UC_MATRICULAR
  usecase "Ligar turma a docente" as UC_ATRIBUIR
  usecase "Listar discentes e docentes" as UC_USUARIOS
  usecase "Atualizar calendário acadêmico" as UC_ATUALCAL
  usecase "Cadastrar livro" as UC_LIVRO
}

Visitante --> UC_RU
Visitante --> UC_TURMAS
Visitante --> UC_CURSOS
Visitante --> UC_CALENDARIO
Visitante --> UC_ACERVO

Usuario --> UC_LOGIN
UC_SENHA .> UC_LOGIN : <<extend>>\nprimeiro acesso
UC_PERFIL .> UC_LOGIN : <<extend>>\nsem perfil ainda
Usuario --> UC_VERPERFIL

Discente --> UC_OPS
Discente --> UC_INTERESSE
Discente --> UC_ENTIDADES
Discente --> UC_MINHAS
Discente --> UC_IRA
Discente --> UC_EMPRESTIMO

Docente --> UC_PUBLICAR
Docente --> UC_EDITAR
Docente --> UC_INTERESSADOS
Docente --> UC_OFERTADAS
Docente --> UC_ALUNOS
Docente --> UC_NOTA
Docente --> UC_EMPRESTIMO

Admin --> UC_ACESSO
Admin --> UC_PUBLICAR
Admin --> UC_MODERAR
Admin --> UC_INTERESSADOS
Admin --> UC_CADENT
Admin --> UC_ATUALRU
Admin --> UC_ATUALSIGAA
Admin --> UC_MATRICULAR
Admin --> UC_ATRIBUIR
Admin --> UC_USUARIOS
Admin --> UC_ATUALCAL
Admin --> UC_LIVRO

UC_ATUALRU --> RU
UC_ATUALSIGAA --> SIGAA
UC_ATUALCAL --> SAA
@enduml
```

Observações:
- **Herança de atores:** todo usuário logado também é visitante, então também vê o RU e as turmas.
  Discente, docente e admin herdam o login de "Usuário logado".
- **`<<extend>>`:** trocar a senha e completar o perfil só acontecem dentro do login, e só quando é preciso
  (primeiro acesso, ou alguém que ainda não tem perfil). O admin nunca completa perfil.
- **Sistemas externos:** o SIGAA, o site do RU e o site da SAA (calendário) são atores secundários; o sistema busca dados neles.
