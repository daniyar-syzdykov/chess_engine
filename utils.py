import time
from enum import Enum, auto
from typing import NamedTuple, Type
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('utils')




class Color(Enum):
    EMPTY = auto()
    WHITE = auto()
    BLACK = auto()

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return str(self.name)


class Pos(NamedTuple):
    x: int
    y: int

    def __str__(self) -> str:
        return f'({self.x}, {self.y})'

    def __repr__(self) -> str:
        return f'({self.x}, {self.y})'


class Move(NamedTuple):
    start: Pos 
    end: Pos

    def __str__(self) -> str:
        return f'({self.start}, {self.end})'

    def __repr__(self) -> str:
        return f'({self.start}, {self.end})'

class Board:
    def get_piece_on_square(self, square: Pos):...

class ChessPiece:
    def __init__(self, *, name: str, color: Color, position: Pos, directions: list[Pos]):
        self.name: str = name
        self.color:Color = color
        self.position: Pos = position
        self.valid_moves: list[Move] = []
        self.pinned: bool = False
        self.enemy_color = Color.BLACK if color is Color.WHITE else Color.WHITE
        self.ally_color = Color.WHITE if color is Color.WHITE else Color.BLACK
        self.directions: list[Pos] = directions

    def adder(self, piece: Pos, direction: Pos) -> Pos:
        return Pos(piece.x + direction.x, piece.y + direction.y)

    def generate_sudo_valid_moves(self, board: Board) -> list[Move]:
        pass
        
    def __str__(self):
        return f'{self.name}, {self.position}'

    def __repr__(self):
        return f'{self.name}'
    
    def __eq__(self, __o: object) -> bool:
        return type(self) == __o


class EmptyPiece(ChessPiece):
    def __init__(self, *, position: Pos):
        super().__init__(name='-', color=Color.EMPTY, position=position, directions=[])


class SlidingPiece(ChessPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)

    def generate_sudo_valid_moves(self, board: Board, pinned_squares: list[Pos], ally_king_in_check: bool) -> list[Move]:
        self.valid_moves.clear()
        if self.position in pinned_squares:
            return self.valid_moves
        for direction in self.directions:
            for n in range(1, 8):
                end: Pos = self.adder(self.position, Pos(n * direction.x, n * direction.y))
                if not (end.x in range(8) and end.y in range(8)):
                    break
                target: ChessPiece = board.get_piece_on_square(end)
                if target.color == self.ally_color:
                    break
                elif target.color == self.enemy_color:
                    self.valid_moves.append(Move(self.position, end)) 
                    break
                self.valid_moves.append(Move(self.position, end))
        if ally_king_in_check:
            self.valid_moves = [move for move in self.valid_moves if move.end in pinned_squares]
        return self.valid_moves


class NotSlidingPiece(ChessPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)

    def generate_sudo_valid_moves(self, board: Board, pinned_squares: list[Pos], ally_king_in_check: bool) -> list[Move]:
        self.valid_moves.clear()
        for d in self.directions:
            end = self.adder(self.position, d)
            if not (end.x in range(8) and end.y in range(8)):
                continue
            target: ChessPiece = board.get_piece_on_square(end)
            if target.color == self.ally_color:
                continue
            elif target.color == self.enemy_color:
                self.valid_moves.append(Move(self.position, end)) 
                continue
            self.valid_moves.append(Move(self.position, end))
        if ally_king_in_check:
            self.valid_moves = [move for move in self.valid_moves if move.end in pinned_squares]
        return self.valid_moves


class Rook(SlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)
        self.castling = True
    
    def __str__(self):
        return f'({self.name}, {self.position}, {self.castling})'


class Queen(SlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)


class Bishop(SlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)


class Knight(NotSlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)


