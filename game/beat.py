import pygame

LANES = 4
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LABELS = ['D', 'F', 'J', 'K']
LANE_COLORS = [(220, 80, 80), (80, 180, 220), (100, 220, 100), (220, 180, 60)]

class Note:
    WIDTH = 70
    HEIGHT = 20

    def __init__(self, lane, y=-30, speed=4, is_hold=False, hold_duration_frames=60):
        self.lane = lane
        self.y = y
        self.speed = speed
        self.hit = False
        self.missed = False
        self.is_hold = is_hold
        self.hold_duration_frames = hold_duration_frames if is_hold else 0
        self.holding = False
        self.hold_progress = 0
        self.completed = False

    def update(self):
        if not self.holding:
            self.y += self.speed
        else:
            self.hold_progress += 1
            if self.hold_progress >= self.hold_duration_frames:
                self.completed = True

    def get_rect(self, lane_x):
        return pygame.Rect(lane_x - self.WIDTH // 2, int(self.y), self.WIDTH, self.HEIGHT)

    def get_tail_height(self):
        return int(self.hold_duration_frames * self.speed)