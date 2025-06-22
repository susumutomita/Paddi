# Video Production Guide for Paddi Demo

## 🎯 Quick Checklist

- [ ] Install OBS Studio or similar screen recording software
- [ ] Set up terminal with proper font size and theme
- [ ] Prepare demo environment with sample data
- [ ] Record narration separately for better quality
- [ ] Edit to exactly 3:00 duration
- [ ] Add captions and visual effects
- [ ] Export as MP4 with proper settings

## 🛠️ Required Tools

### Recording Software
- **OBS Studio** (Free, recommended)
  - Download: https://obsproject.com/
  - Settings: 1920x1080, 30fps, 5000kbps bitrate

### Video Editing
- **DaVinci Resolve** (Free)
  - Professional features
  - Good for color grading
- **OpenShot** (Free, simpler)
  - Easy to use
  - Good for basic editing

### Audio
- **Audacity** (Free)
  - For recording/editing narration
  - Noise reduction capabilities

## 📋 Pre-Production Setup

### 1. Terminal Configuration
```bash
# Install a good terminal font
# macOS
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono

# Linux
sudo apt install fonts-jetbrains-mono

# Configure terminal
# - Font: JetBrains Mono, 16-18pt
# - Theme: Dark (Dracula, One Dark, etc.)
# - Window size: 1280x720 minimum
```

### 2. Demo Data Preparation
```bash
# Create demo directory
mkdir -p ~/projects/paddi-demo
cd ~/projects/paddi-demo

# Copy sample configuration
cp /path/to/paddi/paddi.example.toml paddi.toml

# Prepare sample GCP data
cp /path/to/paddi/examples/gcp_sample.json data/
```

### 3. OBS Scene Setup

Create these scenes in OBS:

1. **Intro Scene**
   - Image: Paddi logo
   - Text: Title overlay
   - Duration: 5 seconds

2. **Terminal Scene**
   - Source: Window Capture (Terminal)
   - Filter: Crop to remove window decorations
   - Background: Solid color (#1A1A1A)

3. **Browser Scene**
   - Source: Window Capture (Browser)
   - Show HTML report

4. **Split Screen Scene**
   - Sources: Browser (left) + VS Code (right)
   - Border: 2px white line between

5. **Outro Scene**
   - Image: Paddi logo
   - Text: GitHub URL, QR code
   - Duration: 10 seconds

## 🎬 Recording Process

### Step 1: Record Terminal Segments
1. Practice commands first
2. Record each scene separately
3. Keep recordings longer than needed (trim in editing)

### Step 2: Record Narration
1. Use a quiet room
2. Keep microphone 6-8 inches from mouth
3. Record in segments matching video scenes
4. Leave pauses for editing

### Step 3: Capture Screenshots
- HTML report (full page)
- Markdown in VS Code
- Architecture diagram
- Before/after comparison

## ✂️ Editing Workflow

### Timeline Structure
```
00:00-00:05  Intro animation
00:05-00:30  Problem introduction (voiceover + visuals)
00:30-01:00  Solution overview (architecture diagram)
01:00-01:30  Terminal demo part 1 (setup)
01:30-02:00  Terminal demo part 2 (analysis)
02:00-02:20  Report showcase (split screen)
02:20-02:30  Multi-cloud & CI/CD
02:30-03:00  Impact & closing
```

### Transitions
- Use 0.3s cross-dissolve between scenes
- Terminal typing: speed up 2x if needed
- Zoom in on important parts

### Text Overlays
```
Font: Google Sans or Inter
Size: 48pt for titles, 32pt for subtitles
Color: White with black shadow
Position: Lower third or center
```

### Audio Mixing
- Narration: -6dB
- Background music: -18dB (duck during speech)
- Sound effects: -12dB

## 🎨 Visual Effects

### Terminal Enhancement
```python
# Example After Effects expression for typing effect
text.sourceText.slice(0, time * 30)
```

### Progress Indicators
- Use animated bars or circles
- Color code: Green (complete), Blue (in progress)

### Highlighting
- Add glow effect to important text
- Use arrows or boxes to point out features

## 📤 Export Settings

### Video
- Format: H.264/MP4
- Resolution: 1920x1080
- Frame rate: 30fps
- Bitrate: 5-10 Mbps
- Profile: High

### Audio
- Codec: AAC
- Sample rate: 48kHz
- Bitrate: 192kbps
- Channels: Stereo

### Final Checklist
- [ ] Exactly 3:00 duration
- [ ] All text is readable
- [ ] Audio levels are consistent
- [ ] No typos in captions
- [ ] Smooth transitions
- [ ] Proper credits

## 🚀 Tips for Success

1. **Practice First**
   - Do a full run-through before recording
   - Time each section carefully

2. **Keep It Simple**
   - Don't overuse effects
   - Focus on clarity over complexity

3. **Show Real Value**
   - Emphasize time savings
   - Show actual AI output
   - Highlight ease of use

4. **Technical Details**
   - Show actual commands
   - Display real output
   - Include error handling

5. **Professional Polish**
   - Consistent styling
   - Smooth animations
   - Clear narration

## 📱 Thumbnail Creation

Create an eye-catching thumbnail:
- Size: 1280x720px
- Include: Paddi logo, "AI Security Audit", "3 min demo"
- Use bright colors that stand out
- Add subtle effects like gradients or glows

## 🎵 Music Resources

Free music sources:
- YouTube Audio Library
- Free Music Archive
- Incompetech
- Bensound

Choose instrumental tracks that are:
- Professional/corporate style
- Not distracting
- Properly licensed

## 📝 Submission Notes

For the hackathon submission:
1. Upload to YouTube as "Unlisted"
2. Enable captions
3. Add timestamps in description
4. Include GitHub link
5. Tag with hackathon name

Remember: The video should demonstrate not just what Paddi does, but WHY it's valuable and HOW it solves real problems using AI.