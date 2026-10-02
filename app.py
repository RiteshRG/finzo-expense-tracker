import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import init_db, seed_db
from routes.auth import router as auth_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)


@app.on_event("startup")
def startup_event():
    try:
        init_db()
        seed_db()
    except Exception:
        pass


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.get("/", name="landing")
def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={})


@app.get("/login", name="login")
def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/terms", name="terms")
def terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={})


@app.get("/privacy", name="privacy")
def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html", context={})


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.get("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.get("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.get("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.get("/expenses/{id}/edit")
def edit_expense(id: int):
    return "Edit expense — coming in Step 8"


@app.get("/expenses/{id}/delete")
def delete_expense(id: int):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5001, reload=True)
