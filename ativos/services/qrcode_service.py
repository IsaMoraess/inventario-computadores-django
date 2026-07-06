from base64 import b64encode
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import reverse

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H

from . import configuracao_service


A4_SIZE = (2480, 3508)
PDF_MARGIN = 120
PRINT_COLUMNS = 4
PRINT_ROWS = 5


def computador_public_url(computador, request=None):
    path = reverse('detalhe_computador', args=[computador.pk])
    public_url = configuracao_service.app_public_url()

    if public_url:
        return f'{public_url}{path}'

    if request is not None:
        return request.build_absolute_uri(path)

    return path


def safe_filename(value):
    invalid_chars = '<>:"/\\|?*'
    filename = ''.join('_' if char in invalid_chars else char for char in str(value))
    return filename.strip().strip('.') or 'qrcode'


def _font(size, bold=False):
    candidates = (
        ('arialbd.ttf', 'arial.ttf'),
        ('DejaVuSans-Bold.ttf', 'DejaVuSans.ttf'),
    )

    for bold_name, regular_name in candidates:
        try:
            return ImageFont.truetype(bold_name if bold else regular_name, size)
        except OSError:
            continue

    return ImageFont.load_default()


def _text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _truncate_text(draw, text, font, max_width):
    text = str(text or '-')

    if _text_width(draw, text, font) <= max_width:
        return text

    suffix = '...'
    while text and _text_width(draw, f'{text}{suffix}', font) > max_width:
        text = text[:-1]

    return f'{text}{suffix}' if text else suffix


def _draw_centered_text(draw, text, y, font, fill, width):
    text = str(text or '-')
    x = (width - _text_width(draw, text, font)) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _add_logo_badge(image):
    draw = ImageDraw.Draw(image)
    size = image.size[0]
    badge_size = max(int(size * 0.22), 96)
    badge_x = (size - badge_size) // 2
    badge_y = (size - badge_size) // 2
    radius = max(int(badge_size * 0.12), 12)

    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_size, badge_y + badge_size),
        radius=radius,
        fill='white',
        outline='#38bdf8',
        width=max(int(size * 0.008), 4),
    )

    logo = _load_logo_image()
    if logo is not None:
        logo_size = int(badge_size * 0.78)
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        logo_layer = Image.new('RGBA', (badge_size, badge_size), (255, 255, 255, 0))
        logo_layer.paste(
            logo,
            ((badge_size - logo.size[0]) // 2, (badge_size - logo.size[1]) // 2),
            logo,
        )
        image.paste(logo_layer, (badge_x, badge_y), logo_layer)
        return

    inner_margin = max(int(badge_size * 0.1), 10)
    draw.rounded_rectangle(
        (
            badge_x + inner_margin,
            badge_y + inner_margin,
            badge_x + badge_size - inner_margin,
            badge_y + badge_size - inner_margin,
        ),
        radius=max(int(radius * 0.7), 8),
        fill='#0c2433',
    )

    jr_font = _font(max(int(badge_size * 0.34), 28), bold=True)
    group_font = _font(max(int(badge_size * 0.12), 12), bold=True)
    center_y = badge_y + badge_size / 2
    _draw_centered_text(draw, 'JR', center_y - badge_size * 0.28, jr_font, '#7dd3fc', size)
    _draw_centered_text(draw, 'GRUPO', center_y + badge_size * 0.14, group_font, '#dff6ff', size)


def _load_logo_image():
    config_logo = configuracao_service.logo_path()
    if config_logo and Path(config_logo).exists():
        try:
            return Image.open(config_logo).convert('RGBA')
        except OSError:
            pass

    logo_path = finders.find('img/logo_jr.png')

    if not logo_path:
        logo_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'logo_jr.png'

    if not logo_path or not Path(logo_path).exists():
        return None

    try:
        return Image.open(logo_path).convert('RGBA')
    except OSError:
        return None


def qr_image(data, size=900, border=4):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=18,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(fill_color='#06111f', back_color='white').convert('RGB')
    image = image.resize((size, size), Image.Resampling.NEAREST)
    _add_logo_badge(image)
    return image


def computador_qr_image(computador, request=None, size=900):
    return qr_image(computador_public_url(computador, request), size=size)


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def computador_qr_png_bytes(computador, request=None, size=900):
    return png_bytes(computador_qr_image(computador, request, size=size))


def computador_qr_data_url(computador, request=None, size=420):
    codigo = b64encode(computador_qr_png_bytes(computador, request, size=size)).decode('ascii')
    return f'data:image/png;base64,{codigo}'


def _qr_label_image(computador, request=None, width=520, height=620, qr_size=360):
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=24, outline='#dbeafe', width=3)

    title_font = _font(42, bold=True)
    meta_font = _font(25)
    meta_bold = _font(25, bold=True)
    small_font = _font(19, bold=True)

    qr = computador_qr_image(computador, request, size=qr_size)
    qr_x = (width - qr_size) // 2
    image.paste(qr, (qr_x, 34))

    y = qr_size + 58
    _draw_centered_text(draw, str(computador.id), y, title_font, '#06111f', width)
    y += 58

    max_width = width - 64
    sala = _truncate_text(draw, f'Sala: {computador.sala or "-"}', meta_font, max_width)
    usuario = _truncate_text(draw, f'Usuario: {computador.usuario or "-"}', meta_font, max_width)

    _draw_centered_text(draw, sala, y, meta_font, '#25364d', width)
    y += 38
    _draw_centered_text(draw, usuario, y, meta_font, '#25364d', width)

    footer = configuracao_service.get_config().nome_empresa or 'JR Grupo'
    footer_y = height - 44
    footer_w = _text_width(draw, footer, small_font)
    footer_h = _text_height(draw, footer, small_font)
    draw.rounded_rectangle(
        (
            (width - footer_w) / 2 - 16,
            footer_y - 8,
            (width + footer_w) / 2 + 16,
            footer_y + footer_h + 10,
        ),
        radius=12,
        fill='#e0f2fe',
    )
    _draw_centered_text(draw, footer, footer_y, small_font, '#075985', width)

    return image


