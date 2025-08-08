# MLB Edge Dashboard — Upload Screenshot → Picks

No-code web app: upload sportsbook screenshots, OCR the odds, pull live MLB data, and compute edges & Kelly stakes.

## Features
- Upload 1+ screenshots of the moneyline slate
- OCR parses teams & odds (you can edit before running)
- Pulls live MLB data (MLB-StatsAPI)
- Outputs fair win%, edge vs market (devig), expected value, and suggested partial-Kelly stake
- Download results as CSV

---

## 1) Deploy to Streamlit Community Cloud (recommended, free)
1. **Create a new GitHub repo** and push this folder’s contents.
2. Go to https://share.streamlit.io → **New app**.
3. Select your repo and set:
   - **Branch:** `main`
   - **App file:** `app.py`
   - **Python version:** 3.10+
4. Click **Deploy** → You’ll get a public URL.

### Optional: Secrets
If you later add paid APIs (e.g., odds vendor), go to Streamlit **App → Settings → Secrets** and add keys. They’ll be available at runtime via `st.secrets[...]`.

---

## 2) Alternative: Deploy on Render (free tier)
1. Create a **New Web Service** at https://render.com
2. Connect your repo and set:
   - **Environment:** Python 3.10+
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
3. Deploy → Render gives you a public URL.

---

## Local Dev
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Notes
- OCR uses **rapidocr-onnxruntime** (no system install). If unavailable on a host, the app will fall back to `pytesseract` (requires system Tesseract).
- Team/player metrics are currently fetched via MLB-StatsAPI; Baseball Savant hooks are scaffolded for future use.
- Model weights are a baseline; refine via backtesting for best performance.
