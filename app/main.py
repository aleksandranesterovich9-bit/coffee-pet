from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def main_root():
    return 'Hello'

@app.get('/health')
def health():
    return {'status':'ok'}
