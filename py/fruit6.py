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
BLUE = (0, 0, 255)
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
            "apple": {
                "default": load_image("apple.png", (60, 60)),
                "gold": load_image("apple_gold.png", (60, 60))
            },
            "banana": {
                "default": load_image("banana.png", (60, 60)),
                "rainbow": load_image("banana_rainbow.png", (60, 60))
            },
            "watermelon": {
                "default": load_image("watermelon.png", (80, 80)),
                "frost": load_image("watermelon_frost.png", (80, 80))
            },
            "pear": {
                "default": load_image("pear.png", (60, 60))
            },
            "strawberry": {
                "default": load_image("strawberry.png", (50, 50))
            }
        }
        self.current_skin = self.game.current_skins[fruit_type]
        self.image = self.images[fruit_type][self.current_skin]
        self.sliced_image = self.create_sliced_image()

        # 加载音效（单个文件）
        self.slice_sound = load_sound("slice.mp3")

        # 水果属性
        self.combo_type = {
            "apple": "fire",
            "banana": "speed",
            "watermelon": "explosion",
            "pear": "freeze",
            "strawberry": "score"
        }.get(fruit_type, "normal")

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

        # 根据水果类型设置不同的切割效果
        if self.fruit_type == "apple":
            s.fill((255, 0, 0, 128))  # 红色半透明
            color = (255, 50, 50)  # 粒子颜色
        elif self.fruit_type == "watermelon":
            s.fill((0, 150, 0, 128))  # 绿色半透明
            color = (50, 200, 100)  # 粒子颜色
        elif self.fruit_type == "banana":
            s.fill((255, 255, 0, 128))  # 黄色半透明
            color = (255, 255, 50)  # 粒子颜色
        else:
            s.fill((255, 100, 100, 128))  # 默认红色半透明
            color = (255, 100, 100)  # 默认粒子颜色

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

            # 根据水果类型创建不同粒子效果
            if self.fruit_type == "apple":
                color = (255, 50, 50)  # 红色火花
                particle_count = 15
            elif self.fruit_type == "watermelon":
                color = (50, 200, 100)  # 绿色水花
                particle_count = 20
            elif self.fruit_type == "banana":
                color = (255, 255, 50)  # 黄色光点
                particle_count = 10
            else:
                color = (255, 100, 100)  # 默认颜色
                particle_count = 12

            # 创建粒子效果
            for _ in range(particle_count):
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


# 道具类
class Powerup:
    def __init__(self, game):
        self.game = game
        self.reset()
        self.image = load_image("powerup.png", (60, 60))

    def reset(self):
        self.radius = 30
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        self.y = WINDOW_HEIGHT + self.radius

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
        self.y += self.speed_y
        self.x += self.speed_x
        self.speed_y += self.gravity

        if self.y > WINDOW_HEIGHT + self.radius * 2 or self.x < -self.radius or self.x > WINDOW_WIDTH + self.radius:
            self.on_screen = False

    def draw(self, surface):
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.image, rect)

    def apply_effect(self):
        # 示例效果：双倍分数
        self.game.double_score_timer = 10 * FPS
        self.game.score_multiplier = 2


