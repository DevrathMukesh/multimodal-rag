# GitHub Pages Demo Site

This directory contains the GitHub Pages site for the Multimodal RAG project demo.

## Structure

- `index.html` - Main demo page with embedded video

## Setup GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Pages** in the sidebar
3. Under **Source**, select:
   - **Deploy from a branch**: `main` branch, `/docs` folder
   - OR if using GitHub Actions workflow (recommended):
     - **GitHub Actions** (the workflow will auto-deploy)

The site will be available at: `https://YOUR_USERNAME.github.io/multimodal-rag/`

## Manual Setup (Alternative)

If you prefer manual deployment:

1. In repository settings → Pages
2. Select **Source**: Deploy from a branch
3. Choose **Branch**: `main`
4. Choose **Folder**: `/docs`

## Video Path

Make sure the video path in `index.html` matches your repository structure:
- Video should be at: `demo/demo.mp4` (repository root)
- HTML references it as: `../demo/demo.mp4` (relative from `/docs`)

