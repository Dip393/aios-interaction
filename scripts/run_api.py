import os
import sys
from pathlib import Path

import uvicorn


# Project root: aios-project/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Make sure Python can import `apps.api.main`
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


if __name__ == "__main__":
    host = os.getenv("AIOS_API_HOST", "127.0.0.1")
    port = int(os.getenv("AIOS_API_PORT", "8000"))

    uvicorn.run(
        "apps.api.main:app",
        host=host,
        port=port,
        reload=True,
    )