import pygame
import sys
import random
import numpy as np
import gym
from gym import spaces

pygame.init()

# Screen <=========================================

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Fonts
FONT = pygame.font.Font(None, 36)

# Game states
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("BricK BreakeR")


# Clock for controlling the frame rate
clock = pygame.time.Clock()


# Paddle <=========================================

# Properties
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_COLOR = WHITE
PADDLE_SPEED = 8


class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2,
                                SCREEN_HEIGHT - 40, PADDLE_WIDTH, PADDLE_HEIGHT)

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += PADDLE_SPEED

    def draw(self):
        pygame.draw.rect(screen, PADDLE_COLOR, self.rect)

# Ball <=========================================


# Properties
BALL_RADIUS = 10
BALL_COLOR = WHITE


class Ball:
    def __init__(self):
        start_x = random.randint(50, SCREEN_WIDTH - 50)
        self.rect = pygame.Rect(start_x, SCREEN_HEIGHT // 2,
                                BALL_RADIUS * 2, BALL_RADIUS * 2)

        self.speed = [random.choice([-4, 4]), random.choice([-4, -3, -2])]

    def move(self):
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]

        # Bounce off walls
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed[0] = -self.speed[0]
        if self.rect.top <= 0:
            self.speed[1] = -self.speed[1]

    def draw(self):
        pygame.draw.ellipse(screen, BALL_COLOR, self.rect)


# Bricks <=========================================

BRICK_WIDTH = 62
BRICK_HEIGHT = 20
BRICK_COLOR = WHITE
BRICK_ROWS = 5
BRICK_COLS = 12
BRICK_PADDING = 5


def create_bricks():
    bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = col * (BRICK_WIDTH + BRICK_PADDING)
            y = row * (BRICK_HEIGHT + BRICK_PADDING) + 40
            brick = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
            bricks.append(brick)
    return bricks


bricks = create_bricks()


def draw_bricks(bricks):
    for brick in bricks:
        pygame.draw.rect(screen, BRICK_COLOR, brick)


# Game over or victory message

def display_message(text):
    message = FONT.render(text, True, WHITE)
    text_rect = message.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(message, text_rect)


# Score and timer <=========================================
def draw_score_and_timer(score, start_time):
    # Calculate elapsed time
    elapsed_time = pygame.time.get_ticks() - start_time
    seconds = elapsed_time // 1000
    centiseconds = elapsed_time % 100

    # Render score and timer
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    timer_text = FONT.render(
        f"Time: {seconds}.{centiseconds:02d}", True, WHITE)

    # Display score and timer
    screen.blit(score_text, (10, 10))
    screen.blit(timer_text, (SCREEN_WIDTH - 200, 10))


# =============================================================================== model


