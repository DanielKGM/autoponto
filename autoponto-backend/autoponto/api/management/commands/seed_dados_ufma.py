import re
import unicodedata
from datetime import date, time

from django.core.management.base import BaseCommand

from api.models import (
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioAula,
    HorarioPadraoUFMA,
    NoBorda,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
    Usuario,
)


ALUNOS_TCC = [
    ("20250013499", "ADRIELLE CAMPELO CUNHA"),
    ("20240065446", "ALISSON EMANUEL DINIZ SANTOS"),
    ("20240001378", "AMANDA CAROLINE OLIVEIRA JORGE"),
    ("20240065517", "AMANDA MAIA SOARES SILVA"),
    ("20240065544", "ANA IARA LOAYZA COSTA"),
    ("20250013597", "ANA POLIANA MESQUITA DE JESUS DE SOUSA"),
    ("20240065590", "ANDERSON ALMEIDA DA SILVEIRA"),
    ("20250013630", "ANDERSON CARVALHAL PIMENTA"),
    ("20250071151", "ANDRE LUIS AGUIAR DO NASCIMENTO"),
    ("2020055304", "ANDRE LUIZ ALMEIDA CARDOSO"),
    ("20240065366", "ANDRE MOURA LIMA"),
    ("20240065428", "ANDRE VICTOR MACEDO PEREIRA"),
    ("20250013480", "ANTONIO LUCAS DA SILVA VALE"),
    ("20250071160", "ANTONIO NETO DE MOURA MELO"),
    ("20240001396", "ARLINDO MACIEIRA MARTINS DE MELO"),
    ("20260001141", "ARLISON GASPAR DE OLIVEIRA"),
    ("2023098557", "ARTHUR SAMPAIO PEREIRA"),
    ("2023098575", "BRUNO JOSE PEREIRA DE SA"),
    ("20260001123", "BRUNO KAUAN RODRIGUES SILVA"),
    ("2022024791", "BRUNO RAFAEL CARVALHO COELHO"),
    ("20260001259", "CARLA SOFIA SANTOS RIBEIRO"),
    ("2023098593", "CARLOS DANIEL DOS SANTOS SILVA"),
    ("2023027500", "CLEILA MONTEIRO DUTRA GALIZA"),
    ("20250013659", "DANIEL CAMPOS GALDEZ MONTEIRO"),
    ("20240065400", "DANIEL LUCAS SILVA AIRES"),
    ("20250013550", "DANIEL NUNES DUARTE"),
    ("20240065562", "DANNIEL CRISTIE MATOS DA SILVA"),
    ("2019061176", "DARIO HENRIQUE SALAZAR MELO"),
    ("20250013748", "DAVI OLIVEIRA CORTES"),
    ("2021071527", "DELRYSON DA SILVA SARAIVA"),
    ("20260001114", "DIOGO BRASIL DA SILVA"),
    ("20260001295", "EDUARDO DOS SANTOS OLIVEIRA"),
    ("20250071170", "ELAYNE REIS TAVARES"),
    ("2022000860", "ELIZABETTE CRISTINA GARCIA PEREIRA DE ASSUNCAO"),
    ("20260001212", "ELLEN CRISTINA DE SOUSA CASTRO"),
    ("20230101342", "ELPIDIO RODRIGUES DO NASCIMENTO NETO"),
    ("20260001105", "EMANOEL SILVA LIMA"),
    ("20250071189", "EMANUEL LOPES SILVA"),
    ("20250013523", "EMERSON PAULO PINHEIRO MUNIZ"),
    ("20240065606", "ENZO FELIPE PRUDENCIO AVELINO LIMA"),
    ("20250071198", "EUDERLAN FREIRE DA SILVA ABREU"),
    ("20250013720", "FELIPE AUGUSTO SOUSA DE ALMADA"),
    ("20250071607", "FERNANDA SOUSA DE ASSUNCAO VALE"),
    ("20250013579", "FERNANDO DA SILVA COSTA"),
    ("20240065384", "FRANCISCO ELIAS DA SILVA FERNANDES"),
    ("20240065491", "GABRIELA FLORENCIO DA SILVA"),
    ("20260001301", "GABRIEL ANDRE BARRETO OLIMPIO DOS SANTOS"),
    ("2023098664", "GABRIEL FELIPE CARVALHO SILVA"),
    ("2023027671", "GABRIEL THIAGO TAVARES RIBEIRO"),
    ("20250013701", "GABRYELLA CRUZ SOUSA"),
    ("20250013541", "GILBERSON RICKELMY AMARAL CAMPOS DINIZ"),
    ("20240065633", "GUILHERME DE AQUINO PACHECO"),
    ("20240001734", "GUILHERME EMANOEL ARAUJO BARROS"),
    ("20260001310", "GUILHERME PESSOA LIMA DINIZ"),
    ("2023098673", "GUILHERME ROBERTO MATOS SILVA"),
    ("20240065473", "GUSTAVO ANTONIO SILVA ROCHA"),
    ("20260001348", "HELLEN NEVES BARBOSA"),
    ("20260001268", "HERICK VINICIUS PINHEIRO DA CONCEICAO"),
    ("20250013695", "HIGOR PINHEIRO COSTA"),
    ("20240001467", "HUDSON COSTA DINIZ"),
    ("20250013345", "IRLANDA HILDENEY OLIVEIRA TEIXEIRA"),
    ("20250013505", "ISABELA OLIVEIRA DE CASTRO MOREIRA"),
    ("20230101389", "ISABEL SILVA DE ARAUJO"),
    ("2020055350", "ISRAEL VITOR DINIZ LIMA"),
    ("20260001230", "ITALO FRANCISCO ALMEIDA DE OLIVEIRA"),
    ("20240001476", "ITALO JOSE SILVA REIS"),
    ("20240065437", "ITALO MATHEUS RODRIGUES SOUSA"),
    ("20250071204", "IZADORA DE PAULA SANTOS LIMA"),
    ("20250071213", "JAMILLY VITORIA FERREIRA BARBOSA"),
    ("20250013677", "JEANDERSON DA SILVA CAMPOS"),
    ("20240001485", "JEFFERSSON DE CARVALHO"),
    ("20250071590", "JENNIFER CAROLINE DA SILVA BARRAZA"),
    ("20250071222", "JEYSRAELLY ALMONE DA SILVA"),
    ("2023098682", "JOAO GABRIEL MUNIZ DA SILVA"),
    ("20260001320", "JOAO GUILHERME MIRANDA LAGO"),
    ("2022024746", "JOAO MANOEL TORRES PADILHA"),
    ("20260001188", "JOAO PEDRO MIRANDA SOUSA"),
    ("20250013640", "JOAO VICTOR LIMA EWERTON"),
    ("20260001375", "JOAO VICTOR OLIVEIRA SANTOS"),
    ("20230101404", "JOSEAN SILVA LIMA"),
    ("20250071231", "JOSE NUNES DE SOUSA NETO"),
    ("20240065615", "JOSE VICTOR BRITO COSTA"),
    ("20250071240", "JOSUEL PINHEIRO BARROS JUNIOR"),
    ("2023098717", "JUSTINO FELIPE LOPES NUNES"),
    ("20250013603", "KAUA FERREIRA GALENO"),
    ("20260001160", "KAUAN GUILHERME ALVES PINHEIRO SANTOS"),
    ("20260001179", "KEVEN GUSTAVO DOS SANTOS GOMES"),
    ("20250013390", "KLEITON LINNEKER BARBOSA PINHEIRO"),
    ("20240065419", "LEONARDO ABREU FERREIRA"),
    ("20240065464", "LEONARDO DOS SANTOS PEREIRA"),
    ("2023027751", "LEONARDO VICTOR DOS SANTOS SA MENEZ"),
    ("20250013514", "LEONIDAS FERREIRA DA SILVA SERRA"),
    ("20260021690", "LETICIA DELFINO DE ARAUJO"),
    ("20260021707", "LIAH RENATA COLINS DA SILVA"),
    ("20250013588", "LOUISE REIS MENDES"),
    ("2022024782", "LUA COIMBRA SANTIAGO SAUNDERS"),
    ("20260001277", "LUCAS ARAUJO DOMINICI"),
    ("20250071250", "LUCAS EMANOEL AMARAL GOMES"),
    ("20250013668", "LUCAS MARTINS CAMPOS MATOS"),
    ("20260001240", "LUCAS SILVA COSTA"),
    ("20260001366", "LUIS EDUARDO BAIMA DO LAGO MELONIO JUNIOR"),
    ("20250071616", "LUIS GUILHERME FREITAS DE ALMEIDA SILVA"),
    ("20250071269", "MANOEL LUCAS PACHECO JUNIOR"),
    ("20260001286", "MARCELO ERYK NASCIMENTO CARDOSO"),
    ("20240065393", "MARCOS ANTONIO BRANCO PEREIRA JUNIOR"),
    ("20260001197", "MARCOS DAVI TAVEIRA DE SOUSA"),
    ("20250071278", "MARCOS VINICIUS JANSEM OLIVEIRA"),
    ("20260001357", "MARIA DALVA MARTINS DE OLIVEIRA SOUSA"),
    ("20250071287", "MARIA LAURA RANGEL URBANO CRONEMBERGER"),
    ("20250071296", "MARIA VITORIA CANTANHEDE SILVA"),
    ("20250013612", "MARINA LUANDA PRIVADO COELHO"),
    ("20250071302", "MATEUS DUTRA VALE"),
    ("20260001150", "MATHEUS COSTA ALVES"),
    ("20250013560", "MATHEUS RYAN CARREIRO COSTA CORREIA"),
    ("20240065535", "MELISSA RODRIGUES PALHANO"),
    ("20250013532", "MILENA FREIRE BRITTO NEVES"),
    ("2021071563", "NATHYANE DE JESUS PEREIRA MORENO"),
    ("2023098216", "NILTON MACIEL MANGUEIRA"),
    ("20240001538", "PACELLE HENRIQUE PARNAIBA SOBRAL"),
    ("2022024666", "PATRICK MORAES CUTRIM"),
    ("20260001203", "PAULO EDUARDO LIMA RABELO"),
    ("20240065580", "PAULO GABRIEL SOARES GOMES"),
    ("20240065455", "PEDRO ARTHUR DA SILVA GUIMARAES"),
    ("20250013621", "RAIANNY CRISTINA FERREIRA DA SILVA"),
    ("20250071311", "RAIMUNDO JOSE DINIZ RIBEIRO"),
    ("20250071320", "RANIERE MENDES DOS SANTOS"),
    ("20240001547", "RAPHAEL CAMARA SA"),
    ("20260001132", "RAYLAN BRUNO SANTANA CARVALHO"),
    ("2023027635", "RENAN SOUSA FREIRE"),
    ("20240001556", "RENATA COSTA ROCHA"),
    ("20250071330", "RENATO MUNIZ GOMES"),
    ("2019000500", "RODRIGO DE FRANCA DE SA MENEZES"),
    ("20240065375", "ROSIVANIA DA SILVA VIANA"),
    ("2023098225", "STEFHANE PEREIRA COSTA"),
    ("20250013686", "STENIO MORAES FONSECA"),
    ("20240001879", "TEREZA CLARICE DA SILVA ROCHA"),
    ("20240001565", "THALES GUSTAVO MENDES NUNES"),
    ("2018019024", "THALLES JHONATAN DOS ANJOS SILVA"),
    ("2022024639", "THALLYSON GABRIEL MARTINS CORREIA FONTENELE"),
    ("20250013710", "THIAGO MATHEUS SOARES DE SOUSA"),
    ("20250013739", "TIAGO DE LIMA BATISTA"),
    ("20240065526", "VICTOR COELHO DA SILVA"),
    ("20240001725", "VICTOR FERREIRA BRAGA"),
    ("2021071581", "VINICIUS SANTOS DO NASCIMENTO"),
    ("20250071349", "VIRGINIA MARIA MONDEGO FERREIRA"),
    ("20260001221", "WANDERSON CAMPOS SOARES"),
    ("20250071358", "WELYAB DA SILVA PAULA"),
    ("20250071367", "WESLEY DOS SANTOS GATINHO"),
    ("20260001339", "YASMIN CANTANHEDE SANTOS"),
    ("20250071376", "YASMIN SEREJO LIMA"),
]

