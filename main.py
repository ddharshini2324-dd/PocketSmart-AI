import os
import json
import shutil
import sqlite3
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from gemini_utils import get_home_recommendations, get_party_recommendations, get_jewelry_recommendations

app = FastAPI(title="PocketSmart AI")

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

COMMON_CSS = """
<style>
    * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }
    body { background-color: #f0f2f5; color: #333; }
    .navbar { background-color: #1e3a8a; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; color: white; }
    .navbar h1 { font-size: 22px; font-weight: bold; }
    .navbar a { color: #f3f4f6; text-decoration: none; margin-left: 20px; font-weight: 600; }
    .container { max-width: 900px; margin: 40px auto; padding: 20px; }
    .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 25px; }
    h2 { color: #1e3a8a; margin-bottom: 20px; }
    label { font-weight: 600; margin-top: 12px; display: block; color: #4b5563; }
    input, select { width: 100%; padding: 10px; margin-top: 6px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 15px; }
    button { background: #2563eb; color: white; padding: 12px 20px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; width: 100%; transition: 0.2s; }
    button:hover { background: #1d4ed8; }
    .btn-secondary { background: #10b981; }
    .btn-secondary:hover { background: #059669; }
    .btn-purple { background: #8b5cf6; }
    .btn-purple:hover { background: #7c3aed; }
    .btn-danger { background: #ef4444; width: auto; padding: 8px 16px; }
    .item-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-top: 15px; }
    .badge { display: inline-block; background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .shop-btn { display: inline-block; background: #ff9900; color: white; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 13px; font-weight: bold; margin-right: 8px; margin-top: 8px; }
    .shop-swiggy { background: #fc8019; }
    .shop-tanishq { background: #861f41; }
    .shop-flipkart { background: #2874f0; }
    .history-card { border-left: 5px solid #2563eb; background: white; padding: 15px; margin-bottom: 15px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
"""

NAVBAR = """
<div class="navbar">
    <h1>PocketSmart AI</h1>
    <div>
        <a href="/dashboard">Dashboard</a>
        <a href="/history">History</a>
        <a href="#" onclick="logout()">Logout</a>
    </div>
</div>
<script>
    function logout() { localStorage.removeItem("user"); window.location.href = "/"; }
</script>
"""

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>PocketSmart AI - Login</title>{COMMON_CSS}</head>
    <body>
        <div class="container" style="max-width: 420px;">
            <div class="card">
                <h2 style="text-align: center;">PocketSmart AI</h2>
                <form action="/login" method="post">
                    <label>Username:</label>
                    <input type="text" name="username" required>
                    <label>Password:</label>
                    <input type="password" name="password" required>
                    <button type="submit">Login</button>
                </form>
                <p style="text-align: center; margin-top: 15px; font-size: 14px;">New user? <a href="/register-page" style="color: #2563eb;">Register here</a></p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/register-page", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>PocketSmart AI - Register</title>{COMMON_CSS}</head>
    <body>
        <div class="container" style="max-width: 420px;">
            <div class="card">
                <h2 style="text-align: center;">Create Account</h2>
                <form action="/register" method="post">
                    <label>Username:</label>
                    <input type="text" name="username" required>
                    <label>Password:</label>
                    <input type="password" name="password" required>
                    <button type="submit" class="btn-secondary">Register</button>
                </form>
                <p style="text-align: center; margin-top: 15px; font-size: 14px;"><a href="/" style="color: #2563eb;">&larr; Back to Login</a></p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/register")