class BrickBreakerEnv(gym.Env):
    def __init__(self):
        super(BrickBreakerEnv, self).__init__()
        self.observation_space = spaces.Box(low=0, high=1, shape=(
            7,), dtype=np.float32)   # State space dimensions
        self.action_space = spaces.Discrete(3)
        self.reset()
        self.bricks = create_bricks()

    def create_bricks(self):
        brick_list = []
        for row in range(5):  # Adjust row/column as needed
            for col in range(12):
                x = col * (BRICK_WIDTH + BRICK_PADDING)
                y = row * (BRICK_HEIGHT + BRICK_PADDING) + 40
                brick = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
                brick_list.append(brick)
        return brick_list

    def reset(self):
        self.ball_x, self.ball_y = random.uniform(0.1, 0.9), 0.5
        self.ball_dx, self.ball_dy = random.choice(
            [-0.03, 0.03]), random.choice([-0.03, 0.03])
        self.paddle_x = 0.5
        self.score = 0
        self.time_elapsed = 0
        self.start_time = pygame.time.get_ticks()
        self.ball_start_x = self.ball_x  # Track starting position
        self.ball_start_y = self.ball_y
        self.bricks = self.create_bricks()
        return np.array([self.ball_x, self.ball_y, self.ball_dx, self.ball_dy, self.paddle_x, self.ball_start_x, self.ball_start_y])

    def step(self, action):
        reward = 0
        done = False

        # Paddle movement logic
        if action == 0:
            self.paddle_x = max(0, self.paddle_x - 0.05)
        elif action == 1:
            self.paddle_x = min(1, self.paddle_x + 0.05)

        # Ball movement logic
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Check for brick collisions
        for brick in self.bricks[:]:
            if (self.ball_x * SCREEN_WIDTH >= brick.left and
                self.ball_x * SCREEN_WIDTH <= brick.right and
                self.ball_y * SCREEN_HEIGHT >= brick.top and
                    self.ball_y * SCREEN_HEIGHT <= brick.bottom):
                self.bricks.remove(brick)
                self.ball_dy *= -1
                self.score += 10
                reward += 20  # Increased reward for breaking bricks
                break

        # Game won
        if not self.bricks:
            done = True
            reward += 100  # Increased bonus for winning

        # Ball-wall collision
        if self.ball_x <= 0 or self.ball_x >= 1:
            self.ball_dx *= -1
        if self.ball_y <= 0:
            self.ball_dy *= -1
        if self.ball_y >= 1:  # Ball lost
            reward -= 50  # Increased penalty for losing
            done = True

        # Paddle collision rewards
        if self.ball_y >= 0.95:
            if abs(self.paddle_x - self.ball_x) < 0.1:
                reward += 40  # Increased reward for successful paddle hit
                # Additional reward for centered hits
                paddle_center = abs(self.paddle_x - self.ball_x) < 0.05
                if paddle_center:
                    reward += 10
            else:
                # Penalty increases as ball gets closer to bottom
                reward -= 10 * (self.ball_y - 0.95) / 0.05

        # Positioning rewards
        predicted_landing = self.ball_x + (self.ball_dx / self.ball_dy) * (1 - self.ball_y)
        distance_to_prediction = abs(self.paddle_x - predicted_landing)
        
        # Reward for moving towards predicted landing position
        if distance_to_prediction < 0.2:
            reward += 5 * (0.2 - distance_to_prediction)  # More reward for better positioning
        
        # Penalty for moving away from the ball when it's falling
        if self.ball_dy > 0:  # Ball is moving down
            if (action == 0 and self.ball_x > self.paddle_x) or \
               (action == 1 and self.ball_x < self.paddle_x):
                reward -= 2

        # Small survival reward
        reward += 0.1

        return (np.array([self.ball_x, self.ball_y, self.ball_dx, self.ball_dy, 
                         self.paddle_x, self.ball_start_x, self.ball_start_y]),
                reward, done, {"score": self.score, "time": self.time_elapsed})


# Main loop <=========================================

def main():
    state = STATE_PLAYING
    end_time = None  # Add this to track when game/round ends
    RESTART_DELAY = 2000  # 2 seconds in milliseconds

    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks()
    score = 0
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill the screen with black
        screen.fill(BLACK)

        if state == STATE_PLAYING:
            # Get key states and update paddle <============================= state
            keys = pygame.key.get_pressed()
            paddle.move(keys)
            ball.move()

            # Draw the bricks, paddle, and ball
            draw_bricks(bricks)
            paddle.draw()
            ball.draw()

            # Paddle collision
            if ball.rect.colliderect(paddle.rect):
                # Check if the ball hits the top of the paddle
                if ball.rect.bottom >= paddle.rect.top and ball.rect.centery < paddle.rect.top:
                    # Ensure the ball always bounces upward
                    ball.speed[1] = -abs(ball.speed[1])
                # Check if the ball hits the left side of the paddle
                elif ball.rect.right >= paddle.rect.left and ball.rect.centerx < paddle.rect.left:
                    ball.speed[0] = -abs(ball.speed[0])  # Bounce horizontally
                    ball.rect.right = paddle.rect.left  # Nudge the ball outside
                # Check if the ball hits the right side of the paddle
                elif ball.rect.left <= paddle.rect.right and ball.rect.centerx > paddle.rect.right:
                    ball.speed[0] = abs(ball.speed[0])  # Bounce horizontally
                    ball.rect.left = paddle.rect.right  # Nudge the ball outside

            # Check for brick collisions
            for brick in bricks[:]:
                if ball.rect.colliderect(brick):
                    ball.speed[1] = -ball.speed[1]
                    bricks.remove(brick)
                    score += 10
                    break

            # Check for game over condition
            if ball.rect.top > SCREEN_HEIGHT:
                state = STATE_GAME_OVER
                end_time = current_time
                
            # Check for victory condition
            if not bricks:
                state = STATE_VICTORY
                end_time = current_time

        elif state == STATE_GAME_OVER:
            display_message("Game Over!")
            if current_time - end_time >= RESTART_DELAY:
                state = STATE_PLAYING
                ball = Ball()
                paddle = Paddle()
                bricks = create_bricks()

        elif state == STATE_VICTORY:
            display_message("You Win!")
            if current_time - end_time >= RESTART_DELAY:
                state = STATE_PLAYING
                ball = Ball()
                paddle = Paddle()
                bricks = create_bricks()

        # Draw the score and timer
        draw_score_and_timer(score, start_time)

        # Refresh the game window
        pygame.display.flip()

        # Tick the clock
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
