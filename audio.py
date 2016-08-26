import pygame
import sys
import time

pygame.mixer.init(44100)
pygame.mixer.music.load(sys.argv[1])
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    sys.stdout.write('%d\r' % pygame.mixer.music.get_pos())
    time.sleep(0.01)

pygame.mixer.quit()
