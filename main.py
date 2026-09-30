import os
import shutil
import sqlite3
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gemini_utils import get_home_recommendations, get_party_recommendations, get_jewelry_recommendations

app = FastAPI(title="PocketSmart AI: Smart Budget Planner")

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def init_db():
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            module TEXT NOT NULL,
            budget REAL NOT NULL,
            details TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Page Routes (Jinja2 Templates)
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request):
    return templates.TemplateResponse("home_planner.html", {"request": request})

@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request):
    return templates.TemplateResponse("party_planner.html", {"request": request})

@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request):
    return templates.TemplateResponse("jewelry_planner.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

# Auth Actions
@app.post("/register")
async def register_user(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return HTMLResponse("<script>alert('Username already exists!'); window.location.href='/register';</script>")
    conn.close()
    return HTMLResponse("<script>alert('Registration Successful!'); window.location.href='/login';</script>")

@app.post("/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return HTMLResponse(content=f"""
        <script>
            localStorage.setItem("user", "{username}");
            window.location.href = "/dashboard";
        </script>
        """)
    else:
        return HTMLResponse("<script>alert('Invalid Credentials!'); window.location.href='/login';</script>")

# API Recommendation Endpoints
@app.post("/api/home-planner")
async def api_home_planner(
    total_budget: float = Form(...),
    num_lights: int = Form(0),
    num_fans: int = Form(0),
    num_furniture: int = Form(0),
    username: str = Form("Guest")
):
    data = {"total_budget": total_budget, "num_lights": num_lights, "num_fans": num_fans, "num_furniture": num_furniture}
    res = get_home_recommendations(data)
    
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (username, module, budget, details) VALUES (?, ?, ?, ?)",
                   (username, "Home Interior", total_budget, f"Lights: {num_lights}, Fans: {num_fans}, Furniture: {num_furniture}"))
    conn.commit()
    conn.close()
    return res

@app.post("/api/party-planner")
async def api_party_planner(
    total_budget: float = Form(...),
    party_type: str = Form("Birthday Party"),
    num_guests: int = Form(10),
    venue_type: str = Form("Home"),
    username: str = Form("Guest")
):
    data = {"total_budget": total_budget, "party_type": party_type, "num_guests": num_guests, "venue_type": venue_type}
    res = get_party_recommendations(data)

    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (username, module, budget, details) VALUES (?, ?, ?, ?)",
                   (username, "Party Planner", total_budget, f"Type: {party_type}, Guests: {num_guests}, Venue: {venue_type}"))
    conn.commit()
    conn.close()
    return res

@app.post("/api/jewelry-planner")
async def api_jewelry_planner(
    total_budget: float = Form(...),
    occasion: str = Form("Wedding"),
    preferences: str = Form("Traditional"),
    username: str = Form("Guest"),
    image: UploadFile = File(None)
):
    data = {"total_budget": total_budget, "occasion": occasion, "preferences": preferences}
    image_path = None
    if image:
        image_path = f"static/uploads/{image.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    res = get_jewelry_recommendations(data, image_path)

    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (username, module, budget, details) VALUES (?, ?, ?, ?)",
                   (username, "Jewelry Planner", total_budget, f"Occasion: {occasion}, Style: {preferences}"))
    conn.commit()
    conn.close()
    return res

@app.get("/api/history")
async def get_history(username: str):
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    cursor.execute("SELECT module, budget, details FROM history WHERE username = ? ORDER BY id DESC", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"module": r[0], "budget": r[1], "details": r[2]} for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)