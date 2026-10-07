import pygame
import random
import math
import array
from game.beat import Note, LANES, LANE_KEYS, LANE_LABELS, LANE_COLORS

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
BG = (15, 10, 25)
LANE_W = WIDTH // LANES

def create_beep_sound(frequency=440, duration=0.1, volume=0.3):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        t = float(i) / sample_rate
        val = int(32767 * volume * math.sin(2.0 * math.pi * frequency * t))
        buf.append(val)
        buf.append(val) # stereo
    return pygame.mixer.Sound(buffer=buf)

class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 40, bold=True)
        
        # Audio generation (Task 1)
        self.hit_sound = create_beep_sound(880, 0.08, 0.4)
        self.miss_sound = create_beep_sound(220, 0.12, 0.3)

        self.bpm = 120
        self.reset()

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0
        self.speed = 5
        self.frame = 0
        self.feedback = []  # [text, color, ttl, x, y]
        self.game_over = False

        # Task 4 Breakdown Counters
        self.perfect_count = 0
        self.great_count = 0
        self.ok_count = 0
        self.miss_count = 0

        # Task 3 BPM-Synced Spawning setup
        self.frames_per_beat = int(FPS * 60 / self.bpm)
        self.beat_counter = 0

        # Track key states for hold notes
        self.lane_pressed = [False] * LANES

    def spawn_note(self):
        lane = random.randint(0, LANES - 1)
        is_hold = random.random() < 0.25 # 25% chance of hold note
        self.notes.append(Note(lane, y=-30, speed=self.speed, is_hold=is_hold, hold_duration_frames=FPS))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif not self.game_over:
                    for i, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.lane_pressed[i] = True
                            self.process_tap(i)

            elif event.type == pygame.KEYUP:
                if not self.game_over:
                    for i, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.lane_pressed[i] = False
                            self.process_release(i)
        return True

    def process_tap(self, lane):
        best = None
        best_dist = 9999
        for note in self.notes:
            if note.lane == lane and not note.hit and not note.missed and not note.holding:
                dist = abs(note.y + Note.HEIGHT // 2 - HIT_Y)
                if dist < best_dist:
                    best_dist = dist
                    best = note

        lane_x = lane * LANE_W + LANE_W // 2
        if best and best_dist <= HIT_WINDOW:
            self.hit_sound.play() # Task 1
            
            if best_dist < 8:
                grade, pts = "PERFECT", 300
                col = (255, 220, 0)
                self.perfect_count += 1
            elif best_dist < 18:
                grade, pts = "GREAT", 200
                col = (100, 220, 100)
                self.great_count += 1
            else:
                grade, pts = "OK", 100
                col = (180, 180, 255)
                self.ok_count += 1

            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            self.score += pts * max(1, self.combo // 5)
            self.feedback.append([grade, col, 40, lane_x, HIT_Y - 30])

            if best.is_hold:
                best.holding = True
            else:
                best.hit = True
        else:
            self.miss_sound.play()
            self.combo = 0
            self.misses += 1
            self.miss_count += 1
            self.feedback.append(["MISS", (220, 60, 60), 40, lane_x, HIT_Y - 30])

    def process_release(self, lane):
        for note in self.notes:
            if note.lane == lane and note.holding and not note.completed:
                # Early release on hold note
                note.holding = False
                note.missed = True
                self.misses += 1
                self.miss_count += 1
                self.combo = 0
                lane_x = lane * LANE_W + LANE_W // 2
                self.feedback.append(["HOLD FAIL", (220, 60, 60), 40, lane_x, HIT_Y - 30])

    def update(self):
        if self.game_over:
            return
            
        self.frame += 1

        # Task 3: BPM Sync Spawning
        if self.frame % self.frames_per_beat == 0:
            self.beat_counter += 1
            self.spawn_note()

            if self.beat_counter % 20 == 0:
                self.speed = min(10, self.speed + 0.5)

        for note in self.notes:
            if note.holding:
                if not self.lane_pressed[note.lane]:
                    self.process_release(note.lane)
                else:
                    note.update()
                    if note.completed:
                        note.hit = True
                        note.holding = False
                        self.score += 150
            else:
                note.update()
                if not note.hit and not note.missed and note.y > HIT_Y + HIT_WINDOW + Note.HEIGHT:
                    note.missed = True
                    self.misses += 1
                    self.miss_count += 1
                    self.combo = 0
                    self.miss_sound.play()

        self.notes = [n for n in self.notes if not (n.hit or (n.missed and n.y > HEIGHT + 10))]
        self.feedback = [[t, c, ttl - 1, x, y] for t, c, ttl, x, y in self.feedback if ttl > 1]

        if self.misses >= 15:
            self.game_over = True

    def draw(self):
        self.screen.fill(BG)

        # Lane dividers
        for i in range(LANES + 1):
            pygame.draw.line(self.screen, (40, 40, 60), (i * LANE_W, 0), (i * LANE_W, HEIGHT), 1)

        # Hit line
        pygame.draw.line(self.screen, (80, 80, 100), (0, HIT_Y), (WIDTH, HIT_Y), 2)
        for i in range(LANES):
            lx = i * LANE_W + LANE_W // 2
            pygame.draw.rect(self.screen, LANE_COLORS[i],
                             pygame.Rect(lx - Note.WIDTH // 2, HIT_Y - 12, Note.WIDTH, 24), border_radius=6)
            lbl = self.font.render(LANE_LABELS[i], True, (20, 20, 20))
            self.screen.blit(lbl, (lx - lbl.get_width() // 2, HIT_Y - 10))

        # Notes
        for note in self.notes:
            if note.hit:
                continue
            lx = note.lane * LANE_W + LANE_W // 2

            if note.is_hold:
                tail_h = note.get_tail_height()
                tail_rect = pygame.Rect(lx - Note.WIDTH // 4, int(note.y) - tail_h, Note.WIDTH // 2, tail_h)
                pygame.draw.rect(self.screen, (150, 150, 220), tail_rect)

            rect = note.get_rect(lx)
            pygame.draw.rect(self.screen, LANE_COLORS[note.lane], rect, border_radius=5)

        # Feedback
        for text, color, ttl, x, y in self.feedback:
            surf = self.font.render(text, True, color)
            surf.set_alpha(min(255, ttl * 7))
            self.screen.blit(surf, (x - surf.get_width() // 2, y))

        # HUD
        sc = self.font.render(f"Score: {self.score}", True, (220, 220, 220))
        co = self.font.render(f"Combo: {self.combo}x", True, (255, 220, 80))
        mi = self.font.render(f"Misses: {self.misses}/15", True, (220, 100, 100))
        bpm_txt = self.font.render(f"BPM: {self.bpm}", True, (120, 200, 120))

        self.screen.blit(sc, (10, 10))
        self.screen.blit(co, (10, 35))
        self.screen.blit(mi, (WIDTH - 170, 10))
        self.screen.blit(bpm_txt, (WIDTH - 170, 35))

        # Task 4: Grade Summary Screen on Game Over
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            self.screen.blit(ov, (0, 0))

            total_notes = self.perfect_count + self.great_count + self.ok_count + self.miss_count
            accuracy = ((self.perfect_count + self.great_count + self.ok_count) / max(1, total_notes)) * 100

            title = self.big_font.render("GAME OVER", True, (220, 60, 60))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

            stats = [
                f"Final Score : {self.score}",
                f"Max Combo   : {self.max_combo}x",
                "-----------------------",
                f"PERFECT     : {self.perfect_count}",
                f"GREAT       : {self.great_count}",
                f"OK          : {self.ok_count}",
                f"MISS        : {self.miss_count}",
                "-----------------------",
                f"Accuracy    : {accuracy:.1f}%"
            ]

            start_y = 150
            for line in stats:
                lbl = self.font.render(line, True, (220, 220, 220))
                self.screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, start_y))
                start_y += 32

            restart = self.font.render("Press R to Restart", True, (160, 160, 160))
            self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, start_y + 20))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()