from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .inventario_metrics import (
    computadores_com_alerta,
    contar_status,
    grafico_por_campo,
    motivos_pendencia,
    pendencias_q,
)
from . import configuracao_service


PRIMARY = colors.HexColor('#0f2742')
ACCENT = colors.HexColor('#0284c7')
SUCCESS = colors.HexColor('#16a34a')
WARNING = colors.HexColor('#d97706')
DANGER = colors.HexColor('#dc2626')
MUTED = colors.HexColor('#64748b')
LIGHT = colors.HexColor('#f8fafc')
LINE = colors.HexColor('#dbe3ee')


def _logo_path():
    config_logo = configuracao_service.logo_path()
    if config_logo:
        return config_logo

    found = finders.find('img/logo_jr.png')
    if found:
        return found

    fallback = Path(settings.BASE_DIR) / 'static' / 'img' / 'logo_jr.png'
    return str(fallback) if fallback.exists() else None


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name='CoverTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            fontSize=28,
            leading=34,
            textColor=PRIMARY,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=12,
            leading=17,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=15,
            leading=20,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name='Small',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1f2937'),
        )
    )
    styles.add(
        ParagraphStyle(
            name='Muted',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=MUTED,
        )
    )
    return styles


def _pdf(story, pagesize=A4):
    config = configuracao_service.get_config()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.1 * cm,
        bottomMargin=1.1 * cm,
        title='Gestao de Ativos de TI',
        author=config.nome_empresa or 'JR Grupo',
    )
    doc.build(story)
    return buffer.getvalue()


def _paragraph(text, style):
    text = str(text if text is not None else '-')
    return Paragraph(text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), style)


def _generated_at():
    return timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')


def _cover(story, styles, title, subtitle=None):
    config = configuracao_service.get_config()
    logo = _logo_path()
    story.append(Spacer(1, 1.4 * cm))
    if logo:
        story.append(Image(logo, width=4.2 * cm, height=4.2 * cm, kind='proportional'))
        story[-1].hAlign = 'CENTER'
        story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph('Gestao de Ativos de TI', styles['CoverTitle']))
    story.append(Paragraph(config.nome_empresa or 'JR Grupo', styles['CoverSubtitle']))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(title, styles['CoverSubtitle']))
    if subtitle:
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph(subtitle, styles['CoverSubtitle']))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(f'Data de geracao: {_generated_at()}', styles['CoverSubtitle']))
    story.append(PageBreak())


def _section(story, styles, title):
    story.append(Paragraph(title, styles['SectionTitle']))


def _summary_cards(story, styles, cards):
    data = []
    row = []
    for label, value in cards:
        row.append(_paragraph(f'<b>{value}</b><br/>{label}', styles['Small']))
        if len(row) == 4:
            data.append(row)
            row = []

    if row:
        while len(row) < 4:
            row.append('')
        data.append(row)

    table = Table(data, colWidths=[4.2 * cm] * 4, hAlign='LEFT')
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef6ff')),
                ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor('#bfdbfe')),
                ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#bfdbfe')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(table)


def _key_value_table(story, styles, rows, col_widths=None):
    data = [[_paragraph('<b>Indicador</b>', styles['Small']), _paragraph('<b>Total</b>', styles['Small'])]]
    data.extend([[_paragraph(label, styles['Small']), _paragraph(value, styles['Small'])] for label, value in rows])
    table = Table(data, colWidths=col_widths or [9 * cm, 4 * cm], hAlign='LEFT', repeatRows=1)
    table.setStyle(_table_style())
    story.append(table)


def _table_style():
    return TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.35, LINE),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]
    )


