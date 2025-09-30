import sys
import os

# Fix imports
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import uvicorn
    # Usar string en lugar del objeto app
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)