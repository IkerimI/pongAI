import pygame
import random

pygame.init()

# Define constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_WIDTH = 20
BALL_HEIGHT = 20

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Pong')

# Set up fonts
font = pygame.font.SysFont('Arial', 48)


class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 0.5
        self.score = 0

    def update(self, direction):
        if direction == 'up':
            self.y -= self.speed
        elif direction == 'down':
            self.y += self.speed

        if self.y < 0:
            self.y = 0
        elif self.y > SCREEN_HEIGHT - PADDLE_HEIGHT:
            self.y = SCREEN_HEIGHT - PADDLE_HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, PADDLE_WIDTH, PADDLE_HEIGHT))


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 0.2
        self.direction = random.choice([(1, 1), (-1, 1)])
        self.reset()

    def reset(self, winner=None):
        self.x = SCREEN_WIDTH / 2 - BALL_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2 - BALL_HEIGHT / 2
        if winner == 'left':
            self.direction = (1, 1)
        elif winner == 'right':
            self.direction = (-1, 1)
        else:
            self.direction = random.choice([(1, 1), (-1, 1)])

    def update(self, left_paddle, right_paddle):
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed

        # Check for collisions with left paddle
        if self.x <= left_paddle.x + PADDLE_WIDTH and \
                left_paddle.y < self.y + BALL_HEIGHT and \
                self.y < left_paddle.y + PADDLE_HEIGHT:
            self.direction = (1, self.direction[1])
            self.x = left_paddle.x + PADDLE_WIDTH
            left_paddle.score += 1
            # self.reset(winner='left')

        # Check for collisions with right paddle
        if self.x >= right_paddle.x - BALL_WIDTH and \
                right_paddle.y < self.y + BALL_HEIGHT and \
                self.y < right_paddle.y + PADDLE_HEIGHT:
            self.direction = (-1, self.direction[1])
            self.x = right_paddle.x - BALL_WIDTH
            right_paddle.score += 1
            # self.reset(winner='right')

        # Check for collisions with top/bottom
        if self.y <= 0:
            self.direction = (self.direction[0], 1)
            self.y = 0
        elif self.y >= SCREEN_HEIGHT - BALL_HEIGHT:
            self.direction = (self.direction[0], -1)
            self.y = SCREEN_HEIGHT - BALL_HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, BALL_WIDTH, BALL_HEIGHT))


class Game:
    def __init__(self):
        self.running = False
        self.winner = None
        self.left_paddle = Paddle(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(SCREEN_WIDTH - 50 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.ball = Ball(SCREEN_WIDTH // 2 - BALL_WIDTH // 2, SCREEN_HEIGHT // 2 - BALL_HEIGHT // 2)
        self.font = pygame.font.SysFont('Arial', 48)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.left_paddle.update('up')
            elif keys[pygame.K_s]:
                self.left_paddle.update('down')
            if keys[pygame.K_UP]:
                self.right_paddle.update('up')
            elif keys[pygame.K_DOWN]:
                self.right_paddle.update('down')

            # Update ball
            self.ball.update(self.left_paddle, self.right_paddle)
            if self.ball.x < 0:
                self.winner = 'right'
                self.running = False
            elif self.ball.x > SCREEN_WIDTH:
                self.winner = 'left'
                self.running = False
            # Check for winner
            if self.winner is not None:
                self.display_winner(self.winner)
                running = False

            # Draw everything to an off-screen buffer
            buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            buffer.fill((0, 0, 0))
            # pygame.draw.rect(buffer, (255, 255, 255), (SCREEN_WIDTH // 2 - 2, 0, 4, SCREEN_HEIGHT))
            self.left_paddle.draw(buffer)
            self.right_paddle.draw(buffer)
            self.ball.draw(buffer)
            score_text = self.font.render(f"{self.left_paddle.score} - {self.right_paddle.score}", True,
                                          (255, 255, 255))
            buffer.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 50))

            # Draw the entire buffer to the screen
            screen.blit(buffer, (0, 0))
            pygame.display.update()

        pygame.quit()

    def display_winner(self, winner):
        winner_text = self.font.render(f"Player {winner} wins!", True, (255, 255, 255))
        screen.blit(winner_text, (
            SCREEN_WIDTH // 2 - winner_text.get_width() // 2, SCREEN_HEIGHT // 2 - winner_text.get_height() // 2))
        pygame.display.update()
        pygame.time.delay(3000)


# Instantiate the game and run it
game = Game()
game.run()
