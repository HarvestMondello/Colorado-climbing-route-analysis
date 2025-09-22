Skip to content
Chat history

You said:
For .md files hosted as a website (depository) on github, should they be page-name.md or page_name.md?

ChatGPT said:
For .md files that are meant to be rendered as individual pages in a GitHub Pages (or MkDocs/Jekyll-style) website, the more web-friendly and conventional choice is:

👉 kebab-case → page-name.md

Why kebab-case is better for .md pages:
Web URLs: When served by GitHub Pages, page-name.md becomes yoursite.com/page-name/ — clean and standard for the web.

Compatibility: Hyphens avoid issues some static site generators or themes have with underscores.

Consistency: Matches how most blogs and docs are structured (e.g., /about-me/, /data-analysis-guide/).

Readability: Easier for humans to read in URLs than underscores.

Underscores (page_name.md) are OK when:
You’re using .md files purely as documentation or notes in the repo, not as published website pages.

You want consistency with CSV and script naming conventions (snake_case), since those won’t ever become URLs.

⚡ Rule of Thumb for your project:

Docs meant for web pages → kebab-case.md

Data/code artifacts → snake_case.csv / snake_case.py

Would you like me to suggest a quick conversion script to rename your current _ files into - ones (and update internal links so nothing breaks)?

You said:
No.  So my doc_convebtions should be updated to reflect this?
ChatGPT said:
Yes 👍 — your doc_conventions.md (or wherever you’re keeping your standards) should be updated to reflect this distinction.

Right now you’ve got:

Scripts & Data Files (Python, CSV, SQL) → snake_case ✅

Images & Folders → kebab-case ✅

You should add a line for Markdown docs:

Markdown Pages (website-facing) → kebab-case (e.g., the-naked-edge.md, scenic-cruise.md)

Markdown Notes (repo-only, not served as pages) → can stay snake_case if you want consistency with data/scripts

Would you like me to draft a clean updated conventions block you can drop straight into your doc_conventions.md?

You said:
Yes
ChatGPT said:
Here’s a clean block you can drop into doc_conventions.md so it matches how you’re actually using things:

# Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions:

🔹 **Scripts & Data Files**  
Use **snake_case** (lowercase with underscores).  
✅ Examples:  
- `scrape_routes.py`  
- `joined_route_tick_cleaned.csv`  
- `eda_routes.sql`  

🔹 **Images**  
Use **kebab-case** (lowercase with hyphens).  
✅ Examples:  
- `naked-edge.png`  
- `scenic-cruise-banner.jpg`  

🔹 **Folders**  
Use **kebab-case** (clean and portable across systems and URLs).  
✅ Examples:  
- `scripts/`  
- `python-visuals/`  
- `docs/routes/`  

🔹 **Markdown Pages**  
- If published on GitHub Pages / website → **kebab-case**  
  ✅ Example: `the-naked-edge.md`, `scenic-cruise.md`  
- If repo-only notes (not web pages) → may use **snake_case** for consistency with scripts  
  ✅ Example: `analysis_notes.md`  

🔹 **CSV Columns**  
Use **snake_case** (SQL/Pandas friendly). Avoid spaces, special characters, or camelCase.  
✅ Examples:  
- `route_name`, `route_type`, `fa_year`, `ffa_year`  
- `area_hierarchy`, `total_ticks`, `unique_climbers`  
- `year_2025`, `january`, `is_trending_now`  

---

⚡ **Rule of Thumb**  
- **Code & CSVs** → `snake_case`  
- **Images, Folders, Markdown Pages (website)** → `kebab-case`  
Do you want me to also show you a before/after example folder tree (with one of your route .md files) so it’s crystal clear how this looks in practice?

You said:
Update this to show the .md conventions: # Documentation Conventions

This repository uses **Google-style Python docstrings** for all scripts, functions, and classes.  
The goal is to keep documentation clear, concise, and consistent across all projects in this portfolio.

---

## 1. Script-Level Docstring

