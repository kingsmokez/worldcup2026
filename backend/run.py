#!/usr/bin/env python3
import uvicorn
import sys
port = int(sys.argv[1]) if len(sys.argv) > 1 else 6240
uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
