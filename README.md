# 🇮🇳 Indian Polity Marathon Video Engine

An automated cloud pipeline that generates full-length, high-definition (1080p) marathon revision videos for competitive government exams (**RRB NTPC, SSC CGL / CHSL, State PCS**).

## 🚀 Features
- **Zero Skip Guarantee**: Every historical act (1773 to 1947), constitutional article, landmark court, and previous year question (PYQ) is thoroughly explained.
- **Dual-Host Conversational Dialogue**: Hosted by **Rohan (Male)** and **Priya (Female)** in natural, conversational Hinglish.
- **Cloud-Rendered via GitHub Actions**: No local CPU load or rendering lag. The complete 35–45 minute 1080p video is synthesized in the cloud and attached as a direct download.

## 📂 Structure
- `chapters/chapter_01/`: 16 widescreen slides (`.png`), editable PowerPoint (`.pptx`), and exhaustive conversational dialogue (`script.json`).
- `scripts/render_video.py`: Assembles high-res slides with dual-voice neural audio into a unified 1080p MP4 marathon.
- `.github/workflows/render_chapter_video.yml`: Automated GitHub Actions pipeline.

## 🎬 How to Run
1. Go to the **Actions** tab in this GitHub repository.
2. Select **Render Polity Marathon Video**.
3. Click **Run workflow** (select `chapter_01`).
4. Once completed, download the full MP4 video from the **Artifacts** or **Releases** section!