Each script starts with a high-level docstring describing purpose, workflow, inputs, outputs, and dependencies:

python
"""
Script: clean_pipeline.py
Purpose:
    Clean raw input datasets and save preprocessed outputs.

Workflow:
    1. Load raw CSV files
    2. Apply cleaning functions
    3. Save processed outputs

Input:
    - Raw CSV files in `data/raw/`

Output:
    - Cleaned CSV files in `data/processed/`
ChatGPT said:
Got it 👍 — here’s an updated version of your Documentation Conventions file with a new section covering .md conventions alongside your Python docstring standards:

# Documentation Conventions

This repository uses **Google-style Python docstrings** for all scripts, functions, and classes.  
The goal is to keep documentation clear, concise, and consistent across all projects in this portfolio.

---

## 1. Script-Level Docstring

Each script starts with a high-level docstring describing purpose, workflow, inputs, outputs, and dependencies:

```python
"""
Script: clean_pipeline.py
Purpose:
    Clean raw input datasets and save preprocessed outputs.

Workflow:
    1. Load raw CSV files
    2. Apply cleaning functions
    3. Save processed outputs

Input:
    - Raw CSV files in `data/raw/`

Output:
    - Cleaned CSV files in `data/processed/`
"""
2. Markdown Conventions
Markdown (.md) files are used for two distinct purposes in this repository:

Website-facing pages (rendered via GitHub Pages or similar)

Repo-only notes/documentation (not published as web pages)

2.1 Naming Conventions
Website-facing Markdown pages → kebab-case
✅ Examples: the-naked-edge.md, scenic-cruise.md
🔗 These produce clean, readable URLs like /the-naked-edge/

Repo-only Markdown notes → snake_case
✅ Examples: analysis_notes.md, scraper_todos.md

2.2 Structure
Each Markdown page should follow a clear, predictable structure:

Begin with a H1 heading (# Title)

Use H2 (##) and H3 (###) headings for sections

Auto-generated content (metrics, seasonality, leaderboards) should be wrapped in
HTML comment markers to allow scripts to overwrite safely:

<!-- AUTO:METRICS:START -->
<!-- AUTO:METRICS:END -->
2.3 Placement
Website-facing .md files → docs/ or subfolders (docs/routes/)

Repo-only notes → root-level or project-specific folders (analysis/, scripts/)

⚡ Rule of Thumb

Scripts → Google-style docstrings

Website-facing .md → kebab-case + clean structure for web

Repo-only .md → snake_case + flexible structure for internal use


Do you want me to also add a **mini example** of a route `.md` page (with the AUTO blocks) so you can standardize how those should look too?
You said:
Is it confusing that some .md are "-" and some are "_" in this case?
ChatGPT said:
Good question — yes, it can be confusing at first glance if you mix - and _ in the same repo for .md files. But whether it’s too confusing depends on how you frame it:

Why it’s acceptable
The purpose is different:

kebab-case.md → published as a webpage, where hyphens are the web standard.

snake_case.md → internal notes, treated more like data/scripts.

If you clearly document this in your doc conventions, the rule is easy to follow.

Why it could be confusing
At a quick glance in your repo, people may not know why some are - and some are _.

Contributors (or even future you) may forget the rule if the difference isn’t reinforced.

Tools/scripts might need to handle both naming patterns.

Options
Keep both (current approach)

Works fine if you document the distinction well.

Best if you really want clean URLs for public-facing pages but prefer snake_case internally.

Unify to kebab-case for all .md

Pros: total consistency, no cognitive overhead.

Cons: internal .md notes look less consistent with your Python/CSV naming (snake_case).

Unify to snake_case for all .md

Pros: matches your Python/CSV convention everywhere.

Cons: web URLs get underscores, which look a bit less standard than hyphens.

⚡ My recommendation (since you’re hosting a website + repo):

Stick with your current split → kebab-case for web pages, snake_case for notes.

Just make it super explicit in your conventions doc (like a table that contrasts them).

Do you want me to draft a visual table (one row for web .md, one for repo .md) so the rule is dead obvious in your doc_conventions.md?

You said:
rework this with the .md conventions for both internal and webpages: # 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Example:  
  - scrape_routes.py    

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Example:    
  - naked-edge.png  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - scripts/  
  - python-visuals/   

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - route_name, route_type, fa_year, ffa_year  
  - area_hierarchy, total_ticks, unique_climbers  
  - year_2025, january, is_trending_now  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images & Folders → kebab-case**

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  

Following these conventions ensures clean, predictable code and datasets that work well across Python, SQL, and GitHub documentation.
ChatGPT said:
Here’s a reworked version of your conventions file with Markdown (.md) conventions for both internal notes and website pages baked in:

# 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Example:  
  - `scrape_routes.py`    

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Example:    
  - `naked-edge.png`  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - `scripts/`  
  - `python-visuals/`   

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - `route_name`, `route_type`, `fa_year`, `ffa_year`  
  - `area_hierarchy`, `total_ticks`, `unique_climbers`  
  - `year_2025`, `january`, `is_trending_now`  

---

## 🔹 Markdown Files
Markdown files are used in two different contexts, so naming differs:

- **Website-facing pages** → **kebab-case**  
  - Ensures clean, SEO-friendly URLs when published via GitHub Pages or similar.  
  - ✅ Examples:  
    - `the-naked-edge.md` → `/the-naked-edge/`  
    - `scenic-cruise.md` → `/scenic-cruise/`  

- **Internal notes/docs** → **snake_case**  
  - Keeps consistency with scripts and datasets when used only inside the repo.  
  - ✅ Examples:  
    - `analysis_notes.md`  
    - `scraper_todos.md`  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images, Folders, Website Markdown Pages → kebab-case**  
- **Internal Markdown Notes → snake_case**  

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  
- Splitting Markdown conventions keeps **internal repo docs consistent with code**, while keeping **website docs consistent with web standards**.  

Following these conventions ensures clean, predictable organization across Python, SQL, datasets, and GitHub documentation.
Do you want me to also add a mini folder tree example (showing both docs/routes/the-naked-edge.md and analysis_notes.md) so the difference is obvious at a glance?

You said:
is this easy for someone to follow or should I change my conventions?
ChatGPT said:
It’s easy once it’s explained clearly, but here’s the trade-off:

✅ Why your current system works
It follows best practices in each domain:

snake_case → matches Python/SQL/data workflows.

kebab-case → matches web/URLs/Markdown links.

The distinction is purpose-driven (internal vs. web-facing).

With your conventions doc, it’s explicit and enforceable.

⚠️ Why it might trip someone up
Someone browsing your repo without reading the conventions might wonder:

“Why are some .md files snake_case and others kebab-case?”

Contributors (or future you) could forget which is which.

Automated scripts may need to handle both styles.

🚦 Options
Keep as-is (my default recommendation)

It’s logical, standards-based, and documented.

Just make the rule visual in your docs (a table or tree).

Unify all .md to kebab-case

Pros: perfect consistency across the repo.

Cons: your internal docs won’t match your Python/CSV style.

Unify all .md to snake_case

Pros: repo consistency with code/data.

Cons: published URLs look a little off (the_naked_edge instead of the-naked-edge).

⚡ My recommendation:
Stick with your split convention (kebab for web, snake for internal). It’s the most professional choice, especially since your repo doubles as a website + data project. Just make it crystal clear in your doc conventions with examples and a table/tree.

Would you like me to draft a one-glance table (web vs internal) that you can drop into your conventions file so nobody ever confuses them?

You said:
yes
ChatGPT said:
Perfect 👌 — here’s a one-glance table you can drop straight into your conventions file so the Markdown rules are crystal clear:

## 🔹 Markdown File Naming

| Context              | Convention   | Examples                        | Result / Purpose                  |
|----------------------|--------------|---------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | `the-naked-edge.md` → `/the-naked-edge/`<br>`scenic-cruise.md` → `/scenic-cruise/` | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | `analysis_notes.md`<br>`scraper_todos.md` | Consistent with Python/CSV naming, easier for internal use |
That way, someone scanning the conventions sees immediately why there are two styles.

Do you also want me to show a mini folder tree example (like docs/routes/ vs analysis/) so it’s even more visual in context?

You said:
where in the naming_conventions file shoudl i put that table?
ChatGPT said:
Good question 👍

The table belongs inside your Markdown section so it doesn’t get lost among scripts, images, and CSV rules. Here’s the flow I’d suggest for your naming_conventions.md:

Scripts & Data Files

Images

Folders

CSV Columns

Markdown Files

Explain briefly that there are two contexts (web vs internal).

Insert the table here.

Rule of Thumb

Why This Convention

That way the table sits right after the intro to Markdown rules, making it obvious and easy to reference.

🔧 Example placement:

## 🔹 Markdown Files
Markdown files are used in two different contexts, so naming differs.

### Naming Table
| Context              | Convention   | Examples                        | Result / Purpose                  |
|----------------------|--------------|---------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | `the-naked-edge.md` → `/the-naked-edge/`<br>`scenic-cruise.md` → `/scenic-cruise/` | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | `analysis_notes.md`<br>`scraper_todos.md` | Consistent with Python/CSV naming, easier for internal use |
Do you want me to also adjust your Rule of Thumb section so it calls back to this table (like “see Markdown table above”)?

You said:
like this: 
# Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions:


## 🔹 Markdown File Naming

| Context              | Convention   | Examples                        | Result / Purpose                  |
|----------------------|--------------|---------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | the-naked-edge.md → /the-naked-edge/<br>scenic-cruise.md → /scenic-cruise/ | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | analysis_notes.md<br>scraper_todos.md | Consistent with Python/CSV naming, easier for internal use |

🔹 **Scripts & Data Files**  
Use **snake_case** (lowercase with underscores).  
✅ Examples:  
- scrape_routes.py  
- joined_route_tick_cleaned.csv  
- eda_routes.sql  

🔹 **Images**  
Use **kebab-case** (lowercase with hyphens).  
✅ Examples:  
- naked-edge.png  
- scenic-cruise-banner.jpg  

🔹 **Folders**  
Use **kebab-case** (clean and portable across systems and URLs).  
✅ Examples:  
- scripts/  
- python-visuals/  
- docs/routes/  

🔹 **Markdown Pages**  
- If published on GitHub Pages / website → **kebab-case**  
  ✅ Example: the-naked-edge.md, scenic-cruise.md  
- If repo-only notes (not web pages) → may use **snake_case** for consistency with scripts  
  ✅ Example: analysis_notes.md  

🔹 **CSV Columns**  
Use **snake_case** (SQL/Pandas friendly). Avoid spaces, special characters, or camelCase.  
✅ Examples:  
- route_name, route_type, fa_year, ffa_year  
- area_hierarchy, total_ticks, unique_climbers  
- year_2025, january, is_trending_now  

---

⚡ **Rule of Thumb**  
- **Code & CSVs** → snake_case  
- **Images, Folders, Markdown Pages (website)** → kebab-case  
Do you want me to also show you a before/after example folder tree (with one of your route .md files) so it’s crystal clear how this looks in practice?

You said:
Update this to show the .md conventions: # Documentation Conventions

This repository uses **Google-style Python docstrings** for all scripts, functions, and classes.  
The goal is to keep documentation clear, concise, and consistent across all projects in this portfolio.

---

## 1. Script-Level Docstring

Each script starts with a high-level docstring describing purpose, workflow, inputs, outputs, and dependencies:

python
"""
Script: clean_pipeline.py
Purpose:
    Clean raw input datasets and save preprocessed outputs.

