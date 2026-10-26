"""Extra random checks outside the pytest suite (about a minute).

    python tests/stress_check.py

Runs every sort on 3,000 random lists (sizes up to 1,000, value ranges from 1
to 10^6, with and without negative numbers) and every search on 20,000 random
queries, and prints the number of wrong answers.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from complexity_lab.searching import SEARCHES   # noqa: E402
from complexity_lab.sorting import ALL_SORTS    # noqa: E402


def main():
    rng = random.Random(99)
    errors = 0
    for _ in range(3000):
        n = rng.choice([0, 1, 2, 3, 5, 17, 64, 257, 1000])
        k = rng.choice([1, 2, 10, 1000, 10**6])
        low = -k if rng.random() < 0.5 else 0
        data = [rng.randrange(low, k) for _ in range(n)]
        expected = sorted(data)
        for name, sort in ALL_SORTS.items():
            if sort(data) != expected:
                errors += 1
                print("sort error:", name, data[:10])
    rng = random.Random(5)
    for _ in range(5000):
        n = rng.randint(0, 300)
        wide = rng.random() < 0.5
        items = sorted({rng.randrange(-10**6, 10**6) if wide else rng.randrange(0, 50) for _ in range(n)})
        for _ in range(4):
            x = rng.choice(items) if items and rng.random() < 0.6 else rng.randrange(-10**6, 10**6)
            expected = items.index(x) if x in items else -1
            for name, search in SEARCHES.items():
                if search(items, x) != expected:
                    errors += 1
                    print("search error:", name, x)
    print(f"sorts: 3,000 random lists x {len(ALL_SORTS)} algorithms; "
          f"searches: 20,000 random queries x {len(SEARCHES)} algorithms; errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
