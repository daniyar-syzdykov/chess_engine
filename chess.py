import time
import sys
import os
import pygame
import random
from utils import Board, ChessPiece, Pawn, Pos, Move, Color
from chess_engine import ChessEngine
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('main')

pygame.init()


SIZE = WIDTH, HEIGHT = 600, 600
SCREEN = pygame.display.set_mode(SIZE)
PIECES = {'n': 'bN', 'p': 'bp', 'r': 'bR', 'b': 'bB', 'q': 'bQ', 'k': 'bK', 'N': 'wN', 'P': 'wp', 'R': 'wR', 'B': 'wB', 'Q': 'wQ', 'K': 'wK', 'highlight': 'highlight'}
ACTIVE = True
CLOCK = pygame.time.Clock()
BOARD_WHITE = (238, 238, 210)
RANDOM_COLOR = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
BOARD_BLACK = (118, 150, 86)
HIGHLIGHT_COLOR = pygame.Color(255, 0, 0)
SQUARE_SIZE = WIDTH // 8
FPS = 10


def load_images():
    images = {}
    for img in PIECES:
        images[img] = pygame.transform.scale(pygame.image.load(os.path.join('images', f'{PIECES[img]}.png')),(SQUARE_SIZE, SQUARE_SIZE))
    return images

def draw_board():
    image = pygame.transform.scale(pygame.image.load(os.path.join('images', 'board.png')), (WIDTH, HEIGHT))
    SCREEN.blit(image, (0, 0))

def draw_images(images, board: Board):
    for x in range(8):
        for y in range(8):
            piece: ChessPiece = board.get_piece_on_square(Pos(x, y))
            if piece.color != Color.EMPTY:
                
                SCREEN.blit(images[piece.name], (SQUARE_SIZE * y, SQUARE_SIZE * x))

def highligh_squares(squares_to_highlight, images):
    if not squares_to_highlight:
        return False
    squares_to_highlight = [i[1] for i in squares_to_highlight]
    for x in range(8):
        for y in range(8):
            if (x, y) in squares_to_highlight:
                SCREEN.blit(images['highlight'], (SQUARE_SIZE * y, SQUARE_SIZE * x))

def draw_game(images, board, valid_moves):
    draw_board()
    draw_images(images, board)
    highligh_squares(valid_moves, images)

def main(arrangment = None):
    engine = ChessEngine(arrangment)
    engine.generate_all_valid_moves()
    move = []
    squares_to_highlight = []
    images = load_images()
    while ACTIVE:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                square_clicked: Pos = (mouse_pos[1] // (HEIGHT // 8), mouse_pos[0] // (WIDTH // 8))
                move.append(square_clicked)
                if len(move) == 1:
                    piece: ChessPiece = engine.board.get_piece_on_square(Pos(move[0][0], move[0][1]))
                    if piece.color is not Color.EMPTY:
                        squares_to_highlight = piece.valid_moves
                elif len(move) == 2:
                    if move[0] == move[1]:
                        move = []
                        squares_to_highlight = []
                    else:
                        squares_to_highlight = []
                        engine.validate_and_make_move(Move(Pos(move[0][0], move[0][1]), Pos(move[1][0], move[1][1])))
                        move = []
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    move = []
                    squares_to_highlight = []
                    engine.undo_move()
        draw_game(images, engine.board, squares_to_highlight)
        CLOCK.tick(FPS)
        pygame.display.flip()


if __name__ == '__main__':
    main()
