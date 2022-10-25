from utils import *
import logging


#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('engine')


class MoveLog(NamedTuple):
    move: Move
    piece_moved: ChessPiece
    piece_eaten: ChessPiece
    en_passnst: bool
    castling: bool


"""
TODO 1. undo pawn promotion and add promotion bool to move log
"""

class ChessEngine:
    def __init__(self, arrangment=None) -> None:
        self.board: Board = Board()
        self.pieces_directions: dict[str, list[Pos]] = {
                    'n': [Pos(2, 1), Pos(2, -1), Pos(-1, -2), Pos(1, -2), Pos(-2, 1), Pos(-2, -1), Pos(-1, 2), Pos(1, 2)],
                    'k': [Pos(1, 0), Pos(-1, 0), Pos(0, 1), Pos(0, -1), Pos(1, 1), Pos(-1, 1), Pos(1, -1), Pos(-1, -1)],
                    'q': [Pos(1, 1), Pos(-1, 1), Pos(1, -1), Pos(-1, -1), Pos(1, 0), Pos(-1, 0), Pos(0, 1), Pos(0, -1)],
                    'b': [Pos(1, 1), Pos(-1, 1), Pos(1, -1), Pos(-1, -1)],
                    'r': [Pos(1, 0), Pos(-1, 0), Pos(0, 1), Pos(0, -1)],
                    'P': [Pos(-1, 0), Pos(-2, 0)],
                    'p': [Pos(1, 0), Pos(2, 0)],
                            }
        self.pieces_class: list[str, ChessPiece] = {
            'n': Knight,
            'k': King,
            'p': Pawn,
            'r': Rook,
            'q': Queen,
            'b': Bishop,
        }
        self.move: int = 0
        self.en_passant_squares: list[Pos] = []
        self.white_king = Pos(7, 4)
        self.black_king = Pos(0, 4)
        self.white_pinned_squares: list[Pos] = []
        self.black_pinned_squares: list[Pos] = []
        self.move_log: list[MoveLog] = []
        self.all_valid_moves = []
        self.white_attack_squares: list[Pos] = []
        self.black_attack_squares: list[Pos] = []
        self.init_new_baord(arrangment) 


    def init_new_baord(self, custom_arrangment: str) -> None:
        arrangment: str = custom_arrangment.strip() if custom_arrangment else self.board.arrangement
        x, y = 0, 0
        row = []
        for i in range(len(arrangment)):
            if i == len(arrangment) - 1:
                self.board.board.append(row)
            if arrangment[i] == '/':
                self.board.board.append(row)
                row = []
                x += 1
                y = 0
            elif arrangment[i].isdigit():
                for _ in range(int(arrangment[i])):
                    row.append(EmptyPiece(position=Pos(x, y)))
                    y += 1
            else:
                name = arrangment[i]
                color = Color.WHITE if arrangment[i].isupper() else Color.BLACK
                position = Pos(x, y)
                if name in 'pP':
                    directions = self.pieces_directions[name]
                else:
                    directions = self.pieces_directions[name.lower()]
                row.append(self.pieces_class[arrangment[i].lower()](
                                                    name=name, 
                                                    color=color,
                                                    position=position,
                                                    directions=directions
                                                    ))
                if name == 'k':
                    self.black_king = position
                elif name == 'K':
                    self.white_king = position
                y += 1

    def move_is_catling(self, move: Move) -> bool:
        piece_moved = self.board.get_piece_on_square(move.start)
        if piece_moved.name not in 'kK':
            return False
        start_sq = Pos(7, 4) if piece_moved.color is Color.WHITE else Pos(0, 4)
        end_sq = [Pos(7 ,6), Pos(7, 2)] if piece_moved.color is Color.WHITE else [Pos(0 ,6), Pos(0, 2)]
        return move.start == start_sq and move.end in end_sq

    def move_is_en_passant(self, move: Move) -> bool:
        piece_moved = self.board.get_piece_on_square(move.start)
        if piece_moved.name not in 'pP':
            return False
        offset = -1 if piece_moved.color is Color.WHITE else 1
        piece_eaten: Pawn = self.board.get_piece_on_square(Pos(move.end.x - offset, move.end.y))
        log.debug(f'piece eaten: {piece_eaten.name}')
        if isinstance(piece_eaten, Pawn) and piece_eaten.ep and piece_eaten.color is piece_moved.enemy_color:
            return True
        return False

    def move_is_promotion(self, move: Move) -> bool:
        piece = self.board.get_piece_on_square(move.start)
        promotion_square = 0 if piece.color is Color.WHITE else 7
        if isinstance(piece, Pawn) and move.end.x == promotion_square:
            return True
        return False

    def validate_and_make_move(self, move: Move) -> None:
        color_to_move = Color.WHITE if self.move % 2 == 0 else Color.BLACK
        piece_moved = self.board.get_piece_on_square(move.start)
        if piece_moved.color != color_to_move:
            pass
        if move not in self.all_valid_moves:
            return
        self.make_move(move)

    def generate_all_sudo_moves(self) -> list[Move]:
        self.all_valid_moves.clear()
        self.white_attack_squares.clear()
        self.black_attack_squares.clear()
        for x in self.board.board:
            for piece in x:
                if piece.color is not Color.EMPTY:
                    if isinstance(piece, Pawn) and self.move - piece.ep_move > 0\
                                               and piece.ep:
                        piece.ep = False
                    pinned_squares = self.white_pinned_squares if piece.color is Color.WHITE else self.black_pinned_squares
                    if isinstance(piece, King):
                        continue
                    ally_king = self.white_king if piece.color is Color.WHITE else self.black_king
                    ally_king_in_check = True if ally_king in self.board.checked_squares else False
                    self.all_valid_moves.extend(piece.generate_sudo_valid_moves(self.board, pinned_squares, ally_king_in_check))
                    if piece.color is Color.WHITE: self.white_attack_squares.extend([i.end for i in piece.valid_moves])
                    elif piece.color is Color.BLACK: self.black_attack_squares.extend([i.end for i in piece.valid_moves])
        kings: list[King] = [self.white_king, self.black_king]
        for king_pos in kings:
            king = self.board.get_piece_on_square(king_pos)
            if not isinstance(king, King):
                continue
            pinned_squares = self.white_pinned_squares if king.color is Color.WHITE else self.black_pinned_squares
            enemy_attack_squares = self.black_attack_squares if king.color is Color.WHITE else self.black_attack_squares
            king.generate_sudo_valid_moves(self.board, pinned_squares, enemy_attack_squares)
            self.all_valid_moves.extend(king.valid_moves)
        return self.all_valid_moves

    def generate_all_valid_moves(self) -> list[Move]:
        self.check_for_check()
        self.all_valid_moves: list[Move] = self.generate_all_sudo_moves()
        return self.all_valid_moves

    def check_for_check(self) -> list[Pos]:
        self.white_pinned_squares.clear()
        self.black_pinned_squares.clear()
        self.board.checked_squares.clear()
        white_king: King = self.board.get_piece_on_square(self.white_king)
        black_king: King = self.board.get_piece_on_square(self.black_king)
        white_king.checked = False
        black_king.checked = False
        kings: list[King] = [white_king, black_king]
        linear_directions = [Pos(1, 1), Pos(-1, 1), Pos(1, -1), Pos(-1, -1), Pos(1, 0), Pos(-1, 0), Pos(0, 1), Pos(0, -1)]
        knigth_directions = [Pos(2, 1), Pos(2, -1), Pos(-1, -2), Pos(1, -2), Pos(-2, 1), Pos(-2, -1), Pos(-1, 2), Pos(1, 2)]
        for king in kings:
            for d in linear_directions:
                pinns: list[Pos] = []
                ally = False
                for n in range(1, 8):
                    end: Pos = king.adder(king.position, Pos(d.x * n, d.y * n))
                    if not (end.x in range(8) and end.y in range(8)):
                        continue
                    target = self.board.get_piece_on_square(end)
                    if isinstance(target, EmptyPiece):
                        pinns.append(end)
                    elif d in linear_directions[:4] and target.color is king.enemy_color:
                        if not target.name in 'bBqQ':
                            break
                        if not ally: king.checked = True
                        pinns.append(end)
                        if king.color is Color.WHITE: self.white_pinned_squares.extend(pinns)
                        elif king.color is Color.BLACK: self.black_pinned_squares.extend(pinns)
                        break
                    elif d in linear_directions[3:] and target.color is king.enemy_color:
                        if not target.name in 'rRqQ':
                            break
                        if not ally: king.checked = True
                        pinns.append(end)
                        if king.color is Color.WHITE: self.white_pinned_squares.extend(pinns)
                        elif king.color is Color.BLACK: self.black_pinned_squares.extend(pinns)
                        break
                    elif target.color is king.ally_color:
                        ally = True
                        pinns.clear()
                        pinns.append(end)
            for d in knigth_directions:
                    end: Pos = king.adder(king.position, d)
                    if not (end.x in range(8) and end.y in range(8)):
                        continue
                    target = self.board.get_piece_on_square(end)
                    if isinstance(target, Knight) and target.color is king.enemy_color:
                        if king.color is Color.WHITE: self.white_pinned_squares.append(end)
                        elif king.color is Color.BLACK: self.black_pinned_squares.append(end)
                        king.checked = True
            if king.checked: self.board.checked_squares.add(king.position)

    def make_move(self, move: Move) -> None:
        self.move += 1
        castling, en_passant, promotion = False, False, False
        piece_moved = self.board.get_piece_on_square(move.start)
        piece_eaten = self.board.get_piece_on_square(move.end)
        empty_piece = EmptyPiece(position=move.start)

        if self.move_is_catling(move): castling = True
        elif self.move_is_en_passant(move): en_passant = True
        elif self.move_is_promotion(move): promotion = True

        if isinstance(piece_moved, King):
            if piece_moved.color is Color.WHITE: self.white_king = move.end
            elif piece_moved.color is Color.BLACK: self.black_king = move.end

        if isinstance(piece_moved, Pawn) and piece_moved.position.x == piece_moved.start_square\
                                         and piece_eaten.position.x == piece_moved.ep_square\
                                         and not piece_moved.ep:
            piece_moved.ep = True
            piece_moved.ep_move = self.move

        if castling:
            self.castle(move)
        elif en_passant:
            log.debug(f'move is en passant')
            self.en_passant(move)
        elif promotion:
            name = 'Q' if piece_moved.color is Color.WHITE else 'q'
            queen = Queen(
                name=name,
                color=piece_moved.color,
                position=move.start,
                directions=self.pieces_directions['q']
                )
            piece_moved = queen

        self.board.move(move, piece_moved, empty_piece)
        piece_moved.position = move.end

        self.move_log.append(MoveLog(move, piece_moved, piece_eaten, en_passnst=en_passant, castling=castling))
        self.generate_all_valid_moves()
        log.debug(f'{self.move_log[-2:]}')

    def castle(self, move: Move):
        short = False
        if move.end.y == 6:
            short = True
        y = 7 if short else 0
        king: King = self.board.get_piece_on_square(move.start)
        rook: Rook = self.board.get_piece_on_square(Pos(move.start.x, y))
        rook_end_pos = Pos(king.position.x, king.position.y - 1) if short else Pos(king.position.x, king.position.y + 1)
        empty_piece_king = EmptyPiece(position=move.start)
        empty_piece_rook = EmptyPiece(position=rook.position)
        self.board.move(move, king, empty_piece_king)
        self.board.move(Move(rook.position, rook_end_pos), rook, empty_piece_rook)
        self.move_log.append(MoveLog(Move(rook.position, rook_end_pos), rook, empty_piece_rook, False, False))
        king.castling = False
        rook.castling = False
        king.position = move.end
        rook.position = rook_end_pos

    def en_passant(self, move: Move):
        piece_moved: Pawn = self.board.get_piece_on_square(move.start)
        offset = -1 if piece_moved.color is Color.WHITE else 1
        piece_eaten: Pawn = self.board.get_piece_on_square(Pos(move.end.x - offset, move.end.y))
        log.debug(f'PIECE EATEN {piece_eaten.name}, {piece_eaten.ep}, {piece_eaten.position}')
        empty_piece = EmptyPiece(position=piece_eaten.position)
        log.debug(f'EMPTY EATEN {empty_piece.name}, {piece_eaten.ep}, {piece_eaten.position}')
        self.move_log.append(MoveLog(Move(piece_eaten.position, piece_eaten.position), piece_eaten, empty_piece, False, False))
        self.board.move(Move(piece_eaten.position, piece_eaten.position), piece_eaten, empty_piece)

    def promote(self, move: Move) -> None:
        piece = self.board.get_piece_on_square(move.start)
        log.debug(f'------> PROMOTING {piece.color} PAWN')
        name = 'Q' if piece.color is Color.WHITE else 'q'
        queen = Queen(
            name=name,
            color=piece.color,
            position=move.start,
            directions=self.pieces_directions['q']
            )
        self.board.board[move.end.x][move.end.y] = queen
        self.board.move(Move(move.end, move.end), queen, piece)

    def undo_move(self):
        if not self.move_log:
            log.debug(f'No Moves')
            return
        self.move -= 1
        last_move: MoveLog = self.move_log.pop()
        move = last_move.move
        piece_moved = last_move.piece_moved
        piece_eaten = last_move.piece_eaten
        piece_moved.position = move.start
        piece_eaten.position = move.end
        if last_move.en_passnst or last_move.castling:
            self.board.move(move, piece_eaten, piece_moved)
            last_move = self.move_log.pop()
            move = last_move.move
            piece_moved = last_move.piece_moved
            piece_eaten = last_move.piece_eaten
            piece_moved.position = move.start
            piece_eaten.position = move.end
            self.board.move(move, piece_eaten, piece_moved)
            return
        log.debug(f'{piece_moved.name}: {piece_moved.position}')
        self.board.move(move, piece_eaten, piece_moved)
        self.generate_all_valid_moves()



if __name__ == '__main__':
    custom_arrangement = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R'
    engine = ChessEngine(custom_arrangement)
    engine.board.print_board()
    start = time.time()
    def test():
        g = 0
        cnt = 0
        global start
        print(start)
        while g <= 10:
            engine.generate_all_valid_moves()
            cnt += 1
            if time.time() - start >= 1:
                g += 1
                print(cnt)
                cnt = 0
                start = time.time()
    test()