PARTICULAS_NOME = {"da", "das", "de", "do", "dos", "e"}

SLOTS_UFMA = {
    "M": {
        "1": (time(7, 30), time(8, 20)),
        "2": (time(8, 20), time(9, 10)),
        "3": (time(9, 20), time(10, 10)),
        "4": (time(10, 10), time(11, 0)),
        "5": (time(11, 10), time(12, 0)),
        "6": (time(12, 0), time(12, 50)),
    },
    "T": {
        "1": (time(13, 10), time(14, 0)),
        "2": (time(14, 0), time(14, 50)),
        "3": (time(14, 50), time(15, 40)),
        "4": (time(15, 50), time(16, 40)),
        "5": (time(16, 40), time(17, 30)),
        "6": (time(17, 30), time(18, 30)),
    },
    "N": {
        "1": (time(18, 30), time(19, 20)),
        "2": (time(19, 20), time(20, 10)),
        "3": (time(20, 20), time(21, 10)),
        "4": (time(21, 10), time(22, 0)),
    },
}


class Command(BaseCommand):
    help = "Cria/atualiza o cenario de seed do TCC AutoPonto na UFMA."

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha-padrao",
            dest="senha_padrao",
            default=None,
            help="Senha inicial opcional para usuarios criados pelo seed. Se omitida, usuarios ficam sem senha utilizavel.",
        )

    def handle(self, *args, **options):
        senha_padrao = options.get("senha_padrao")
        campus = self._criar_topologia_academica()
        curso, disciplina, periodo, sala = self._criar_oferta_academica(campus)
        professor = self._criar_professor(senha_padrao)
        turma = self._criar_turma(periodo, disciplina, professor)
        self._criar_alunos(senha_padrao)
        self._criar_horarios_ufma()
        self._criar_horarios_aula(turma, sala)
        self._criar_infraestrutura_iot(sala)
        self.stdout.write(self.style.SUCCESS("Seed UFMA/TCC criado ou atualizado."))

    def _criar_topologia_academica(self):
        campus, _ = Campus.objects.update_or_create(
            nome="Cidade Universitaria Dom Delgado - Sao Luis",
            defaults={"ativo": True},
        )
        Predio.objects.update_or_create(
            campus=campus,
            nome="BICT",
            defaults={"ativo": True},
        )
        predio_paulo_freire, _ = Predio.objects.update_or_create(
            campus=campus,
            nome="Paulo Freire",
            defaults={"ativo": True},
        )
        Sala.objects.update_or_create(
            predio=predio_paulo_freire,
            codigo="105N",
            defaults={"nome": "105 Norte", "ativo": True},
        )
        return campus

    def _criar_oferta_academica(self, campus):
        periodo, _ = PeriodoLetivo.objects.update_or_create(
            nome="2026.1",
            defaults={"data_inicio": date(2026, 3, 16), "data_fim": date(2026, 7, 18), "ativo": True},
        )
        curso, _ = Curso.objects.update_or_create(
            campus=campus,
            nome="Engenharia da Computacao",
            defaults={"ativo": True},
        )
        disciplina, _ = Disciplina.objects.update_or_create(
            curso=curso,
            codigo="EECP0021",
            defaults={"nome": "SISTEMAS DISTRIBUIDOS", "ativo": True},
        )
        sala = Sala.objects.get(predio__campus=campus, codigo="105N")
        return curso, disciplina, periodo, sala

    def _criar_professor(self, senha_padrao):
        professor = Usuario.objects.filter(username="luiz.henrique").first()
        if professor is None:
            professor = Usuario(username="luiz.henrique", email="")
            self._configurar_senha(professor, senha_padrao)
        professor.papel = PapelUsuario.PROFESSOR
        professor.nome_completo = "LUIZ HENRIQUE NEVES RODRIGUES"
        professor.matricula = professor.matricula or "PROF-LHNR"
        professor.is_active = True
        professor.save()
        return professor

    def _criar_turma(self, periodo, disciplina, professor):
        turma, _ = Turma.objects.update_or_create(
            periodo_letivo=periodo,
            disciplina=disciplina,
            codigo="20261EECP0021",
            defaults={"ativo": True},
        )
        turma.professores.set([professor])
        return turma

    def _criar_alunos(self, senha_padrao):
        usados = set(Usuario.objects.values_list("username", flat=True))
        for matricula, nome in ALUNOS_TCC:
            usuario = Usuario.objects.filter(matricula=matricula).first()
            if usuario is None:
                username = self._gerar_username(nome, usados)
                usados.add(username)
                usuario = Usuario(username=username, email="", matricula=matricula)
                self._configurar_senha(usuario, senha_padrao)
            usuario.papel = PapelUsuario.ALUNO
            usuario.nome_completo = nome
            usuario.is_active = True
            usuario.save()

    def _criar_horarios_ufma(self):
        for dia in range(2, 8):
            for turno, slots in SLOTS_UFMA.items():
                for numero in slots:
                    self._criar_horario_padrao(f"{dia}{turno}{numero}")
        self._criar_horario_padrao("2N34")
        self._criar_horario_padrao("4N34")

    def _criar_horarios_aula(self, turma, sala):
        for codigo in ("2N34", "4N34"):
            HorarioAula.objects.update_or_create(
                turma=turma,
                horario_padrao=HorarioPadraoUFMA.objects.get(codigo=codigo),
                defaults={"sala": sala, "ativo": True},
            )

    def _criar_infraestrutura_iot(self, sala):
        no, _ = NoBorda.objects.update_or_create(
            codigo="88A29E606012",
            defaults={
                "nome": "raspberry-tcc",
                "ativo": True,
                "interscity_uuid": "91723758-5fe0-4a76-8f1a-6aaf97463d66",
            },
        )
        DispositivoEsp32.objects.update_or_create(
            codigo="9084CED6CDC0",
            defaults={
                "nome": "esp32-tcc",
                "no": no,
                "sala": sala,
                "ativo": True,
                "status": DispositivoEsp32.STATUS_OFFLINE,
                "interscity_uuid": "8cf4ce45-3aff-4aa2-81e0-27a2fc361f09",
            },
        )

    def _criar_horario_padrao(self, codigo):
        codigo = codigo.upper()
        dia = int(codigo[0])
        turno = codigo[1]
        numeros = codigo[2:]
        inicio = SLOTS_UFMA[turno][numeros[0]][0]
        fim = SLOTS_UFMA[turno][numeros[-1]][1]
        HorarioPadraoUFMA.objects.update_or_create(
            codigo=codigo,
            defaults={
                "dia_semana": dia,
                "horario_inicio": inicio,
                "horario_fim": fim,
                "ativo": True,
            },
        )

    def _gerar_username(self, nome, usados):
        palavras = self._palavras_login(nome)
        primeiro = palavras[0]
        candidatos = [p for p in palavras[1:] if p not in PARTICULAS_NOME]
        if not candidatos:
            candidatos = ["aluno"]
        for candidato in candidatos:
            username = f"{primeiro}.{candidato}"
            if username not in usados and not Usuario.objects.filter(username=username).exists():
                return username
        base = f"{primeiro}.{candidatos[0]}"
        indice = 2
        while True:
            username = f"{base}{indice}"
            if username not in usados and not Usuario.objects.filter(username=username).exists():
                return username
            indice += 1

    def _palavras_login(self, nome):
        ascii_nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
        palavras = re.findall(r"[a-z0-9]+", ascii_nome.lower())
        return palavras or ["usuario"]

    def _configurar_senha(self, usuario, senha_padrao):
        if senha_padrao:
            usuario.set_password(senha_padrao)
        else:
            usuario.set_unusable_password()
