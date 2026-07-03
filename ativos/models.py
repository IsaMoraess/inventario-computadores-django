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

    def __str__(self):
        return f'{self.id} - {self.sala}'


class Movimentacao(models.Model):
    computador = models.ForeignKey(
        Computador,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
    )
    campo = models.CharField(max_length=100)
    valor_anterior = models.TextField(blank=True)
    valor_novo = models.TextField(blank=True)
    acao = models.CharField(max_length=100)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'

    def __str__(self):
        return f'{self.computador_id} - {self.acao}'


class Planta(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='plantas/')
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'Planta'
        verbose_name_plural = 'Plantas'

    def __str__(self):
        return self.nome
