import pygame
import sys
import random
import math
import os
from pygame.constants import MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, K_r, K_ESCAPE, QUIT

# 初始化pygame
os.environ["SDL_VIDEO_ACCELERATED"] = "1"  # 启用硬件加速
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
ORANGE = (255, 165, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("切水果游戏")
clock = pygame.time.Clock()


# 加载字体
def get_font(size):
    return pygame.font.Font(font_path, size)


# 增强版资源加载函数
def load_image(name, scale=None):
    try:
        path = os.path.join("assets", name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")

        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except Exception as e:
        print(f"加载图像失败: {name} - 错误: {str(e)}")

        # 创建带错误信息的替代图像
        error_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        error_surface.fill(RED)

        font = pygame.font.Font(font_path, 24)
        error_text = font.render(f"无法加载: {name}", True, WHITE)
        path_text = font.render(f"路径: {os.path.abspath('assets')}", True, WHITE)
        help_text = font.render("请检查assets文件夹是否存在", True, WHITE)

        error_surface.blit(error_text, (20, 20))
        error_surface.blit(path_text, (20, 60))
        error_surface.blit(help_text, (20, 100))

        return error_surface


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
        self.on_screen = True
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

        # 加载音效
        self.slice_sound = load_sound("slice.mp3")

        # 水果属性
        self.combo_type = {
            "apple": "fire",
            "banana": "speed",
            "watermelon": "explosion",
            "pear": "freeze",
            "strawberry": "score"
        }.get(fruit_type, "normal")

        # 新增初始化 sliced
        self.sliced = False  # 添加这一行
        self.slice_particles = []
        self.particle_life = 30

        # 新增返回标志
        self.returning = False  # 添加返回标志
    def reset(self):
        """重置水果属性"""
        self.radius = 30
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        # 调整初始Y坐标，确保水果从屏幕下方开始但不会立即出界
        self.y = WINDOW_HEIGHT + self.radius  # 初始位置在屏幕下方边界

        # 根据难度设置初始速度
        difficulty = getattr(self.game, 'difficulty', "medium")  # 如果没有 difficulty 属性，则使用 "medium"
        base_vertical_speed = -10  # 基础垂直速度（负值表示向上）
        base_horizontal_speed = 2.5  # 基础水平速度

        if difficulty == "easy":
            speed_factor = 0.8
        elif difficulty == "hard":
            speed_factor = 1.2
        else:
            speed_factor = 1.0

        self.speed_y = base_vertical_speed * speed_factor
        self.speed_x = random.uniform(-base_horizontal_speed, base_horizontal_speed) * speed_factor
        self.gravity = 0.18  # 统一降低重力加速度
        self.on_screen = True

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
            # 应用天气效果
            weather_effect = self.game.get_weather_effect()
            self.speed_y *= weather_effect["speed"]
            self.gravity *= weather_effect["gravity"]

            # 更新位置
            self.y += self.speed_y
            self.x += self.speed_x
            self.speed_y += self.gravity

            # 检查是否达到折返点
            if not self.returning and self.y < WINDOW_HEIGHT / 2:  # 折返点在屏幕中间
                self.returning = True
                self.speed_y = abs(self.speed_y)  # 改变方向向下

            # 调整出界判断条件
            if (self.y > WINDOW_HEIGHT + self.radius * 2 or
                    self.x < -self.radius or
                    self.x > WINDOW_WIDTH + self.radius or
                    self.y < -self.radius * 2):  # 增加顶部边界检测
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
        # 调整炸弹初始Y坐标
        self.y = WINDOW_HEIGHT + random.randint(self.radius * 2, self.radius * 4)

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
        # 应用天气效果
        weather_effect = self.game.get_weather_effect()
        self.speed_y *= weather_effect["speed"]
        self.gravity *= weather_effect["gravity"]

        self.y += self.speed_y
        self.x += self.speed_x
        self.speed_y += self.gravity

        # 调整出界判断条件
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
class PowerUp:
    def __init__(self, power_type, game):
        self.game = game
        self.power_type = power_type
        self.reset()
        self.images = {
            "slow": load_image("slow_powerup.png", (40, 40)),
            "double": load_image("double_powerup.png", (40, 40)),
            "freeze": load_image("freeze_powerup.png", (40, 40)),
            "extra_life": load_image("extra_life.png", (40, 40))
        }
        self.image = self.images.get(power_type, self.images["slow"])
        self.pickup_sound = load_sound("powerup.mp3")

    def reset(self):
        """重置道具属性"""
        self.radius = 20
        self.x = random.randint(self.radius, WINDOW_WIDTH - self.radius)
        # 调整道具初始Y坐标
        self.y = WINDOW_HEIGHT + random.randint(self.radius * 2, self.radius * 4)
        self.speed_y = random.randint(-12, -8)
        self.speed_x = random.uniform(-2, 2)
        self.gravity = 0.25
        self.on_screen = True
        self.effect_duration = 300  # 效果持续时间(帧)

    def update(self):
        """更新道具位置"""
        self.y += self.speed_y
        self.x += self.speed_x
        self.speed_y += self.gravity

        # 调整出界判断条件
        if self.y > WINDOW_HEIGHT + self.radius * 2 or self.x < -self.radius or self.x > WINDOW_WIDTH + self.radius:
            self.on_screen = False

    def draw(self, surface):
        """绘制道具"""
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.image, rect)

    def apply_effect(self):
        """应用道具效果"""
        self.pickup_sound.play()

        if self.power_type == "slow":
            for fruit in self.game.fruits:
                fruit.speed_y *= 0.6
                fruit.speed_x *= 0.6
        elif self.power_type == "double":
            self.game.score_multiplier = 2
            self.game.double_score_timer = self.effect_duration
        elif self.power_type == "freeze":
            self.game.freeze_time = self.effect_duration
        elif self.power_type == "extra_life":
            self.game.lives += 1


# 游戏类
class Game:
    def __init__(self):
        # 初始化属性
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

        # 确保在调用reset_game之前初始化所有依赖的属性
        self.powerup_spawn_chance = 0.03  # 3%概率生成道具

        self.reset_game()
        self.last_mouse_pos = None
        self.slicing = False
        self.current_screen = "main_menu"  # main_menu, difficulty, game, game_over

        # 新增初始化 last_spawn_time
        self.last_spawn_time = pygame.time.get_ticks()  # 添加这一行

        # 组合技系统
        self.combo_active = False
        self.combo_type = None
        self.combo_timer = 0
        self.recent_slices = []
        self.combo_sound = load_sound("combo.mp3")


        # 道具系统
        self.powerups = []
        # 已在上方初始化

        # 成就系统
        self.achievements = {
            "first_slice": False,
            "combo_master": False,
            "100_score": False,
            "all_weather": False,
            "hard_mode": False
        }
        self.unlocked_skins = {
            "apple": ["default", "gold"],
            "banana": ["default", "rainbow"],
            "watermelon": ["default", "frost"]
        }
        self.current_skins = {
            "apple": "default",
            "banana": "default",
            "watermelon": "default"
        }

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
        # 减少初始水果数量，避免同时出界导致游戏立即结束
        self.fruits = [self.create_random_fruit() for _ in range(1)]
        self.bombs = []
        self.powerups = []
        self.score = 0
        self.score_multiplier = 1
        self.double_score_timer = 0
        self.lives = 3
        self.game_over = False
        self.level = 1
        self.fruit_speed = 1.0
        self.spawn_timer = 0
        self.freeze_time = 0
        self.highest_combo = 0

        # 根据难度设置生成延迟
        if self.difficulty == "easy":
            self.spawn_delay = 80  # 增加简单模式的生成间隔
        elif self.difficulty == "medium":
            self.spawn_delay = 55
        else:  # hard
            self.spawn_delay = 40  # 减少困难模式的生成间隔，但不过度

        # 调整初始水果数量
        self.fruits = [self.create_random_fruit() for _ in range(2)]

    def create_random_fruit(self):
        """创建随机水果"""
        # 3%概率生成道具
        if random.random() < self.powerup_spawn_chance and len(self.powerups) < 2:
            power_type = random.choice(["slow", "double", "freeze", "extra_life"])
            return PowerUp(power_type, self)

        return Fruit(random.choice(self.fruit_types), self)

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
        if current_time - self.last_spawn_time > self.spawn_delay * 1000 / FPS and self.freeze_time == 0:
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
        if self.slicing and self.last_mouse_pos and self.freeze_time == 0:
            current_mouse_pos = pygame.mouse.get_pos()

            # 检查是否切到水果
            for fruit in self.fruits:
                if isinstance(fruit, Fruit) and not fruit.sliced:  # 确保只有Fruit对象才检查sliced属性
                    distance = self.point_to_line_distance(
                        self.last_mouse_pos[0], self.last_mouse_pos[1],
                        current_mouse_pos[0], current_mouse_pos[1],
                        fruit.x, fruit.y
                    )
                    if distance <= fruit.radius * self.weather_effects[self.weather]["accuracy"]:
                        fruit.slice()
                        self.score += 1 * self.score_multiplier
                        self.recent_slices.append((fruit.combo_type, pygame.time.get_ticks()))
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


    def update_weather(self):
        """更新天气状态"""
        self.weather_timer += 1
        if self.weather_timer >= self.weather_change_interval:
            self.weather = random.choice(["sunny", "rainy", "snowy"])
            self.weather_timer = 0
            self.weather_change_interval = random.randint(300, 600)
        elif self.score >= 100 and self.weather != "rainy":
            self.weather = "rainy"
        elif self.score >= 200 and self.weather != "snowy":
            self.weather = "snowy"
    def get_weather_effect(self):
        """获取当前天气效果"""
        return self.weather_effects.get(self.weather, self.weather_effects["sunny"])
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
        """触发组合技效果"""
        self.combo_active = True
        self.combo_timer = 180  # 组合技持续3秒(180帧)
        self.combo_sound.play()

        # 根据组合类型应用不同效果
        if "fire" in combo_types and "explosion" in combo_types:
            # 火焰爆炸 - 摧毁屏幕上所有水果并加分
            for fruit in self.fruits[:]:
                if not fruit.sliced:
                    fruit.slice()
                    self.score += 3 * self.score_multiplier
        elif "speed" in combo_types and "freeze" in combo_types:
            # 速度冻结 - 暂停所有水果移动5秒
            self.freeze_time = 300
        elif "score" in combo_types and any(t in combo_types for t in ["fire", "speed", "explosion", "freeze"]):
            # 分数加成 - 双倍分数10秒
            self.score_multiplier = 4
            self.double_score_timer = min(self.double_score_timer, 600)  # 最多10秒

        # 更新最高连击
        current_combo = len(self.recent_slices)
        if current_combo > self.highest_combo:
            self.highest_combo = current_combo
            if self.highest_combo >= 5 and not self.achievements["combo_master"]:
                self.achievements["combo_master"] = True
                self.unlock_skin("banana", "rainbow")

    def unlock_skin(self, fruit_type, skin_name):
        """解锁水果皮肤"""
        if fruit_type in self.unlocked_skins and skin_name not in self.unlocked_skins[fruit_type]:
            self.unlocked_skins[fruit_type].append(skin_name)
            print(f"解锁新皮肤: {fruit_type} - {skin_name}")

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

        # 成就按钮
        achievement_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 80, button_width,
                                         button_height)
        self.draw_button(surface, achievement_button, "成就", (100, 150, 255))

        # 皮肤按钮
        skin_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 160, button_width, button_height)
        self.draw_button(surface, skin_button, "皮肤", (150, 200, 100))

        # 退出按钮
        exit_button = pygame.Rect(WINDOW_WIDTH // 2 - button_width // 2, button_y + 240, button_width, button_height)
        self.draw_button(surface, exit_button, "退出游戏", (100, 100, 100))

        # 存储按钮位置供事件处理使用
        self.menu_buttons = {
            "start": start_button,
            "achievements": achievement_button,
            "skins": skin_button,
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
            freeze_text = get_font(36).render(f"时间冻结! {self.freeze_time // FPS + 1}", True, BLUE)
            freeze_rect = freeze_text.get_rect(topright=(WINDOW_WIDTH - 20, 60))
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
            {"name": "高分选手", "description": "获得100分以上", "achieved": self.achievements["100_score"]},
            {"name": "天气专家", "description": "体验所有天气",
             "achieved": self.achievements.get("all_weather", False)},
            {"name": "困难模式", "description": "在困难模式下完成游戏",
             "achieved": self.achievements.get("hard_mode", False)}
        ]

        y_position = 140
        for achievement in achievements:
            color = GREEN if achievement["achieved"] else RED
            status = "已解锁" if achievement["achieved"] else "未解锁"

            # 绘制成就名称
            name_text = get_font(28).render(achievement["name"], True, WHITE)
            surface.blit(name_text, (100, y_position))

            # 绘制成就状态
            status_text = get_font(24).render(status, True, color)
            surface.blit(status_text, (WINDOW_WIDTH - 150, y_position))

            # 绘制成就描述
            desc_text = get_font(20).render(achievement["description"], True, WHITE)
            surface.blit(desc_text, (120, y_position + 35))

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
        """绘制按钮"""
        # 绘制按钮背景
        pygame.draw.rect(surface, color, rect, border_radius=10)
        # 绘制按钮边框
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)
        # 绘制按钮文本
        text_surface = get_font(28).render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def point_to_line_distance(self, x1, y1, x2, y2, x3, y3):
        """计算点(x3,y3)到线段(x1,y1)-(x2,y2)的距离"""
        px = x2 - x1
        py = y2 - y1

        norm = px * px + py * py

        if norm == 0:
            return math.hypot(x3 - x1, y3 - y1)

        t = ((x3 - x1) * px + (y3 - y1) * py) / norm

        if t < 0:
            dx = x3 - x1
            dy = y3 - y1
        elif t > 1:
            dx = x3 - x2
            dy = y3 - y2
        else:
            nx = x1 + t * px
            ny = y1 + t * py
            dx = x3 - nx
            dy = y3 - ny

        return math.hypot(dx, dy)

    def get_difficulty_name(self):
        """获取难度名称"""
        if self.difficulty == "easy":
            return "简单"
        elif self.difficulty == "medium":
            return "中等"
        else:
            return "困难"

    def get_weather_name(self):
        """获取天气名称"""
        if self.weather == "sunny":
            return "晴天"
        elif self.weather == "rainy":
            return "雨天"
        else:
            return "雪天"

    def get_combo_effect_name(self):
        """获取组合技效果名称"""
        if not self.combo_active:
            return ""

        combo_types = set([s[0] for s in self.recent_slices])

        if "fire" in combo_types and "explosion" in combo_types:
            return "火焰爆炸"
        elif "speed" in combo_types and "freeze" in combo_types:
            return "速度冻结"
        elif "score" in combo_types and any(t in combo_types for t in ["fire", "speed", "explosion", "freeze"]):
            return "分数加成"
        else:
            return "组合技"

    def handle_event(self, event):
        """处理游戏事件"""
        if event.type == QUIT:
            return False

        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if self.current_screen == "game":
                    self.current_screen = "main_menu"
                elif self.current_screen == "difficulty":
                    self.current_screen = "main_menu"
                elif self.current_screen == "game_over":
                    self.current_screen = "main_menu"
                elif self.current_screen in ["achievements", "skins"]:
                    self.current_screen = "main_menu"

        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                self.slicing = True
                self.last_mouse_pos = pygame.mouse.get_pos()

                # 处理按钮点击
                if self.current_screen == "main_menu":
                    if hasattr(self, 'menu_buttons'):
                        if self.menu_buttons["start"].collidepoint(event.pos):
                            self.current_screen = "difficulty"
                        elif self.menu_buttons["achievements"].collidepoint(event.pos):
                            self.current_screen = "achievements"
                        elif self.menu_buttons["skins"].collidepoint(event.pos):
                            self.current_screen = "skins"
                        elif self.menu_buttons["exit"].collidepoint(event.pos):
                            return False

                elif self.current_screen == "difficulty":
                    if hasattr(self, 'difficulty_buttons'):
                        if self.difficulty_buttons["easy"].collidepoint(event.pos):
                            self.difficulty = "easy"
                            self.reset_game()
                            self.current_screen = "game"
                        elif self.difficulty_buttons["medium"].collidepoint(event.pos):
                            self.difficulty = "medium"
                            self.reset_game()
                            self.current_screen = "game"
                        elif self.difficulty_buttons["hard"].collidepoint(event.pos):
                            self.difficulty = "hard"
                            self.reset_game()
                            self.current_screen = "game"
                        elif self.difficulty_buttons["back"].collidepoint(event.pos):
                            self.current_screen = "main_menu"

                elif self.current_screen == "game":
                    if hasattr(self, 'game_buttons') and self.game_buttons["back"].collidepoint(event.pos):
                        self.current_screen = "main_menu"

                elif self.current_screen == "game_over":
                    if hasattr(self, 'game_over_buttons'):
                        if self.game_over_buttons["restart"].collidepoint(event.pos):
                            self.reset_game()
                            self.current_screen = "game"
                        elif self.game_over_buttons["menu"].collidepoint(event.pos):
                            self.current_screen = "main_menu"

                elif self.current_screen == "achievements":
                    if hasattr(self, 'achievement_buttons') and self.achievement_buttons["back"].collidepoint(
                            event.pos):
                        self.current_screen = "main_menu"

                elif self.current_screen == "skins":
                    if hasattr(self, 'skin_buttons'):
                        if self.skin_buttons["back"].collidepoint(event.pos):
                            self.current_screen = "main_menu"
                        else:
                            # 处理皮肤选择
                            for button_id, rect in self.skin_buttons.items():
                                if button_id != "back" and rect.collidepoint(event.pos):
                                    fruit, skin = button_id.split("_")
                                    if skin in self.unlocked_skins.get(fruit, []):
                                        self.current_skins[fruit] = skin

        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:  # 左键
                self.slicing = False

        return True
    def run(self):
        """运行游戏主循环"""
        running = True
        while running:
            clock.tick(FPS)

            # 处理事件
            for event in pygame.event.get():
                running = self.handle_event(event)

            # 更新游戏状态
            self.update()

            # 绘制游戏
            self.draw(screen)

            # 刷新屏幕
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # 游戏入口
if __name__ == "__main__":
    game = Game()
    game.run()