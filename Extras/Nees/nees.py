#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import time
import random
import signal
from PIL import Image, ImageDraw
from waveshare_epd import epd7in5_V2 as epd_driver


def exithandler(signum, frame):
    try:
        epd_driver.epdconfig.module_exit()
    finally:
        sys.exit()


signal.signal(signal.SIGTERM, exithandler)
signal.signal(signal.SIGINT, exithandler)

epd = epd_driver.EPD()
epd.init()
epd.Clear()

while 1:
    type = random.randint(0, 2)

    print('Drawing style %d' % type)

    pageSize = (800, 480)

    gridX = int(random.triangular(1, 18, 4))
    gridY = int(gridX * 0.6)
    if gridY < 1:
        gridY = 1
    print('grid of %d by %d blocks' % (gridX, gridY))
    size = (int(pageSize[0] / gridX), int(pageSize[0] / gridX))
    spacerX = (pageSize[0] - size[0] * gridX) / gridX
    spacerY = (pageSize[1] - size[1] * gridY) / gridY

    print('each block is %d by %d' % size)

    print('with x space of %d and y space of %d' % (spacerX, spacerY))
    print('making total width of %d and height of %d' % ((size[0] + spacerX) * gridX, (size[1] + spacerY) * gridY))

    vertices = random.randint(2, 40)

    spacer = 0

    # img = Image.new("RGB", pageSize, color='white')

    img = Image.new('1', pageSize, color=1)

    d = ImageDraw.Draw(img)

    def clip(val, min_, max_):
        return (min_ if val < min_ else (max_ if val > max_ else val))

    if type == 0:
        for x in range(0, gridX):
            for y in range(0, gridY):
                randomX = random.randint(0, size[0])
                randomY = random.randint(0, size[1])
                offsetX = x * (size[0] + spacerX)
                offsetY = y * (size[1] + spacerY)
                points = [(randomX, randomY)]
                line = [(randomX + offsetX, randomY + offsetY)]

                dir = random.randint(0, 2)

                for i in range(1, vertices):
                    oldX = points[i - 1][0]
                    oldY = points[i - 1][1]
                    newX = oldX + random.randint(-oldX, size[0] - oldX - 1) * dir
                    newY = oldY + random.randint(-oldY, size[1] - oldY - 1) * (not dir)
                    newX = clip(newX, 0, size[0])
                    newY = clip(newY, 0, size[1])
                    points.append((newX, newY))
                    line.append((newX + offsetX, newY + offsetY))
                    dir = not dir

                points.append((randomX, randomY))
                line.append((randomX + offsetX, randomY + offsetY))

        #         d.line(points,0,2)

                d.line(line, 0, 1)
    if type == 1:

        for x in range(0, gridX):
            for y in range(0, gridY):
                randomX = random.randint(0, size[0])
                randomY = random.randint(0, size[1])
                offsetX = x * (size[0] + spacerX)
                offsetY = y * (size[1] + spacerY)
                points = [(randomX, randomY)]
                line = [(randomX + offsetX, randomY + offsetY)]

                dir = random.randint(0, 2)

                for i in range(1, vertices):
                    oldX = points[i - 1][0]
                    oldY = points[i - 1][1]
                    newX = oldX + random.randint(-oldX, size[0] - oldX - 1)
                    newY = oldY + random.randint(-oldY, size[1] - oldY - 1)
                    newX = clip(newX, 0, size[0])
                    newY = clip(newY, 0, size[1])
                    points.append((newX, newY))
                    line.append((newX + offsetX, newY + offsetY))
                    dir = not dir

                points.append((randomX, randomY))
                line.append((randomX + offsetX, randomY + offsetY))

        #         d.line(points,0,2)

                d.line(line, 0, 1)

    if type == 2:

        for x in range(0, gridX):
            for y in range(0, gridY):
                randomX = random.randint(0, size[0])
                randomY = random.randint(0, size[1])
                offsetX = x * (size[0] + spacerX)
                offsetY = y * (size[1] + spacerY)
                points = [(randomX, randomY)]
                line = [(randomX + offsetX, randomY + offsetY)]

                dir = random.randint(0, 2)

                for i in range(1, vertices):
                    oldX = points[i - 1][0]
                    oldY = points[i - 1][1]
                    newX = oldX + random.randint(-oldX, size[0] - oldX - 1) * dir
                    newY = oldY + random.randint(-oldY, size[1] - oldY - 1) * (not dir)
                    newX = clip(newX, 0, size[0])
                    newY = clip(newY, 0, size[1])
                    points.append((newX, newY))
                    line.append((newX + offsetX, newY + offsetY))
                    dir = not dir

                d.line(line, 0, 1)
    if type == 3:

        gridX = 1
        gridY = 1
        print('grid of %d by %d blocks' % (gridX, gridY))
        size = (pageSize[0] / gridX, pageSize[0] / gridX)
        spacerX = (pageSize[0] - size[0] * gridX) / gridX
        spacerY = (pageSize[1] - size[1] * gridY) / gridY

        vertices = random.randint(10, 200)
        fuzz = random.randint(0, 100)
        xTilt = random.randint(-100, 100)
        yTilt = random.randint(-80, 80)
        radius = random.randint(20, 80)
        dir = random.randint(0, 2)
        for x in range(0, gridX):
            for y in range(0, gridY):
                randomX = random.randint(0, size[0])
                randomY = random.randint(0, size[1])
                lineLengthX = size[0] - radius * 2
                lineLengthY = size[1] - radius * 2
                offsetX = x * (size[0] + spacerX)
                offsetY = y * (size[1] + spacerY)
                line = [(random.randint(-radius, radius) + lineLengthX * dir, offsetY - radius + random.randint(-radius, radius))]
                line2 = [offsetX - radius + random.randint(-radius, radius), random.randint(-radius, radius) + lineLengthY * dir]

                for i in range(1, vertices):
                    dir = not dir
                    line.append((radius + random.randint(-radius, radius) + lineLengthX * dir + random.randint(-fuzz, fuzz), yTilt * dir + offsetY + random.randint(-radius, radius) + random.randint(-fuzz, fuzz)))
                    line2.append((xTilt * dir + offsetX + random.randint(-radius, radius) + random.randint(-fuzz, fuzz), radius + random.randint(-radius, radius) + lineLengthY * dir + random.randint(-fuzz, fuzz)))
        width = 1
        d.line(line, 0, width)
        d.line(line2, 0, width)

    epd.display(epd.getbuffer(img))
    time.sleep(60)
