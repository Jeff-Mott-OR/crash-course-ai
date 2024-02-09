import pygame
import random

# WARNING! Using exceptions for control flow.
# In another languagae this might be considered bad, but here it's Pythonic. ;-)
# Also it achieves what I need: break the game loop and return through multiple stack frames.
class Pygame_quit_exception(Exception):
    pass

def prompt_main_menu(screen):
    screen.fill("black")

    text = pygame.font.SysFont("serif", 42).render("The Oregon Trail", True, "white")
    screen.blit(text, (
        screen.get_width() * 0.5 - text.get_width() * 0.5,
        screen.get_height() * 0.15 - text.get_height() * 0.5
    ))
    text = pygame.font.SysFont("sans-serif", 24).render("Hunting mini-game with learning AI", True, "white")
    screen.blit(text, (
        screen.get_width() * 0.5 - text.get_width() * 0.5,
        screen.get_height() * 0.25 - text.get_height() * 0.5
    ))

    text = pygame.font.SysFont("monospace", 24).render("Ready Player One", False, "white")
    screen.blit(text, (
        screen.get_width() * 0.5 - text.get_width() * 0.5,
        screen.get_height() * 0.65 - text.get_height() * 0.5
    ))
    text = pygame.font.SysFont("monospace", 18).render("(P)lay game", False, "white")
    screen.blit(text, (
        screen.get_width() * 0.33 - text.get_width() * 0.5,
        screen.get_height() * 0.75 - text.get_height() * 0.5
    ))
    text = pygame.font.SysFont("monospace", 18).render("(T)rain AI", False, "white")
    screen.blit(text, (
        screen.get_width() * 0.67 - text.get_width() * 0.5,
        screen.get_height() * 0.75 - text.get_height() * 0.5
    ))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    raise Pygame_quit_exception()

                case pygame.KEYDOWN:
                    keys_pressed = pygame.key.get_pressed()
                    if keys_pressed[pygame.K_p]:
                        return pygame.K_p
                    if keys_pressed[pygame.K_t]:
                        return pygame.K_t

hunter_sprite = pygame.image.load("assets/hunter_sprite.png")
buffalo_img = pygame.image.load("assets/buffalo.png")
obstacles_deer_sprite = pygame.image.load("assets/obstacles_deer_sprite.png")

# WARNING! The order of these enum values "just happen" to match the order of the hunter sprite.
class Direction:
    UP = 0
    UP_RIGHT = 1
    RIGHT = 2
    DOWN_RIGHT = 3
    DOWN = 4
    DOWN_LEFT = 5
    LEFT = 6
    UP_LEFT = 7

class Hunter:
    height = 46
    width = 57
    speed_px_per_tick = 3

    def __init__(self, xy = (0, 0), direction = Direction.UP):
        self.direction = direction
        self.moving = False
        self.rect = pygame.Rect(xy, (Hunter.width, Hunter.height))

class Bullet:
    speed_px_per_tick = 10

    def __init__(self, created_on_tick = 0, xy = (0, 0), direction = Direction.UP):
        self.created_on_tick = created_on_tick
        self.direction = direction
        self.rect = pygame.Rect(xy, (1, 1))

class Buffalo:
    height = buffalo_img.get_rect().height
    width = buffalo_img.get_rect().width
    speed_px_per_tick = 5

    def __init__(self, xy = (0, 0), direction = Direction.UP):
        self.alive = True
        self.direction = direction
        self.rect = pygame.Rect(xy, (Buffalo.width, Buffalo.height))

MAIN_SURFACE_SIZE = (960, 540)
FOOTER_SURFACE_SIZE = (MAIN_SURFACE_SIZE[0], 40)
SCREEN_SIZE = (MAIN_SURFACE_SIZE[0], MAIN_SURFACE_SIZE[1] + FOOTER_SURFACE_SIZE[1])

# Keep the player bound to the visible screen.
INVISIBLE_WALLS = [
    # Top edge.
    pygame.Rect(- Hunter.width, - Hunter.height, MAIN_SURFACE_SIZE[0] + Hunter.width * 2, Hunter.height),
    # Bottom edge.
    pygame.Rect(- Hunter.width, MAIN_SURFACE_SIZE[1], MAIN_SURFACE_SIZE[0] + Hunter.width * 2, Hunter.height),
    # Left edge.
    pygame.Rect(- Hunter.width, - Hunter.height, Hunter.width, MAIN_SURFACE_SIZE[1] + Hunter.height * 2),
    # Right edge.
    pygame.Rect(MAIN_SURFACE_SIZE[0], - Hunter.height, Hunter.width, MAIN_SURFACE_SIZE[1] + Hunter.height * 2),
]

# 60 seconds, assuming 15 ticks per second.
GAME_MAX_TICKS = 60 * 15

