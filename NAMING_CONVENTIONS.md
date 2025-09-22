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
```
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
