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
        self.observation_space = spaces.Box(low=0, high=1, shape=(7,), dtype=np.float32)   # State space dimensions
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
        self.ball_dx, self.ball_dy = random.choice([-0.03, 0.03]), random.choice([-0.03, 0.03])
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
        for brick in self.bricks[:]:  # Use a copy of the list to avoid modification during iteration
            if (self.ball_x * SCREEN_WIDTH >= brick.left and
                self.ball_x * SCREEN_WIDTH <= brick.right and
                self.ball_y * SCREEN_HEIGHT >= brick.top and
                self.ball_y * SCREEN_HEIGHT <= brick.bottom):
                
                self.bricks.remove(brick)  
                self.ball_dy *= -1         
                self.score += 10           
                reward += 10               
                break  


                                                    #         <============================= Rewards
        
        # Game won
        if not self.bricks:  # All bricks broken
            done = True
            reward += 50  # Bonus reward for clearing all bricks


        # Ball-wall collision
        if self.ball_x <= 0 or self.ball_x >= 1:
            self.ball_dx *= -1
        if self.ball_y <= 0:
            self.ball_dy *= -1
        if self.ball_y >= 1:  # Ball lost
            reward = -20  # Strong penalty for losing
            done = True



        # Check for paddle collision
        if self.ball_y >= 0.95 and abs(self.paddle_x - self.ball_x) < 0.1:
            self.ball_dy *= -1
            reward += 30


        # Close to ball 
        if abs(self.paddle_x - self.ball_x) < 0.1:
            reward += 2  # Small reward for being near the ball


        # Predict trajectory
        predicted_ball_x = self.ball_x + self.ball_dx * (1 - self.ball_y)  # Approximate where ball will land
        if abs(self.paddle_x - predicted_ball_x) < 0.1:
            reward += 5  # Reward for being aligned with the predicted trajectory  
        if (action == 0 and self.paddle_x < predicted_ball_x) or (action == 1 and self.paddle_x > predicted_ball_x):
            reward -= 1 # Penalize for moving away


        # Update time and add small reward
        current_time = pygame.time.get_ticks()
        self.time_elapsed = (current_time - self.start_time) / 1000  # Time in seconds
        reward += 0.1  # Reward for survival

        return (np.array([self.ball_x, self.ball_y, self.ball_dx, self.ball_dy, self.paddle_x, self.ball_start_x, self.ball_start_y]),
        reward, done, {"score": self.score, "time": self.time_elapsed})


# Main loop <=========================================

def main():
    state = STATE_PLAYING  # <============================= state

    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks()
    score = 0
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Restart game with Spacebar
                if state != STATE_PLAYING and event.key == pygame.K_SPACE:  # <============= state
                    state = STATE_PLAYING
                    ball = Ball()
                    paddle = Paddle()
                    bricks = create_bricks()
                    score = 0
                    start_time = pygame.time.get_ticks()

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

            # Draw the score and timer
            draw_score_and_timer(score, start_time)

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

            # Check for game over condition    <============================= conclusion states
            if ball.rect.top > SCREEN_HEIGHT:
                state = STATE_GAME_OVER

            # Check for victory condition
            if not bricks:
                state = STATE_VICTORY

        elif state == STATE_GAME_OVER:
            display_message("Game Over! Press Space to Restart")

        elif state == STATE_VICTORY:
            display_message("You Win! Press Space to Restart")

        # Refresh the game window
        pygame.display.flip()

        # Tick the clock
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
