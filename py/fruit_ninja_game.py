import pygame
import sys
import random
import math

from pygame.constants import MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, K_r, QUIT

#from pygame.locals import *

# 初始化pygame
pygame.init()
pygame.mixer.init()

# 确保中文正常显示
pygame.font.init()
font_path = pygame.font.match_font('simsun') or pygame.font.match_font('simhei')
if not font_path:
    # 如果没有找到中文字体，使用默认字体
    font_path = pygame.font.get_default_font()

# 游戏常量
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
FRUIT_COLORS = [RED, GREEN, YELLOW, ORANGE, PURPLE]

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("切水果游戏")
clock = pygame.time.Clock()


# 加载字体
def get_font(size):
    return pygame.font.Font(font_path, size)


# 水果类
class Fruit:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置水果属性"""
        self.radius = random.randint(20, 40)
        self.color = random.choice(FRUIT_COLORS)
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        self.y = WINDOW_HEIGHT + self.radius
        self.speed_y = random.randint(-15, -10)
        self.speed_x = random.uniform(-3, 3)
        self.gravity = 0.3
        self.sliced = False
        self.on_screen = True
        self.slice_particles = []
        self.particle_life = 30

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
            # 更新切片粒子
            for particle in self.slice_particles:
                particle[0] += particle[2]  # x移动
                particle[1] += particle[3]  # y移动
                particle[3] += 0.1  # 粒子重力

            self.particle_life -= 1
            if self.particle_life <= 0:
                self.on_screen = False

    def draw(self, surface):
        """绘制水果"""
        if not self.sliced:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), self.radius, 2)
        else:
            # 绘制切片粒子
            for particle in self.slice_particles:
                pygame.draw.circle(surface, particle[4], (int(particle[0]), int(particle[1])), particle[5])

    def slice(self):
        """切水果效果"""
        if not self.sliced:
            self.sliced = True
            # 创建切片粒子
            for _ in range(10):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 5)
                size = random.randint(5, 10)
                particle_x = self.x + random.uniform(-self.radius / 2, self.radius / 2)
                particle_y = self.y + random.uniform(-self.radius / 2, self.radius / 2)
                particle_speed_x = math.cos(angle) * speed
                particle_speed_y = math.sin(angle) * speed
                self.slice_particles.append(
                    [particle_x, particle_y, particle_speed_x, particle_speed_y, self.color, size])


# 炸弹类
class Bomb:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置炸弹属性"""
        self.radius = 30
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        self.y = WINDOW_HEIGHT + self.radius
        self.speed_y = random.randint(-15, -10)
        self.speed_x = random.uniform(-3, 3)
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
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius - 5)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)


# 游戏类
class Game:
    def __init__(self):
        self.reset_game()
        self.last_mouse_pos = None
        self.slicing = False

    def reset_game(self):
        """重置游戏状态"""
        self.fruits = [Fruit() for _ in range(3)]
        self.bombs = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.level = 1
        self.fruit_speed = 1.0
        self.spawn_timer = 0
        self.spawn_delay = 60  # 每隔60帧生成一个新水果/炸弹
        self.last_spawn_time = pygame.time.get_ticks()

    def update(self):
        """更新游戏状态"""
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()

        # 生成新水果/炸弹
        if current_time - self.last_spawn_time > self.spawn_delay * 1000 / FPS:
            self.spawn_timer += 1
            self.last_spawn_time = current_time

            # 每5个生成周期增加一个难度级别
            if self.spawn_timer % 5 == 0:
                self.level += 1
                if self.spawn_delay > 20:
                    self.spawn_delay -= 5
                self.fruit_speed += 0.1

            # 生成水果或炸弹
            if random.random() < 0.8:  # 80%概率生成水果
                new_fruit = Fruit()
                new_fruit.speed_y *= self.fruit_speed
                new_fruit.speed_x *= self.fruit_speed
                self.fruits.append(new_fruit)
            else:  # 20%概率生成炸弹
                new_bomb = Bomb()
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
                    self.game_over = True

        self.last_mouse_pos = pygame.mouse.get_pos()

    def draw(self, surface):
        """绘制游戏界面"""
        # 绘制背景
        surface.fill(WHITE)

        # 绘制水果
        for fruit in self.fruits:
            fruit.draw(surface)

        # 绘制炸弹
        for bomb in self.bombs:
            bomb.draw(surface)

        # 绘制分数
        score_text = get_font(30).render(f"分数: {self.score}", True, BLACK)
        surface.blit(score_text, (20, 20))

        # 绘制生命值
        lives_text = get_font(30).render(f"生命值: {self.lives}", True, BLACK)
        surface.blit(lives_text, (20, 60))

        # 绘制等级
        level_text = get_font(30).render(f"等级: {self.level}", True, BLACK)
        surface.blit(level_text, (20, 100))

        # 绘制游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            game_over_text = get_font(60).render("游戏结束", True, WHITE)
            game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            surface.blit(game_over_text, game_over_rect)

            final_score_text = get_font(40).render(f"最终分数: {self.score}", True, WHITE)
            final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
            surface.blit(final_score_text, final_score_rect)

            restart_text = get_font(30).render("按R键重新开始", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
            surface.blit(restart_text, restart_rect)

    def handle_event(self, event):
        """处理游戏事件"""
        if event.type == MOUSEBUTTONDOWN:
            self.slicing = True
        elif event.type == MOUSEBUTTONUP:
            self.slicing = False
            self.last_mouse_pos = None
        elif event.type == KEYDOWN:
            if event.key == K_r and self.game_over:
                self.reset_game()

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
            game.handle_event(event)

        game.update()
        game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()