from PIL import Image, ImageDraw, ImageFont
import textwrap

import os
from PIL import ImageFont

# Ruta relativa a la fuente en tu proyecto



def multiple_text_image(
    parrafos,
    colores=None,
    ancho=190,
    alto=190,
    ruta_fuente='assets/Clash_Regular.otf',
    tam_fuente=35,
    max_line_length=23,
    spacing_linea=8,
    spacing_parrafo=15
):
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 200))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(ruta_fuente, tam_fuente)
    except IOError:
        font = ImageFont.load_default()

    if colores is None:
        colores = ['white'] * len(parrafos)

    # Dividir cada párrafo en líneas
    lineas_por_parrafo = [textwrap.wrap(p, width=max_line_length) for p in parrafos]

    bbox = draw.textbbox((0, 0), 'A', font=font)
    linea_altura = bbox[3] - bbox[1] + spacing_linea

    total_lineas = sum(len(lp) for lp in lineas_por_parrafo)
    total_espacios_parrafo = spacing_parrafo * (len(parrafos) - 1)
    bloque_altura = linea_altura * total_lineas + total_espacios_parrafo

    y_texto = (alto - bloque_altura) / 2

    for i, lineas in enumerate(lineas_por_parrafo):
        color = colores[i % len(colores)]  # Color que corresponde al párrafo
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            w = bbox[2] - bbox[0]
            x_texto = (ancho - w) / 2
            draw.text((x_texto, y_texto), linea, font=font, fill=color)
            y_texto += linea_altura
        y_texto += spacing_parrafo

    return img