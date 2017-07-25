from music21 import *
import pygame
import pygame.draw
import sys
import time
import math
import random

if '-f' in sys.argv:
    sys.argv.remove('-f')
    mode = pygame.FULLSCREEN

FIDDLE = 0.5
if len(sys.argv) > 3:
    FIDDLE = float(sys.argv[3])

def getPitchRange(stream):
    pitches = list(map(lambda note: note.pitch.ps, filter(lambda t: isinstance(t, note.Note), stream.flat.notes)))
    return (min(pitches), max(pitches))

def getPartNumber(score, note):
    return list(score.parts).index(note.activeSite.derivation.origin)

def toColor(n):
    return (255 - (n * 219 % 255), n * 47 % 255, n * 111 % 255)

pygame.init()
WIDTH, HEIGHT = 1920, 1080
mode = 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), mode, 32)

score = converter.parse(sys.argv[1])
metronome = tempo.MetronomeMark('slow', number=int(sys.argv[2]))

dots = []
notes = list(score.flat.elements)

sp = midi.realtime.StreamPlayer(score)

startTime = None
curMeasure = 0

chords = score.chordify()
cr = analysis.reduceChords.ChordReducer()
key = score.analyze('key')
cadence = []
backgroundColor = (0, 0, 0)
targetBgColor = (0, 0, 0)
timesig = (4, 4)
minPitch, maxPitch = getPitchRange(score)

background = pygame.Surface((WIDTH, HEIGHT))
background.fill((70, 70, 70))

cadenceMap = {
    ('IV', 'I'): (180, 180, 255),
    ('iv', 'i'): (255, 255, 180),
    ('V', 'I'): (255, 180, 180),
    ('v', 'i'): (180, 255, 255),
    ('I', 'IV'): (180, 255, 127),
    ('i', 'iv'): (255, 180, 255)
}

redChords = []
rings = []
curChord = None
streak = 0
dumb = 0

def update(*args):
    # :-(
    global startTime, curMeasure, cadence, backgroundColor, targetBgColor, timesig, rings, curChord, streak, dumb
    if not startTime:
        startTime = time.time()

    t = time.time()
    while notes:
        while not notes[0].measureNumber:
            notes.pop(0)
        offset = score.measure(notes[0].measureNumber).offset + notes[0].offset
        sec = offset * metronome.secondsPerQuarter() - FIDDLE
        if (t - startTime) < sec:
            break
        thing = notes.pop(0)
        if isinstance(thing, note.Note):
            dots.append([thing.pitch.ps, thing.duration, offset, 255, getPartNumber(score, thing), streak])
        elif isinstance(thing, chord.Chord):
            for pitch in thing.pitches:
                dots.append([pitch.ps, thing.duration, offset, 255, getPartNumber(score, thing), streak])
        elif isinstance(thing, meter.TimeSignature):
            timesig = (thing.numerator, thing.denominator)
        
        if thing.measureNumber != curMeasure:
            # Measure change; figure out the new chords.
            curMeasure = thing.measureNumber
            #cm = cr.reduceMeasureToNChords(chords.measure(curMeasure), 4)
            cm = chords.measure(curMeasure)
            for ch in cm.notes:
                redChords.append(ch)

    while redChords:
        offset = score.measure(redChords[0].measureNumber).offset + redChords[0].offset
        sec = offset * metronome.secondsPerQuarter() - FIDDLE
        if (t - startTime) < sec:
            break
        ch = redChords.pop(0)
        numeral = roman.romanNumeralFromChord(ch, key).figure.strip('0123456789b#')
        if numeral and numeral.lower() == 'v':
            streak += 1
        else:
            streak = 0
        color = cadenceMap.get((curChord, numeral), None)
        curChord = numeral
        print(curChord, streak)
        if color:
            print(color)
            #rings.insert(0, color)
            #background.fill((100, 100, 100))
            pygame.draw.circle(background, color, (WIDTH/2+random.randrange(-3, 4), HEIGHT/2+random.randrange(-3, 4)), 6)
            #scaled = pygame.transform.smoothscale(background, (WIDTH*2, HEIGHT*2))
            #background.blit(scaled, (0, 0), (WIDTH/2, HEIGHT/2, WIDTH, HEIGHT))
            #for i, color in list(enumerate(rings))[::-1]:
            #    pygame.draw.circle(background, color, (WIDTH/2, HEIGHT/2), (i+1)*50)

    bigW, bigH = WIDTH*1.05, HEIGHT*1.05
    scaled = pygame.transform.smoothscale(background, (int(round(bigW)), int(round(bigH))))
    print((bigW, bigH, round((bigW-WIDTH)/2), round((bigH-HEIGHT)/2), WIDTH, HEIGHT))
    background.blit(scaled, (0, 0), (round((bigW-WIDTH)/2)-(3*(dumb%2)-2), round((bigH-HEIGHT)/2)-(3*(dumb%2)-2), WIDTH, HEIGHT))
    dumb += 1
    screen.blit(background, (0, 0))
    curDots = dots[:]
    partVerts = [[] for _ in range(len(list(score.parts)))]
    for dot in curDots:
        pitch, duration, offset, alpha, part, tStreak = dot
        color = toColor(part)
        offsetSec = metronome.secondsPerQuarter() * offset
        if t - startTime >= offsetSec + metronome.durationToSeconds(duration) - FIDDLE:
            dot[3] /= 1.1
            if dot[3] < 0.1:
                dots.remove(dot)
        radius = 16 + 8 * tStreak
        surf = pygame.Surface((radius*2, radius*2))
        beat = offset % (timesig[0] * timesig[1] / 4.0)
        theta = beat / (timesig[0] * timesig[1] / 4.0) * 2 * math.pi
        x = int((60+(pitch-minPitch)*(400.0 / (maxPitch - minPitch)))*math.cos(math.pi/2+theta) + WIDTH/2)
        y = int((60+(pitch-minPitch)*(400.0 / (maxPitch - minPitch)))*math.sin(math.pi/2+theta) + HEIGHT/2)
        surf.set_alpha(alpha)
        pygame.draw.circle(surf, color, (radius, radius), radius)
        surf.set_colorkey((0, 0, 0))
        #screen.blit(surf, (int(80+(offsetSec*120 % (WIDTH-160))), int(300-(pitch-60)*10)))
        screen.blit(surf, (x-radius, y-radius))
        if alpha == 255:
            pygame.draw.line(screen, (100, 200, 100), (WIDTH/2, HEIGHT/2), (x, y))
        partVerts[part].append((x, y))
    for part, verts in enumerate(partVerts):
        if len(verts) >= 4:
            draw_bezier(screen, verts[-4:], toColor(part))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            exit()
    pygame.display.flip()

