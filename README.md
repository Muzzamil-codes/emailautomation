# 📬 Discord Email Automation Bot (CrewAI-Powered)

A Discord bot to manage cold leads, personalize outreach, and run email automation with multi-agent AI — all through simple commands.

## ⚙️ Features

- Add/manage leads from Discord
- Store each lead as a JSON file
- Stage/unstage/commit files (Git-style)
- Run email campaigns via CrewAI agents
- Background processing with live Discord updates

## 🚀 Setup

1. **Clone & Install:**

```bash
git clone https://github.com/yourusername/discord-email-bot.git
cd discord-email-bot
pip install uv
uv lock && uv sync
```

2. **Create a .env:**

```env
DISCORD_BOT_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key
```

## 💬 Key Commands

| Command                          | Description          |
| -------------------------------- | -------------------- |
| `DuDe addlead ...`               | Add a new lead       |
| `DuDe listcoldleads`             | List all lead files  |
| `DuDe showlead 1`                | View specific lead   |
| `DuDe add_gmail file.json email` | Add Gmail to a lead  |
| `DuDe stagefile .`               | Stage all leads      |
| `DuDe unstagefile .`             | Unstage all leads    |
| `DuDe commit message="..."`      | Commit staged leads  |
| `DuDe runemailcrew`              | Run email automation |

## For full commands help

```bash
DuDe help_leads
DuDe help_git
```
