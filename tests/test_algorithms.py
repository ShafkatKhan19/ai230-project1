"""Correctness tests. Run with:  python -m pytest -q

Every sort is checked against Python's built-in sorted() and every search
against a brute-force reference, on hand-picked edge cases and on many
random lists.
"""

import random

import pytest

from complexity_lab.searching import (SEARCHES, binary_search, interpolation_search,
                                      jump_search, linear_search)
from complexity_lab.sorting import ALL_SORTS, COMPARISON_SORTS, INTEGER_SORTS

EDGE_CASES = [
    [],
    [7],
    [2, 1],
    [1, 2],
    [5, 5, 5, 5],
    [3, -1, 0, -7, 2, -1],
    list(range(50)),
    list(range(50, 0, -1)),
    [1, 0] * 25,
]
HUGE_RANGE = [10**9, 0, 10**9 - 1, 1]


@pytest.mark.parametrize("name", ALL_SORTS)
@pytest.mark.parametrize("case", EDGE_CASES, ids=lambda c: f"len{len(c)}")
def test_sort_edge_cases(name, case):
    assert ALL_SORTS[name](case) == sorted(case)


@pytest.mark.parametrize("name", [n for n in ALL_SORTS if n != "counting"])
def test_sort_huge_value_range(name):
    assert ALL_SORTS[name](HUGE_RANGE) == sorted(HUGE_RANGE)


def test_counting_sort_refuses_huge_range():
    # k = 10^9 counters would need gigabytes of memory for 4 numbers.
    with pytest.raises(ValueError):
        INTEGER_SORTS["counting"](HUGE_RANGE)


@pytest.mark.parametrize("name", ALL_SORTS)
def test_sort_random_lists(name):
    rng = random.Random(230)
    for _ in range(200):
        n = rng.randint(0, 120)
        case = [rng.randint(-1000, 1000) for _ in range(n)]
        assert ALL_SORTS[name](case) == sorted(case)


@pytest.mark.parametrize("name", ALL_SORTS)
def test_sort_does_not_modify_input(name):
    case = [3, 1, 2]
    ALL_SORTS[name](case)
    assert case == [3, 1, 2]


@pytest.mark.parametrize("name", COMPARISON_SORTS)
def test_comparison_sorts_work_on_strings_and_floats(name):
    words = ["pear", "apple", "fig", "apple", "kiwi"]
    floats = [2.5, -0.5, 1e-9, 3.14, -2.0]
    assert COMPARISON_SORTS[name](words) == sorted(words)
    assert COMPARISON_SORTS[name](floats) == sorted(floats)


@pytest.mark.parametrize("name", ["insertion", "merge"])
def test_stable_sorts_keep_equal_keys_in_order(name):
    # Records compare only by key; the tag shows the original order.
    class Rec:
        def __init__(self, key, tag):
            self.key, self.tag = key, tag

        def __lt__(self, other):
            return self.key < other.key

    recs = [Rec(1, "a"), Rec(0, "b"), Rec(1, "c"), Rec(0, "d")]
    out = COMPARISON_SORTS[name](recs)
    assert [r.tag for r in out] == ["b", "d", "a", "c"]


@pytest.mark.parametrize("name", INTEGER_SORTS)
def test_integer_sorts_large_and_negative_values(name):
    rng = random.Random(1)
    case = [rng.randint(-10**6, 10**6) for _ in range(500)]
    assert INTEGER_SORTS[name](case) == sorted(case)


def test_binary_search_returns_leftmost_duplicate():
    assert binary_search([1, 2, 2, 2, 3], 2) == 1


@pytest.mark.parametrize("name", SEARCHES)
def test_search_found_and_missing(name):
    search = SEARCHES[name]
    rng = random.Random(7)
    for _ in range(300):
        items = sorted(rng.sample(range(-500, 500), rng.randint(0, 60)))
        target = rng.randint(-520, 520)
        expected = items.index(target) if target in items else -1
        assert search(items, target) == expected


@pytest.mark.parametrize("name", SEARCHES)
def test_search_empty_and_boundaries(name):
    search = SEARCHES[name]
    assert search([], 3) == -1
    assert search([4], 4) == 0
    items = [1, 3, 5, 7]
    assert search(items, 1) == 0
    assert search(items, 7) == 3
    assert search(items, 0) == -1
    assert search(items, 8) == -1


def test_linear_search_works_on_unsorted_input():
    assert linear_search([9, 4, 7, 4], 4) == 1


def test_jump_search_returns_leftmost_duplicate():
    assert jump_search([1, 2, 2, 2, 2, 2, 3, 4, 5], 2) == 1


def test_interpolation_search_with_duplicates_returns_a_match():
    items = [1, 2, 2, 2, 2, 2, 3, 4, 5]
    assert items[interpolation_search(items, 2)] == 2
    assert interpolation_search([5, 5, 5], 5) == 0
    assert interpolation_search([5, 5, 5], 4) == -1


@pytest.mark.parametrize("name", SEARCHES)
def test_search_on_skewed_values(name):
    # Values far from evenly spread: the case where interpolation search guesses badly.
    items = [i ** 4 for i in range(300)] + [10**15]
    for target in [0, 1, 16, 81 ** 2, 299 ** 4, 10**15, 2, 10**15 - 1]:
        expected = items.index(target) if target in items else -1
        assert SEARCHES[name](items, target) == expected


@pytest.mark.parametrize("name", SEARCHES)
def test_search_every_element_of_a_list(name):
    for n in [1, 2, 3, 15, 16, 17, 100]:            # sizes around perfect squares matter for jump search
        items = list(range(0, 3 * n, 3))
        for i, x in enumerate(items):
            assert SEARCHES[name](items, x) == i
            assert SEARCHES[name](items, x + 1) == -1