def draw_bezier(surf, vertices, color=(0, 0, 0)):
    points = compute_bezier_points(vertices)
    pygame.draw.lines(surf, color, False, points, 2)

def compute_bezier_points(vertices, numPoints=None):
    if numPoints is None:
        numPoints = 30
    if numPoints < 2 or len(vertices) != 4:
        return None
 
    result = []
 
    b0x = vertices[0][0]
    b0y = vertices[0][1]
    b1x = vertices[1][0]
    b1y = vertices[1][1]
    b2x = vertices[2][0]
    b2y = vertices[2][1]
    b3x = vertices[3][0]
    b3y = vertices[3][1]
 
 
 
    # Compute polynomial coefficients from Bezier points
    ax = -b0x + 3 * b1x + -3 * b2x + b3x
    ay = -b0y + 3 * b1y + -3 * b2y + b3y
 
    bx = 3 * b0x + -6 * b1x + 3 * b2x
    by = 3 * b0y + -6 * b1y + 3 * b2y
 
    cx = -3 * b0x + 3 * b1x
    cy = -3 * b0y + 3 * b1y
 
    dx = b0x
    dy = b0y
 
    # Set up the number of steps and step size
    numSteps = numPoints - 1 # arbitrary choice
    h = 1.0 / numSteps # compute our step size
 
    # Compute forward differences from Bezier points and "h"
    pointX = dx
    pointY = dy
 
    firstFDX = ax * (h * h * h) + bx * (h * h) + cx * h
    firstFDY = ay * (h * h * h) + by * (h * h) + cy * h
 
 
    secondFDX = 6 * ax * (h * h * h) + 2 * bx * (h * h)
    secondFDY = 6 * ay * (h * h * h) + 2 * by * (h * h)
 
    thirdFDX = 6 * ax * (h * h * h)
    thirdFDY = 6 * ay * (h * h * h)
 
    # Compute points at each step
    result.append((int(pointX), int(pointY)))
 
    for i in range(numSteps):
        pointX += firstFDX
        pointY += firstFDY
 
        firstFDX += secondFDX
        firstFDY += secondFDY
 
        secondFDX += thirdFDX
        secondFDY += thirdFDY
 
        result.append((int(pointX), int(pointY)))
 
    return result

sp.play(busyFunction=update)
