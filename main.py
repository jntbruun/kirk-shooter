import random
import asyncio
import sys
import pygame
from os.path import join, dirname, abspath

clock = pygame.time.Clock()

# classes
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(("images/player.png")).convert_alpha()
        self.rect = self.image.get_frect(center = (window_width/2, window_height / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 500
        # cooldown
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 250
        # ultimate
        self.ultimate_ready = False
        self.ultimate_active = False
        self.ultimate_charge_time = pygame.time.get_ticks()
        self.ultimate_start_time = 0
        self.ultimate_last_shot = 0
        self.ultimate_cooldown = 10000
        self.ultimate_duration = 5000
        self.ultimate_fire_rate = 300
        self.ultimate_spread = 50
    # Laser timer
    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def ultimate(self):
        global touch_ultimate_triggered
        current_time = pygame.time.get_ticks()

        if not self.ultimate_ready and not self.ultimate_active:
            if current_time - self.ultimate_charge_time >= self.ultimate_cooldown:
                self.ultimate_ready = True

        # keyboard OR the on-screen ultimate button can trigger it
        ultimate_pressed = pygame.key.get_just_pressed()[pygame.K_e] or touch_ultimate_triggered
        touch_ultimate_triggered = False  # consume the tap so it doesn't fire twice

        if self.ultimate_ready and ultimate_pressed:
            self.ultimate_ready = False
            self.ultimate_active = True
            self.ultimate_start_time = current_time
            self.ultimate_last_shot = 0

        if self.ultimate_active:
            if current_time - self.ultimate_start_time >= self.ultimate_duration:
                self.ultimate_active = False
                self.ultimate_charge_time = current_time
            elif current_time - self.ultimate_last_shot >= self.ultimate_fire_rate:
                self.ultimate_last_shot = current_time
                for angle in (-self.ultimate_spread, 0, self.ultimate_spread):
                    direction = pygame.Vector2(0, -1).rotate(angle)
                    Laser(laser_surf, self.rect.midtop, (laser_sprites, all_sprites), direction)
                    if laser_sound: laser_sound.play()

    def ultimate_progress(self):
        if self.ultimate_active:
            return 1
        if self.ultimate_ready:
            return 1
        elapsed = pygame.time.get_ticks() - self.ultimate_charge_time
        return min(elapsed / self.ultimate_cooldown, 1)

    # Key presses + touch
    def update(self, dt):
        keys = pygame.key.get_pressed()
        keyboard_dir = pygame.Vector2(int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
                                       int(keys[pygame.K_s]) - int(keys[pygame.K_w]))

        # the joystick finger, if one is active, overrides the keyboard
        if joystick_finger_id is not None and joystick_offset.length() > JOYSTICK_DEADZONE:
            self.direction = joystick_offset.normalize()
        elif keyboard_dir:
            self.direction = keyboard_dir.normalize()
        else:
            self.direction = pygame.Vector2()

        self.rect.center += self.direction * self.speed * dt

        #Laser action - spacebar OR holding the fire button
        recent_keys = pygame.key.get_just_pressed()
        want_to_shoot = recent_keys[pygame.K_SPACE] or fire_finger_id is not None
        if want_to_shoot and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (laser_sprites, all_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            if laser_sound: laser_sound.play()
        self.laser_timer()
        self.ultimate()

class Star(pygame.sprite.Sprite):
    def __init__ (self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center =(random.randint(0,window_width), random.randint(0, window_height)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups, direction = (0, -1)):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos)
        self.direction = pygame.Vector2(direction)
        self.speed = 400

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if not display_surface.get_rect().colliderect(self.rect):
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = self.original_surf
        self.rect = self.image.get_frect(midbottom = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(random.uniform(-0.3, 0.3),1)
        self.speed = random.randint(300, 400)
        self.rotation_speed = random.randint(-50, 50)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        current_time = pygame.time.get_ticks()
        if current_time > self.start_time + self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_frect(center = self.rect.center)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frames_index = 0
        self.image = self.frames[self.frames_index]
        self.rect = self.image.get_frect(center = pos)
    
    def update(self, dt):
        self.frames_index += 20 * dt
        if self.frames_index < len(self.frames):
            self.image = self.frames[int(self.frames_index)]
        else:
            self.kill()

def collisions():
    global game_state, final_score, high_score, meteors_killed
    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        game_state = "game_over"
        final_score = get_score()
        if damage_sound: damage_sound.play()
        if final_score > high_score:
            high_score = final_score
            save_high_score(high_score)
    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            meteors_killed += len(collided_sprites)
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            if explosion_sound: explosion_sound.play()

def display_score():
    text_surf = font.render(str(get_score()), True, (0, 59, 255))
    text_rect = text_surf.get_frect(midbottom = (window_width/2, window_height - 50))
    box = text_rect.inflate(15, 5)
    box.centery -= 6
    pygame.draw.rect(display_surface, "white", box, 0, 15)
    display_surface.blit(text_surf, text_rect)

def display_ultimate():
    bar_width, bar_height = 240, 18
    x = window_width / 2 - bar_width / 2
    y = window_height - 40

    outline = pygame.FRect(x, y, bar_width, bar_height)

    if player.ultimate_active:
        fill_ratio = 1 - (pygame.time.get_ticks() - player.ultimate_start_time) / player.ultimate_duration
        colour = (255, 80, 0)
    elif player.ultimate_ready:
        fill_ratio = 1
        colour = (255, 255, 255) if pygame.time.get_ticks() % 600 < 300 else (0, 59, 255)
    else:
        fill_ratio = player.ultimate_progress()
        colour = (0, 59, 255)

    fill = pygame.FRect(x, y, bar_width * max(fill_ratio, 0), bar_height)
    pygame.draw.rect(display_surface, colour, fill, 0, 4)
    pygame.draw.rect(display_surface, "white", outline, 3, 4)

# ---- touch controls (phone / pygbag web build) ----
def draw_touch_controls():
    touch_ui_surface.fill((0, 0, 0, 0))

    # joystick base + knob
    pygame.draw.circle(touch_ui_surface, (255, 255, 255, 60), JOYSTICK_CENTER, JOYSTICK_BASE_RADIUS)
    pygame.draw.circle(touch_ui_surface, (255, 255, 255, 120), JOYSTICK_CENTER, JOYSTICK_BASE_RADIUS, 3)
    knob_pos = JOYSTICK_CENTER + joystick_offset
    knob_colour = (0, 180, 255, 160) if joystick_finger_id is not None else (255, 255, 255, 100)
    pygame.draw.circle(touch_ui_surface, knob_colour, knob_pos, 36)

    # fire button
    fire_colour = (255, 60, 60, 170) if fire_finger_id is not None else (255, 255, 255, 70)
    pygame.draw.circle(touch_ui_surface, fire_colour, FIRE_BUTTON_CENTER, FIRE_BUTTON_RADIUS)
    pygame.draw.circle(touch_ui_surface, (255, 255, 255, 140), FIRE_BUTTON_CENTER, FIRE_BUTTON_RADIUS, 3)
    fire_label = small_font.render("FIRE", True, (255, 255, 255))
    touch_ui_surface.blit(fire_label, fire_label.get_frect(center = FIRE_BUTTON_CENTER))

    # ultimate button
    if player.ultimate_ready:
        ult_colour = (255, 255, 255, 160) if pygame.time.get_ticks() % 600 < 300 else (0, 59, 255, 160)
    else:
        ult_colour = (255, 255, 255, 50)
    pygame.draw.circle(touch_ui_surface, ult_colour, ULTIMATE_BUTTON_CENTER, ULTIMATE_BUTTON_RADIUS)
    pygame.draw.circle(touch_ui_surface, (255, 255, 255, 140), ULTIMATE_BUTTON_CENTER, ULTIMATE_BUTTON_RADIUS, 3)
    ult_label = small_font.render("ULT", True, (255, 255, 255))
    touch_ui_surface.blit(ult_label, ult_label.get_frect(center = ULTIMATE_BUTTON_CENTER))

    display_surface.blit(touch_ui_surface, (0, 0))

def reset_game():
    global player, round_start_time, meteors_killed
    all_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    meteors_killed = 0

    for _ in range(50):
        Star(all_sprites, star_surf)
    player = Player(all_sprites)

    round_start_time = pygame.time.get_ticks()
    
def game_over_screen():
    display_surface.blit(deathbakgrunn_surf, deathbakgrunn_rect)

    title_surf = font_gameover.render("Game Over", True, (255, 255, 255))
    title_rect = title_surf.get_frect(center = (window_width / 2, window_height / 2 - 80))
    display_surface.blit(title_surf, title_rect)

    score_surf = font.render(f"Score: {final_score}", True, (255, 255, 255))
    score_rect = score_surf.get_frect(center = (window_width / 2, window_height / 2 + 20))
    display_surface.blit(score_surf, score_rect)

    high_surf = font.render(f"Best: {high_score}", True, (255, 255, 255))
    high_rect = high_surf.get_frect(center = (window_width / 2, window_height / 2 + 70))
    display_surface.blit(high_surf, high_rect)

    prompt_surf = font.render("Press R or tap to play again", True, (255, 255, 255))
    prompt_rect = prompt_surf.get_frect(center = (window_width / 2, window_height / 2 + 160))
    display_surface.blit(prompt_surf, prompt_rect)

def get_score():
    #return (pygame.time.get_ticks() - round_start_time) // 100
    return meteors_killed

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(score))

# gen setup
pygame.display.init()
pygame.font.init()
window_width, window_height = 1280, 720
display_surface = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Kirk Shooter")
running = True
game_state = "playing"
HIGH_SCORE_FILE = join(dirname(abspath(__file__)), "highscore.txt")
high_score = load_high_score()

# imports
font = pygame.font.Font("images/Oxanium-Bold.ttf", 40)
font_gameover = pygame.font.Font("images/Oxanium-Bold.ttf", 100)
small_font = pygame.font.Font("images/Oxanium-Bold.ttf", 24)
star_surf = pygame.image.load(("images/star.png")).convert_alpha()
meteor_surf = pygame.image.load(("images/kirkmeteor.png")).convert_alpha()
laser_surf = pygame.image.load(("images/laser.png")).convert_alpha()
explosion_frames = [pygame.image.load(join("images", "explosion", f"{i}.png")).convert_alpha() for i in range(21)]
bakgrunn_surf = pygame.image.load(("images/bakgrunn.png")).convert()
bakgrunn_rect = bakgrunn_surf.get_frect(center = (window_width / 2, window_height / 2))
deathbakgrunn_surf = pygame.image.load(("images/gameoverscreen.png")).convert()
deathbakgrunn_rect = bakgrunn_surf.get_frect(center = (window_width / 2, window_height / 2))

laser_sound = None
explosion_sound = None
damage_sound = None

# sprites
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
reset_game()

# Meteor spawn timing.
# pygame.time.set_timer is not implemented on WASM (pygbag), so meteors spawn
# from a manual accumulator in the main loop instead of a repeating timer event.
METEOR_SPAWN_INTERVAL = 0.3  # seconds
meteor_spawn_timer = 0.0

# ---- touch control state (phone / pygbag web build) ----
JOYSTICK_CENTER = pygame.Vector2(150, window_height - 150)
JOYSTICK_BASE_RADIUS = 90
JOYSTICK_KNOB_RADIUS = 70
JOYSTICK_DEADZONE = 10

FIRE_BUTTON_CENTER = pygame.Vector2(window_width - 120, window_height - 120)
FIRE_BUTTON_RADIUS = 75

ULTIMATE_BUTTON_CENTER = pygame.Vector2(window_width - 120, window_height - 260)
ULTIMATE_BUTTON_RADIUS = 55

joystick_finger_id = None
joystick_offset = pygame.Vector2()
fire_finger_id = None
touch_ultimate_triggered = False

touch_ui_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)


# THE GAME
async def main():
    global running, game_state
    global joystick_finger_id, joystick_offset, fire_finger_id, touch_ultimate_triggered
    global laser_sound, explosion_sound, damage_sound
    global meteor_spawn_timer

    audio_ready = False

    while running:
        dt = clock.tick(60) / 1000

        # spawn meteors on a fixed interval (replaces pygame.time.set_timer)
        if game_state == "playing":
            meteor_spawn_timer += dt
            while meteor_spawn_timer >= METEOR_SPAWN_INTERVAL:
                meteor_spawn_timer -= METEOR_SPAWN_INTERVAL
                Meteor(meteor_surf, (random.randint(0, window_width), 0), (all_sprites, meteor_sprites))

        # event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- touch input ---
            if event.type == pygame.FINGERDOWN:
                pos = pygame.Vector2(event.x * window_width, event.y * window_height)
                if joystick_finger_id is None and pos.distance_to(JOYSTICK_CENTER) <= JOYSTICK_BASE_RADIUS:
                    joystick_finger_id = event.finger_id
                    joystick_offset = pos - JOYSTICK_CENTER
                elif fire_finger_id is None and pos.distance_to(FIRE_BUTTON_CENTER) <= FIRE_BUTTON_RADIUS:
                    fire_finger_id = event.finger_id
                elif pos.distance_to(ULTIMATE_BUTTON_CENTER) <= ULTIMATE_BUTTON_RADIUS:
                    touch_ultimate_triggered = True
                elif game_state == "game_over":
                    reset_game()
                    game_state = "playing"

            elif event.type == pygame.FINGERMOTION:
                if event.finger_id == joystick_finger_id:
                    pos = pygame.Vector2(event.x * window_width, event.y * window_height)
                    offset = pos - JOYSTICK_CENTER
                    if offset.length() > JOYSTICK_KNOB_RADIUS:
                        offset.scale_to_length(JOYSTICK_KNOB_RADIUS)
                    joystick_offset = offset

            elif event.type == pygame.FINGERUP:
                if event.finger_id == joystick_finger_id:
                    joystick_finger_id = None
                    joystick_offset = pygame.Vector2()
                elif event.finger_id == fire_finger_id:
                    fire_finger_id = None

        if game_state == "game_over":
            keys = pygame.key.get_just_pressed()
            if keys[pygame.K_r]:
                reset_game()
                game_state = "playing"

        # draw the game
        if game_state == "playing":
            all_sprites.update(dt)
            collisions()
            display_surface.blit(bakgrunn_surf, bakgrunn_rect)
            all_sprites.draw(display_surface)
            display_score()
            display_ultimate()
            draw_touch_controls()
        else:
            game_over_screen()

        pygame.display.update()

        await asyncio.sleep(0)  # hands control back to the browser each frame

        if not audio_ready:
            audio_ready = True
            if sys.platform != "emscripten":
                try:
                    pygame.mixer.init()
                    laser_sound = pygame.mixer.Sound(join("audio", "laser.ogg"))
                    laser_sound.set_volume(0.5)
                    explosion_sound = pygame.mixer.Sound(join("audio", "explosion.ogg"))
                    explosion_sound.set_volume(0.6)
                    damage_sound = pygame.mixer.Sound(join("audio", "damage.ogg"))
                    damage_sound.set_volume(0.7)
                    pygame.mixer.music.load(join("audio", "game_music.ogg"))
                    pygame.mixer.music.set_volume(0.35)
                    pygame.mixer.music.play(loops=-1)
                except Exception:
                    pass  # audio didn't come up this session; game still runs, just silently

    pygame.quit()

asyncio.run(main())