Workflow:
    1. Load raw CSV files
    2. Apply cleaning functions
    3. Save processed outputs

Input:
    - Raw CSV files in data/raw/

Output:
    - Cleaned CSV files in data/processed/
ChatGPT said:
Got it 👍 — here’s an updated version of your Documentation Conventions file with a new section covering .md conventions alongside your Python docstring standards:

# Documentation Conventions

This repository uses **Google-style Python docstrings** for all scripts, functions, and classes.  
The goal is to keep documentation clear, concise, and consistent across all projects in this portfolio.

---

## 1. Script-Level Docstring

Each script starts with a high-level docstring describing purpose, workflow, inputs, outputs, and dependencies:

python
"""
Script: clean_pipeline.py
Purpose:
    Clean raw input datasets and save preprocessed outputs.

Workflow:
    1. Load raw CSV files
    2. Apply cleaning functions
    3. Save processed outputs

Input:
    - Raw CSV files in `data/raw/`

Output:
    - Cleaned CSV files in `data/processed/`
"""
2. Markdown Conventions
Markdown (.md) files are used for two distinct purposes in this repository:

Website-facing pages (rendered via GitHub Pages or similar)

Repo-only notes/documentation (not published as web pages)

2.1 Naming Conventions
Website-facing Markdown pages → kebab-case
✅ Examples: the-naked-edge.md, scenic-cruise.md
🔗 These produce clean, readable URLs like /the-naked-edge/

