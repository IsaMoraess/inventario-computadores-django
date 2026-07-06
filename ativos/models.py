from django.db import models


class Computador(models.Model):
    class Status(models.TextChoices):
        ATIVO = 'Ativo', 'Ativo'
        MANUTENCAO = 'Manutenção', 'Manutenção'
        DESLIGADO = 'Desligado', 'Desligado'
        RESERVA = 'Reserva', 'Reserva'

    id = models.CharField(max_length=50, primary_key=True)
    sala = models.CharField(max_length=100)
    x = models.IntegerField()
    y = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
    )
    armazenamento = models.CharField(max_length=100, blank=True)
    placa_video = models.CharField(max_length=100, blank=True)
    usuario = models.CharField(max_length=150, blank=True)
    sistema = models.CharField(max_length=100, blank=True)
    ram = models.CharField(max_length=100, blank=True)
    processador = models.CharField(max_length=150, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sala', 'id']
        verbose_name = 'Computador'
        verbose_name_plural = 'Computadores'
        permissions = [
            ('can_reposition_computador', 'Pode reposicionar computadores'),
            ('can_download_qrcodes', 'Pode baixar QR Codes'),
            ('can_download_reports', 'Pode baixar relatorios'),
        ]

    def __str__(self):
        return f'{self.id} - {self.sala}'


class Movimentacao(models.Model):
    computador = models.ForeignKey(
        Computador,
        on_delete=models.SET_NULL,
        related_name='movimentacoes',
        null=True,
        blank=True,
    )
    computador_identificador = models.CharField(max_length=50, blank=True, db_index=True)
    tipo_acao = models.CharField(max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    usuario_responsavel = models.CharField(max_length=150, blank=True)
    campo = models.CharField(max_length=100, blank=True)
    valor_anterior = models.TextField(blank=True)
    valor_novo = models.TextField(blank=True)
    acao = models.CharField(max_length=100)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'

    def __str__(self):
        computador = self.computador_id or self.computador_identificador or '-'
        return f'{computador} - {self.acao}'


class Planta(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='plantas/')
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'
        permissions = [
            ('can_manage_plantas', 'Pode gerenciar plantas'),
        ]

    def __str__(self):
        return self.nome


class ConfiguracaoSistema(models.Model):
    class Tema(models.TextChoices):
        ESCURO = 'escuro', 'Escuro'
        CLARO = 'claro', 'Claro'

    nome_empresa = models.CharField(max_length=120, default='JR Grupo')
    logo = models.ImageField(upload_to='configuracoes/', blank=True)
    cor_principal = models.CharField(max_length=20, default='#38bdf8')
    cor_secundaria = models.CharField(max_length=20, default='#0f2742')
    cor_cards = models.CharField(max_length=20, default='#111925')
    tema = models.CharField(max_length=20, choices=Tema.choices, default=Tema.ESCURO)
    rodape_pdfs = models.CharField(
        max_length=180,
        default='JR Grupo - Gestao de Ativos de TI',
    )
    app_public_url = models.URLField(
        'URL publica do sistema',
        blank=True,
        help_text='Quando preenchida, sobrescreve APP_PUBLIC_URL do .env.',
    )
    ultima_sincronizacao = models.DateTimeField(null=True, blank=True)
    ultima_sincronizacao_total = models.PositiveIntegerField(default=0)
    ultimo_backup = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuracao do sistema'
        verbose_name_plural = 'Configuracoes do sistema'
        permissions = [
            ('can_manage_configuracoes', 'Pode gerenciar configuracoes'),
        ]

    def save(self, *args, **kwargs):
        self.pk = 1
        self.app_public_url = (self.app_public_url or '').rstrip('/')
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        configuracao, _ = cls.objects.get_or_create(pk=1)
        return configuracao

    def __str__(self):
        return self.nome_empresa


class LogSistema(models.Model):
    data_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150, blank=True)
    acao = models.CharField(max_length=120)
    resultado = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Log do sistema'
        verbose_name_plural = 'Logs do sistema'

    def __str__(self):
        return f'{self.data_hora:%Y-%m-%d %H:%M} - {self.acao}'
