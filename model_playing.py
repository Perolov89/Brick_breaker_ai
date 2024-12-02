import pygame
import sys
import numpy as np
import tensorflow as tf
import keras


# Initialize Pygame
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Brick Breaker - AI Player")
clock = pygame.time.Clock()
model = keras.models.load_model('brick_breaker_dqn.keras')


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class ModelPlayer:
    def __init__(self):
        self.model = model
        self.reset_game()

    def reset_game(self):
        # Initialize game objects
        self.paddle = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 40, 100, 20)
        self.ball = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 20, 20)
        self.ball_speed = [4, -4]
        self.bricks = self.create_bricks()
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)
        self.game_over = False
    
    def calculate_intercept(self):
    # Calculate x-coordinate where the ball will intersect the paddle's y-level
        if self.ball_speed[1] != 0:
            steps_to_paddle = (self.paddle.top - self.ball.bottom) / self.ball_speed[1]
            intercept_x = self.ball.centerx + self.ball_speed[0] * steps_to_paddle

            # Handle wall collisions (wrapping effect)
            while intercept_x < 0 or intercept_x > SCREEN_WIDTH:
                if intercept_x < 0:
                    intercept_x = -intercept_x
                elif intercept_x > SCREEN_WIDTH:
                    intercept_x = 2 * SCREEN_WIDTH - intercept_x
            return intercept_x / SCREEN_WIDTH
        return self.ball.centerx / SCREEN_WIDTH

    def create_bricks(self):
        bricks = []
        for row in range(5):
            for col in range(12):
                brick = pygame.Rect(col * 67, row * 25 + 40, 62, 20)
                bricks.append(brick)
        return bricks

    def get_state(self):
        # Convert game state to model input format
        # Normalize all values to be between 0 and 1
        intercept_x = self.calculate_intercept()
        return np.array([
        self.paddle.centerx / SCREEN_WIDTH,
        self.ball.centerx / SCREEN_WIDTH,
        self.ball.centery / SCREEN_HEIGHT,
        (self.ball_speed[0] + 10) / 20,
        (self.ball_speed[1] + 10) / 20,
        intercept_x
    ], dtype=np.float32)

    def update(self):
        if self.game_over:
            return True

        # Get model prediction
        state = self.get_state()
        q_values = self.model.predict(state[np.newaxis], verbose=0)[0]
        action = np.argmax(q_values)
        
        # Move paddle based on prediction
        # Action: 0 = left, 1 = stay, 2 = right
        paddle_speed = 8
        if action == 0:  # Left
            self.paddle.x = max(0, self.paddle.x - paddle_speed)
        elif action == 2:  # Right
            self.paddle.x = min(SCREEN_WIDTH - self.paddle.width, self.paddle.x + paddle_speed)

        # Debug info                         <==================================== debug
        print(f"State: {state}")
        print(f"Q-values: {q_values}")
        print(f"Chosen action: {action}")

        # Update ball position
        self.ball.x += self.ball_speed[0]
        self.ball.y += self.ball_speed[1]

        # Ball collisions with walls
        if self.ball.left <= 0 or self.ball.right >= SCREEN_WIDTH:
            self.ball_speed[0] = -self.ball_speed[0]
        if self.ball.top <= 0:
            self.ball_speed[1] = -self.ball_speed[1]

        # Paddle collision
        if self.ball.colliderect(self.paddle):
            # Calculate relative position of collision
            relative_intersect = (self.paddle.centerx - self.ball.centerx) / (self.paddle.width / 2)
            # Adjust angle based on where ball hits paddle
            self.ball_speed[0] = -relative_intersect * 5
            self.ball_speed[1] = -abs(self.ball_speed[1])  # Always bounce up

        # Brick collisions
        for brick in self.bricks[:]:
            if self.ball.colliderect(brick):
                self.bricks.remove(brick)
                self.ball_speed[1] = -self.ball_speed[1]
                self.score += 10
                break

        # Check game over conditions
        if self.ball.bottom > SCREEN_HEIGHT:
            self.game_over = True
        elif not self.bricks:  # Victory condition
            self.game_over = True

        return self.game_over
    
    def draw(self):
        screen.fill(BLACK)
        
        # Draw game objects
        pygame.draw.rect(screen, WHITE, self.paddle)
        pygame.draw.ellipse(screen, WHITE, self.ball)
        for brick in self.bricks:
            pygame.draw.rect(screen, WHITE, brick)

        # Draw score and time
        elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        time_text = self.font.render(f"Time: {elapsed_time:.2f}s", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(time_text, (SCREEN_WIDTH - 200, 10))

        # Draw game over message if applicable
        if self.game_over:
            game_over_font = pygame.font.Font(None, 48)
            if self.bricks:  # Lost
                text = game_over_font.render("Game Over! Press R to Restart", True, WHITE)
            else:  # Won
                text = game_over_font.render("Victory! Press R to Restart", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(text, text_rect)

    

def main():
    try:
        player = ModelPlayer()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and player.game_over:
                        player.reset_game()

            player.update()
            player.draw()
            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