# 2 seconds, assuming 15 ticks per second.
BULLET_MAX_TICKS = 2 * 15

# 5 seconds, assuming 15 ticks per second.
BUFFALO_SPAWN_AVG_TICKS = 5 * 15

BUFFALO_SPAWN_AREAS = [
    # Top edge.
    {
        "x": range(0, SCREEN_SIZE[0] - Buffalo.width),
        "y": range(- Buffalo.height, - Buffalo.height + 1),
        "direction": Direction.DOWN
    },
    # Bottom edge.
    {
        "x": range(0, SCREEN_SIZE[0] - Buffalo.width),
        "y": range(SCREEN_SIZE[1], SCREEN_SIZE[1] + 1),
        "direction": Direction.UP
    },
    # Left edge.
    {
        "x": range(- Buffalo.width, - Buffalo.width + 1),
        "y": range(0, SCREEN_SIZE[1] - Buffalo.height),
        "direction": Direction.RIGHT
    },
    # Right edge.
    {
        "x": range(SCREEN_SIZE[0], SCREEN_SIZE[0] + 1),
        "y": range(0, SCREEN_SIZE[1] - Buffalo.height),
        "direction": Direction.LEFT
    },
]

# 1 second, assuming 15 ticks per second.
BUFFALO_CHANGE_DIRECTION_AVG_TICKS = 1 * 15