# 游戏类
class Game:
    def __init__(self):
        # 初始化属性（顺序很重要）
        self.difficulty = "medium"  # 默认难度
        self.weather = "sunny"  # 默认天气
        self.weather_timer = 0  # 天气切换计时器
        self.weather_change_interval = random.randint(300, 600)  # 天气切换间隔（帧数）
        self.weather_effects = {
            "sunny": {"speed": 1.0, "gravity": 0.9, "accuracy": 1.0},
            "rainy": {"speed": 0.9, "gravity": 1.0, "accuracy": 0.8},
            "snowy": {"speed": 0.8, "gravity": 0.8, "accuracy": 0.7}
        }

        # 水果类型列表（提前定义）
        self.fruit_types = ["apple", "banana", "watermelon", "pear", "strawberry"]

        # 皮肤系统（在reset_game之前初始化）
        self.unlocked_skins = {
            "apple": ["default", "gold"],
            "banana": ["default", "rainbow"],
            "watermelon": ["default", "frost"]
        }
        self.current_skins = {
            "apple": "default",
            "banana": "default",
            "watermelon": "default",
            "pear": "default",
            "strawberry": "default"
        }

        # 组合技系统
        self.combo_active = False
        self.combo_type = None
        self.combo_timer = 0
        self.recent_slices = []
        self.combo_sound = load_sound("combo.mp3")
        self.highest_combo = 0  # 新增属性记录最高连击

        # 道具系统
        self.powerups = []
        self.powerup_spawn_chance = 0.03  # 3%概率生成道具
        self.double_score_timer = 0
        self.score_multiplier = 1
        self.freeze_time = 0

        # 成就系统
        self.achievements = {
            "first_slice": False,
            "combo_master": False,
            "100_score": False,
            "all_weather": False,
            "hard_mode": False
        }

        # 现在可以安全地调用reset_game()
        self.reset_game()
        self.last_mouse_pos = None
        self.slicing = False
        self.current_screen = "main_menu"  # main_menu, difficulty, game, game_over

        # 新增初始化 last_spawn_time
        self.last_spawn_time = pygame.time.get_ticks()  # 添加这一行

        # 加载背景音乐
        self.background_music = load_sound("background.mp3")
        self.background_music.set_volume(0.3)
        self.background_music.play(-1)  # 循环播放

        # 预加载背景图片
        self.backgrounds = {
            "main_menu": load_image("background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "game_easy": load_image("beach_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "game_medium": load_image("beach_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "game_hard": load_image("beach_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "weather_sunny": load_image("sunny_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "weather_rainy": load_image("rainy_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT)),
            "weather_snowy": load_image("snowy_background.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
        }
    def reset_game(self):
        """重置游戏状态"""
        self.fruits = [self.create_random_fruit() for _ in range(3)]
        self.bombs = []
        self.powerups = []
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

    def point_to_line_distance(self, x1, y1, x2, y2, px, py):
        """计算点 (px, py) 到线段 (x1, y1) - (x2, y2) 的垂直距离"""
        numerator = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1)
        denominator = ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5
        return numerator / denominator if denominator != 0 else 0

    def check_button_click(self, pos, button_dict, action_map):
        """检查鼠标点击是否在按钮上并执行相应操作"""
        for button_name, button_rect in button_dict.items():
            if button_rect.collidepoint(pos):
                if button_name in action_map:
                    action_map[button_name]()
                return True
        return False

    def line_segment_intersects_circle(self, x1, y1, x2, y2, cx, cy, r):
        # 线段向量
        dx = x2 - x1
        dy = y2 - y1

        # 计算线段长度的平方
        line_len_sq = dx * dx + dy * dy

        # 处理线段长度为零的情况（起点和终点相同）
        if line_len_sq == 0:
            return False

        # 圆心到线段起点的向量
        fx = cx - x1
        fy = cy - y1

        # 计算点积
        dot_product = fx * dx + fy * dy

        # 计算投影参数t
        t = max(0, min(1, dot_product / line_len_sq))

        # 计算线段上最近点的坐标
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # 计算最近点到圆心的距离平方
        dist_sq = (closest_x - cx) ** 2 + (closest_y - cy) ** 2

        # 判断是否相交
        return dist_sq <= r * r

    def update(self):
        """更新游戏状态"""
        if self.current_screen != "game":
            return

        current_time = pygame.time.get_ticks()

        # 更新天气
        self.update_weather()

        # 检查组合技
        self.check_combo()

        # 处理冻结时间
        if self.freeze_time > 0:
            self.freeze_time -= 1
            if self.freeze_time == 0:
                # 恢复水果速度
                for fruit in self.fruits:
                    if isinstance(fruit, Fruit):  # 确保只有Fruit对象才调整速度
                        fruit.speed_y /= 0.2  # 假设冻结时速度为0.2倍
        # 双倍分数计时器
        if self.double_score_timer > 0:
            self.double_score_timer -= 1
            if self.double_score_timer == 0:
                self.score_multiplier = 1

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
                # 创建随机水果或道具
                new_fruit = self.create_random_fruit()

                # 调整水果初始速度，确保能飞到屏幕中上部
                base_vertical_speed = -10  # 基础垂直速度（负值表示向上）
                base_horizontal_speed = 2  # 基础水平速度

                # 根据难度调整速度
                if self.difficulty == "easy":
                    speed_factor = 0.8
                elif self.difficulty == "hard":
                    speed_factor = 1.2
                else:
                    speed_factor = 1.0

                # 应用难度和游戏进度的速度因子
                new_fruit.speed_y = base_vertical_speed * speed_factor * self.fruit_speed
                new_fruit.speed_x = random.uniform(-base_horizontal_speed,
                                                   base_horizontal_speed) * speed_factor * self.fruit_speed

                self.fruits.append(new_fruit)
            else:
                # 创建炸弹
                new_bomb = Bomb(self)

                # 调整炸弹初始速度，与水果保持一致
                base_vertical_speed = -10
                base_horizontal_speed = 2

                if self.difficulty == "easy":
                    speed_factor = 0.8
                elif self.difficulty == "hard":
                    speed_factor = 1.2
                else:
                    speed_factor = 1.0

                new_bomb.speed_y = base_vertical_speed * speed_factor * self.fruit_speed
                new_bomb.speed_x = random.uniform(-base_horizontal_speed,
                                                  base_horizontal_speed) * speed_factor * self.fruit_speed

                self.bombs.append(new_bomb)

            # 随机生成道具
            if random.random() < 0.05:
                new_powerup = Powerup(self)
                new_powerup.speed_y = base_vertical_speed * speed_factor * self.fruit_speed
                new_powerup.speed_x = random.uniform(-base_horizontal_speed,
                                                     base_horizontal_speed) * speed_factor * self.fruit_speed
                self.powerups.append(new_powerup)

        # 更新水果
        for fruit in self.fruits[:]:
            if self.freeze_time == 0:
                fruit.update()
            if not fruit.on_screen:
                if isinstance(fruit, Fruit) and not fruit.sliced:  # 确保只有Fruit对象才检查sliced属性
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        self.current_screen = "game_over"
                self.fruits.remove(fruit)

        # 更新炸弹
        for bomb in self.bombs[:]:
            if self.freeze_time == 0:
                bomb.update()
            if not bomb.on_screen:
                self.bombs.remove(bomb)

        # 更新道具
        for powerup in self.powerups[:]:
            if self.freeze_time == 0:
                powerup.update()
            if not powerup.on_screen:
                self.powerups.remove(powerup)

            # 处理鼠标切片
        if self.slicing and self.last_mouse_pos:
            current_mouse_pos = pygame.mouse.get_pos()

            # 检查是否切到水果
            for fruit in self.fruits:
                if isinstance(fruit, Fruit) and not fruit.sliced:
                    # 使用改进的线段与圆相交检测
                    if self.line_segment_intersects_circle(
                            self.last_mouse_pos[0], self.last_mouse_pos[1],
                            current_mouse_pos[0], current_mouse_pos[1],
                            fruit.x, fruit.y, fruit.radius * 0.8  # 略微缩小碰撞半径
                    ):
                        fruit.slice()
                        self.score += 1 * self.score_multiplier
                        self.recent_slices.append((fruit.combo_type, pygame.time.get_ticks()))
                        if not self.achievements["first_slice"]:
                            self.achievements["first_slice"] = True
                        # 检查成就
                        if self.score >= 100 and not self.achievements["100_score"]:
                            self.achievements["100_score"] = True
                            self.unlock_skin("watermelon", "frost")

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

            # 检查是否切到道具
            for powerup in self.powerups:
                distance = self.point_to_line_distance(
                    self.last_mouse_pos[0], self.last_mouse_pos[1],
                    current_mouse_pos[0], current_mouse_pos[1],
                    powerup.x, powerup.y
                )
                if distance <= powerup.radius:
                    powerup.apply_effect()
                    self.powerups.remove(powerup)

        self.last_mouse_pos = pygame.mouse.get_pos()

        # 清理过期的切片记录
        current_time = pygame.time.get_ticks()
        self.recent_slices = [s for s in self.recent_slices if current_time - s[1] < 2000]  # 保留2秒内的切片

        # 限制水果最大速度，防止飞出屏幕
        max_vertical_speed = 20
        max_horizontal_speed = 8

        for fruit in self.fruits:
            if isinstance(fruit, Fruit):  # 确保只有Fruit对象才调整速度
                fruit.speed_y = max(-max_vertical_speed, min(fruit.speed_y, max_vertical_speed))
                fruit.speed_x = max(-max_horizontal_speed, min(fruit.speed_x, max_horizontal_speed))

    def draw(self, surface):
        """绘制游戏界面"""
        if self.current_screen == "main_menu":
            self.draw_main_menu(surface)
        elif self.current_screen == "difficulty":
            self.draw_difficulty_menu(surface)
        elif self.current_screen == "game":
            self.draw_game(surface)
        elif self.current_screen == "game_over":
            self.draw_game_over(surface)
        elif self.current_screen == "achievements":
            self.draw_achievements(surface)
        elif self.current_screen == "skins":
            self.draw_skins(surface)

    def draw_main_menu(self, surface):
        """绘制主菜单"""
        # 绘制背景
        surface.blit(self.backgrounds["main_menu"], (0, 0))

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
        self.draw_button(surface, start_button, "开始游戏", (255, 100, 100))

        # 选择难度按钮
        difficulty_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 80, button_width, button_height)
        self.draw_button(surface, difficulty_button, "选择难度", (255, 165, 0))

        # 成就按钮
        achievements_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 160, button_width, button_height)
        self.draw_button(surface, achievements_button, "成就", (0, 200, 0))

        # 皮肤按钮
        skins_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 240, button_width, button_height)
        self.draw_button(surface, skins_button, "皮肤", (200, 0, 0))

        # 退出按钮
        exit_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 320, button_width, button_height)
        self.draw_button(surface, exit_button, "退出游戏", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.menu_buttons = {
            "start": start_button,
            "difficulty": difficulty_button,
            "achievements": achievements_button,
            "skins": skins_button,
            "exit": exit_button
        }

    def draw_difficulty_menu(self, surface):
        """绘制难度选择菜单"""
        # 绘制背景
        surface.blit(self.backgrounds["main_menu"], (0, 0))

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
        self.draw_button(surface, easy_button, "简单", (0, 200, 0))

        # 中等按钮
        medium_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y, button_width, button_height)
        self.draw_button(surface, medium_button, "中等", (255, 165, 0))

        # 困难按钮
        hard_button = pygame.Rect(WINDOW_WIDTH * 3 // 4 - button_width // 2, button_y, button_width, button_height)
        self.draw_button(surface, hard_button, "困难", (200, 0, 0))

        # 返回按钮
        back_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, button_y + 80, 200, 50)
        self.draw_button(surface, back_button, "返回", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.difficulty_buttons = {
            "easy": easy_button,
            "medium": medium_button,
            "hard": hard_button,
            "back": back_button
        }

    def draw_game(self, surface):
        """绘制游戏界面"""
        # 根据难度和天气选择背景
        if self.difficulty == "easy":
            base_bg = self.backgrounds["game_easy"]
        elif self.difficulty == "hard":
            base_bg = self.backgrounds["game_hard"]
        else:
            base_bg = self.backgrounds["game_medium"]

        weather_bg = self.backgrounds[f"weather_{self.weather}"]

        # 绘制背景
        surface.blit(base_bg, (0, 0))
        # 叠加天气效果
        surface.blit(weather_bg, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # 绘制水果
        for fruit in self.fruits:
            fruit.draw(surface)

        # 绘制炸弹
        for bomb in self.bombs:
            bomb.draw(surface)

        # 绘制道具
        for powerup in self.powerups:
            powerup.draw(surface)

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

        # 绘制天气
        weather_text = get_font(36).render(f"天气: {self.get_weather_name()}", True, WHITE)
        surface.blit(weather_text, (20, 180))

        # 绘制当前鼠标轨迹
        if self.slicing and self.last_mouse_pos:
            current_pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, WHITE, self.last_mouse_pos, current_pos, 3)

        # 绘制组合技效果
        if self.combo_active:
            combo_text = get_font(48).render(f"COMBO! {self.get_combo_effect_name()}", True, YELLOW)
            combo_rect = combo_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
            # 添加发光效果
            glow_surface = pygame.Surface(combo_rect.size, pygame.SRCALPHA)
            glow_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(glow_surface, (255, 255, 0, 128), glow_surface.get_rect(), border_radius=10)
            surface.blit(glow_surface, combo_rect.topleft)
            surface.blit(combo_text, combo_rect)

        # 绘制双倍分数效果
        if self.double_score_timer > 0:
            multiplier_text = get_font(36).render(f"双倍分数! x{self.score_multiplier}", True, RED)
            multiplier_rect = multiplier_text.get_rect(topright=(WINDOW_WIDTH - 20, 20))
            surface.blit(multiplier_text, multiplier_rect)

            # 绘制冻结时间效果
            if self.freeze_time > 0:
                # 创建半透明覆盖层
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 255, 50))  # 蓝色半透明
                surface.blit(overlay, (0, 0))

                # 显示冻结时间倒计时
                freeze_text = get_font(72).render(f"时间冻结! {self.freeze_time // FPS + 1}", True, BLUE)
                freeze_rect = freeze_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

                # 添加文字阴影效果
                shadow_text = get_font(72).render(f"时间冻结! {self.freeze_time // FPS + 1}", True, BLACK)
                shadow_rect = shadow_text.get_rect(center=(freeze_rect.centerx + 3, freeze_rect.centery + 3))
                surface.blit(shadow_text, shadow_rect)

                surface.blit(freeze_text, freeze_rect)

        # 返回按钮
        back_button = pygame.Rect(20, WINDOW_HEIGHT - 60, 120, 50)
        self.draw_button(surface, back_button, "返回菜单", (100, 100, 100))
        self.game_buttons = {"back": back_button}

    def draw_game_over(self, surface):
        """绘制游戏结束界面"""
        # 绘制半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 绘制游戏结束文本
        game_over_text = get_font(60).render("游戏结束", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(game_over_text, game_over_rect)

        # 绘制最终分数
        final_score_text = get_font(40).render(f"最终分数: {self.score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(final_score_text, final_score_rect)

        # 绘制最高连击
        combo_text = get_font(30).render(f"最高连击: {self.highest_combo}", True, WHITE)
        combo_rect = combo_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        surface.blit(combo_text, combo_rect)

        # 绘制按钮
        button_width = 200
        button_height = 50
        button_y = WINDOW_HEIGHT * 2 // 3

        # 重新开始按钮
        restart_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width - 20, button_y, button_width, button_height)
        self.draw_button(surface, restart_button, "重新开始", (255, 100, 100))

        # 返回菜单按钮
        menu_button = pygame.Rect(WINDOW_WIDTH // 2 + 20, button_y, button_width, button_height)
        self.draw_button(surface, menu_button, "返回菜单", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.game_over_buttons = {
            "restart": restart_button,
            "menu": menu_button
        }

    def draw_achievements(self, surface):
        """绘制成就界面"""
        # 绘制背景
        surface.blit(self.backgrounds["main_menu"], (0, 0))

        # 绘制标题
        title_text = get_font(50).render("成就", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 60))
        surface.blit(title_text, title_rect)

        # 绘制成就列表
        achievements = [
            {"name": "第一次切割", "description": "切到第一个水果", "achieved": self.achievements["first_slice"]},
            {"name": "连击大师", "description": "获得5次以上连击", "achieved": self.achievements["combo_master"]},
            {"name": "天气专家", "description": "体验所有天气",
             "achieved": self.achievements.get("all_weather", False)},
            {"name": "困难模式", "description": "在困难模式下完成游戏",
             "achieved": self.achievements.get("hard_mode", False)}
        ]

        y_position = 140
        for achievement in achievements:
            color = GREEN if achievement["achieved"] else RED
            status = "已解锁" if achievement["achieved"] else "未解锁"

            # 增加框的宽度（边距从150减少到100，框会更宽）
            box_width = WINDOW_WIDTH - 100  # 调整此处！
            box_height = 90
            box_x = 50  # 可能需要微调x坐标，保持居中
            box_y = y_position - 10

            # 绘制象牙色圆角背景框
            TRANSLUCENT_YELLOW = (255, 248, 220, 13)
            pygame.draw.rect(surface, TRANSLUCENT_YELLOW, (box_x, box_y, box_width, box_height), 0, border_radius=15)

            # 绘制成就名称（位置可能需要微调）
            name_text = get_font(28).render(achievement["name"], True, BLACK)
            surface.blit(name_text, (70, y_position))  # 微调x坐标

            # 绘制成就状态（位置可能需要微调）
            status_text = get_font(24).render(status, True, color)
            surface.blit(status_text, (WINDOW_WIDTH - 120, y_position))  # 微调x坐标

            # 绘制成就描述（位置可能需要微调）
            desc_text = get_font(20).render(achievement["description"], True, BLACK)
            surface.blit(desc_text, (90, y_position + 35))  # 微调x坐标

            y_position += 100
        # 返回按钮
        back_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 80, 200, 50)
        self.draw_button(surface, back_button, "返回", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.achievement_buttons = {"back": back_button}

    def draw_skins(self, surface):
        """绘制皮肤界面"""
        # 绘制背景
        surface.blit(self.backgrounds["main_menu"], (0, 0))

        # 绘制标题
        title_text = get_font(50).render("皮肤", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 60))
        surface.blit(title_text, title_rect)

        # 绘制水果和可用皮肤
        fruits = ["apple", "banana", "watermelon"]
        y_position = 150

        for fruit in fruits:
            # 绘制水果名称
            fruit_name = fruit.capitalize()
            name_text = get_font(32).render(fruit_name, True, WHITE)
            surface.blit(name_text, (50, y_position))

            # 绘制可用皮肤
            available_skins = self.unlocked_skins.get(fruit, ["default"])
            x_position = 200

            for skin in available_skins:
                # 绘制皮肤图标
                skin_image = load_image(f"{fruit}_{skin}.png", (80, 80))
                if skin_image.get_size() == (WINDOW_WIDTH, WINDOW_HEIGHT):
                    # 如果是错误图像，使用默认尺寸
                    skin_image = pygame.transform.scale(skin_image, (80, 80))
                rect = pygame.Rect(x_position, y_position - 20, 80, 80)
                surface.blit(skin_image, rect)

                # 绘制边框表示当前选中的皮肤
                if self.current_skins[fruit] == skin:
                    pygame.draw.rect(surface, YELLOW, rect, 3)

                # 绘制皮肤名称
                skin_name = skin.capitalize()
                if skin == "default":
                    skin_name = "默认"
                skin_text = get_font(18).render(skin_name, True, WHITE)
                surface.blit(skin_text, (x_position, y_position + 70))

                # 存储皮肤按钮位置供事件处理使用
                if not hasattr(self, "skin_buttons"):
                    self.skin_buttons = {}
                button_id = f"{fruit}_{skin}"
                self.skin_buttons[button_id] = rect

                x_position += 120

            y_position += 150

        # 返回按钮
        back_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 80, 200, 50)
        self.draw_button(surface, back_button, "返回", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.skin_buttons["back"] = back_button

    def draw_button(self, surface, rect, text, color):
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, rect, 3, border_radius=10)
        text_surface = get_font(36).render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def handle_main_menu_click(self, pos):
        """处理主菜单按钮点击"""
        action_map = {
            "start": lambda: setattr(self, "current_screen", "game"),
            "difficulty": lambda: setattr(self, "current_screen", "difficulty"),
            "achievements": lambda: setattr(self, "current_screen", "achievements"),
            "skins": lambda: setattr(self, "current_screen", "skins"),
            "exit": lambda: (pygame.quit(), sys.exit())
        }
        self.check_button_click(pos, self.menu_buttons, action_map)

    def handle_difficulty_click(self, pos):
        """处理难度选择菜单按钮点击"""
        action_map = {
            "easy": lambda: (setattr(self, "difficulty", "easy"), setattr(self, "current_screen", "main_menu")),
            "medium": lambda: (setattr(self, "difficulty", "medium"), setattr(self, "current_screen", "main_menu")),
            "hard": lambda: (setattr(self, "difficulty", "hard"), setattr(self, "current_screen", "main_menu")),
            "back": lambda: setattr(self, "current_screen", "main_menu")
        }
        self.check_button_click(pos, self.difficulty_buttons, action_map)

    def handle_game_click(self, pos):
        """处理游戏界面按钮点击"""
        action_map = {
            "back": lambda: setattr(self, "current_screen", "main_menu")
        }
        self.check_button_click(pos, self.game_buttons, action_map)

    def handle_game_over_click(self, pos):
        """处理游戏结束界面按钮点击"""
        action_map = {
            "restart": lambda: (self.reset_game(), setattr(self, "current_screen", "game")),
            "menu": lambda: setattr(self, "current_screen", "main_menu")
        }
        self.check_button_click(pos, self.game_over_buttons, action_map)

    def handle_achievements_click(self, pos):
        """处理成就界面按钮点击"""
        action_map = {
            "back": lambda: setattr(self, "current_screen", "main_menu")
        }
        self.check_button_click(pos, self.achievement_buttons, action_map)

    def handle_skins_click(self, pos):
        """处理皮肤界面按钮点击"""
        for button_id, rect in self.skin_buttons.items():
            if rect.collidepoint(pos):
                if button_id == "back":
                    self.current_screen = "main_menu"
                else:
                    # 解析按钮ID为水果和皮肤类型
                    fruit, skin = button_id.split('_')
                    self.current_skins[fruit] = skin
                break

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if self.current_screen == "game":
                        self.current_screen = "main_menu"
                    elif self.current_screen in ["difficulty", "achievements", "skins"]:
                        self.current_screen = "main_menu"
                elif event.key == K_r:
                    if self.current_screen == "game_over":
                        self.reset_game()
                        self.current_screen = "game"
            elif event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.slicing = True
                self.last_mouse_pos = mouse_pos

                # 处理不同屏幕的按钮点击
                if self.current_screen == "main_menu":
                    self.handle_main_menu_click(mouse_pos)
                elif self.current_screen == "difficulty":
                    self.handle_difficulty_click(mouse_pos)
                elif self.current_screen == "game":
                    self.handle_game_click(mouse_pos)
                elif self.current_screen == "game_over":
                    self.handle_game_over_click(mouse_pos)
                elif self.current_screen == "achievements":
                    self.handle_achievements_click(mouse_pos)
                elif self.current_screen == "skins":
                    self.handle_skins_click(mouse_pos)

            elif event.type == MOUSEBUTTONUP:
                self.slicing = False
                self.last_mouse_pos = None

    def check_combo(self):
        """检查并触发组合技"""
        if self.combo_active:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_active = False

        # 至少需要2个切片才能触发组合技
        if len(self.recent_slices) >= 2 and not self.combo_active:
            combo_types = [s[0] for s in self.recent_slices]

            # 检查是否有至少两种不同类型的水果被同时切开
            unique_types = set(combo_types)
            if len(unique_types) >= 2:
                # 触发组合技
                self.trigger_combo(unique_types)

    def trigger_combo(self, combo_types):
        self.combo_active = True
        self.combo_timer = 2 * FPS  # 组合技持续2秒

        # 简单示例：根据组合类型增加分数或冻结时间
        if "fire" in combo_types and "explosion" in combo_types:
            self.score += 20 * self.score_multiplier
        elif "freeze" in combo_types:
            self.freeze_time = 3 * FPS

        # 更新最高连击
        if len(self.recent_slices) > self.highest_combo:
            self.highest_combo = len(self.recent_slices)

    def update_weather(self):
        # 简单示例：每30秒随机切换一次天气
        if pygame.time.get_ticks() % 30000 < FPS:
            self.weather = random.choice(list(self.weather_effects.keys()))
            if len(set(self.weather_effects.keys())) == len(self.achievements.get("weather_history", [])) + 1:
                self.achievements["all_weather"] = True
            if "weather_history" not in self.achievements:
                self.achievements["weather_history"] = []
            if self.weather not in self.achievements["weather_history"]:
                self.achievements["weather_history"].append(self.weather)

    def get_difficulty_name(self):
        if self.difficulty == "easy":
            return "简单"
        elif self.difficulty == "medium":
            return "中等"
        else:
            return "困难"

    def get_weather_name(self):
        if self.weather == "sunny":
            return "晴天"
        elif self.weather == "rainy":
            return "雨天"
        else:
            return "有风"

    def get_combo_effect_name(self):
        # 简单示例：根据组合类型返回效果名称
        combo_types = [s[0] for s in self.recent_slices]
        if "fire" in combo_types and "explosion" in combo_types:
            return "火焰爆炸"
        elif "freeze" in combo_types:
            return "时间冻结"
        return "未知组合技"

    def unlock_skin(self, fruit, skin):
        if fruit not in self.unlocked_skins:
            self.unlocked_skins[fruit] = []
        if skin not in self.unlocked_skins[fruit]:
            self.unlocked_skins[fruit].append(skin)

    def run(self):
        while True:
            self.handle_events()  # 调用 handle_events 处理所有事件
            self.update()
            self.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
if __name__ == "__main__":
    game = Game()
    game.run()
