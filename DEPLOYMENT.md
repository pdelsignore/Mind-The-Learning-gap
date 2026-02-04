# Deploying to Vercel

## Prerequisites
- A [Vercel account](https://vercel.com/signup)
- A [Claude API key](https://console.anthropic.com/)

## Deployment Steps

### 1. Install Vercel CLI (optional, for command-line deployment)
```bash
npm install -g vercel
```

### 2. Deploy via Vercel Dashboard (recommended)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository (or upload the project folder)
3. Configure the project:
   - Framework Preset: `Other`
   - Root Directory: `./` (or the path to this folder)
4. Add Environment Variable:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Claude API key (starts with `sk-ant-...`)
5. Click **Deploy**

### 3. Deploy via CLI

```bash
cd "project x"
vercel

# When prompted, link to your Vercel account
# Then add the environment variable:
vercel env add ANTHROPIC_API_KEY
# Paste your API key when prompted

# Deploy to production
vercel --prod
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Claude API key from console.anthropic.com |

## Project Structure

```
project x/
├── index-pearson.html    # Main frontend page
├── api/
│   └── analyze.js        # Serverless function (handles Claude API calls)
├── vercel.json           # Vercel configuration
└── DEPLOYMENT.md         # This file
```

## Security Notes

- The API key is stored securely in Vercel's environment variables
- It is never exposed to the client/browser
- All Claude API calls are made server-side through the `/api/analyze` endpoint

## Testing Locally

To test locally before deploying:

```bash
# Install Vercel CLI
npm install -g vercel

# Run local development server
vercel dev
```

This will start a local server (usually at `http://localhost:3000`) that simulates the Vercel environment.

**Note:** You'll need to set up the environment variable locally. Create a `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

(Make sure `.env` is in your `.gitignore` to avoid committing it!)
