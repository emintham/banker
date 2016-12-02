from itertools import islice
import random


CORNER_COMPETITOR_PENALTY = 30
EDGE_COMPETITOR_PENALTY = 10


class InvalidMove(Exception):
    pass


class Bankrupt(Exception):
    pass


def grouper(n, iterable):
    it = iter(iterable)

    while True:
        chunk = tuple(islice(it, n))
        if not chunk:
            return

        yield chunk


class Banker(object):
    def __init__(self, board=None, next_tile=None, moves=0, cash=10, score=10):
        self.board = [None for _ in range(25)] if not board else board[:]
        if not board:
            self.board[12] = 1

        self.moves = moves
        self.cash = cash
        self.score = score

    @classmethod
    def copy(cls, other, **kwargs):
        fields = ['board', 'moves', 'cash', 'score']
        data = kwargs.copy()

        for field in fields:
            if field not in data:
                data[field] = getattr(other, field)

        return cls(**data)

    def get_random_tile(self):
        return random.choice([1, 2, 0, -1, -2])

    @property
    def next_tiles(self):
        if self.score <= 300:
            return [2, 1, 0, -1, -2]
        else:
            return [2, 1, 0, -1, -2, -3]

    @property
    def tile_probabilities(self):
        if self.score <= 300:
            return [0.35, 0.35, 0.2, 0.09, 0.01]
        else:
            return [0.23, 0.27, 0.23, 0.09, 0.09, 0.09]

    def get_tile(self, x, y):
        return self.board[x + 5*y]

    def set_tile(self, x, y, value):
        self.board[x + 5*y] = value

    def _index_to_coord(self, index):
        return (index % 5, index/5)

    def get_competitor_costs(self):
        return sum(i for i in self.board if i and i < 0)

    def __str__(self):
        return '\n'.join(', '.join([str(i) for i in chunk])
                         for chunk in grouper(5, self.board))

    @property
    def corner_indices(self):
        return [0, 4, 20, 24]

    @property
    def edge_indices(self):
        return [1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23]

    @property
    def central_indices(self):
        return [6, 7, 8, 11, 12, 13, 16, 17, 18]

    @property
    def own_tiles(self):
        return (self._index_to_coord(index)
                for index, item in enumerate(self.board)
                if item and item > 0)

    def get_moveset(self):
        """Returns all possible moves (x1, y1) -> [(x2, y2)]."""
        all_possible_moves = set()

        for source in self.own_tiles:
            x, y = source

            horizontal_moves = [(i, y) for i in range(5) if i != x]
            vertical_moves = [(x, i) for i in range(5) if i != y]

            for dest in set(horizontal_moves + vertical_moves):
                all_possible_moves.add((source, dest))

        return all_possible_moves

    @property
    def terminal(self):
        for source in self.own_tiles:
            x, y = source
            val = self.get_tile(x, y)

            for i in range(5):
                if i == x:
                    continue

                walk = abs(i-x) == 1 and self.get_tile(i, y) is None
                jump = abs(i-x) != 1 and self.get_tile(i, y) == val

                if walk or jump:
                    return False

            for i in range(5):
                if i == y:
                    continue

                walk = abs(i-y) == 1 and self.get_tile(x, i) is None
                jump = abs(i-y) != 1 and self.get_tile(x, i) == val

                if walk or jump:
                    return False

        return True

    def heuristic_score(self):
        available_combos = 0

        for move in self.get_moveset():
            source, dest = move

            try:
                new_node = self.move(source, dest, None)
            except (Bankrupt, InvalidMove):
                continue

            if new_node.score > self.score:
                available_combos += 1

        corner_penalty = sum((CORNER_COMPETITOR_PENALTY
                              for i in self.corner_indices
                              if self.board[i] is not None and self.board[i] <= 0))
        edge_penalty = sum((EDGE_COMPETITOR_PENALTY
                            for i in self.edge_indices
                            if self.board[i] is not None and self.board[i] <= 0))
        center_penalty = sum((-(self.board[i] - 1)
                              for i in self.central_indices
                              if self.board[i] is not None and self.board[i] <= 0))
        penalty = corner_penalty + edge_penalty + center_penalty

        # add one to available_combos so that having no combo does not get 0
        # from the first product
        return self.score * (available_combos + 1) - penalty

    def best_move(self, next_tile, depth=8):
        """
        Given the next_tile, returns the best move and its heuristic score.
        """
        if depth == 0 or self.terminal:
            return (None, None, self.heuristic_score())

        scores = []

        for move in self.get_moveset():
            source, dest = move
            try:
                new_node = self.move(source, dest, next_tile)
            except (InvalidMove, Bankrupt):
                continue

            scores.append(
                (source, dest, Banker.emm(new_node, depth=depth-1))
            )

        if scores:
            return max(scores, key=lambda x: x[2])
        else:
            return (None, None, -1)

    @classmethod
    def emm(cls, node, depth=8):
        if depth == 0 or node.terminal:
            return node.heuristic_score()

        tile_with_probabilities = zip(node.next_tiles, node.tile_probabilities)

        max_scores = []
        for next_tile, probability in tile_with_probabilities:
            source, dest, score = node.best_move(next_tile, depth-1)

            max_scores.append(int(probability * score))

        return sum(max_scores)

    def move(self, source, dest, next_tile):
        x1, y1 = source
        x2, y2 = dest

        source_tile = self.get_tile(x1, y1)
        dest_tile = self.get_tile(x2, y2)

        horizontal_move = y1 == y2
        vertical_move = x1 == x2

        if horizontal_move:
            start = min(x1, x2)
            dist = max(x1, x2) - start
        else:
            start = min(y1, y2)
            dist = max(y1, y2) - start

        move_competitor = source_tile <= 0
        invalid_dest = not horizontal_move and not vertical_move
        jump_to_empty = dist > 1 and dest_tile is None
        invalid_target = source_tile != dest_tile and dest_tile is not None
        no_move = x1 == x2 and y1 == y2

        if any([move_competitor, invalid_dest, jump_to_empty, invalid_target, no_move]):
            raise InvalidMove

        if source_tile != dest_tile:
            new_dest = source_tile
            cash_delta = -1
            score_delta = 0
        else:
            new_dest = source_tile + 1
            cash_delta = new_dest
            score_delta = new_dest

        if dist == 1:
            new_source = next_tile
        else:
            new_source = None

        next_state = Banker(board=self.board,
                            moves=self.moves+1,
                            cash=self.cash,
                            score=self.score)

        if horizontal_move:
            for i in range(1, dist):
                if next_state.get_tile(start + i, y1) <= 0:
                    next_state.set_tile(start + i, y1, None)
        else:
            for i in range(1, dist):
                if next_state.get_tile(x1, start + i) < 0:
                    next_state.set_tile(x1, start + i, None)

        next_state.set_tile(x1, y1, new_source)
        next_state.set_tile(x2, y2, new_dest)

        # cost of new tile and competitor costs
        next_state.cash += next_state.get_competitor_costs() + cash_delta
        next_state.score += score_delta

        if next_state.cash < 0:
            raise Bankrupt

        return next_state


if __name__ == '__main__':
    b = Banker()

    while True:
        next_tile = int(raw_input())
        s, d, score = b.best_move(next_tile, 5)
        print s, d, score
        b = b.move(s, d, next_tile)
        print b
