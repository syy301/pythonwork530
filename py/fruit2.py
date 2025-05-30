import pygame
import sys
import random
import math
import os

from pygame.constants import MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, K_r, K_ESCAPE, QUIT

# 初始化pygame
pygame.init()
pygame.mixer.init()

# 确保中文正常显示
pygame.font.init()
font_path = pygame.font.match_font('simsun') or pygame.font.match_font('simhei')
if not font_path:
    font_path = pygame.font.get_default_font()

# 游戏常量
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("切水果游戏")
clock = pygame.time.Clock()


# 加载字体
def get_font(size):
    return pygame.font.Font(font_path, size)


# 加载资源
def load_image(name, scale=None):
    try:
        image = pygame.image.load(os.path.join("assets", name)).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except:
        print(f"无法加载图像: {name}")
        # 创建临时彩色方块
        temp_surface = pygame.Surface((50, 50))
        temp_surface.fill(random.choice([RED, GREEN, YELLOW]))
        return temp_surface


def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join("assets", name))
    except:
        print(f"无法加载音效: {name}")

        # 创建无声替代
        class DummySound:
            def play(self): pass

        return DummySound()


# 水果类
class Fruit:
    def __init__(self, fruit_type, game):
        self.game = game
        self.fruit_type = fruit_type
        self.reset()

        # 加载图像
        self.images = {
            "apple": load_image("apple.png", (60, 60)),
            "banana": load_image("banana.png", (60, 60)),
            "watermelon": load_image("watermelon.png", (80, 80)),
        }
        self.image = self.images.get(fruit_type, self.images["apple"])
        self.sliced_image = self.create_sliced_image()

        # 加载音效（单个文件）
        self.slice_sound = load_sound("slice.mp3")

    def reset(self):
        """重置水果属性"""
        self.radius = 30
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        self.y = WINDOW_HEIGHT + self.radius

        # 根据难度设置初始速度
        difficulty = self.game.difficulty
        speed_factor = 1.0
        if difficulty == "easy":
            speed_factor = 0.8
        elif difficulty == "hard":
            speed_factor = 1.2

        self.speed_y = random.randint(-15, -10) * speed_factor
        self.speed_x = random.uniform(-3, 3) * speed_factor
        self.gravity = 0.3
        self.sliced = False
        self.on_screen = True
        self.slice_particles = []
        self.particle_life = 30

    def create_sliced_image(self):
        """创建水果被切开的效果图像"""
        original = self.image
        sliced = original.copy()
        s = pygame.Surface(original.get_size(), pygame.SRCALPHA)
        s.fill((255, 0, 0, 128))

        # 绘制切割线
        angle = random.uniform(0, math.pi)
        width, height = original.get_size()
        center = (width // 2, height // 2)
        length = min(width, height) * 0.8
        start = (center[0] - math.cos(angle) * length / 2, center[1] - math.sin(angle) * length / 2)
        end = (center[0] + math.cos(angle) * length / 2, center[1] + math.sin(angle) * length / 2)
        pygame.draw.line(s, (255, 0, 0, 192), start, end, 3)
        sliced.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        return sliced

    def update(self):
        """更新水果位置"""
        if not self.sliced:
            self.y += self.speed_y
            self.x += self.speed_x
            self.speed_y += self.gravity

            # 检查是否出界
            if self.y > WINDOW_HEIGHT + self.radius * 2 or self.x < -self.radius or self.x > WINDOW_WIDTH + self.radius:
                self.on_screen = False
        else:
            # 更新粒子效果
            for particle in self.slice_particles:
                particle[0] += particle[2]  # x移动
                particle[1] += particle[3]  # y移动
                particle[3] += 0.1  # 重力

            self.particle_life -= 1
            if self.particle_life <= 0:
                self.on_screen = False

    def draw(self, surface):
        """绘制水果"""
        if not self.sliced:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, rect)
        else:
            rect = self.sliced_image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sliced_image, rect)

            # 绘制粒子
            for particle in self.slice_particles:
                pygame.draw.circle(surface, particle[4], (int(particle[0]), int(particle[1])), particle[5])

    def slice(self):
        """切水果效果"""
        if not self.sliced:
            self.sliced = True
            self.slice_sound.play()  # 播放切水果音效

            # 创建粒子效果
            color = random.choice([RED, GREEN, YELLOW])
            for _ in range(10):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 5)
                size = random.randint(5, 10)
                px = self.x + random.uniform(-self.radius / 2, self.radius / 2)
                py = self.y + random.uniform(-self.radius / 2, self.radius / 2)
                self.slice_particles.append([px, py, math.cos(angle) * speed, math.sin(angle) * speed, color, size])