def _computer_table(story, styles, computadores, title='Tabela de computadores'):
    _section(story, styles, title)
    data = [
        [
            _paragraph('<b>ID</b>', styles['Small']),
            _paragraph('<b>Status</b>', styles['Small']),
            _paragraph('<b>Sala</b>', styles['Small']),
            _paragraph('<b>Usuario</b>', styles['Small']),
            _paragraph('<b>Sistema</b>', styles['Small']),
            _paragraph('<b>RAM</b>', styles['Small']),
            _paragraph('<b>Processador</b>', styles['Small']),
        ]
    ]
    for computador in computadores:
        data.append(
            [
                _paragraph(computador.id, styles['Small']),
                _paragraph(computador.status, styles['Small']),
                _paragraph(computador.sala, styles['Small']),
                _paragraph(computador.usuario or '-', styles['Small']),
                _paragraph(computador.sistema or '-', styles['Small']),
                _paragraph(computador.ram or '-', styles['Small']),
                _paragraph(computador.processador or '-', styles['Small']),
            ]
        )

    table = Table(
        data,
        colWidths=[2.1 * cm, 2.5 * cm, 3.1 * cm, 3.1 * cm, 3 * cm, 1.8 * cm, 4.6 * cm],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    story.append(table)


def _alerts_table(story, styles, alertas, title='Computadores com alerta'):
    _section(story, styles, title)
    if not alertas:
        story.append(Paragraph('Nenhum computador com alerta encontrado.', styles['Muted']))
        return

    data = [[_paragraph('<b>ID</b>', styles['Small']), _paragraph('<b>Sala</b>', styles['Small']), _paragraph('<b>Motivos</b>', styles['Small'])]]
    for item in alertas:
        computador = item['computador']
        data.append(
            [
                _paragraph(computador.id, styles['Small']),
                _paragraph(computador.sala or '-', styles['Small']),
                _paragraph(', '.join(item['motivos']), styles['Small']),
            ]
        )

    table = Table(data, colWidths=[3 * cm, 5 * cm, 9 * cm], repeatRows=1)
    table.setStyle(_table_style())
    story.append(table)


def _pendencias_table(story, styles, computadores, title='Pendencias do inventario'):
    _section(story, styles, title)
    pendentes = [
        {
            'computador': computador,
            'motivos': motivos_pendencia(computador),
        }
        for computador in computadores
        if motivos_pendencia(computador)
    ]
    if not pendentes:
        story.append(Paragraph('Nenhuma pendencia encontrada.', styles['Muted']))
        return

    data = [[_paragraph('<b>ID</b>', styles['Small']), _paragraph('<b>Sala</b>', styles['Small']), _paragraph('<b>Pendencias</b>', styles['Small'])]]
    for item in pendentes:
        computador = item['computador']
        data.append(
            [
                _paragraph(computador.id, styles['Small']),
                _paragraph(computador.sala or '-', styles['Small']),
                _paragraph(', '.join(item['motivos']), styles['Small']),
            ]
        )

    table = Table(data, colWidths=[3 * cm, 5 * cm, 9 * cm], repeatRows=1)
    table.setStyle(_table_style())
    story.append(table)


def _movimentacoes_table(story, styles, movimentacoes, title='Ultimas movimentacoes'):
    _section(story, styles, title)
    data = [
        [
            _paragraph('<b>Data</b>', styles['Small']),
            _paragraph('<b>Computador</b>', styles['Small']),
            _paragraph('<b>Acao</b>', styles['Small']),
            _paragraph('<b>Campo</b>', styles['Small']),
            _paragraph('<b>Anterior</b>', styles['Small']),
            _paragraph('<b>Novo</b>', styles['Small']),
        ]
    ]
    for mov in movimentacoes:
        data.append(
            [
                _paragraph(timezone.localtime(mov.data_hora).strftime('%d/%m/%Y %H:%M'), styles['Small']),
                _paragraph(mov.computador_id or mov.computador_identificador or '-', styles['Small']),
                _paragraph(mov.acao or '-', styles['Small']),
                _paragraph(mov.campo or '-', styles['Small']),
                _paragraph(mov.valor_anterior or '-', styles['Small']),
                _paragraph(mov.valor_novo or '-', styles['Small']),
            ]
        )

    if len(data) == 1:
        story.append(Paragraph('Nenhuma movimentacao encontrada.', styles['Muted']))
        return

    table = Table(
        data,
        colWidths=[3 * cm, 2.5 * cm, 3.8 * cm, 2.4 * cm, 4.2 * cm, 4.2 * cm],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    story.append(table)


def _status_rows(computadores):
    status = contar_status(computadores)
    return [
        ('Ativos', status['ativos']),
        ('Em manutencao', status['manutencao']),
        ('Desligados', status['desligados']),
        ('Reservas', status['reservas']),
    ]


def relatorio_geral_pdf(computadores, movimentacoes):
    styles = _styles()
    story = []
    total = computadores.count()
    alertas = computadores_com_alerta(computadores)
    pendentes_qs = computadores.filter(pendencias_q()).distinct()

    _cover(story, styles, 'Relatorio geral do inventario')
    _section(story, styles, 'Resumo geral')
    status = contar_status(computadores)
    _summary_cards(
        story,
        styles,
        [
            ('Total de computadores', total),
            ('Ativos', status['ativos']),
            ('Em manutencao', status['manutencao']),
            ('Desligados', status['desligados']),
            ('Reservas', status['reservas']),
            ('Setores/salas', computadores.exclude(sala='').values('sala').distinct().count()),
            ('Computadores com alerta', len(alertas)),
            ('Pendencias', pendentes_qs.count()),
        ],
    )

    _section(story, styles, 'Resumo por status')
    _key_value_table(story, styles, _status_rows(computadores))

    _section(story, styles, 'Resumo por sala')
    salas = [(item['label'], item['value']) for item in grafico_por_campo(computadores, 'sala', fallback='Sem sala')]
    _key_value_table(story, styles, salas)

    _alerts_table(story, styles, alertas)
    _pendencias_table(story, styles, computadores.order_by('sala', 'id'))
    _computer_table(story, styles, computadores.order_by('sala', 'id'), 'Tabela completa de computadores')
    _movimentacoes_table(story, styles, movimentacoes[:12], 'Ultimas movimentacoes')
    return _pdf(story, landscape(A4))


def relatorio_setor_pdf(computadores, sala):
    styles = _styles()
    story = []
    alertas = computadores_com_alerta(computadores)

    _cover(story, styles, f'Relatorio do setor: {sala}')
    _section(story, styles, 'Resumo do setor')
    status = contar_status(computadores)
    _summary_cards(
        story,
        styles,
        [
            ('Total de computadores', computadores.count()),
            ('Ativos', status['ativos']),
            ('Em manutencao', status['manutencao']),
            ('Desligados', status['desligados']),
            ('Reservas', status['reservas']),
            ('Alertas do setor', len(alertas)),
            ('Pendencias do setor', computadores.filter(pendencias_q()).distinct().count()),
        ],
    )
    _section(story, styles, 'Status')
    _key_value_table(story, styles, _status_rows(computadores))
    _alerts_table(story, styles, alertas, 'Alertas do setor')
    _pendencias_table(story, styles, computadores.order_by('id'), 'Pendencias do setor')
    _computer_table(story, styles, computadores.order_by('id'), 'Computadores do setor')
    return _pdf(story, landscape(A4))


def relatorio_alertas_pdf(computadores):
    styles = _styles()
    story = []
    alertas = computadores_com_alerta(computadores)

    _cover(story, styles, 'Relatorio de alertas')
    _section(story, styles, 'Resumo de alertas')
    _summary_cards(
        story,
        styles,
        [
            ('Computadores com alerta', len(alertas)),
            ('Em manutencao', sum(1 for item in alertas if 'Em manutencao' in item['motivos'])),
            ('Desligados', sum(1 for item in alertas if 'Desligado' in item['motivos'])),
            ('Pouca RAM', sum(1 for item in alertas if 'Pouca RAM' in item['motivos'])),
            ('Dados pendentes', sum(1 for item in alertas if 'Dados pendentes' in item['motivos'])),
            ('Sem usuario', sum(1 for item in alertas if 'Sem usuario' in item['motivos'])),
        ],
    )
    _alerts_table(story, styles, alertas, 'Lista de computadores com alerta')
    return _pdf(story, landscape(A4))


def relatorio_movimentacoes_pdf(movimentacoes, filtros=None):
    styles = _styles()
    story = []
    filtros = filtros or {}
    detalhes = []
    if filtros.get('computador'):
        detalhes.append(f"Computador: {filtros['computador']}")
    if filtros.get('data_inicio'):
        detalhes.append(f"Inicio: {filtros['data_inicio']}")
    if filtros.get('data_fim'):
        detalhes.append(f"Fim: {filtros['data_fim']}")

    _cover(story, styles, 'Relatorio de movimentacoes', ' | '.join(detalhes) if detalhes else 'Historico geral')
    _movimentacoes_table(story, styles, movimentacoes, 'Historico de movimentacoes')
    return _pdf(story, landscape(A4))
