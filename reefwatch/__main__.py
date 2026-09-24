import argparse
import os
from pathlib import Path

import uvicorn

from .app import create_app


def main():
    parser = argparse.ArgumentParser(description="Reef Watch local aquarium camera monitor")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--demo", action="store_true", help="Synthetic test frames in a separate data directory"
    )
    args = parser.parse_args()
    os.umask(0o077)
    uvicorn.run(
        create_app(args.data_dir, args.demo),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
