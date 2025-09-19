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

Dependencies:
    - pandas
    - numpy
"""
```
## 2. Function-Level Docstring

Each function includes a docstring with:

- **Summary line**: Short description of what the function does.  
- **Blank line**: After the summary for readability.  
- **Args**: List each argument with name, type, and purpose.  
- **Returns**: Specify return type and description.  
- **Raises** (optional): List exceptions the function may raise.

### Example
```python
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw dataset by handling missing values and normalizing column names.

    Args:
        df (pd.DataFrame): Raw input dataframe.

    Returns:
        pd.DataFrame: Cleaned dataframe ready for analysis.

    Raises:
        ValueError: If required columns are missing.
    """
```
## 3. Class Docstrings

Each class includes:
- A short summary describing the purpose of the class.
- (Optional) Attributes: documented with name, type, and description.
- (Optional) Methods: only if non-obvious.

### Example
```python
class DataCleaner:
    """
    A utility class for cleaning raw datasets.

    Attributes:
        rules (dict): Cleaning rules to apply.
    """

    def __init__(self, rules: dict):
        """
        Initialize the DataCleaner with cleaning rules.

        Args:
            rules (dict): Dictionary of column cleaning rules.
        """
        self.rules = rules
```

## 4. General Rules

- Use triple double quotes (""") for all docstrings.
- Keep the first line short (summary), followed by a blank line, then details.
- Use Google style for Args, Returns, and Attributes.
- Document all public functions, classes, and modules.
- Private helpers (_helper_function) may omit docstrings unless non-trivial.

## 5. Enforcement

- Tools to check docstring compliance:
- ruff (recommended, fast linter that checks docstrings and PEP8):
```
pip install ruff
ruff check .
```
- pydocstyle (alternative, checks only docstring rules):
```
pip install pydocstyle
pydocstyle your_script.py
```
## 6. References

- PEP 257 – Docstring Conventions
- Google Python Style Guide – Docstrings