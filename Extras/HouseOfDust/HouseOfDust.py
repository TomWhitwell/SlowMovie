#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import sys
import random
import textwrap
import signal
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2 as epd_driver


def exithandler(signum, frame):
    try:
        epd_driver.epdconfig.module_exit()
    finally:
        sys.exit()


signal.signal(signal.SIGTERM, exithandler)
signal.signal(signal.SIGINT, exithandler)

try:
    epd = epd_driver.EPD()
    epd.init()
    epd.Clear()
except:
    print('*********no screen attached')

material = [
    'SAND',
    'DUST',
    'LEAVES',
    'PAPER',
    'TIN',
    'ROOTS',
    'BRICK',
    'STONE',
    'DISCARDED CLOTHING',
    'GLASS',
    'STEEL',
    'PLASTIC',
    'MUD',
    'BROKEN DISHES',
    'WOOD',
    'STRAW',
    'WEEDS',
    ]

location = [
    'IN A GREEN, MOSSY TERRAIN',
    'IN AN OVERPOPULATED AREA',
    'BY THE SEA',
    'BY AN ABANDONED LAKE',
    'IN A DESERTED FACTORY',
    'IN DENSE WOODS',
    'IN JAPAN',
    'AMONG SMALL HILLS',
    'IN SOUTHERN FRANCE',
    'AMONG HIGH MOUNTAINS',
    'ON AN ISLAND',
    'IN A COLD, WINDY CLIMATE',
    'IN A PLACE WITH BOTH HEAVY RAIN AND BRIGHT SUN',
    'IN A DESERTED AIRPORT',
    'IN A HOT CLIMATE',
    'INSIDE A MOUNTAIN',
    'ON THE SEA',
    'IN MICHIGAN',
    'IN HEAVY JUNGLE UNDERGROWTH',
    'BY A RIVER',
    'AMONG OTHER HOUSES',
    'IN A DESERTED CHURCH',
    'IN A METROPOLIS',
    'UNDERWATER',
    ]

light_source = ['CANDLES', 'ALL AVAILABLE LIGHTING', 'ELECTRICITY', 'NATURAL LIGHT']

inhabitants = [
    'PEOPLE WHO SLEEP VERY LITTLE',
    'VEGETARIANS',
    'HORSES AND BIRDS',
    'PEOPLE SPEAKING MANY LANGUAGES WEARING LITTLE OR NO CLOTHING',
    'ALL RACES OF MEN REPRESENTED WEARING PREDOMINANTLY RED CLOTHING',
    'CHILDREN AND OLD PEOPLE',
    'VARIOUS BIRDS AND FISH',
    'LOVERS',
    'PEOPLE WHO ENJOY EATING TOGETHER',
    'PEOPLE WHO EAT A GREAT DEAL',
    'COLLECTORS OF ALL TYPES',
    'FRIENDS AND ENEMIES',
    'PEOPLE WHO SLEEP ALMOST ALL THE TIME',
    'VERY TALL PEOPLE',
    'AMERICAN INDIANS',
    'LITTLE BOYS',
    'PEOPLE FROM MANY WALKS OF LIFE',
    'WOMEN WEARING ALL COLORS',
    'FRIENDS',
    'FRENCH AND GERMAN SPEAKING PEOPLE',
    'FISHERMEN AND FAMILIES',
    'PEOPLE WHO LOVE TO READ',
    ]

while 1:
    color = (55, 65, 65)

    size = (800, 480)
    background = Image.new('RGB', size, color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(background)

    # font = ImageFont.truetype("dotmatrix.TTF", 24)

    font = ImageFont.truetype('daisywhl.otf', 28)
    ruleCount = 8

    tab = '   '
    tabSize = font.getsize(tab)[0]  # six spaces for a tab
    lineHeight = font.getsize('M')[1]
    charWidth = font.getsize('M')[0]
    lineSpacing = 2

    ruleHeight = lineHeight * lineSpacing / ruleCount
    rules = int(size[1] / ruleHeight)
    for x in range(rules):
        shape = [(0, x * ruleHeight), (size[0], x * ruleHeight)]
        if x / ruleCount % 2 == 1:
            for y in range(0, size[0], 4):
                shape = [(y, x * ruleHeight), (y, x * ruleHeight)]
                draw.line(shape, fill=(0, 0, 0, 0), width=0)

    y_text = 3
    x_text = 20

    random.shuffle(material)
    random.shuffle(location)
    random.shuffle(light_source)
    random.shuffle(inhabitants)

    for x in range(4):
        x_text = 20
        text = ['A HOUSE OF ' + material[x]]
        text.append(location[x])
        text.append('USING ' + light_source[x])
        text.append('INHABITED BY ' + inhabitants[x])

        for line in text:
            columns = int((size[0] - x_text) / charWidth)
            lines = textwrap.wrap(line, width=columns, replace_whitespace=False)
            for line in lines:
                draw.text((x_text, y_text), line, color, font=font)
                y_text += ruleHeight * ruleCount
            x_text += tabSize
        y_text += ruleHeight * ruleCount

    background = background.convert(mode='1', dither=Image.NONE)
    epd.display(epd.getbuffer(background))
    time.sleep(60)
