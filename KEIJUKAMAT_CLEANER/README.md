## KEIJUKAMAT Cleaner

This folder contains a self-contained cleanup tool for the `KEIJUKAMAT` repo.
Copy the entire `KEIJUKAMAT_CLEANER/` directory into the root of the KEIJUKAMAT repo.

### What it does
- Deletes everything in the repo **except** `docs/`, `.github/`, `.git/`, and `KEIJUKAMAT_CLEANER/`.
- Removes files under `docs/` whose **last git commit** is older than 7 days.
- Prunes empty directories under `docs/`.

### Safety checks
- The script exits if the `origin` remote URL does not contain `KEIJUKAMAT`.

### Install in KEIJUKAMAT
1. Copy this folder into the KEIJUKAMAT repo root.
2. Ensure the workflow exists at:
   `KEIJUKAMAT_CLEANER/.github/workflows/keijukamat_clean.yml`
3. Commit and push to KEIJUKAMAT.

### Manual run (optional)
```bash
python3 KEIJUKAMAT_CLEANER/clean_keijukamat.py
```

