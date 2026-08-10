# Deploy this as a live link for your résumé

Goal: a public URL a recruiter can click and the app just runs — plus the code
on GitHub. Free, ~10 minutes. You'll do two things: (1) put the code on GitHub,
(2) deploy it on Streamlit Community Cloud.

The app is already deploy-ready: tiny (2 MB), models are prebuilt, and it needs
no paid services or API keys.

---

## Step 1 — Put the code on GitHub (new public repo)

Easiest, no command line:

1. Go to <https://github.com/new>.
2. Repository name: **`nba-matchup-predictor`** · set to **Public** · don't add
   a README (you already have one) · click **Create repository**.
3. On the new empty repo page, click **“uploading an existing file.”**
4. Open your **`matchup_dashboard`** folder, select **everything inside it**
   (app.py, src/, data/, models/, scripts/, .streamlit/, README.md, etc.) and
   drag it into the browser. ⚠️ Upload the *contents* of `matchup_dashboard`, so
   that **`app.py` sits at the top level of the repo** (not inside a subfolder).
   You can skip `run.command` and any `.venv` folder.
5. Click **Commit changes.**

(Prefer the terminal? From inside `matchup_dashboard`:
`git init && git add . && git commit -m "NBA matchup predictor" &&
git branch -M main && git remote add origin <your-repo-url> && git push -u origin main`)

## Step 2 — Deploy on Streamlit Community Cloud (free)

1. Go to <https://share.streamlit.io> and **sign in with GitHub** (authorize it).
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `your-username/nba-matchup-predictor`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy.** It installs `requirements.txt` and launches (~2–4 min).
5. You get a public URL like **`https://nba-matchup-predictor.streamlit.app`.**

That URL is your live demo. It auto-redeploys whenever you push to GitHub.

## Step 3 — Put it on your résumé

Link **both**:

> **NBA Matchup Predictor** — Live demo: nba-matchup-predictor.streamlit.app ·
> Code: github.com/you/nba-matchup-predictor

Recruiters click the live demo first (it just works); engineers check the code.

---

## Good to know

- **The live-data buttons may not work on the cloud.** stats.nba.com and some
  feeds block cloud server IPs, so “Refresh live data” / “Load injury report”
  can fail there — that's expected, and the app falls back to the bundled
  2026-27 projection automatically. It works fully when run locally.
- **Nothing to configure / no secrets.** No API keys, no environment variables.
- **To update the live app**, just push new commits to GitHub — Streamlit Cloud
  redeploys on its own.
- **README is your repo's front page** — it already explains the model, results,
  and how to run it. `PROJECT_WRITEUP.md` has résumé bullets and interview Q&A.
