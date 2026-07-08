from pathlib import Path
from shutil import copy2
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ativos.models import Planta


class Command(BaseCommand):
    help = 'Importa a planta da versao Streamlit para o Django.'

    destino_relativo = Path('plantas') / 'planta_real.png'
    github_raw_url = (
        'https://raw.githubusercontent.com/'
        'IsaMoraess/inventario-computadores-planta/main/assets/planta_real.png'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'imagem_path',
            nargs='?',
            type=str,
            help='Caminho opcional para assets/planta_real.png da versao Streamlit.',
        )

    def handle(self, *args, **options):
        destino = Path(settings.MEDIA_ROOT) / self.destino_relativo
        destino.parent.mkdir(parents=True, exist_ok=True)

        origem = self.encontrar_origem(options.get('imagem_path'))

        if origem:
            self.copiar_imagem(origem, destino)
            origem_msg = str(origem)
        else:
            self.baixar_imagem(destino)
            origem_msg = self.github_raw_url

        with transaction.atomic():
            Planta.objects.filter(ativa=True).update(ativa=False)
            planta, criada = Planta.objects.update_or_create(
                nome='Planta principal',
                defaults={
                    'imagem': self.destino_relativo.as_posix(),
                    'ativa': True,
                },
            )

        acao = 'criada' if criada else 'atualizada'
        self.stdout.write(self.style.SUCCESS('Planta Streamlit importada com sucesso.'))
        self.stdout.write(f'Origem: {origem_msg}')
        self.stdout.write(f'Destino: {destino}')
        self.stdout.write(f'Planta {acao}: {planta.nome}')
        self.stdout.write('Planta ativa: sim')

    def encontrar_origem(self, imagem_path):
        if imagem_path:
            origem = Path(imagem_path).expanduser()
            if origem.exists():
                return origem

            self.stdout.write(
                self.style.WARNING(
                    f'Arquivo informado nao encontrado, procurando caminhos padrao: {origem}'
                )
            )

        for origem in self.caminhos_padrao():
            if origem.exists():
                return origem

        self.stdout.write(
            self.style.WARNING(
                'Arquivo local assets/planta_real.png nao encontrado, tentando GitHub.'
            )
        )
        return None

    def caminhos_padrao(self):
        repo_nome = 'inventario-computadores-planta'
        arquivo = Path('assets') / 'planta_real.png'
        home = Path.home()

        return [
            settings.BASE_DIR.parent / repo_nome / arquivo,
            settings.BASE_DIR / repo_nome / arquivo,
            home / 'Desktop' / repo_nome / arquivo,
            home / 'OneDrive' / 'Desktop' / repo_nome / arquivo,
            Path('C:/Users/isabelly/Desktop') / repo_nome / arquivo,
            *[
                perfil / 'Desktop' / repo_nome / arquivo
                for perfil in Path('C:/Users').glob('*')
                if perfil.is_dir()
            ],
            *[
                perfil / 'OneDrive' / 'Desktop' / repo_nome / arquivo
                for perfil in Path('C:/Users').glob('*')
                if perfil.is_dir()
            ],
        ]

    def copiar_imagem(self, origem, destino):
        if origem.resolve() == destino.resolve():
            self.stdout.write('Origem e destino ja sao o mesmo arquivo.')
            return

        copy2(origem, destino)

    def baixar_imagem(self, destino):
        try:
            with urlopen(self.github_raw_url, timeout=30) as response:
                conteudo = response.read()
        except HTTPError as error:
            raise CommandError(
                f'Erro ao baixar planta do GitHub: HTTP {error.code}'
            ) from error
        except URLError as error:
            raise CommandError(
                f'Erro ao baixar planta do GitHub: {error.reason}'
            ) from error

        if not conteudo:
            raise CommandError('Download da planta retornou arquivo vazio.')

        destino.write_bytes(conteudo)
