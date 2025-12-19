# 🤖 GitHub Actions Automation Setup

This workflow automatically updates your Strategic Cockpit dashboard data every 15 minutes.

## 📋 Prerequisites

### 1. Add FRED API Key to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `FRED_API_KEY`
   - **Value**: Your FRED API key from [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)

### 2. Verify Repository Permissions

The workflow needs write access to push changes. This is granted by default in the workflow file via:
```yaml
permissions:
  contents: write
```

If you encounter permission errors, check:
1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **"Read and write permissions"**
4. Enable **"Allow GitHub Actions to create and approve pull requests"** (optional)

## 🚀 How It Works

### Automatic Updates (Every 15 Minutes)
The workflow runs automatically every 15 minutes using a cron schedule:
```yaml
schedule:
  - cron: '*/15 * * * *'
```

**Note**: GitHub Actions cron jobs may have a delay of 3-10 minutes during high load times.

### Manual Trigger
You can manually trigger the workflow at any time:
1. Go to the **Actions** tab in your repository
2. Click on **"Update Dashboard Data"** workflow
3. Click **"Run workflow"** button
4. Select the branch (usually `main`)
5. Click **"Run workflow"**

## 🔄 Workflow Steps

1. **Checkout**: Fetches the latest repository code
2. **Setup Python**: Installs Python 3.9
3. **Install Dependencies**: Installs required packages from `requirements.txt`
4. **Run Script**: Executes `fetch_metrics.py` with FRED_API_KEY
5. **Check Changes**: Compares new data with existing `dashboard_data.json`
6. **Commit & Push**: If data changed, commits with timestamp and pushes to `main`

## 📊 Monitoring

### Check Workflow Status
- Go to the **Actions** tab in your repository
- View recent workflow runs and their status (✅ Success / ❌ Failed)
- Click on any run to see detailed logs

### Commit History
Every successful data update creates a commit with the message:
```
data: auto-update 2025-12-18 13:15:00 UTC
```

View these in your repository's commit history.

## 🛠️ Troubleshooting

### Workflow Not Running
- **Problem**: Scheduled jobs aren't triggering
- **Solution**: GitHub disables scheduled workflows in inactive repos. Push a commit or manually trigger once to reactivate.

### Permission Denied Error
- **Problem**: `Permission denied` when pushing
- **Solution**: Check workflow permissions (see Prerequisites #2 above)

### Script Fails
- **Problem**: `fetch_metrics.py` errors
- **Solution**: 
  1. Check the Actions logs for error details
  2. Verify `FRED_API_KEY` secret is set correctly
  3. Test the script locally first

### API Rate Limits
- **FRED**: 120 requests/minute (should be fine)
- **CoinGecko**: 10-50 calls/minute (free tier)
- **DefiLlama**: No official limit, but be reasonable

If you hit rate limits, consider increasing the cron interval (e.g., every 30 minutes: `*/30 * * * *`)

## 🎯 Vercel Auto-Deploy

Since your Vercel deployment is connected to GitHub:

1. **Workflow updates data** → Commits to `main`
2. **GitHub detects commit** → Triggers webhook
3. **Vercel auto-deploys** → Rebuilds with fresh data

This creates a fully automated pipeline! 🎉

## 📝 Customization

### Change Update Frequency
Edit `.github/workflows/update_data.yml`:
```yaml
schedule:
  # Every 30 minutes
  - cron: '*/30 * * * *'
  
  # Every hour
  - cron: '0 * * * *'
  
  # Every 6 hours
  - cron: '0 */6 * * *'
```

### Add Notifications
Add a Discord/Slack notification step if the workflow fails:
```yaml
- name: Notify on failure
  if: failure()
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"content": "⚠️ Dashboard data update failed!"}'
```

## 🔐 Security Best Practices

✅ **DO:**
- Keep API keys in GitHub Secrets (never commit them)
- Use minimal permissions for the GITHUB_TOKEN
- Review workflow logs periodically

❌ **DON'T:**
- Hardcode API keys in the workflow file
- Commit sensitive data to the repository
- Ignore failed workflow notifications

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Expression Generator](https://crontab.guru/)
- [FRED API Docs](https://fred.stlouisfed.org/docs/api/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