Repo-only Markdown notes → snake_case
✅ Examples: analysis_notes.md, scraper_todos.md

2.2 Structure
Each Markdown page should follow a clear, predictable structure:

Begin with a H1 heading (# Title)

Use H2 (##) and H3 (###) headings for sections

Auto-generated content (metrics, seasonality, leaderboards) should be wrapped in
HTML comment markers to allow scripts to overwrite safely:

<!-- AUTO:METRICS:START -->
<!-- AUTO:METRICS:END -->
2.3 Placement
Website-facing .md files → docs/ or subfolders (docs/routes/)

Repo-only notes → root-level or project-specific folders (analysis/, scripts/)

⚡ Rule of Thumb

Scripts → Google-style docstrings

Website-facing .md → kebab-case + clean structure for web

Repo-only .md → snake_case + flexible structure for internal use


Do you want me to also add a **mini example** of a route `.md` page (with the AUTO blocks) so you can standardize how those should look too?
You said:
Is it confusing that some .md are "-" and some are "_" in this case?
ChatGPT said:
Good question — yes, it can be confusing at first glance if you mix - and _ in the same repo for .md files. But whether it’s too confusing depends on how you frame it:

Why it’s acceptable
The purpose is different:

kebab-case.md → published as a webpage, where hyphens are the web standard.

snake_case.md → internal notes, treated more like data/scripts.

If you clearly document this in your doc conventions, the rule is easy to follow.

Why it could be confusing
At a quick glance in your repo, people may not know why some are - and some are _.

Contributors (or even future you) may forget the rule if the difference isn’t reinforced.

Tools/scripts might need to handle both naming patterns.

Options
Keep both (current approach)

Works fine if you document the distinction well.

Best if you really want clean URLs for public-facing pages but prefer snake_case internally.

Unify to kebab-case for all .md

Pros: total consistency, no cognitive overhead.

Cons: internal .md notes look less consistent with your Python/CSV naming (snake_case).

Unify to snake_case for all .md

Pros: matches your Python/CSV convention everywhere.

Cons: web URLs get underscores, which look a bit less standard than hyphens.

⚡ My recommendation (since you’re hosting a website + repo):

Stick with your current split → kebab-case for web pages, snake_case for notes.

Just make it super explicit in your conventions doc (like a table that contrasts them).

Do you want me to draft a visual table (one row for web .md, one for repo .md) so the rule is dead obvious in your doc_conventions.md?

You said:
rework this with the .md conventions for both internal and webpages: # 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Example:  
  - scrape_routes.py    

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Example:    
  - naked-edge.png  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - scripts/  
  - python-visuals/   

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - route_name, route_type, fa_year, ffa_year  
  - area_hierarchy, total_ticks, unique_climbers  
  - year_2025, january, is_trending_now  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images & Folders → kebab-case**

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  

Following these conventions ensures clean, predictable code and datasets that work well across Python, SQL, and GitHub documentation.
ChatGPT said:
Here’s a reworked version of your conventions file with Markdown (.md) conventions for both internal notes and website pages baked in:

# 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Example:  
  - `scrape_routes.py`    

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Example:    
  - `naked-edge.png`  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - `scripts/`  
  - `python-visuals/`   

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - `route_name`, `route_type`, `fa_year`, `ffa_year`  
  - `area_hierarchy`, `total_ticks`, `unique_climbers`  
  - `year_2025`, `january`, `is_trending_now`  

---

## 🔹 Markdown Files
Markdown files are used in two different contexts, so naming differs:

- **Website-facing pages** → **kebab-case**  
  - Ensures clean, SEO-friendly URLs when published via GitHub Pages or similar.  
  - ✅ Examples:  
    - `the-naked-edge.md` → `/the-naked-edge/`  
    - `scenic-cruise.md` → `/scenic-cruise/`  

- **Internal notes/docs** → **snake_case**  
  - Keeps consistency with scripts and datasets when used only inside the repo.  
  - ✅ Examples:  
    - `analysis_notes.md`  
    - `scraper_todos.md`  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images, Folders, Website Markdown Pages → kebab-case**  
- **Internal Markdown Notes → snake_case**  

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  
- Splitting Markdown conventions keeps **internal repo docs consistent with code**, while keeping **website docs consistent with web standards**.  

Following these conventions ensures clean, predictable organization across Python, SQL, datasets, and GitHub documentation.
Do you want me to also add a mini folder tree example (showing both docs/routes/the-naked-edge.md and analysis_notes.md) so the difference is obvious at a glance?



No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
ChatGPT said:
Yes — the way you placed it is good 👍

Here’s how I’d finalize the structure of your Naming Conventions file so the .md rules are clear and easy to follow:

# 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Markdown File Naming

| Context              | Convention     | Examples                                                    | Result / Purpose                  |
|----------------------|----------------|-------------------------------------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | `the-naked-edge.md` → `/the-naked-edge/`<br>`scenic-cruise.md` → `/scenic-cruise/` | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | `analysis_notes.md`<br>`scraper_todos.md`                   | Consistent with Python/CSV naming, easier for internal use |

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Examples:  
  - `scrape_routes.py`  
  - `joined_route_tick_cleaned.csv`  
  - `eda_routes.sql`  

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Examples:  
  - `naked-edge.png`  
  - `scenic-cruise-banner.jpg`  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - `scripts/`  
  - `python-visuals/`  
  - `docs/routes/`  

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - `route_name`, `route_type`, `fa_year`, `ffa_year`  
  - `area_hierarchy`, `total_ticks`, `unique_climbers`  
  - `year_2025`, `january`, `is_trending_now`  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images, Folders, Website Markdown Pages → kebab-case**  
- **Internal Markdown Notes → snake_case**  

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  
- Splitting Markdown conventions keeps **internal repo docs consistent with code**, while keeping **website docs consistent with web standards**.  
This way the table sits right at the top of the Markdown section, and the rest of the file stays clean.

👉 Do you want me to also add a mini folder tree example (like docs/routes/the-naked-edge.md vs analysis/analysis_notes.md) right under the table, so readers immediately see the difference in context?

You said:
yes
ChatGPT said:
Great — here’s your Naming Conventions file updated with a mini folder tree right under the Markdown table so it’s visually clear how kebab vs snake applies in practice:

# 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Markdown File Naming

| Context              | Convention     | Examples                                                    | Result / Purpose                  |
|----------------------|----------------|-------------------------------------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | `the-naked-edge.md` → `/the-naked-edge/`<br>`scenic-cruise.md` → `/scenic-cruise/` | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | `analysis_notes.md`<br>`scraper_todos.md`                   | Consistent with Python/CSV naming, easier for internal use |

### Example Folder Structure
```plaintext
docs/
  routes/
    the-naked-edge.md        # Website-facing page (kebab-case)
    scenic-cruise.md         # Website-facing page (kebab-case)

analysis/
  analysis_notes.md          # Internal notes (snake_case)
  scraper_todos.md           # Internal notes (snake_case)
🔹 Scripts & Data Files
Use snake_case (lowercase with underscores).

Applies to: Python scripts, CSVs, SQL files, etc.

✅ Examples:

scrape_routes.py

joined_route_tick_cleaned.csv

eda_routes.sql

🔹 Images
Use kebab-case (lowercase with hyphens).

This is more web/Markdown friendly and avoids issues with spaces or capitalization.

✅ Examples:

naked-edge.png

scenic-cruise-banner.jpg

🔹 Folders
Use kebab-case (clean and portable across systems and URLs).

✅ Examples:

scripts/

python-visuals/

docs/routes/

🔹 CSV Columns
Use snake_case (SQL/Pandas friendly).

Avoid spaces, special characters, or camelCase.

✅ Examples:

route_name, route_type, fa_year, ffa_year

area_hierarchy, total_ticks, unique_climbers

year_2025, january, is_trending_now

⚡ Rule of Thumb
Code & CSVs → snake_case

Images, Folders, Website Markdown Pages → kebab-case

Internal Markdown Notes → snake_case

💡 Why This Convention?
snake_case: Standard in Python, SQL, and data analysis workflows.

kebab-case: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).

Splitting Markdown conventions keeps internal repo docs consistent with code, while keeping website docs consistent with web standards.


This way the **table shows the rule**, and the **folder tree shows it in action** — making it super easy to follow.  

Do you want me to also add a **“Common mistakes to avoid” box** (like mixing cases in the same folder), so contributors know what *not* to do?
You said:
show the whole completed .md file
ChatGPT said:
Here’s the full completed naming_conventions.md file with everything integrated — Markdown rules, table, folder tree, and your other naming standards:

# 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Markdown File Naming

| Context              | Convention     | Examples                                                    | Result / Purpose                  |
|----------------------|----------------|-------------------------------------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | `the-naked-edge.md` → `/the-naked-edge/`<br>`scenic-cruise.md` → `/scenic-cruise/` | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | `analysis_notes.md`<br>`scraper_todos.md`                   | Consistent with Python/CSV naming, easier for internal use |

### Example Folder Structure
```plaintext
docs/
  routes/
    the-naked-edge.md        # Website-facing page (kebab-case)
    scenic-cruise.md         # Website-facing page (kebab-case)

analysis/
  analysis_notes.md          # Internal notes (snake_case)
  scraper_todos.md           # Internal notes (snake_case)
🔹 Scripts & Data Files
Use snake_case (lowercase with underscores).

Applies to: Python scripts, CSVs, SQL files, etc.

✅ Examples:

scrape_routes.py

joined_route_tick_cleaned.csv

eda_routes.sql

🔹 Images
Use kebab-case (lowercase with hyphens).

This is more web/Markdown friendly and avoids issues with spaces or capitalization.

✅ Examples:

naked-edge.png

scenic-cruise-banner.jpg

🔹 Folders
Use kebab-case (clean and portable across systems and URLs).

✅ Examples:

scripts/

python-visuals/

docs/routes/

🔹 CSV Columns
Use snake_case (SQL/Pandas friendly).

Avoid spaces, special characters, or camelCase.

✅ Examples:

route_name, route_type, fa_year, ffa_year

area_hierarchy, total_ticks, unique_climbers

year_2025, january, is_trending_now

⚡ Rule of Thumb
Code & CSVs → snake_case

Images, Folders, Website Markdown Pages → kebab-case

Internal Markdown Notes → snake_case

💡 Why This Convention?
snake_case: Standard in Python, SQL, and data analysis workflows.

kebab-case: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).

Splitting Markdown conventions keeps internal repo docs consistent with code, while keeping website docs consistent with web standards.

Following these conventions ensures clean, predictable organization across Python, SQL, datasets, and GitHub documentation.


This is now a **ready-to-commit file** that gives both the **rules** and a **visual example** so anyone reading it knows exactly when to use `-` and when to use `_`.  

Would you like me to also add a **“Common mistakes to avoid” section** at the very end (e.g., don’t mix styles in the same folder, don’t capitalize, don’t use spaces)?
You said:
is this better than the prior: # 📖 Naming Conventions

To keep this project consistent, readable, and easy to maintain, all files, folders, and dataset columns follow these conventions.

---

## 🔹 Markdown File Naming

| Context              | Convention     | Examples                                                    | Result / Purpose                  |
|----------------------|----------------|-------------------------------------------------------------|-----------------------------------|
| Website-facing pages | **kebab-case** | the-naked-edge.md → /the-naked-edge/<br>scenic-cruise.md → /scenic-cruise/ | Clean, SEO-friendly URLs on GitHub Pages or docs site |
| Internal notes/docs  | **snake_case** | analysis_notes.md<br>scraper_todos.md                   | Consistent with Python/CSV naming, easier for internal use |

---

## 🔹 Scripts & Data Files
- Use **snake_case** (lowercase with underscores).  
- Applies to: Python scripts, CSVs, SQL files, etc.  
- ✅ Examples:  
  - scrape_routes.py  
  - joined_route_tick_cleaned.csv  
  - eda_routes.sql  

---

## 🔹 Images
- Use **kebab-case** (lowercase with hyphens).  
- This is more web/Markdown friendly and avoids issues with spaces or capitalization.  
- ✅ Examples:  
  - naked-edge.png  
  - scenic-cruise-banner.jpg  

---

## 🔹 Folders
- Use **kebab-case** (clean and portable across systems and URLs).  
- ✅ Examples:  
  - scripts/  
  - python-visuals/  
  - docs/routes/  

---

## 🔹 CSV Columns
- Use **snake_case** (SQL/Pandas friendly).  
- Avoid spaces, special characters, or camelCase.  
- ✅ Examples:  
  - route_name, route_type, fa_year, ffa_year  
  - area_hierarchy, total_ticks, unique_climbers  
  - year_2025, january, is_trending_now  

---

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images, Folders, Website Markdown Pages → kebab-case**  
- **Internal Markdown Notes → snake_case**  

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  
- Splitting Markdown conventions keeps **internal repo docs consistent with code**, while keeping **website docs consistent with web standards**.  
ChatGPT said:
I’d say the version with the folder tree example is better for clarity — because it doesn’t just tell people the rule, it shows them how it looks in practice.

Here’s the comparison:

Your prior version (the one you just pasted)
✅ Pros:

Clean and short.

Covers all categories (scripts, images, folders, CSVs, Markdown).

Easy to skim.

⚠️ Cons:

Someone new might still ask: “Okay, but where do these files actually live?”

The split between kebab/snake in Markdown is explained, but not visualized in context.

The version with the folder tree
✅ Pros:

Same as above, plus a visual anchor showing docs/routes/the-naked-edge.md vs analysis/analysis_notes.md.

Removes ambiguity at a glance — readers don’t have to interpret, they just see the pattern.

Great for contributors or your future self after stepping away for months.

⚠️ Cons:

Slightly longer (adds ~6 lines).

Might feel like overkill if you’re the only one maintaining the repo.

⚡ Recommendation

If this repo is mainly for you → the short version is fine (less to scroll).

If this repo is shared or portfolio-facing → keep the folder tree version, it’s clearer and looks more professional.

👉 Do you want me to tighten up the folder tree version so it stays compact (not too verbose) but still shows the key example?




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
