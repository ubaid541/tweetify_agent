---
description: How to automate the Tweetify pipeline twice daily with catch-up logic
---

## Objective
Automate the full pipeline (Fetch → Extract → Generate) to run at **6:00 AM** and **8:00 PM** every day, with a built-in safety to "catch up" if your computer was off during a scheduled run.

## Key Components

### 1. The Pipeline Runner (`tools/run_pipeline.py`)
This is the master orchestration script. It handles:
- **Scheduling**: Detects if it's being run by a scheduler or manually.
- **Catch-up**: If more than 14 hours have passed since the last successful run, it triggers immediately on startup.
- **Deduplication**: Only processes today's newsletters and only once per day per sender.
- **Logging**: All activity is tracked in `.tmp/pipeline.log`.

### 2. The Setup Script (`tools/setup_automation.py`)
This script configures your computer to run the pipeline automatically.

---

## Initial Setup

### Windows
1. Open your terminal in the project root.
2. Run the setup script:
   ```bash
   python tools/setup_automation.py
   ```
3. This will create three tasks in your **Task Scheduler**:
   - `Tweetify_Morning`: Runs at 6 AM.
   - `Tweetify_Evening`: Runs at 8 PM.
   - `Tweetify_Catchup`: Runs when you log in (checks if it needs to catch up).

### Linux / Mac
1. Run the setup script:
   ```bash
   python tools/setup_automation.py
   ```
2. Follow the printed instructions to add the lines to your `crontab` and `.bashrc`.

---

## Monitoring and Logs
You can check the status of your automated runs at any time by viewing the log file:
- **Log Path**: `.tmp/pipeline.log`
- **State Path**: `.tmp/state.json` (Stores the last run timestamp)

## Manual Overrides
If you want to force the pipeline to run immediately regardless of the schedule or catch-up logic:
```bash
python tools/run_pipeline.py --force
```

## Moving to a Server
If you move this project to a VPS (always-on server):
1. Copy the entire project folder.
2. Ensure you have your `.env`, `credentials.json`, and `token.json` files.
3. Run `python tools/setup_automation.py` on the server.
4. On a server, the "Catchup" logic isn't strictly necessary but won't hurt.
