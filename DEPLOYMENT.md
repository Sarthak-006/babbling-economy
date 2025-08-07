# Deployment Guide

## GitHub Deployment

1. **Create a GitHub Repository**
   - Go to [GitHub.com](https://github.com)
   - Click the "+" icon and select "New repository"
   - Name it `babbling-economy` or your preferred name
   - Make it public
   - Don't initialize with README (we already have one)
   - Click "Create repository"

2. **Connect Local Repository to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Vercel Deployment

1. **Install Vercel CLI** (optional)
   ```bash
   npm install -g vercel
   ```

2. **Deploy to Vercel**
   - Go to [Vercel.com](https://vercel.com)
   - Sign up/Login with your GitHub account
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will automatically detect it's a Python Flask app
   - Click "Deploy"

3. **Configuration**
   - The `vercel.json` file is already configured
   - Vercel will automatically:
     - Build the Python app
     - Set up the API routes
     - Deploy to a live URL

## Environment Variables (if needed)

If you need to add environment variables later:
- Go to your Vercel project dashboard
- Navigate to Settings > Environment Variables
- Add any required variables

## Custom Domain (optional)

1. Go to your Vercel project dashboard
2. Navigate to Settings > Domains
3. Add your custom domain
4. Follow the DNS configuration instructions

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python api/index.py

# Access at http://localhost:5000
```

## Features Deployed

✅ **Multi-language Support**: Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese
✅ **Interactive Stories**: Choose-your-own-adventure learning
✅ **Vocabulary Building**: Track and learn new words
✅ **Achievement System**: Unlock badges and rewards
✅ **Progress Sharing**: Share achievements on social media
✅ **Responsive Design**: Works on all devices
✅ **Kid-Friendly Interface**: Bright, engaging design

## Testing

After deployment, test all languages:
1. Visit your deployed URL
2. Click the language toggle button
3. Test each language (Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese)
4. Verify that native language text appears with English translations
5. Test the interactive story choices
6. Check that vocabulary words are displayed correctly