class Game:
    def __init__(self):
        self.buffalos = []
        self.bullets = []
        self.hunter = Hunter()
        self.keys_pressed = [False for ascii_key_index in range(128)]
        self.obstacles = [
            pygame.Rect(
                random.choice(range(Hunter.width, MAIN_SURFACE_SIZE[0] - 80)),
                random.choice(range(Hunter.height, MAIN_SURFACE_SIZE[1] - 80)),
                80, 80
            )
        ]
        self.ticks = 0
        self.score = 0

    def tick(self, keys_pressed):
        self.ticks += 1
        if self.ticks >= GAME_MAX_TICKS:
            return False

        # Remember key presses for later rendering.
        self.keys_pressed = keys_pressed

        # Move bullets.
        diagonal_px_per_tick = (Bullet.speed_px_per_tick ** 2 / 2) ** 0.5
        for bullet in self.bullets:
            match bullet.direction:
                case Direction.UP:
                    bullet.rect.move_ip(0, - Bullet.speed_px_per_tick)

                case Direction.UP_RIGHT:
                    bullet.rect.move_ip(diagonal_px_per_tick, - diagonal_px_per_tick)

                case Direction.RIGHT:
                    bullet.rect.move_ip(Bullet.speed_px_per_tick, 0)

                case Direction.DOWN_RIGHT:
                    bullet.rect.move_ip(diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.DOWN:
                    bullet.rect.move_ip(0, Bullet.speed_px_per_tick)

                case Direction.DOWN_LEFT:
                    bullet.rect.move_ip(- diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.LEFT:
                    bullet.rect.move_ip(- Bullet.speed_px_per_tick, 0)

                case Direction.UP_LEFT:
                    bullet.rect.move_ip(- diagonal_px_per_tick, - diagonal_px_per_tick)

        # Move living buffalo.
        diagonal_px_per_tick = (Buffalo.speed_px_per_tick ** 2 / 2) ** 0.5
        for buffalo in filter(lambda buffalo: buffalo.alive, self.buffalos):
            if random.randrange(BUFFALO_CHANGE_DIRECTION_AVG_TICKS) == 0:
                buffalo.direction = random.randrange(8) # One of eight direction enums.

            match buffalo.direction:
                case Direction.UP:
                    moved_buffalo_rect = buffalo.rect.move(0, - Buffalo.speed_px_per_tick)

                case Direction.UP_RIGHT:
                    moved_buffalo_rect = buffalo.rect.move(diagonal_px_per_tick, - diagonal_px_per_tick)

                case Direction.RIGHT:
                    moved_buffalo_rect = buffalo.rect.move(Buffalo.speed_px_per_tick, 0)

                case Direction.DOWN_RIGHT:
                    moved_buffalo_rect = buffalo.rect.move(diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.DOWN:
                    moved_buffalo_rect = buffalo.rect.move(0, Buffalo.speed_px_per_tick)

                case Direction.DOWN_LEFT:
                    moved_buffalo_rect = buffalo.rect.move(- diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.LEFT:
                    moved_buffalo_rect = buffalo.rect.move(- Buffalo.speed_px_per_tick, 0)

                case Direction.UP_LEFT:
                    moved_buffalo_rect = buffalo.rect.move(- diagonal_px_per_tick, - diagonal_px_per_tick)

            # Immediately invoked function for early returns.
            def buffalo_collision():
                if moved_buffalo_rect.colliderect(self.hunter.rect):
                    return True
                other_buffalo_rects = [other_buffalo.rect for other_buffalo in self.buffalos if not other_buffalo is buffalo]
                if moved_buffalo_rect.collidelist(other_buffalo_rects) != -1:
                    return True
                if moved_buffalo_rect.collidelist(self.obstacles) != -1:
                    return True
                return False
            if not buffalo_collision():
                buffalo.rect = moved_buffalo_rect

        # Remove expired or colliding bullets.
        # WARNING! This filter predicate has a side-effect on the buffalo.
        # If the bullet collides with the buffalo, the buffalo dies.
        def bullet_collision(bullet):
            colliding_buffalo_index = bullet.rect.collidelist([buffalo.rect for buffalo in self.buffalos])
            if colliding_buffalo_index != -1:
                if self.buffalos[colliding_buffalo_index].alive:
                    self.buffalos[colliding_buffalo_index].alive = False
                    self.score += 1000
                return True
            if bullet.rect.collidelist(self.obstacles) != -1:
                return True
            return False
        self.bullets = [
            bullet
                for bullet in self.bullets
                if self.ticks - bullet.created_on_tick < BULLET_MAX_TICKS
                    and not bullet_collision(bullet)
        ]

        # Randomly generate new bufflo.
        if random.randrange(BUFFALO_SPAWN_AVG_TICKS) == 0:
            spawn_area = random.choice(BUFFALO_SPAWN_AREAS)
            self.buffalos.append(Buffalo(
                (random.choice(spawn_area["x"]), random.choice(spawn_area["y"])),
                spawn_area["direction"]
            ))

        # Update hunter direction.
        if keys_pressed[pygame.K_w] and keys_pressed[pygame.K_d]:
            self.hunter.direction = Direction.UP_RIGHT
        elif keys_pressed[pygame.K_s] and keys_pressed[pygame.K_d]:
            self.hunter.direction = Direction.DOWN_RIGHT
        elif keys_pressed[pygame.K_s] and keys_pressed[pygame.K_a]:
            self.hunter.direction = Direction.DOWN_LEFT
        elif keys_pressed[pygame.K_w] and keys_pressed[pygame.K_a]:
            self.hunter.direction = Direction.UP_LEFT
        elif keys_pressed[pygame.K_w]:
            self.hunter.direction = Direction.UP
        elif keys_pressed[pygame.K_d]:
            self.hunter.direction = Direction.RIGHT
        elif keys_pressed[pygame.K_s]:
            self.hunter.direction = Direction.DOWN
        elif keys_pressed[pygame.K_a]:
            self.hunter.direction = Direction.LEFT

        # Start/stop moving.
        if keys_pressed[pygame.K_RETURN]:
            self.hunter.moving = not self.hunter.moving

        # Move hunter.
        if self.hunter.moving:
            diagonal_px_per_tick = (Hunter.speed_px_per_tick ** 2 / 2) ** 0.5

            match self.hunter.direction:
                case Direction.UP:
                    moved_hunter_rect = self.hunter.rect.move(0, - Hunter.speed_px_per_tick)

                case Direction.UP_RIGHT:
                    moved_hunter_rect = self.hunter.rect.move(diagonal_px_per_tick, - diagonal_px_per_tick)

                case Direction.RIGHT:
                    moved_hunter_rect = self.hunter.rect.move(Hunter.speed_px_per_tick, 0)

                case Direction.DOWN_RIGHT:
                    moved_hunter_rect = self.hunter.rect.move(diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.DOWN:
                    moved_hunter_rect = self.hunter.rect.move(0, Hunter.speed_px_per_tick)

                case Direction.DOWN_LEFT:
                    moved_hunter_rect = self.hunter.rect.move(- diagonal_px_per_tick, diagonal_px_per_tick)

                case Direction.LEFT:
                    moved_hunter_rect = self.hunter.rect.move(- Hunter.speed_px_per_tick, 0)

                case Direction.UP_LEFT:
                    moved_hunter_rect = self.hunter.rect.move(- diagonal_px_per_tick, - diagonal_px_per_tick)

            # Immediately invoked function for early returns.
            def hunter_collision():
                if moved_hunter_rect.collidelist([buffalo.rect for buffalo in self.buffalos]) != -1:
                    return True
                if moved_hunter_rect.collidelist(INVISIBLE_WALLS) != -1:
                    return True
                if moved_hunter_rect.collidelist(self.obstacles) != -1:
                    return True
                return False
            if not hunter_collision():
                self.hunter.rect = moved_hunter_rect

                # Small reward to encourage use.
                self.score += 1

        # Fire bullet.
        if keys_pressed[pygame.K_SPACE]:
            match self.hunter.direction:
                case Direction.UP:
                    bullet_xy = (self.hunter.rect.x + 36, self.hunter.rect.y)

                case Direction.UP_RIGHT:
                    bullet_xy = (self.hunter.rect.x + Hunter.width, self.hunter.rect.y - 5)

                case Direction.RIGHT:
                    bullet_xy = (self.hunter.rect.x + Hunter.width, self.hunter.rect.y + 17)

                case Direction.DOWN_RIGHT:
                    bullet_xy = (self.hunter.rect.x + Hunter.width, self.hunter.rect.y + 29)

                case Direction.DOWN:
                    bullet_xy = (self.hunter.rect.x + 18, self.hunter.rect.y + Hunter.height)

                case Direction.DOWN_LEFT:
                    bullet_xy = (self.hunter.rect.x, self.hunter.rect.y + 27)

                case Direction.LEFT:
                    bullet_xy = (self.hunter.rect.x, self.hunter.rect.y + 17)

                case Direction.UP_LEFT:
                    bullet_xy = (self.hunter.rect.x, self.hunter.rect.y - 5)

            self.bullets.append(Bullet(self.ticks, bullet_xy, self.hunter.direction))

            # Small reward to encourage use.
            self.score += 1

        return True

    def render(self):
        main_surface = pygame.Surface(MAIN_SURFACE_SIZE)
        main_surface.fill("black")
        main_surface.blit(
            hunter_sprite,
            self.hunter.rect,
            # Sprite revealing window area.
            pygame.Rect(Hunter.width * self.hunter.direction, 15, Hunter.width, Hunter.height)
        )
        for bullet in self.bullets:
            pygame.draw.circle(main_surface, "white", (bullet.rect.x, bullet.rect.y), 2)
        for buffalo in self.buffalos:
            transformed_buffalo = buffalo_img
            match buffalo.direction:
                case Direction.UP | Direction.UP_RIGHT | Direction.RIGHT | Direction.DOWN_RIGHT:
                    transformed_buffalo = pygame.transform.flip(transformed_buffalo, True, False)
            if not buffalo.alive:
                transformed_buffalo = pygame.transform.flip(transformed_buffalo, False, True)
            main_surface.blit(transformed_buffalo, buffalo.rect)
        for obstacle in self.obstacles:
            main_surface.blit(
                obstacles_deer_sprite,
                obstacle,
                # Sprite revealing window area.
                pygame.Rect(66, 125, 80, 80)
            )
        pygame.draw.lines(
            main_surface,
            "white",
            True,
            [
                (0, 0),
                (MAIN_SURFACE_SIZE[0] - 1, 0),
                (MAIN_SURFACE_SIZE[0] - 1, MAIN_SURFACE_SIZE[1] - 1),
                (0, MAIN_SURFACE_SIZE[1] - 1)
            ]
        )

        footer_surface = pygame.Surface(FOOTER_SURFACE_SIZE)
        footer_surface.fill("black")
        if Game._keypress_rects_labels_cache:
            keypress_rects_labels = Game._keypress_rects_labels_cache
        else:
            button_label_font = pygame.font.SysFont("monospace", 12)
            keypress_rects_labels = [
                (pygame.K_w, pygame.Rect(40, 4, 25, 15), button_label_font.render("w", False, "white")),
                (pygame.K_a, pygame.Rect(10, 21, 25, 15), button_label_font.render("a", False, "white")),
                (pygame.K_s, pygame.Rect(40, 21, 25, 15), button_label_font.render("s", False, "white")),
                (pygame.K_d, pygame.Rect(70, 21, 25, 15), button_label_font.render("d", False, "white")),
                (pygame.K_SPACE, pygame.Rect(115, 7, 100, 26), button_label_font.render("space", False, "white")),
                (pygame.K_RETURN, pygame.Rect(235, 7, 50, 26), button_label_font.render("enter", False, "white")),
            ]
            Game._keypress_rects_labels_cache = keypress_rects_labels
        for key, rect, label in keypress_rects_labels:
            pygame.draw.rect(footer_surface, "white", rect, width = 0 if self.keys_pressed[key] else 1, border_radius = 2)
            footer_surface.blit(label, (rect.x + rect.width / 2 - label.get_width() / 2, rect.y + rect.height / 2 - label.get_height() / 2))
        footer_surface.blit(pygame.font.SysFont("monospace", 18).render(f"SCORE: {self.score}", False, "white"), (720, 10))
        footer_surface.blit(
            pygame.font.SysFont("monospace", 18).render(
                f"0:{round((GAME_MAX_TICKS - self.ticks) * 60 // GAME_MAX_TICKS):02d}", False, "white"
            ),
            (880, 10)
        )

        render_surface = pygame.Surface(SCREEN_SIZE)
        render_surface.blit(main_surface, (0, 0))
        render_surface.blit(footer_surface, (0, MAIN_SURFACE_SIZE[1]))

        return render_surface

    # Font render was expensive in the profiler, so cache the static button labels.
    _keypress_rects_labels_cache = None
