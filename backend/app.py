from fastapi import FastAPI, Depends
app = FastAPI()

def get_app_version():
    return "0.1.0"

@app.get("/health")
def health(version: str = Depends(get_app_version)):
    return {
        "status": "ok",
        "version": version
    }