def _pdf_bytes_from_pages(pages):
    buffer = BytesIO()
    first_page, *other_pages = pages
    first_page.save(
        buffer,
        format='PDF',
        resolution=300,
        save_all=True,
        append_images=other_pages,
    )
    return buffer.getvalue()


def computador_qr_pdf_bytes(computador, request=None):
    page = Image.new('RGB', A4_SIZE, 'white')
    label = _qr_label_image(computador, request, width=1000, height=1180, qr_size=760)
    x = (A4_SIZE[0] - label.size[0]) // 2
    y = (A4_SIZE[1] - label.size[1]) // 2
    page.paste(label, (x, y))
    return _pdf_bytes_from_pages([page])


def qrcodes_zip_bytes(computadores, request=None, size=900):
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        for computador in computadores:
            filename = f'{safe_filename(computador.id)}.png'
            archive.writestr(filename, computador_qr_png_bytes(computador, request, size=size))

    return buffer.getvalue()


def folha_impressao_pdf_bytes(computadores, request=None):
    pages = []
    cell_width = (A4_SIZE[0] - PDF_MARGIN * 2) // PRINT_COLUMNS
    cell_height = (A4_SIZE[1] - PDF_MARGIN * 2) // PRINT_ROWS
    label_width = cell_width - 34
    label_height = cell_height - 32
    qr_size = min(340, label_width - 90)
    por_pagina = PRINT_COLUMNS * PRINT_ROWS

    computadores = list(computadores)
    if not computadores:
        computadores = []

    for page_start in range(0, max(len(computadores), 1), por_pagina):
        page = Image.new('RGB', A4_SIZE, 'white')
        draw = ImageDraw.Draw(page)
        header_font = _font(42, bold=True)
        empresa = configuracao_service.get_config().nome_empresa or 'JR Grupo'
        draw.text((PDF_MARGIN, 50), f'QR Codes - {empresa}', font=header_font, fill='#06111f')

        for index, computador in enumerate(computadores[page_start:page_start + por_pagina]):
            col = index % PRINT_COLUMNS
            row = index // PRINT_COLUMNS
            x = PDF_MARGIN + col * cell_width + 17
            y = PDF_MARGIN + row * cell_height + 50
            label = _qr_label_image(
                computador,
                request,
                width=label_width,
                height=label_height,
                qr_size=qr_size,
            )
            page.paste(label, (x, y))

        pages.append(page)

    return _pdf_bytes_from_pages(pages)
