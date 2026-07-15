# Balaji Amines — ESG Compliance Command Center

A live web dashboard that tracks every SEBI ESG compliance obligation affecting Balaji Amines,
scans for changes **automatically every morning**, and is viewable by your whole team at a single web link.

You do **not** need a server, and you do **not** need to write any code. GitHub runs the daily scan
for you, for free.

---

## What you get

- **A web link** you can share with anyone (`https://<your-name>.github.io/esg-dashboard/`).
- **An automatic daily scan at 10:00 AM IST** that looks for new/changed SEBI ESG rules and updates the page by itself.
- **A "sticky" compliance register:** existing obligations are never deleted. When a rule changes, its card is
  flagged **UPDATED** (with a source link) but stays in place. Genuinely new rules appear as **NEW** cards for you to confirm.
- **A daily change feed** at the top, so you only read what *changed* — not the whole rulebook.

---

## One-time setup (about 15 minutes, all in your web browser)

### Step 1 — Create a free GitHub account
Go to **https://github.com/signup** and make an account (free). If Balaji Amines already has a
GitHub organisation, you can use that instead.

### Step 2 — Create a new repository
1. Click the **+** in the top-right → **New repository**.
2. **Repository name:** `esg-dashboard`
3. Choose **Public**. *(This only contains public SEBI information — no passwords or private data. Public is what makes the web link free.)*
4. Click **Create repository**.

### Step 3 — Upload these files
1. Unzip the `esg-dashboard.zip` I gave you on your computer.
2. On the new repository page, click **uploading an existing file** (the link in the middle of the page).
3. Open the unzipped `esg-dashboard` folder, select **everything inside it** (including the `.github` folder), and drag it into the browser.
   - If the `.github` folder doesn't drag in, that's OK — see "If the .github folder won't upload" at the bottom.
4. Click **Commit changes**.

### Step 4 — Allow the daily scan to save updates
1. In your repository, go to **Settings** (top menu) → **Actions** → **General** (left menu).
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions** → **Save**.

### Step 5 — Turn on the web page (GitHub Pages)
1. Go to **Settings** → **Pages** (left menu).
2. Under **Source**, choose **Deploy from a branch**.
3. **Branch:** `main`, **Folder:** `/ (root)` → **Save**.
4. Wait about a minute, then refresh. GitHub shows your live link at the top, e.g.
   `https://your-name.github.io/esg-dashboard/`. **This is the link you share.**

### Step 6 — Run the first scan now (don't wait for tomorrow)
1. Go to the **Actions** tab.
2. If you see a prompt, click **"I understand my workflows, go ahead and enable them."**
3. Click **Daily ESG Compliance Scan** (left) → **Run workflow** (right) → **Run workflow**.
4. After a minute it turns green. Your dashboard is live and will now update itself every morning.

**That's it.** Share the link from Step 5 with your team.

---

## How it works, day to day

- Every morning at **10:00 AM IST**, GitHub runs `scanner.py` on its own servers.
- It scans recent SEBI / BRSR / LODR / ESG-rating / ESG-fund news.
- **It never deletes an obligation.** For each change it finds:
  - **Matches an existing obligation** → that card gets an **UPDATED** flag + a source link (card stays put).
  - **A brand-new SEBI requirement** → a **NEW** card is added, marked *"To be confirmed"* so you can verify the details.
  - Everything found is logged in the **daily change feed** at the top.
- If nothing changed, the page simply stays as-is.

### Reading the dashboard
- **Top feed = what changed recently.** Badges: `Added`, `Updated`, `Removed`, `Deadline`.
- **Register = the full living list**, filterable by your stream of work (Listed Company is Balaji Amines).
- `RELEVANT` = applies to Balaji Amines as a listed manufacturer.

---

## Common questions

**Can I change the scan time?**
Yes. Edit `.github/workflows/daily-scan.yml`, line `cron: "30 4 * * *"`. The time is in UTC.
`30 4` = 04:30 UTC = 10:00 AM IST. For 8:00 AM IST use `30 2`; for 6:00 PM IST use `30 12`.

**A NEW card says "To be confirmed" — why?**
The scan detects new rules from public news, which is fast and free but not always precise on exact dates
and thresholds. Open the source link, confirm against the actual SEBI circular, then edit the card's details
(see below) or ask me to.

**How do I edit an obligation by hand (or remove a NEW card I don't want)?**
Open `data.json` in your repository, click the pencil ✏️ to edit, change the text, and **Commit**.
The site updates within a minute. (Happy to make any edits for you — just ask.)

**Will the daily scan keep running forever?**
GitHub pauses *scheduled* jobs if a repository has had no activity for 60 days. Running the scan manually
once in a while (Step 6), or any edit, resets that. Realistically you'll be opening/editing it well within 60 days.

**Is our data safe / private?**
The repository only holds public SEBI regulatory information — no passwords, no internal Balaji Amines data.
If you ever want it behind a company login instead of a public link, that's the "company server" option — ask me.

---

## If the `.github` folder won't upload
Some browsers hide folders that start with a dot. If it won't drag in:
1. In your repository, click **Add file** → **Create new file**.
2. In the filename box, type exactly: `.github/workflows/daily-scan.yml`
   (typing the `/` creates the folders automatically).
3. Open `daily-scan.yml` from the unzipped folder in Notepad/TextEdit, copy all of it, paste it in, and **Commit**.

---

## What's in this folder
| File | What it does |
|------|--------------|
| `index.html` | The dashboard (what your team sees). |
| `data.json` | The compliance data — the register, feed, and timeline. The scanner updates this. |
| `scanner.py` | The daily scan. Runs on GitHub, needs no setup. |
| `.github/workflows/daily-scan.yml` | The timer that runs the scan every morning. |
| `README.md` | This guide. |

*Built for the Office of Director Hemanth Reddy, Balaji Amines Ltd. Source of record: SEBI Board Memorandum on the Balanced Framework for ESG Disclosures, Ratings and Investing.*
