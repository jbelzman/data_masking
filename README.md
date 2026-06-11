# Local Data Masking Tool

A local Windows and macOS desktop app for preparing CSV and Excel data for AI analysis without exposing sensitive dimension values.

## Features

- Batch-select dimensions and numeric metrics.
- Mask selected dimensions with keyed HMAC-SHA256.
- Aggregate metrics with sum, average, minimum, maximum, or count.
- Store lookup mappings in a separate password-encrypted `.maskvault`.
- Restore authorized data with strict masked-file and vault matching.
- Include a `Mapper` tab in restored Excel workbooks.
- Add an optional AI context layer explaining what dimensions represent.
- Keep the complete Mask workflow accessible with a master scrollbar.

## Output

### Excel masking

- `Masked_Data`: masked and aggregated data.
- `Context_Layer`: optional AI-facing context.
- Separate `.maskvault`: encrypted lookup mappings and masking key.

### Excel restoration

- `Restored_Data`: original dimension values restored.
- `Mapper`: dimension name, masked value, and original value.

CSV output uses companion `_context.txt` and `_mapper.csv` files because CSV does not support tabs.

## Security model

- Processing is local; the app does not upload data.
- Each masking job receives a fresh random key.
- Masked output and the vault must be saved in different folders.
- The vault password is never saved or logged.
- A mismatched vault is rejected instead of producing a partially restored file.

Keep the vault and password separate from the masked output. Do not include sensitive values in the context layer.

## How AI was used to build this

This tool was designed and built in active collaboration with Claude. AI wasn't used just for boilerplate — it shaped the core architecture.

**Security architecture.** Early versions offered selectable hash algorithms (MD5, SHA-256, SHA-512). Working through the threat model with Claude surfaced the dictionary-attack vulnerability of unsalted hashes against predictable values like campaign names and placement labels. That analysis led directly to the keyed HMAC-SHA256 approach with a per-job random key.

**The vault model.** The original design combined masked data and lookup keys in a single workbook — convenient, but it puts "safe to share" and "never share" material in the same file. Claude helped reason through the threat model and spec the separate encrypted `.maskvault` design that ships in v2.0.

**UI and workflow design.** The scrollable blue-and-white interface, the batch column selection model, the dimension/metric/ignore role system, show/hide password controls, and the bottom status bar were all built iteratively with Claude — adjusting after seeing each version run.

**The AI Context Layer.** Claude drafted the auto-generated starter text that seeds the context blurb from actual column names in the loaded file. The goal: give users something concrete to edit instead of a blank textarea, while keeping the prompt tight enough that they won't accidentally include real values.

**Documentation.** The user guide and release notes were drafted with Claude from a working spec, then reviewed and corrected against actual app behavior.

The result is a production-ready workflow that lets analysts share masked data with AI tools — passing sensitive column names through HMAC, adding plain-language context about what masked dimensions represent, and restoring original values locally when needed. No sensitive identifiers leave the machine.

## Run on Windows

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/) and enable **Add Python to PATH**.
2. Double-click `setup.bat` once.
3. Double-click `run.bat` whenever you want to open the app.

## Run on macOS

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/macos/).
2. In Terminal, open the project folder and run:

```bash
chmod +x setup.command run.command setup-mac.sh run-mac.sh
./setup.command
```

3. After setup, double-click `run.command` or run `./run.command` in Terminal.

If Gatekeeper blocks a launcher, use **System Settings > Privacy & Security > Open Anyway**. If a `.command` file opens in a text editor, right-click it and choose **Open With > Terminal**, or run it from Terminal.

## Share the app

Create a ZIP containing:

- `app.py`
- `masking_tool/`
- `requirements.txt`
- Windows launchers: `setup.bat`, `run.bat`, `setup.ps1`, `run.ps1`
- macOS launchers: `setup.command`, `run.command`, `setup-mac.sh`, `run-mac.sh`
- `README.md`
- `Local Data Masking Tool User Guide v2.0.docx`

Do not include `.venv/`, `.testdeps/`, `__pycache__/`, source data, output data, context files, mapper files, or `.maskvault` files.

See [Local Data Masking Tool User Guide v2.0.docx](Local%20Data%20Masking%20Tool%20User%20Guide%20v2.0.docx) for detailed instructions.

## Test

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Important limitation

Masking reduces exposure but does not automatically anonymize a dataset. Review free-text fields, dates, rare combinations, and small groups before sharing data.
