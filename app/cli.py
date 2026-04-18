from __future__ import annotations

import argparse

from app.batch import process_next_batch
from app.db import DEFAULT_DB_PATH, get_connection, init_db
from app.repository import NumberRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Process the next batch of Collatz numbers.")
    parser.add_argument("count", type=int, help="How many sequential numbers to process next.")
    args = parser.parse_args()

    connection = get_connection(DEFAULT_DB_PATH)
    try:
        init_db(connection)
        repository = NumberRepository(connection)
        result = process_next_batch(repository, args.count)
    finally:
        connection.close()

    print(f"Processed {result.processed_count} numbers.")
    print(f"Range: {result.start_n} through {result.end_n}")
    print(f"last_processed_n={result.last_processed_n}")
    print(f"max_steps_seen={result.max_steps_seen}")
    print(f"max_peak_seen={result.max_peak_seen}")


if __name__ == "__main__":
    main()