async def register_user(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("pocketsmart.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return HTMLResponse("<script>alert('Username already exists!'); window.location.href='/register-page';</script>")
    conn.close()
    return HTMLResponse("<script>alert('Registration Successful!'); window.location.href='/';</script>")

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
        return HTMLResponse("<script>alert('Invalid Credentials!'); window.location.href='/';</script>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>PocketSmart AI Dashboard</title>{COMMON_CSS}</head>
    <body>
        {NAVBAR}
        <div class="container">
            <div class="card">
                <h2>Welcome, <span id="uName" style="color: #2563eb;"></span>!</h2>
                <p style="color: #6b7280; margin-bottom: 25px;">Select an AI Planner module to generate smart budget recommendations:</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    <div style="background: #eff6ff; padding: 20px; border-radius: 8px; border: 1px solid #bfdbfe;">
                        <h3 style="color: #1e40af;">Home Interior</h3>
                        <p style="font-size: 14px; margin: 10px 0; color: #4b5563;">AI suggestions for lighting, fans, and furniture.</p>
                        <a href="/home-planner"><button style="margin-top: 10px;">Open Planner &rarr;</button></a>
                    </div>
                    <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; border: 1px solid #a7f3d0;">
                        <h3 style="color: #065f46;">Party Planning</h3>
                        <p style="font-size: 14px; margin: 10px 0; color: #4b5563;">Smart allocations for catering, venue & decor.</p>
                        <a href="/party-planner"><button class="btn-secondary" style="margin-top: 10px;">Open Planner &rarr;</button></a>
                    </div>
                    <div style="background: #f3e8ff; padding: 20px; border-radius: 8px; border: 1px solid #ddd6fe;">
                        <h3 style="color: #5b21b6;">Jewelry Selection</h3>
                        <p style="font-size: 14px; margin: 10px 0; color: #4b5563;">Multimodal outfit matching & jewelry design.</p>
                        <a href="/jewelry-planner"><button class="btn-purple" style="margin-top: 10px;">Open Planner &rarr;</button></a>
                    </div>
                </div>
            </div>
        </div>
        <script>
            const user = localStorage.getItem("user");
            if(!user) window.location.href = "/";
            document.getElementById("uName").innerText = user;
        </script>
    </body>
    </html>
    """)

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Home Interior Planner</title>{COMMON_CSS}</head>
    <body>
        {NAVBAR}
        <div class="container">
            <div class="card">
                <h2>Home Interior Planner</h2>
                <form id="pForm">
                    <label>Total Budget (₹):</label>
                    <input type="number" id="tb" value="50000" required>
                    <label>Number of Lights:</label>
                    <input type="number" id="nl" value="2">
                    <label>Number of Fans:</label>
                    <input type="number" id="nf" value="1">
                    <label>Number of Furniture Items:</label>
                    <input type="number" id="nfurn" value="1">
                    <button type="button" onclick="runPlanner()">Generate Recommendations</button>
                </form>
            </div>
            <div id="result" class="card" style="display:none;">
                <h2>Recommendation Breakdown</h2>
                <div id="out"></div>
            </div>
        </div>
        <script>
            async function runPlanner() {{
                const btn = document.querySelector("button");
                btn.innerText = "Processing AI Recommendations...";
                btn.disabled = true;
                const fd = new FormData();
                fd.append("total_budget", document.getElementById("tb").value);
                fd.append("num_lights", document.getElementById("nl").value);
                fd.append("num_fans", document.getElementById("nf").value);
                fd.append("num_furniture", document.getElementById("nfurn").value);
                fd.append("username", localStorage.getItem("user") || "Guest");
                try {{
                    const res = await fetch("/api/home-planner", {{ method: "POST", body: fd }});
                    const data = await res.json();
                    renderOutput(data);
                }} catch(e) {{ alert("Error processing request!"); }}
                finally {{ btn.innerText = "Generate Recommendations"; btn.disabled = false; }}
            }}
            function renderOutput(data) {{
                let html = "";
                const breakdown = data.budget_breakdown || [];
                breakdown.forEach(cat => {{
                    html += `<div class="item-box"><h3 style="color:#1e3a8a;">${{cat.category}} - ₹${{cat.allocation}}</h3>`;
                    (cat.items || []).forEach(item => {{
                        html += `<div style="margin-top:10px;"><strong>${{item.name}}</strong> (Est: ₹${{item.estimated_price}})<p style="font-size:13px; color:#6b7280;">${{item.description}}</p>`;
                        if(item.shopping_links) {{
                            for(let [store, link] of Object.entries(item.shopping_links)) {{
                                html += `<a href="${{link}}" target="_blank" class="shop-btn">${{store}}</a>`;
                            }}
                        }}
                        html += `</div>`;
                    }});
                    html += `</div>`;
                }});
                document.getElementById("out").innerHTML = html;
                document.getElementById("result").style.display = "block";
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Party Budget Planner</title>{COMMON_CSS}</head>
    <body>
        {NAVBAR}
        <div class="container">
            <div class="card">
                <h2>Party Budget Planner</h2>
                <form id="partyForm">
                    <label>Total Budget (₹):</label>
                    <input type="number" id="tb" value="15000" required>
                    <label>Party Type:</label>
                    <select id="pt">
                        <option value="Birthday Party">Birthday Party</option>
                        <option value="Wedding / Reception">Wedding / Reception</option>
                        <option value="Get Together">Get Together</option>
                    </select>
                    <label>Number of Guests:</label>
                    <input type="number" id="ng" value="25">
                    <label>Venue Type:</label>
                    <input type="text" id="vt" value="Home / Hall">
                    <button type="button" class="btn-secondary" onclick="runPartyPlanner()">Generate Party Plan</button>
                </form>
            </div>
            <div id="result" class="card" style="display:none;">
                <h2>Party Recommendation Breakdown</h2>
                <div id="out"></div>
            </div>
        </div>
        <script>
            async function runPartyPlanner() {{
                const btn = document.querySelector("button");
                btn.innerText = "Processing Party AI...";
                btn.disabled = true;
                const fd = new FormData();
                fd.append("total_budget", document.getElementById("tb").value);
                fd.append("party_type", document.getElementById("pt").value);
                fd.append("num_guests", document.getElementById("ng").value);
                fd.append("venue_type", document.getElementById("vt").value);
                fd.append("username", localStorage.getItem("user") || "Guest");
                try {{
                    const res = await fetch("/api/party-planner", {{ method: "POST", body: fd }});
                    const data = await res.json();
                    renderOutput(data);
                }} catch(e) {{ alert("Error!"); }}
                finally {{ btn.innerText = "Generate Party Plan"; btn.disabled = false; }}
            }}
            function renderOutput(data) {{
                let html = "";
                const breakdown = data.budget_breakdown || [];
                breakdown.forEach(cat => {{
                    html += `<div class="item-box"><h3 style="color:#065f46;">${{cat.category}} - ₹${{cat.allocation}}</h3>`;
                    (cat.items || []).forEach(item => {{
                        html += `<div style="margin-top:10px;"><strong>${{item.name}}</strong> (Est: ₹${{item.estimated_price}})<p style="font-size:13px; color:#6b7280;">${{item.description}}</p>`;
                        if(item.shopping_links) {{
                            for(let [store, link] of Object.entries(item.shopping_links)) {{
                                let cls = store === "Swiggy" ? "shop-swiggy" : "shop-btn";
                                html += `<a href="${{link}}" target="_blank" class="shop-btn ${{cls}}">${{store}}</a>`;
                            }}
                        }}
                        html += `</div>`;
                    }});
                    html += `</div>`;
                }});
                document.getElementById("out").innerHTML = html;
                document.getElementById("result").style.display = "block";
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Jewelry Budget Planner</title>{COMMON_CSS}</head>
    <body>
        {NAVBAR}
        <div class="container">
            <div class="card">
                <h2>Jewelry Budget Planner</h2>
                <form id="jewelryForm">
                    <label>Total Budget (₹):</label>
                    <input type="number" id="tb" value="20000" required>
                    <label>Occasion:</label>
                    <input type="text" id="occ" value="Wedding / Festive">
                    <label>Style Preferences:</label>
                    <input type="text" id="pref" value="Traditional Gold / Silver finish">
                    <label>Upload Outfit Image (Optional):</label>
                    <input type="file" id="imgFile" accept="image/*">
                    <button type="button" class="btn-purple" onclick="runJewelryPlanner()">Get Jewelry Recommendations</button>
                </form>
            </div>
            <div id="result" class="card" style="display:none;">
                <h2>Jewelry Recommendation Breakdown</h2>
                <div id="out"></div>
            </div>
        </div>
        <script>
            async function runJewelryPlanner() {{
                const btn = document.querySelector("button");
                btn.innerText = "Analyzing Style & Budget...";
                btn.disabled = true;
                const fd = new FormData();
                fd.append("total_budget", document.getElementById("tb").value);
                fd.append("occasion", document.getElementById("occ").value);
                fd.append("preferences", document.getElementById("pref").value);
                fd.append("username", localStorage.getItem("user") || "Guest");
                const fileInput = document.getElementById("imgFile");
                if (fileInput.files.length > 0) fd.append("image", fileInput.files[0]);
                try {{
                    const res = await fetch("/api/jewelry-planner", {{ method: "POST", body: fd }});
                    const data = await res.json();
                    renderOutput(data);
                }} catch(e) {{ alert("Error!"); }}
                finally {{ btn.innerText = "Get Jewelry Recommendations"; btn.disabled = false; }}
            }}
            function renderOutput(data) {{
                let html = "";
                const recs = data.jewelry_recommendations || [];
                recs.forEach(item => {{
                    html += `<div class="item-box"><h3 style="color:#5b21b6;">${{item.item_type || 'Jewelry Set'}} - ₹${{item.estimated_price}}</h3>`;
                    html += `<p style="font-size:14px; color:#4b5563; margin-top:5px;">${{item.description}}</p>`;
                    if(item.shopping_links) {{
                        for(let [store, link] of Object.entries(item.shopping_links)) {{
                            let cls = store === "Tanishq" ? "shop-tanishq" : "shop-btn";
                            html += `<a href="${{link}}" target="_blank" class="shop-btn ${{cls}}">${{store}}</a>`;
                        }}
                    }}
                    html += `</div>`;
                }});
                document.getElementById("out").innerHTML = html;
                document.getElementById("result").style.display = "block";
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/history", response_class=HTMLResponse)
async def history_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Recommendation History</title>{COMMON_CSS}</head>
    <body>
        {NAVBAR}
        <div class="container">
            <div class="card">
                <h2>Recommendation History</h2>
                <div id="historyList">Loading history...</div>
            </div>
        </div>
        <script>
            async function loadHistory() {{
                const user = localStorage.getItem("user") || "Guest";
                const res = await fetch(`/api/history?username=${{user}}`);
                const data = await res.json();
                let html = "";
                if(data.length === 0) {{
                    html = "<p style='color:#6b7280;'>No previous recommendation history found.</p>";
                }} else {{
                    data.forEach(row => {{
                        html += `<div class="history-card">
                            <span class="badge">${{row.module}}</span>
                            <h3 style="margin-top:8px; color:#1e3a8a;">Budget: ₹${{row.budget}}</h3>
                            <p style="font-size:13px; color:#4b5563; margin-top:5px;">${{row.details}}</p>
                        </div>`;
                    }});
                }}
                document.getElementById("historyList").innerHTML = html;
            }}
            loadHistory();
        </script>
    </body>
    </html>
    """)

# API Endpoints with DB History logging
@app.post("/api/home-planner")
async def api_home_planner(
    total_budget: float = Form(...),
    num_lights: int = Form(0),
    num_fans: int = Form(0),
    num_furniture: int = Form(0),
    username: str = Form("Guest")
):
    data = {"total_budget": total_budget, "num_lights": num_lights, "num_fans": num_fans, "num_furniture": num_furniture, "rooms": ["Living Room"]}
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