# Deploying DifyBaziWorkflow to Raspberry Pi 4B (DietPi OS)

This guide will help you deploy your Python Telegram bot to a Raspberry Pi running DietPi OS.

## Prerequisites

- Raspberry Pi 4B with **DietPi OS** installed.
- Internet connection on the Pi.
- SSH access (default user: `root`, pass: `dietpi`) or terminal access.
- **Python 3** and **Git** (Install via `dietpi-software` if not present: Search IDs `130` and `17`).

## Step 1: Create a Non-Root User (Optional but Recommended)

By default, DietPi uses `root`. It is safer to run the bot as `dietpi` user.
If you are logged in as `root`:

```bash
# Check if dietpi user exists (it usually does)
id dietpi
```

Switch to `dietpi` user or continue as is (adjust paths accordingly). This guide assumes you are using the `dietpi` user.

## Step 2: Transfer Files

### Option A: Using Git (Recommended)
1.  SSH/Login as `dietpi`:
    ```bash
    su - dietpi
    ```
2.  Clone your repository:
    ```bash
    git clone <your-repo-url>
    cd DifyBaziWorkflow
    ```

### Option B: Using SCP
From your local computer:
```bash
scp -r /path/to/DifyBaziWorkflow dietpi@<your-pi-ip>:/home/dietpi/
```

## Step 3: Set Up Virtual Environment

1.  Navigate to the project directory:
    ```bash
    cd /home/dietpi/DifyBaziWorkflow
    ```
2.  Create the virtual environment:
    ```bash
    python3 -m venv venv
    ```
3.  Activate it:
    ```bash
    source venv/bin/activate
    ```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

1.  Create `.env`:
    ```bash
    nano .env
    ```
2.  Paste your secrets:
    ```env
    TOKEN=your_telegram_bot_token_here
    DIFY_WEBHOOK_URL=your_dify_webhook_url_here
    ```
3.  Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## Step 6: Test Manually

```bash
python botScript.py
```
- Send `/start` to your bot.
- `Ctrl+C` to stop.

## Step 7: Set Up Systemd Service (Auto-start)

1.  **Edit `bot.service`** (if needed):
    The included `bot.service` is pre-configured for the `dietpi` user.
    ```bash
    nano bot.service
    ```
    - Ensure `User=dietpi` and `Group=dietpi`.
    - Ensure paths point to `/home/dietpi/DifyBaziWorkflow`.

2.  **Copy to systemd** (requires sudo/root):
    ```bash
    sudo cp bot.service /etc/systemd/system/difybot.service
    ```

3.  **Enable and Start**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable difybot
    sudo systemctl start difybot
    ```

4.  **Check Status**:
    ```bash
    sudo systemctl status difybot
    ```

## Troubleshooting

- **Logs**:
    ```bash
    sudo journalctl -u difybot -f
    ```

