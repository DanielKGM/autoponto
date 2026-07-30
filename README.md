<a id="topo"></a>

[![DOI][doi-shield]][doi-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/DanielKGM/autoponto">
    <img src="assets/logo.png" alt="Logo" height="70">
  </a>

<h3 align="center">Chamadas Acadêmicas por Reconhecimento Facial</h3><br />
  <p align="center">
    <strong>AutoPonto</strong> é um sistema distribuído de computação de borda composto por três repositórios: código de <i>firmware</i>, aplicação <i>web</i> e servidor de borda. O objetivo é criar uma solução <b>barata</b> e <b>escalável</b> para automatização de chamadas acadêmicas através do reconhecimento facial, utilizando camadas independentes e conectadas por uma rede local. 
    <br /><br />
    <u>Este repositório</u> guarda o código-fonte do <i>backend</i> e do <i>frontend</i> da aplicação <i>web</i>, responsável pelas regras de negócio e interface com alunos, professores e administradores.
    <br />
    <br />
    Um <i>deploy</i> temporário da aplicação pode estar disponível <a href="https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/"><strong>POR ESTE LINK »</strong></a>
    <br />
    <br />
    Uma documentação da API em <i>Swagger</i> pode estar disponível <a href="https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/api/docs/"><strong>POR ESTE LINK »</strong></a>
    <br />
    <br />
    <a href="https://github.com/DanielKGM/autoponto-firmware">AutoPonto <i>Firmware</i></a>
    &middot;
    <a href="https://github.com/DanielKGM/autoponto-edgenode">AutoPonto <i>EdgeNode</i></a>
    &middot;
    <a href="https://github.com/DanielKGM/autoponto/issues/new?labels=bug&template=bug-report---.md">Reportar Erro</a>
    &middot;
    <a href="https://github.com/DanielKGM/autoponto/issues/new?labels=enhancement&template=feature-request---.md">Sugerir Algo</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Sumário</summary>
  <ol>
    <li><a href="#arquitetura-geral">Arquitetura Geral</a></li>
    <li><a href="#principais-tecnologias">Principais Tecnologias</a></li>
    <li><a href="#diagrama-entidade-e-relacionamento">Diagrama Entidade e Relacionamento</a></li>
    <li>
      <a href="#capturas-de-tela">Capturas de Tela</a>
      <ul>
        <li><a href="#telas-de-relatório">Telas de Relatório</a></li>
        <li><a href="#telas-de-crud">Telas de CRUD</a></li>
        <li><a href="#outras-telas">Outras telas</a></li>
      </ul>
    </li>
    <li><a href="#ambientes">Ambientes</a></li>
    <li>
      <a href="#instalação">Instalação</a>
      <ul>
        <li><a href="#pré-requisitos">Pré-requisitos</a></li>
        <li><a href="#desenvolvimento">Desenvolvimento</a></li>
        <li><a href="#produção--ambiente-de-vm">Produção / Ambiente de VM</a></li>
      </ul>
    </li>
    <li><a href="#contato">Contato</a></li>
    <li><a href="#licença-e-citação">Licença e Citação</a></li>
    <li><a href="#agradecimentos">Agradecimentos</a></li>
  </ol>
</details>

## Arquitetura Geral

<img src="assets/arquitetura_geral.png" alt="Logo" width="100%">
<p align="justify">Quanta coisa é preciso para automatizar chamadas acadêmicas? Por exemplo, informações sobre o curso e rostos de alunos precisam ser cadastrados, então, em sala de aula, fotos precisam ser capturadas e capturas precisam ser processadas. Para atingir esses e (muitos) outros objetivos, o projeto utiliza uma arquitetura distribuída chamada <a href="https://www.intel.com/content/www/us/en/learn/what-is-edge-computing.html">computação de borda</a>. Isso permite diluir um monte de funcionalidades em camadas independentes mas cooperativas:</p>
<ul>
<li><b><a href="https://github.com/DanielKGM/autoponto-firmware">Dispositivos Embarcados</a></b>: dispositivos eletrônicos posicionados em salas de aula. Eles são responsáveis por capturar fotos e exibir mensagens, portanto, interagem frequente e diretamente com os usuários;</li>
<li><b><a href="https://github.com/DanielKGM/autoponto-edgenode">Nó de Borda</a></b>: servidor intermediário implementado em Raspberry Pi 4 ou outros <i>Single Board Computer</i> (SBC), seu propósito é fazer o reconhecimento facial, conectar os dispositivos embarcados com o servidor principal e armazenar uma parte <b>relevante</b> dos dados a cada sincronização (como rostos, aulas, alunos, matrículas, etc);</li>
<li><b>Servidor Principal</b> <u>(este repositório)</u>: regras de negócio, gerenciamento de usuários, persistência de dados, coleta biométrica, interface <i>web, dashboards</i>, relatórios, formulários CRUD, sincronização com nós, mapa IOT.</li>
<li><b><a href="https://github.com/DanielKGM/Playground_InterSCity">InterSCity</a></b> (opcional): trata-se de um middleware IOT feito por pesquisadores brasileiros da USP, onde métricas e status dos dispositivos podem ser publicados (pelos nós) e lidos (por aplicações). Não é necessário para o funcionamento do projeto, mas altamente recomendado como camada de <u>telemetria e monitoramento</u>.</li>
</ul>
<br/>
<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

## Principais Tecnologias

<!-- TABELA TECH -->

| Parte      | Tecnologia                                                    | Uso No Projeto                    | Justificativa                                                                                                                  |
| :--------- | :------------------------------------------------------------ | :-------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| Backend    | [![Python][python-badge]](#)                                  | Linguagem da API principal        | Ecossistema maduro para web, automação, testes e integração com bibliotecas de visão computacional.                            |
| Backend    | [![Django][django-badge]](#)                                  | Base da aplicação web             | Entrega estrutura robusta para modelos, autenticação, admin, migrations e organização de projeto.                              |
| Backend    | [![Django REST Framework][drf-badge]](#)                      | API REST                          | Facilita serializers, ViewSets, permissões e contratos HTTP para frontend, edge e integrações.                                 |
| Backend    | [![PostgreSQL][postgres-badge]](#)                            | Banco de dados único do sistema   | Banco relacional robusto para domínio acadêmico, presenças, relatórios e integridade referencial.                              |
| Backend    | [![Redis][redis-badge]](#)                                    | Cache de embeddings faciais       | Acelera a validação de duplicidade facial e isola o cache biométrico do banco relacional.                                      |
| Backend    | [![Simple JWT][jwt-badge]](#)                                 | Autenticação do frontend          | Usa access token curto em memória no React e refresh token em cookie HttpOnly.                                                 |
| Backend    | [![OpenCV][opencv-badge]](#)                                  | Geração de embeddings faciais     | Alinha o cadastro biométrico do backend com o reconhecimento usado no edge.                                                    |
| Backend    | [![Gunicorn][gunicorn-badge]](#)                              | Servidor WSGI em container        | Opção comum e estável para servir Django em deploy Linux.                                                                      |
| Backend    | [![WhiteNoise][whitenoise-badge]](#)                          | Arquivos estáticos do Django      | Permite servir estáticos administrativos/coletados no container sem serviço extra.                                             |
| Backend    | [![CORS Headers][cors-badge]](#)                              | CORS para o frontend              | Controla origens permitidas quando frontend e backend rodam em portas/domínios diferentes.                                     |
| Frontend   | [![React][react-badge]](#)                                    | Interface web                     | Componentização simples para telas por papel, calendário, perfil, mapa público e atualização reativa dos dados da API.         |
| Frontend   | [![TypeScript][ts-badge]](#)                                  | Tipagem do frontend               | Reduz erros de contrato entre telas e respostas da API.                                                                        |
| Frontend   | [![Vite][vite-badge]](#)                                      | Build e servidor local            | Build rápido, configuração pequena e boa ergonomia para MVP.                                                                   |
| Frontend   | [![Leaflet][leaflet-badge]](#) [![ECharts][echarts-badge]](#) | Mapa e gráficos operacionais      | Exibe nós/dispositivos IoT, histórico do Collector e gráficos de telemetria/PIR.                                               |
| Frontend   | [![Nginx][nginx-badge]](#)                                    | Servir build em container         | Entrega arquivos estáticos e faz proxy de `/api/` para o backend no Compose.                                                   |
| Infra      | [![Docker Compose][docker-compose-badge]](#)                  | Orquestração local/deploy simples | Sobe PostgreSQL, backend e frontend com um comando, facilitando demonstração do TCC.                                           |
| Integração | [![Interscity UFMA][interscity-badge]](#)                     | Camada IoT opcional               | Representa recursos, capacidades, descoberta e telemetria operacional sem tornar o AutoPonto dependente da plataforma externa. |

<!-- FIM TABELA TECH -->
<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

## Diagrama Entidade e Relacionamento

A imagem a seguir se limita às entidades principais do _backend_, referentes à modelagem do cenário acadêmico. Para mais detalhes sobre as tabelas e relacionamentos construídos a partir do ORM Django, visite os [modelos](https://github.com/DanielKGM/autoponto/tree/main/autoponto-backend/autoponto/api/models) da API.

![Diagrama ERD](assets/ERD.png)

<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

## Capturas de Tela

_Screenshots_ de algumas telas do <i>website</i>.

### 📊 Telas de Relatório

|                                                                                                                                          |                                                                                                      |
| :--------------------------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------: |
| ![Dashboard do aluno tema claro](assets/telas_relatorios/dashboard_aluno_claro.png)<br><sub><i>Dashboard</i> do aluno (tema claro)</sub> | ![Dashboard do alnuo tema escuro](assets/telas_relatorios/dashboard_aluno.png)<br><sub><i>Dashboard</i> do aluno (tema escuro)</sub> |
|      ![Detalhes da aula professor](assets/telas_relatorios/detalhes_aula_professor.png)<br><sub>Detalhes da aula (professor)</sub>       |            ![Biometrias](assets/telas_relatorios/detalhes_perfil.png)<br><sub>Biometrias e reconhecimentos (perfil)</sub>            |
|     ![Métricas recentes de IOT](assets/telas_relatorios/metricas_recentes.png)<br><sub>Métricas recentes de um dispositivo IOT</sub>     |   ![Histórico de métricas de IOT](assets/telas_relatorios/metricas.png)<br><sub>Histórico de métricas de um dispositivo IOT</sub>    |

### 📝 Telas de CRUD

|                                                                         |                                                                       |
| :---------------------------------------------------------------------: | :-------------------------------------------------------------------: |
| ![Listagem de usuários](assets/telas_crud/admin.png)<br><sub>Listagem de usuários (administrador)</sub> | ![Cadastro biometria](assets/telas_crud/cadastro_biometria.png)<br><sub>Cadastro de biometria</sub> |
|        ![Modal formulário](assets/telas_crud/formulario_aluno.png)<br><sub>Modal-formulário</sub>       |  ![Deleção biometria](assets/telas_crud/remover_biometria.png)<br><sub>Deleção de biometria</sub>   |

### 📄 Outras telas

|                                                                                  |                                                                                  |
| :------------------------------------------------------------------------------: | :------------------------------------------------------------------------------: |
|        ![Calendário aulas](assets/outras_telas/calendario_academico.png)<br><sub>Calendário de aulas</sub>       | ![Login claro](assets/outras_telas/login_tema_claro.png)<br><sub>Autenticação (tema claro)</sub> |
| ![Mapa interativo](assets/outras_telas/mapa.png)<br><sub>Mapa interativo de dispositivos em <i>Leaflet</i></sub> |    ![Tela pelo celular](assets/outras_telas/responsividade.png)<br><sub>Responsividade</sub>     |

## Ambientes

- O projeto centraliza as variáveis de ambiente na raiz do repositório, eliminando arquivos `.env` nas pastas do backend e frontend.

- Para o desenvolvimento local, utiliza-se o arquivo `.env` (baseado no `.env.example`), que é consumido automaticamente pelo backend, frontend (via Vite) e pelo `docker-compose.yml`.

- Já para a produção em VM, adota-se o `.env.prod` (baseado no `.env.prod.example`), que deve ser executado em conjunto com o `docker-compose.prod.yml`.

- Os _composes_ propositalmente não definem valores de _fallback_, garantindo que a aplicação falhe imediatamente na subida caso falte alguma variável obrigatória.

<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

## Instalação

### Pré-requisitos

Antes de começar, certifique-se de que sua máquina possui as ferramentas necessárias instaladas.

- **Git** (Sistema de Controle de Versão)
  - _Windows/Linux:_ [Baixar Git](https://git-scm.com/downloads).

- **Python** (Versão 3.9 ou Superior)
  - _Windows:_ [Baixar Python Installer](https://www.python.org/downloads/).
  - _Linux:_ Geralmente já vem instalado. Verifique com `python3 --version`. Se necessário: `sudo apt-get install python3 python3-pip`.

- **Docker**
  - _Windows:_ [Instalar Docker Desktop](https://www.docker.com/products/docker-desktop/).
  - _Linux:_ [Instalar Docker Engine](https://docs.docker.com/engine/install/).
  - [Tutorial Completo](https://gist.github.com/marciojg/1e6a3cf3d3cd2bf7b3e87dad259142d9).

- **Código-Fonte**
  - **Opção A: Via Git Clone (Recomendado)**

    Abra seu terminal e execute:

    ```sh
    git clone https://github.com/DanielKGM/autoponto.git
    ```

  - **Opção B: Via Download ZIP**
    1. Clique no botão verde **Code** no topo desta página.
    2. Selecione **Download ZIP**.
    3. Extraia o conteúdo para uma pasta de sua preferência.

### Desenvolvimento

Copie o ambiente da raiz:

```bash
cp .env.example .env
```

Preencha os valores sensiveis que aparecem vazios, como `DJANGO_SECRET_KEY`, `DATABASE_PASSWORD`, `FACE_EMBEDDING_ENCRYPTION_KEY` e `FACE_EMBEDDING_CACHE_PASSWORD`. O Compose e o backend devem falhar se uma variavel obrigatoria nao estiver configurada.

Para usar cadastro biometrico real, baixe os modelos ONNX em `autoponto-backend/autoponto/data/models/` antes de subir o backend. Eles nao sao versionados:

```bash

mkdir -p autoponto-backend/autoponto/data/models

# linux

wget https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx -O autoponto-backend/autoponto/data/models/face_detection_yunet.onnx

wget https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx -O autoponto-backend/autoponto/data/models/face_recognition_sface.onnx
# windows

curl.exe -L "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx" -o "autoponto-backend\autoponto\data\models\face_detection_yunet.onnx"

curl.exe -L "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" -o "autoponto-backend\autoponto\data\models\face_recognition_sface.onnx"

```

Suba os servicos:

```bash
docker compose up --build
```

**Criação de Superusuário:** Para criar o primeiro administrador, execute o comando de gerenciamento mapeado no container:

```bash
docker compose --env-file .env -f docker-compose.yml exec backend python /app/autoponto/manage.py createsuperuser
```

URLs:

- Frontend: `http://localhost:8080` por padrao, ou a porta que voce mapear no Compose
- Backend: `http://localhost:8000/api/`
- Health check: `http://localhost:8000/api/health/`
- PostgreSQL local: `localhost:5432`

### Produção / Ambiente de VM

Para rodar em ambiente de produção ou em uma VM dedicada, utilize os arquivos de configuração específico de produção `docker-compose.prod.yml` e `.env.prod.example`

<!-- CONTACT -->

## Contato

[Daniel Galdez (LINKEDIN)](https://www.linkedin.com/in/daniel-campos-galdez-monteiro/) &middot; <a href="mailto:danielgaldez10@hotmail.com?subject=AUTOPONTO&body=Olá! Vim do repositório AUTOPONTO e ...">danielgaldez10@hotmail.com</a>

<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

## Licença e Citação

<p align="justify">Este projeto é protegido por direitos autorais (<i>All Rights Reserved</i>). A cópia, distribuição, uso comercial ou modificação não são permitidas sem autorização prévia. Para mais informações, consulte o arquivo <b>LICENSE.md</b> ou a <b>aba de licença</b> do repositório.<br/><br/>Caso utilize este projeto em trabalhos acadêmicos ou científicos, utilize a seguinte referência BibTeX:</p>

```Latex
@software{AutoPonto_2026,
  author  = {Campos Galdez Monteiro, Daniel},
  month   = jul,
  title   = {{AutoPonto: Chamadas Acadêmicas por Reconhecimento Facial}},
  url     = {https://github.com/DanielKGM/autoponto},
  version = {1.0.0},
  year    = {2026}
}
```

<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Agradecimentos

<p align="justify">Agradeço a todos os professores do curso de Engenharia da Computação pela Universidade Federal do Maranhão (UFMA), pelos conhecimentos indispensáveis para realização desse projeto. Em especial, agradeço aos membros da minha bancada de TCC pela disponibilidade e paciência para avaliar este projeto com a nota máxima, e ao meu orientador Prof. Dr. Luis Henrique Neves Rodrigues.</p>

<p align="right">(<a href="#topo">voltar ao topo</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[doi-shield]: https://img.shields.io/badge/DOI-10.5281/zenodo.21705784-black?style=for-the-badge
[doi-url]: https://doi.org/10.5281/zenodo.21705784
[contributors-shield]: https://img.shields.io/github/contributors/DanielKGM/autoponto.svg?style=for-the-badge
[contributors-url]: https://github.com/DanielKGM/autoponto/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/DanielKGM/autoponto.svg?style=for-the-badge
[forks-url]: https://github.com/DanielKGM/autoponto/network/members
[stars-shield]: https://img.shields.io/github/stars/DanielKGM/autoponto.svg?style=for-the-badge
[stars-url]: https://github.com/DanielKGM/autoponto/stargazers
[issues-shield]: https://img.shields.io/github/issues/DanielKGM/autoponto.svg?style=for-the-badge
[issues-url]: https://github.com/DanielKGM/autoponto/issues
[license-shield]: https://img.shields.io/github/license/DanielKGM/autoponto.svg?style=for-the-badge
[license-url]: https://github.com/DanielKGM/autoponto/blob/main/LICENSE.md
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/daniel-campos-galdez-monteiro/

<!-- BADGES TABELA-->

[python-badge]: https://img.shields.io/badge/Python_3.13-3776AB?style=for-the-badge&logo=python&logoColor=fff
[django-badge]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white
[drf-badge]: https://img.shields.io/badge/Django_REST-a30000?style=for-the-badge&logo=django&logoColor=white
[postgres-badge]: https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white
[redis-badge]: https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white
[jwt-badge]: https://img.shields.io/badge/Simple_JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white
[opencv-badge]: https://img.shields.io/badge/OpenCV_YuNet/SFace-27338e?style=for-the-badge&logo=OpenCV&logoColor=white
[gunicorn-badge]: https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white
[whitenoise-badge]: https://img.shields.io/badge/WhiteNoise-ffffff?style=for-the-badge&logo=python&logoColor=black
[cors-badge]: https://img.shields.io/badge/CORS_Headers-092E20?style=for-the-badge&logo=django&logoColor=white
[react-badge]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[ts-badge]: https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white
[vite-badge]: https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white
[leaflet-badge]: https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=Leaflet&logoColor=white
[echarts-badge]: https://img.shields.io/badge/ECharts-AA344D?style=for-the-badge&logo=apacheecharts&logoColor=white
[nginx-badge]: https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white
[docker-compose-badge]: https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white
[interscity-badge]: https://img.shields.io/badge/Interscity_UFMA-00529b?style=for-the-badge
