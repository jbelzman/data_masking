# Windows Download and Installation

Windows may mark scripts downloaded from GitHub as internet files. Unblock the ZIP before extracting it so that mark is not copied to every launcher.

## Recommended installation

1. Download the project ZIP from GitHub.
2. In File Explorer, right-click the downloaded ZIP and choose **Properties**.
3. On the **General** tab, select **Unblock** near the bottom, then choose **Apply**.
4. Extract the ZIP to a normal local folder such as Documents or Desktop.
5. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/). Enable **Add Python to PATH** during installation.
6. Double-click `setup.bat`.
7. After setup completes, double-click `run.bat`.

The current `.bat` launchers use standard Command Prompt commands. They do not change PowerShell execution policy.

## If the ZIP was already extracted

Delete the extracted folder, unblock the original ZIP using the steps above, and extract it again. This is usually simpler than unblocking every extracted script.

If Windows still shows a warning:

1. Confirm the ZIP came from the expected GitHub repository.
2. Right-click `setup.bat`, choose **Properties**, and select **Unblock** if shown.
3. Repeat for `run.bat`.

Corporate security software may block all downloaded scripts by policy. In that case, ask IT to approve the repository or run these commands manually from Command Prompt inside the app folder:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Files not to share

Do not upload or distribute `.venv`, source data, masked/restored files, mapper/context files, passwords, or `.maskvault` files.
