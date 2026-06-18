# cadre-sonde

Radiosonde profile diagnostics using
[PyGSI](https://github.com/NOAA-EMC/PyGSI).

This repository provides a Jupyter notebook and supporting scripts to:

1. **Download** GSI conventional diagnostic netCDF4 files from a remote server.
2. **Load** the files with the PyGSI `Conventional` class.
3. **Filter** data to a specific radiosonde station.
4. **Plot** vertical profiles (as a function of pressure) of:
   - Temperature (K)
   - Specific humidity (g/kg)
   - U-wind and V-wind (m/s)

   For each variable the following quantities are shown:
   - Observation (Obs)
   - Observation minus background / first guess (O-F)
   - Observation minus analysis (O-A)
   - Model background equivalent H(x)

---

## Repository layout

```
cadre-sonde/
├── .devcontainer/
│   └── devcontainer.json      # GitHub Codespace configuration
├── notebooks/
│   └── radiosonde_profile.ipynb  # Main analysis notebook
├── scripts/
│   └── download_diag.py       # Script to download GSI diagnostic files
├── requirements.txt           # Python dependencies
├── DISCLAIMER
└── LICENSE
```

---

## Quick start — GitHub Codespace (recommended)

GitHub Codespaces provides a fully configured cloud development environment
with zero local setup.

### Steps

1. On the repository page, click the green **Code** button.
2. Select the **Codespaces** tab.
3. Click **Create codespace on main** (or your branch).
4. Wait for the container to build (~2 minutes on first launch).  
   The `postCreateCommand` in `.devcontainer/devcontainer.json` will
   automatically run:
   ```bash
   pip install -r requirements.txt
   ```
5. Open `notebooks/radiosonde_profile.ipynb` in the VS Code Jupyter
   extension that is pre-installed in the Codespace.
6. Set the `DIAG_BASE_URL` environment variable (or edit the `BASE_URL`
   variable inside the first configuration cell) to point to the server
   that hosts your GSI diagnostic files.
7. Run all cells.

> **Tip:** To persist `DIAG_BASE_URL` across Codespace sessions, add it
> as a **Codespace secret** under
> *Settings → Codespaces → Secrets* in your GitHub account.

---

## Quick start — local setup

### Prerequisites

- Python ≥ 3.10
- `pip`

### Install

```bash
git clone https://github.com/CoryMartin-NOAA/cadre-sonde.git
cd cadre-sonde
pip install -r requirements.txt
```

### Run the notebook

```bash
jupyter notebook notebooks/radiosonde_profile.ipynb
```

---

## Downloading diagnostic files

### Via the notebook

Set `BASE_URL` in the configuration cell of
`notebooks/radiosonde_profile.ipynb` and run **Cell 2**.

### Via the command-line script

```bash
python scripts/download_diag.py \
    --date 2020092000 \
    --variables t q uv \
    --ftypes ges anl \
    --base-url https://example.com/gsi_diags \
    --outdir ./data
```

The script downloads:

| Variable | File type | File name |
|----------|-----------|-----------|
| Temperature | first guess | `diag_conv_t_ges.YYYYMMDDHH.nc4` |
| Temperature | analysis | `diag_conv_t_anl.YYYYMMDDHH.nc4` |
| Specific humidity | first guess | `diag_conv_q_ges.YYYYMMDDHH.nc4` |
| Specific humidity | analysis | `diag_conv_q_anl.YYYYMMDDHH.nc4` |
| Wind (U/V) | first guess | `diag_conv_uv_ges.YYYYMMDDHH.nc4` |
| Wind (U/V) | analysis | `diag_conv_uv_anl.YYYYMMDDHH.nc4` |

Run `python scripts/download_diag.py --help` for all options.

---

## Configuration options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CYCLE_DATE` | `"2020092000"` | Cycle date-time (`YYYYMMDDHH`) |
| `STATION_ID` | `"72469"` | WMO / BUFR station ID |
| `BASE_URL` | `""` (reads `DIAG_BASE_URL` env var) | Remote server base URL |
| `DATA_DIR` | `../data` | Local directory for downloaded files |

---

## GSI diagnostic file naming convention

```
diag_conv_<variable>_<ftype>.<YYYYMMDDHH>.nc4
```

- `<variable>`: `t` (temperature), `q` (specific humidity), `uv` (wind), `ps` (surface pressure)
- `<ftype>`: `ges` (6-hour first guess → used for O-F) or `anl` (analysis → used for O-A)

---

## DISCLAIMER

This project is provided on an "as is" basis.
The user assumes all responsibility for its use.

See [DISCLAIMER](DISCLAIMER) and [LICENSE](LICENSE) for details.