# 炸弹类
class Bomb:
    def __init__(self, game):
        self.game = game
        self.reset()
        self.image = load_image("bomb.png", (60, 60))
        self.explosion_sound = load_sound("explosion.mp3")

    def reset(self):
        """重置炸弹属性"""
        self.radius = 30
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        self.y = WINDOW_HEIGHT + self.radius

        # 根据难度设置初始速度
        difficulty = self.game.difficulty
        speed_factor = 1.0
        if difficulty == "easy":
            speed_factor = 0.8
        elif difficulty == "hard":
            speed_factor = 1.2

        self.speed_y = random.randint(-15, -10) * speed_factor
        self.speed_x = random.uniform(-3, 3) * speed_factor
        self.gravity = 0.3
        self.on_screen = True

    def update(self):
        """更新炸弹位置"""
        self.y += self.speed_y
        self.x += self.speed_x
        self.speed_y += self.gravity

        # 检查是否出界
        if self.y > WINDOW_HEIGHT + self.radius * 2 or self.x < -self.radius or self.x > WINDOW_WIDTH + self.radius:
            self.on_screen = False

    def draw(self, surface):
        """绘制炸弹"""
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.image, rect)

    def explode(self):
        """炸弹爆炸效果"""
        self.explosion_sound.play()


# 游戏类
class Game:
    def __init__(self):
        # 初始化属性（顺序很重要）
        self.difficulty = "medium"  # 默认难度
        self.fruit_types = ["apple", "banana", "watermelon"]

        self.reset_game()
        self.last_mouse_pos = None
        self.slicing = False
        self.current_screen = "main_menu"  # main_menu, difficulty, game, game_over

        # 加载背景音乐
        self.background_music = load_sound("background.mp3")
        self.background_music.set_volume(0.3)
        self.background_music.play(-1)  # 循环播放

    def reset_game(self):
        """重置游戏状态"""
        self.fruits = [self.create_random_fruit() for _ in range(3)]
        self.bombs = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.level = 1
        self.fruit_speed = 1.0
        self.spawn_timer = 0

        # 根据难度设置生成延迟
        if self.difficulty == "easy":
            self.spawn_delay = 70  # 每隔70帧生成一个新水果/炸弹
        elif self.difficulty == "medium":
            self.spawn_delay = 50  # 每隔50帧生成一个新水果/炸弹
        else:  # hard
            self.spawn_delay = 35  # 每隔35帧生成一个新水果/炸弹

        self.last_spawn_time = pygame.time.get_ticks()

    def create_random_fruit(self):
        """创建随机水果"""
        return Fruit(random.choice(self.fruit_types), self)

    def update(self):
        """更新游戏状态"""
        if self.current_screen != "game":
            return

        current_time = pygame.time.get_ticks()

        # 生成新水果/炸弹
        if current_time - self.last_spawn_time > self.spawn_delay * 1000 / FPS:
            self.spawn_timer += 1
            self.last_spawn_time = current_time

            # 每5个生成周期增加一个难度级别
            if self.spawn_timer % 5 == 0:
                self.level += 1
                if self.spawn_delay > 15:  # 难度上限
                    self.spawn_delay -= 2
                self.fruit_speed += 0.05

            # 根据难度调整炸弹生成概率
            bomb_chance = 0.15  # 中等难度
            if self.difficulty == "easy":
                bomb_chance = 0.1
            elif self.difficulty == "hard":
                bomb_chance = 0.25

            # 生成水果或炸弹
            if random.random() > bomb_chance:
                new_fruit = self.create_random_fruit()
                # 应用难度速度因子
                new_fruit.speed_y *= self.fruit_speed
                new_fruit.speed_x *= self.fruit_speed
                self.fruits.append(new_fruit)
            else:
                new_bomb = Bomb(self)
                # 应用难度速度因子
                new_bomb.speed_y *= self.fruit_speed
                new_bomb.speed_x *= self.fruit_speed
                self.bombs.append(new_bomb)

        # 更新水果
        for fruit in self.fruits[:]:
            fruit.update()
            if not fruit.on_screen:
                if not fruit.sliced:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        self.current_screen = "game_over"
                self.fruits.remove(fruit)

        # 更新炸弹
        for bomb in self.bombs[:]:
            bomb.update()
            if not bomb.on_screen:
                self.bombs.remove(bomb)

        # 处理鼠标切片
        if self.slicing and self.last_mouse_pos:
            current_mouse_pos = pygame.mouse.get_pos()

            # 检查是否切到水果
            for fruit in self.fruits:
                if not fruit.sliced:
                    # 计算鼠标轨迹与水果的距离
                    distance = self.point_to_line_distance(
                        self.last_mouse_pos[0], self.last_mouse_pos[1],
                        current_mouse_pos[0], current_mouse_pos[1],
                        fruit.x, fruit.y
                    )
                    if distance <= fruit.radius:
                        fruit.slice()
                        self.score += 1

            # 检查是否切到炸弹
            for bomb in self.bombs:
                # 计算鼠标轨迹与炸弹的距离
                distance = self.point_to_line_distance(
                    self.last_mouse_pos[0], self.last_mouse_pos[1],
                    current_mouse_pos[0], current_mouse_pos[1],
                    bomb.x, bomb.y
                )
                if distance <= bomb.radius:
                    bomb.explode()
                    self.game_over = True
                    self.current_screen = "game_over"

        self.last_mouse_pos = pygame.mouse.get_pos()

    def draw(self, surface):
        """绘制游戏界面"""
        # 绘制背景
        surface.fill(WHITE)

        if self.current_screen == "main_menu":
            self.draw_main_menu(surface)
        elif self.current_screen == "difficulty":
            self.draw_difficulty_menu(surface)
        elif self.current_screen == "game":
            self.draw_game(surface)
        elif self.current_screen == "game_over":
            self.draw_game_over(surface)

    def draw_main_menu(self, surface):
        """绘制主菜单"""
        # 绘制背景
        bg_image = load_image("background.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
        surface.blit(bg_image, (0, 0))

        # 绘制标题
        title_text = get_font(60).render("切水果游戏", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(title_text, title_rect)

        # 绘制按钮
        button_width = 250
        button_height = 60
        button_y = WINDOW_HEIGHT // 2

        # 开始游戏按钮
        start_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y, button_width, button_height)
        pygame.draw.rect(surface, (255, 100, 100), start_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, start_button, 3, border_radius=10)

        start_text = get_font(36).render("开始游戏", True, WHITE)
        start_text_rect = start_text.get_rect(center=start_button.center)
        surface.blit(start_text, start_text_rect)

        # 退出按钮
        exit_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 80, button_width, button_height)
        pygame.draw.rect(surface, (100, 100, 100), exit_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, exit_button, 3, border_radius=10)

        exit_text = get_font(36).render("退出游戏", True, WHITE)
        exit_text_rect = exit_text.get_rect(center=exit_button.center)
        surface.blit(exit_text, exit_text_rect)

        # 存储按钮位置供事件处理使用
        self.menu_buttons = {
            "start": start_button,
            "exit": exit_button
        }

    def draw_difficulty_menu(self, surface):
        """绘制难度选择菜单"""
        # 绘制背景
        bg_image = load_image("background.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
        surface.blit(bg_image, (0, 0))

        # 绘制标题
        title_text = get_font(50).render("选择难度", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        surface.blit(title_text, title_rect)

        # 绘制难度说明
        desc_font = get_font(24)
        easy_desc = desc_font.render("简单: 水果速度慢，炸弹少", True, WHITE)
        medium_desc = desc_font.render("中等: 水果速度中等，炸弹适中", True, WHITE)
        hard_desc = desc_font.render("困难: 水果速度快，炸弹多", True, WHITE)

        surface.blit(easy_desc, (WINDOW_WIDTH // 2 - easy_desc.get_width() // 2, WINDOW_HEIGHT // 2 - 80))
        surface.blit(medium_desc, (WINDOW_WIDTH // 2 - medium_desc.get_width() // 2, WINDOW_HEIGHT // 2 - 20))
        surface.blit(hard_desc, (WINDOW_WIDTH // 2 - hard_desc.get_width() // 2, WINDOW_HEIGHT // 2 + 40))

        # 绘制按钮
        button_width = 180
        button_height = 60
        button_y = WINDOW_HEIGHT // 2 + 120

        # 简单按钮
        easy_button = pygame.Rect(WINDOW_WIDTH // 4 - button_width // 2, button_y, button_width, button_height)
        pygame.draw.rect(surface, (0, 200, 0), easy_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, easy_button, 3, border_radius=10)

        easy_text = get_font(32).render("简单", True, WHITE)
        easy_text_rect = easy_text.get_rect(center=easy_button.center)
        surface.blit(easy_text, easy_text_rect)

        # 中等按钮
        medium_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y, button_width, button_height)
        pygame.draw.rect(surface, (255, 165, 0), medium_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, medium_button, 3, border_radius=10)

        medium_text = get_font(32).render("中等", True, WHITE)
        medium_text_rect = medium_text.get_rect(center=medium_button.center)
        surface.blit(medium_text, medium_text_rect)

        # 困难按钮
        hard_button = pygame.Rect(WINDOW_WIDTH * 3 // 4 - button_width // 2, button_y, button_width, button_height)
        pygame.draw.rect(surface, (200, 0, 0), hard_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, hard_button, 3, border_radius=10)

        hard_text = get_font(32).render("困难", True, WHITE)
        hard_text_rect = hard_text.get_rect(center=hard_button.center)
        surface.blit(hard_text, hard_text_rect)

        # 返回按钮
        back_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, button_y + 80, 200, 50)
        pygame.draw.rect(surface, (100, 100, 100), back_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, back_button, 3, border_radius=10)

        back_text = get_font(30).render("返回", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        surface.blit(back_text, back_text_rect)

        # 存储按钮位置供事件处理使用
        self.difficulty_buttons = {
            "easy": easy_button,
            "medium": medium_button,
            "hard": hard_button,
            "back": back_button
        }

    def draw_game(self, surface):
        """绘制游戏界面"""
        # 绘制背景
        bg_image = load_image("game_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
        surface.blit(bg_image, (0, 0))

        # 绘制水果
        for fruit in self.fruits:
            fruit.draw(surface)

        # 绘制炸弹
        for bomb in self.bombs:
            bomb.draw(surface)

        # 绘制分数
        score_text = get_font(36).render(f"分数: {self.score}", True, WHITE)
        surface.blit(score_text, (20, 20))

        # 绘制生命值
        lives_text = get_font(36).render(f"生命值: {self.lives}", True, WHITE)
        surface.blit(lives_text, (20, 60))

        # 绘制等级
        level_text = get_font(36).render(f"等级: {self.level}", True, WHITE)
        surface.blit(level_text, (20, 100))

        # 绘制难度
        difficulty_text = get_font(36).render(f"难度: {self.get_difficulty_name()}", True, WHITE)
        surface.blit(difficulty_text, (20, 140))

        # 绘制当前鼠标轨迹
        if self.slicing and self.last_mouse_pos:
            current_pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, WHITE, self.last_mouse_pos, current_pos, 3)

    def draw_game_over(self, surface):
        """绘制游戏结束画面"""
        # 绘制游戏画面
        self.draw_game(surface)

        # 绘制半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 绘制游戏结束文字
        game_over_text = get_font(72).render("游戏结束", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(game_over_text, game_over_rect)

        # 绘制最终分数
        final_score_text = get_font(48).render(f"最终分数: {self.score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(final_score_text, final_score_rect)

        # 绘制难度
        difficulty_text = get_font(36).render(f"难度: {self.get_difficulty_name()}", True, WHITE)
        difficulty_rect = difficulty_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        surface.blit(difficulty_text, difficulty_rect)

        # 绘制重新开始按钮
        restart_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 130, 300, 60)
        pygame.draw.rect(surface, (0, 200, 0), restart_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, restart_button, 3, border_radius=10)

        restart_text = get_font(36).render("重新开始", True, WHITE)
        restart_text_rect = restart_text.get_rect(center=restart_button.center)
        surface.blit(restart_text, restart_text_rect)

        # 绘制返回菜单按钮
        menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 200, 300, 60)
        pygame.draw.rect(surface, (255, 165, 0), menu_button, border_radius=10)
        pygame.draw.rect(surface, WHITE, menu_button, 3, border_radius=10)

        menu_text = get_font(36).render("返回菜单", True, WHITE)
        menu_text_rect = menu_text.get_rect(center=menu_button.center)
        surface.blit(menu_text, menu_text_rect)

        # 存储按钮位置供事件处理使用
        self.game_over_buttons = {
            "restart": restart_button,
            "menu": menu_button
        }

    def get_difficulty_name(self):
        """获取难度名称"""
        if self.difficulty == "easy":
            return "简单"
        elif self.difficulty == "medium":
            return "中等"
        else:
            return "困难"

    def handle_event(self, event):
        """处理游戏事件"""
        if event.type == QUIT:
            return False

        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                if self.current_screen == "main_menu":
                    self.handle_main_menu_click(event.pos)
                elif self.current_screen == "difficulty":
                    self.handle_difficulty_menu_click(event.pos)
                elif self.current_screen == "game":
                    self.slicing = True
                elif self.current_screen == "game_over":
                    self.handle_game_over_click(event.pos)

        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:  # 左键
                self.slicing = False
                self.last_mouse_pos = None

        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if self.current_screen == "game":
                    self.current_screen = "main_menu"
                elif self.current_screen == "difficulty":
                    self.current_screen = "main_menu"
                elif self.current_screen == "game_over":
                    self.current_screen = "main_menu"

            if event.key == K_r and self.current_screen == "game_over":
                self.reset_game()
                self.current_screen = "game"

        return True

    def handle_main_menu_click(self, pos):
        """处理主菜单点击事件"""
        if self.menu_buttons["start"].collidepoint(pos):
            self.current_screen = "difficulty"
        elif self.menu_buttons["exit"].collidepoint(pos):
            pygame.quit()
            sys.exit()

    def handle_difficulty_menu_click(self, pos):
        """处理难度选择菜单点击事件"""
        if self.difficulty_buttons["easy"].collidepoint(pos):
            self.difficulty = "easy"
            self.reset_game()
            self.current_screen = "game"
        elif self.difficulty_buttons["medium"].collidepoint(pos):
            self.difficulty = "medium"
            self.reset_game()
            self.current_screen = "game"
        elif self.difficulty_buttons["hard"].collidepoint(pos):
            self.difficulty = "hard"
            self.reset_game()
            self.current_screen = "game"
        elif self.difficulty_buttons["back"].collidepoint(pos):
            self.current_screen = "main_menu"

    def handle_game_over_click(self, pos):
        """处理游戏结束画面点击事件"""
        if self.game_over_buttons["restart"].collidepoint(pos):
            self.reset_game()
            self.current_screen = "game"
        elif self.game_over_buttons["menu"].collidepoint(pos):
            self.current_screen = "main_menu"

    def point_to_line_distance(self, x1, y1, x2, y2, x0, y0):
        """计算点到线段的距离"""
        A = x0 - x1
        B = y0 - y1
        C = x2 - x1
        D = y2 - y1

        dot = A * C + B * D
        len_sq = C * C + D * D
        param = -1

        if len_sq != 0:  # 避免除零错误
            param = dot / len_sq

        xx = 0
        yy = 0

        if param < 0:
            xx = x1
            yy = y1
        elif param > 1:
            xx = x2
            yy = y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D

        dx = x0 - xx
        dy = y0 - yy

        return math.sqrt(dx * dx + dy * dy)


# 主游戏循环
def main():
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            running = game.handle_event(event)

        game.update()
        game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()