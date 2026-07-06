from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from ativos.models import Computador, ConfiguracaoSistema, Movimentacao, Planta
from ativos.permissions import ADMIN_GROUP, READ_GROUP, TI_GROUP


class Command(BaseCommand):
    help = 'Cria os grupos padrao do sistema e aplica permissoes iniciais.'

    def handle(self, *args, **options):
        computador_ct = ContentType.objects.get_for_model(Computador)
        movimentacao_ct = ContentType.objects.get_for_model(Movimentacao)
        planta_ct = ContentType.objects.get_for_model(Planta)
        configuracao_ct = ContentType.objects.get_for_model(ConfiguracaoSistema)

        def perms(content_type, codenames):
            return Permission.objects.filter(content_type=content_type, codename__in=codenames)

        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        ti_group, _ = Group.objects.get_or_create(name=TI_GROUP)
        leitura_group, _ = Group.objects.get_or_create(name=READ_GROUP)

        admin_group.permissions.set(Permission.objects.all())

        ti_permissions = list(
            perms(
                computador_ct,
                [
                    'view_computador',
                    'add_computador',
                    'change_computador',
                    'can_reposition_computador',
                    'can_download_qrcodes',
                    'can_download_reports',
                ],
            )
        )
        ti_permissions += list(perms(planta_ct, ['view_planta']))
        ti_permissions += list(perms(configuracao_ct, ['view_configuracaosistema']))
        ti_permissions += list(perms(movimentacao_ct, ['view_movimentacao']))
        ti_group.permissions.set(ti_permissions)

        leitura_permissions = list(perms(computador_ct, ['view_computador']))
        leitura_permissions += list(perms(planta_ct, ['view_planta']))
        leitura_permissions += list(perms(configuracao_ct, ['view_configuracaosistema']))
        leitura_permissions += list(perms(movimentacao_ct, ['view_movimentacao']))
        leitura_group.permissions.set(leitura_permissions)

        self.stdout.write(self.style.SUCCESS('Grupos padrao criados/atualizados com sucesso.'))
        self.stdout.write('Administrador: acesso total no sistema. Para acessar /admin/, o usuario tambem precisa estar com is_staff=True.')
        self.stdout.write('TI: pode cadastrar, editar, reposicionar, baixar QR Codes e relatorios.')
        self.stdout.write('Leitura: pode visualizar dashboard, mapa, computadores e QR Codes.')
