"""Run the AICMMS API server via: python -m cafm.api"""

from __future__ import annotations

import uvicorn

from cafm.api.config import APIConfig


def main() -> None:
    config = APIConfig()
    uvicorn.run(
        "cafm.api.app:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.debug and "debug" or "info",
    )


if __name__ == "__main__":
    main()
