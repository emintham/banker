from unittest import TestCase

from banker.banker import Banker, InvalidMove, Bankrupt


class BankerTests(TestCase):
    def setUp(self):
        self.banker = Banker()

    def test_init(self):
        self.assertEquals(self.banker.board,
                          [None, None, None, None, None,
                           None, None, None, None, None,
                           None, None, 1, None, None,
                           None, None, None, None, None,
                           None, None, None, None, None])

        banker = Banker([1 for _ in range(25)])
        self.assertEquals(banker.board, [1 for _ in range(25)])

    def test_get_tile(self):
        banker = Banker(range(25))

        self.assertEquals(banker.get_tile(1, 1), 6)
        self.assertEquals(banker.get_tile(3, 2), 13)
        self.assertEquals(banker.get_tile(4, 4), 24)

    def test_set_tile(self):
        self.banker.set_tile(1, 1, 1)
        self.banker.set_tile(3, 4, 5)
        self.banker.set_tile(2, 0, 2)

        self.assertEquals(self.banker.get_tile(1, 1), 1)
        self.assertEquals(self.banker.get_tile(3, 4), 5)
        self.assertEquals(self.banker.get_tile(2, 0), 2)
        self.assertEquals(self.banker.get_tile(2, 2), 1)
        self.assertEquals(self.banker.get_tile(0, 3), None)

    def test_get_competitor_costs(self):
        self.assertEquals(self.banker.get_competitor_costs(), 0)

        banker = Banker([-1, 2, -5, None, 10])
        self.assertEquals(banker.get_competitor_costs(), -6)

    def test_non_straight_moves_raises_error(self):
        bad_moves = [
            ((2, 2), (1, 1), 1),
            ((2, 2), (4, 4), 1),
            ((2, 2), (3, 4), 1)
        ]

        for move in bad_moves:
            with self.assertRaises(InvalidMove):
                self.banker.move(*move)

    def test_competitors_cannot_be_moved(self):
        self.banker.set_tile(2, 2, -1)

        with self.assertRaises(InvalidMove):
            self.banker.move((2, 2), (2, 1), 1)

    def test_staying_still_raises_error(self):
        with self.assertRaises(InvalidMove):
            self.banker.move((2, 2), (2, 2), 1)

    def test_jumping_to_empty_tile_raises_error(self):
        with self.assertRaises(InvalidMove):
            self.banker.move((2, 2), (2, 0), 1)

    def test_jumping_to_tile_with_different_value_raises_error(self):
        self.banker.set_tile(2, 0, 2)

        with self.assertRaises(InvalidMove):
            self.banker.move((2, 2), (2, 0), 1)

    def test_move_one_step(self):
        # combination move
        self.banker.set_tile(3, 2, 1)

        banker = self.banker.move((2, 2), (3, 2), 2)

        self.assertEquals(banker.board,
                          [None, None, None, None, None,
                           None, None, None, None, None,
                           None, None, 2, 2, None,
                           None, None, None, None, None,
                           None, None, None, None, None])
        self.assertEquals(banker.cash, 12)
        self.assertEquals(banker.moves, 1)
        self.assertEquals(banker.score, 12)

        # non-combination move
        self.banker = Banker()

        banker = self.banker.move((2, 2), (1, 2), 2)

        self.assertEquals(banker.board,
                          [None, None, None, None, None,
                           None, None, None, None, None,
                           None, 1, 2, None, None,
                           None, None, None, None, None,
                           None, None, None, None, None])
        self.assertEquals(banker.cash, 9)
        self.assertEquals(banker.moves, 1)
        self.assertEquals(banker.score, 10)

    def test_jump(self):
        self.banker.set_tile(4, 2, 1)
        self.banker.set_tile(3, 2, 5)

        banker = self.banker.move((2, 2), (4, 2), 2)

        self.assertEquals(banker.board,
                          [None, None, None, None, None,
                           None, None, None, None, None,
                           None, None, None, 5, 2,
                           None, None, None, None, None,
                           None, None, None, None, None])
        self.assertEquals(banker.cash, 12)
        self.assertEquals(banker.moves, 1)
        self.assertEquals(banker.score, 12)

        banker.set_tile(1, 2, 2)
        banker.set_tile(2, 2, -1)
        banker.set_tile(1, 1, -2)

        banker2 = banker.move((4, 2), (1, 2), 2)

        self.assertEquals(banker2.board,
                          [None, None, None, None, None,
                           None, -2, None, None, None,
                           None, 3, None, 5, None,
                           None, None, None, None, None,
                           None, None, None, None, None])
        # 12 +3 -2 (+3 from new, -2 from [1,1] competitor)
        # [2,2] competitor gone.
        self.assertEquals(banker2.cash, 13)
        self.assertEquals(banker2.moves, 2)
        self.assertEquals(banker2.score, 15)

    def test_bankrupt(self):
        self.banker.cash = 0

        with self.assertRaises(Bankrupt):
            self.banker.move((2, 2), (1, 2), 2)

    def test_own_tiles(self):
        self.banker.set_tile(4, 2, 1)
        self.banker.set_tile(3, 2, 5)

        expected = set([(2, 2), (4, 2), (3, 2)])
        actual = set(self.banker.own_tiles)

        self.assertEquals(expected, actual)

    def test_get_moveset(self):
        expected = set([
            ((2, 2), (0, 2)),
            ((2, 2), (1, 2)),
            ((2, 2), (3, 2)),
            ((2, 2), (4, 2)),
            ((2, 2), (2, 0)),
            ((2, 2), (2, 1)),
            ((2, 2), (2, 3)),
            ((2, 2), (2, 4)),
        ])
        actual = self.banker.get_moveset()

        self.assertEquals(expected, actual)

        self.banker.set_tile(0, 0, 1)

        extra = set([
            ((0, 0), (1, 0)),
            ((0, 0), (2, 0)),
            ((0, 0), (3, 0)),
            ((0, 0), (4, 0)),
            ((0, 0), (0, 1)),
            ((0, 0), (0, 2)),
            ((0, 0), (0, 3)),
            ((0, 0), (0, 4)),
        ])
        expected = expected.union(extra)
        actual = self.banker.get_moveset()

        self.assertEquals(expected, actual)

    def test_heuristic_combos_are_good(self):
        """
        1 combo available is better than no combos available, ceteris paribus.
        """
        self.banker.set_tile(2, 2, None)
        self.banker.set_tile(1, 2, 2)
        self.banker.set_tile(3, 2, 1)

        no_combo = self.banker.heuristic_score()

        self.banker.set_tile(3, 2, 2)

        combo = self.banker.heuristic_score()

        self.assertGreater(combo, no_combo)

    def test_heuristic_higher_score_is_better(self):
        """
        Higher score is better, ceteris paribus.
        """
        low_score = self.banker.heuristic_score()
        self.banker.score += 1
        high_score = self.banker.heuristic_score()

        self.assertGreater(high_score, low_score)

    def test_heuristic_competitors(self):
        """
        No competitors > central competitors w/ low numbers > ...
         central_competitors w/ high numbers > edge competitors > ...
         corner competitors,
        ceteris paribus.
        """
        no_competitors = self.banker.heuristic_score()

        self.banker.set_tile(3, 2, 0)
        central_competitor = self.banker.heuristic_score()

        self.banker.set_tile(3, 2, -1)
        central_competitor_high = self.banker.heuristic_score()

        self.banker.set_tile(3, 2, None)
        self.banker.set_tile(0, 1, 0)
        edge_competitor = self.banker.heuristic_score()

        self.banker.set_tile(0, 1, None)
        self.banker.set_tile(0, 0, 0)
        corner_competitor = self.banker.heuristic_score()

        self.assertGreater(no_competitors, central_competitor)
        self.assertGreater(central_competitor, central_competitor_high)
        self.assertGreater(central_competitor_high, edge_competitor)
        self.assertGreater(edge_competitor, corner_competitor)