class Pawn(NotSlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)
        self.start_square: int = 6 if self.color == Color.WHITE else 1
        self.ep_square: int = 4 if self.color == Color.WHITE else 3
        self.ep: bool = False
        self.eat_directions: list[Pos] = [Pos(-1, -1), Pos(-1, 1)] if self.color == Color.WHITE else [Pos(1, -1), Pos(1, 1)]
        self.ep_directions: list[Pos] = [Pos(0, 1), Pos(0, -1)]
        self.ep_move: int = float('-inf')

    def generate_sudo_valid_moves(self, board: Board, pinned_squares: list[Pos], ally_king_in_check: bool) -> list[Move]:
        self.valid_moves.clear()
        self.valid_moves.extend(self.generate_forword_moves(board))
        self.valid_moves.extend(self.generage_eat_moves(board))
        self.valid_moves.extend(self.generate_en_passant_moves(board))
        if ally_king_in_check:
            self.valid_moves = [move for move in self.valid_moves if move.end in pinned_squares]
        return self.valid_moves

    def generate_forword_moves(self, board: Board):
        valid_moves: list[Move] = []
        for d in self.directions:
            if self.position.x != self.start_square and d == self.directions[1]:
                continue
            end = self.adder(self.position, d)
            if not (end.x in range(8) and end.y in range(8)):
                continue
            target: ChessPiece = board.get_piece_on_square(end)
            if target.color is Color.EMPTY:
                valid_moves.append(Move(self.position, end))
            elif target.color is self.ally_color:
                break
        return valid_moves

    def generage_eat_moves(self, board: Board):
        valid_moves: list[Move] = []
        for d in self.eat_directions:
            end = self.adder(self.position, d)
            if not (end.x in range(8) and end.y in range(8)):
                continue
            target: ChessPiece = board.get_piece_on_square(end)
            if target.color is self.enemy_color:
                valid_moves.append(Move(self.position, end))
        return valid_moves

    def generate_en_passant_moves(self, board: Board):
        valid_moves: list[Move] = []
        offset: int = -1 if self.color is Color.WHITE else 1
        for d in self.ep_directions:
            end = self.adder(self.position, d)
            if not (end.x in range(8) and end.y in range(8)):
                continue
            target: Pawn = board.get_piece_on_square(end)
            if isinstance(target, Pawn) and target.color is self.enemy_color and target.ep and target.position.x == target.ep_square:
                valid_moves.append(Move(self.position, Pos(end.x + offset, end.y)))
        return valid_moves

    def __str__(self):
        return f'{self.position}, {self.ep_move}, {self.ep}'


class King(NotSlidingPiece):
    def __init__(self, *, name, color, position, directions):
        super().__init__(name=name, color=color, position=position, directions=directions)
        self.long_side = Pos(self.position.x, 2)
        self.short_side = Pos(self.position.x, 6)
        self.checked = False
        self.start_position = Pos(7, 4) if self.color is Color.WHITE else Pos(0, 4)
        self.castling = True
    
    def generate_sudo_valid_moves(self, board: Board, pinned_squares: list[Pos], enemy_attack_squares: list[Pos]) -> list[Move]:
        self.valid_moves.clear()
        for d in self.directions:
            end = self.adder(self.position, d)
            skip = False
            for sd in self.directions:
                end2 = self.adder(end, sd)
                if not (end2.x in range(8) and end2.y in range(8)):
                    continue
                target2 = board.get_piece_on_square(end2)
                if isinstance(target2, King) and target2.color is self.enemy_color:
                    skip = True
            if not (end.x in range(8) and end.y in range(8)) or skip:
                continue
            target: ChessPiece = board.get_piece_on_square(end)
            if target.color == self.ally_color:
                continue
            elif target.color == self.enemy_color and end not in pinned_squares:
                self.valid_moves.append(Move(self.position, end)) 
                continue
            if end not in pinned_squares:
                self.valid_moves.append(Move(self.position, end))
        if self.position != self.start_position or not self.castling or self.checked:
            return self.valid_moves
        short_side_rook: Rook = board.get_piece_on_square(Pos(self.position.x, 7))
        long_side_rook: Rook = board.get_piece_on_square(Pos(self.position.x, 0))
        short_side = board.get_piece_on_square(self.short_side)
        long_side = board.get_piece_on_square(self.long_side)
        if (isinstance(short_side_rook, Rook)\
                        and short_side_rook.castling\
                        and short_side_rook.color == self.color\
                        and isinstance(short_side, EmptyPiece)\
                        and short_side.position not in enemy_attack_squares
            ):
            self.valid_moves.append(Move(self.position, self.short_side))
        if (isinstance(long_side_rook, Rook)\
                        and long_side_rook.castling\
                        and long_side_rook.color == self.color\
                        and isinstance(long_side, EmptyPiece)\
                        and long_side.position not in enemy_attack_squares
            ):
            self.valid_moves.append(Move(self.position, self.long_side))
        return self.valid_moves

    def in_check(self, board: Board) -> bool:
        pass

class Board:
    def __init__(self):
        self.board: list[list[ChessPiece]] = []
        self.arrangement = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        self.checked_squares: set[Pos] = set()
        self.pinned_squares: list[Pos] = []

    def get_piece_on_square(self, position: Pos) -> ChessPiece:
        return self.board[position.x][position.y]

    def move(self, move: Move, piece_moved: ChessPiece, empty_piece: ChessPiece):
        self.board[move.end.x][move.end.y] = piece_moved
        self.board[move.start.x][move.start.y] = empty_piece

    def print_board(self):
        for x in range(8):
            row = []
            for y in range(8):
                row.append(self.board[x][y].__repr__())
            print(row)

    def __str__(self) -> str:
        return self.board

    def __repr__(self) -> str:
        return self.board

    def __eq__(self, __o: object) -> bool:
        return type(self) == __o

if __name__ == '__main__':
    piece = King(name='K', color=Color.WHITE, position=Pos(7,4), directions=[])
    board = Board()
    print(piece.directions)
