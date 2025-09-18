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

## ⚡ Rule of Thumb
- **Code & CSVs → snake_case**  
- **Images & Folders → kebab-case**

---

## 💡 Why This Convention?
- **snake_case**: Standard in Python, SQL, and data analysis workflows.  
- **kebab-case**: Standard for web projects and file paths (works smoothly with GitHub URLs and Markdown).  

Following these conventions ensures clean, predictable code and datasets that work well across Python, SQL, and GitHub documentation.
