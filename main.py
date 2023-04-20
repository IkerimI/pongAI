import pickle
import time
import neat
import pygame
import random
import os
from numba import jit, cuda

pygame.init()

# Define constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 100
BALL_WIDTH = 20
BALL_HEIGHT = 20
SPEED = 0.7

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Pong')

# Set up fonts
font = pygame.font.SysFont('Arial', 48)


class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = SPEED
        self.score = 0

    def update(self, direction):
        if direction == 'up':
            self.y -= self.speed
        elif direction == 'down':
            self.y += self.speed

        if self.y < 0:
            return False
        elif self.y > SCREEN_HEIGHT - PADDLE_HEIGHT:
            return False
        else:
            return True

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, PADDLE_WIDTH, PADDLE_HEIGHT))


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = SPEED
        self.direction = (random.choice([1, -1]), random.randrange(-100, 100))
        self.reset()

    def reset(self, winner=None):
        if winner == 'left':
            self.direction = (1, 1)
        elif winner == 'right':
            self.direction = (-1, 1)
        else:
            self.direction = (random.choice([1, -1]), random.randrange(-10, 10))
        self.x = SCREEN_WIDTH / 2 - BALL_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2 - BALL_HEIGHT / 2

    def update(self, left_paddle, right_paddle):
        if self.direction[1] == 0:
            self.reset()
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


class GameInformation:
    def __init__(self, left_hits, right_hits, left_score, right_score):
        self.left_hits = left_hits
        self.right_hits = right_hits
        self.left_score = left_score
        self.right_score = right_score


class Game:
    def __init__(self):
        self.running = False
        self.winner = None
        self.left_paddle = Paddle(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(SCREEN_WIDTH - 50 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.ball = Ball(SCREEN_WIDTH // 2 - BALL_WIDTH // 2, SCREEN_HEIGHT // 2 - BALL_HEIGHT // 2)
        self.font = pygame.font.SysFont('Arial', 48)
        self.left_score = 0
        self.right_score = 0

    # @jit(forceobj=True)
    def run(self):
        keys = pygame.key.get_pressed()
        """if keys[pygame.K_w]:
            self.left_paddle.update('up')
        elif keys[pygame.K_s]:
            self.left_paddle.update('down')"""
        if keys[pygame.K_UP]:
            self.right_paddle.update('up')
        elif keys[pygame.K_DOWN]:
            self.right_paddle.update('down')
        # self.right_paddle.y = self.ball.y

        # Update ball
        self.ball.update(self.left_paddle, self.right_paddle)
        if self.ball.x < 0:
            self.winner = 'right'
        elif self.ball.x > SCREEN_WIDTH:
            self.winner = 'left'
        # Check for winner
        if self.winner is not None:
            # self.display_winner(self.winner)
            if self.winner == 'left':
                self.left_score += 1
            else:
                self.right_score += 1
            self.ball.reset(None)

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
        game_info = GameInformation(
            self.left_paddle.score, self.right_paddle.score, self.left_score, self.right_score)

        return game_info

    """def display_winner(self, winner):
        winner_text = self.font.render(f"Player {winner} wins!", True, (255, 255, 255))
        screen.blit(winner_text, (
            SCREEN_WIDTH // 2 - winner_text.get_width() // 2, SCREEN_HEIGHT // 2 - winner_text.get_height() // 2))
        pygame.display.update()
        pygame.time.delay(3000)"""


class PongGame:
    def __init__(self):
        self.game = Game()
        self.ball = self.game.ball
        self.left_paddle = self.game.left_paddle
        self.right_paddle = self.game.right_paddle

    # @jit(forceobj=True)
    def test_ai(self, net):
        """
        Test the AI against a human player by passing a NEAT neural network
        """
        clock = pygame.time.Clock()
        run = True
        while run:
            clock.tick(60)
            game_info = self.game.run()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break

            output = net.activate((self.right_paddle.y, abs(
                self.right_paddle.x - self.ball.x), self.ball.y))
            decision = output.index(max(output))

            if decision == 1:  # AI moves up
                self.game.left_paddle.update('up')
            elif decision == 2:  # AI moves down
                self.game.left_paddle.update('down')

            # self.game.draw(draw_score=True)
            pygame.display.update()

    def train_ai(self, genome1, genome2, config):
        """
        Train the AI by passing two NEAT neural networks and the NEAt config object.
        These AI's will play against eachother to determine their fitness.
        """
        run = True
        start_time = time.time()

        net1 = neat.nn.FeedForwardNetwork.create(genome1, config)
        net2 = neat.nn.FeedForwardNetwork.create(genome2, config)
        self.genome1 = genome1
        self.genome2 = genome2

        max_hits = 50

        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True

            game_info = self.game.run()

            self.move_ai_paddles(net1, net2)

            pygame.display.update()

            duration = time.time() - start_time
            if game_info.left_score == 1 or game_info.right_score == 1 or game_info.left_hits >= max_hits:
                self.calculate_fitness(game_info, duration)
                break

        return False

    def move_ai_paddles(self, net1, net2):
        """
        Determine where to move the left and the right paddle based on the two
        neural networks that control them.
        """
        players = [(self.genome1, net1, self.left_paddle, True), (self.genome2, net2, self.right_paddle, False)]
        for (genome, net, paddle, left) in players:
            output = net.activate(
                (paddle.y, abs(paddle.x - self.ball.x), self.ball.y))
            decision = output.index(max(output))
            valid = True
            if decision == 0:  # Don't move
                genome.fitness -= 1  # we want to discourage this
            elif decision == 1:  # Move up
                if left is True:
                    valid = self.game.left_paddle.update('up')
                # else:
                    # valid = self.game.right_paddle.update('up')
            elif decision == 2:  # Move down
                if left is True:
                    valid = self.game.left_paddle.update('down')
                # else:
                    # valid = self.game.right_paddle.update('down')

            if not valid:  # If the movement makes the paddle go off the screen punish the AI
                genome.fitness -= 1

    def calculate_fitness(self, game_info, duration):
        self.genome1.fitness += game_info.left_hits + duration
        self.genome2.fitness += game_info.right_hits + duration


def eval_genomes(genomes, config):
    """
    Run each genome against eachother one time to determine the fitness.
    """
    width, height = 800, 600
    pygame.display.set_caption("Pong")

    for i, (genome_id1, genome1) in enumerate(genomes):
        print(round(i / len(genomes) * 100), end=" ")
        genome1.fitness = 0
        for genome_id2, genome2 in genomes[min(i + 1, len(genomes) - 1):]:
            genome2.fitness = 0 if genome2.fitness == None else genome2.fitness
            pong = PongGame()

            force_quit = pong.train_ai(genome1, genome2, config)
            if force_quit:
                quit()


def run_neat(config):
    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-49')
    # p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    winner = p.run(eval_genomes, 50)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)


def test_best_network(config):
    with open("best.pickle", "rb") as f:
        winner = pickle.load(f)
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)

    """width, height = 800, 600
    win = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Pong")"""
    pong = PongGame()
    pong.test_ai(winner_net)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    run_neat(config)
    test_best_network(config)
