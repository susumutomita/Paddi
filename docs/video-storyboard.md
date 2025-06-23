# Paddi Demo Video Storyboard

## 🎨 Visual Storyboard (3 Minutes)

### Opening (0:00-0:05)
```
┌─────────────────────────────────┐
│                                 │
│         PADDI                   │
│   AI-Driven Security Audit      │
│                                 │
│   [Logo Animation]              │
│                                 │
└─────────────────────────────────┘
```
**Audio:** Intro music fade in
**Effect:** Logo reveal with particle effect

### Scene 1: Problem (0:05-0:30)
```
┌─────────────────────────────────┐
│  [Security Engineer at desk]    │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Excel │ │Docs  │ │Manual│   │
│  │Sheet │ │      │ │Work  │   │
│  └──────┘ └──────┘ └──────┘   │
│          ↓                      │
│    ⏰ Time Consuming            │
│    ❌ Error Prone              │
│    💸 Expensive                │
└─────────────────────────────────┘
```
**Transition:** Fade to next scene
**Caption:** "従来の手動監査の課題"

### Scene 2: Solution Architecture (0:30-1:00)
```
┌─────────────────────────────────┐
│        Paddi Architecture       │
│                                 │
│  ┌─────────┐                   │
│  │   CLI   │ (Python Fire)     │
│  └────┬────┘                   │
│       ↓                         │
│  ┌─────────┐ → ┌──────────┐ → ┌────────┐
│  │Collector│   │Explainer │   │Reporter│
│  │ Agent   │   │  Agent   │   │ Agent  │
│  └─────────┘   └──────────┘   └────────┘
│       ↓             ↓               ↓
│   [GCP APIs]   [Gemini AI]    [Reports]
└─────────────────────────────────┘
```
**Animation:** Flow animation between agents
**Highlight:** Gemini AI integration

### Scene 3-4: Terminal Setup (1:00-1:30)
```
┌─────────────────────────────────┐
│  Terminal                   □×  │
├─────────────────────────────────┤
│ $ cd ~/projects/paddi-demo      │
│ $ ls -la                        │
│ total 24                        │
│ drwxr-xr-x  .                  │
│ -rw-r--r--  paddi.toml         │
│ -rw-r--r--  README.md          │
│                                 │
│ $ python main.py init           │
│ Welcome to Paddi! 🚀            │
│ Select cloud provider:          │
│ > gcp                          │
│   aws                          │
│   azure                        │
└─────────────────────────────────┘
```
**Effect:** Terminal typing animation
**Focus:** Interactive setup process

### Scene 5: Live Analysis (1:30-2:00)
```
┌─────────────────────────────────┐
│  Terminal                   □×  │
├─────────────────────────────────┤
│ $ python main.py audit --project-id example-project │
│                                 │
│ 🔍 Starting security audit...   │
│                                 │
│ ✓ Collecting IAM policies      │
│   └─ Found 47 policies         │
│ ✓ Fetching SCC findings        │
│   └─ Found 12 findings         │
│ ✓ Analyzing with Gemini AI     │
│   ├─ HIGH: 3 issues            │
│   ├─ MEDIUM: 5 issues          │
│   └─ LOW: 4 issues             │
│ ✓ Generating reports           │
│                                 │
│ ✅ Audit completed in 47s      │
└─────────────────────────────────┘
```
**Animation:** Progress indicators
**Sound:** Success chime on completion

### Scene 6: Report Display (2:00-2:20)
```
Split Screen View:
┌────────────────┬────────────────┐
│  Browser       │  VS Code       │
├────────────────┼────────────────┤
│ Paddi Report   │ # Audit Report │
│                │                │
│ ⚠️ HIGH Risk   │ ## High Risk   │
│ • Owner Role   │ ### Owner Role │
│   Excessive    │ This account.. │
│                │                │
│ ⚡ MEDIUM Risk │ ## Medium Risk │
│ • Public       │ ### Public     │
│   Storage      │ Storage bucket │
└────────────────┴────────────────┘
```
**Effect:** Smooth scroll through reports
**Highlight:** AI-generated explanations

### Scene 7: Multi-Cloud & CI/CD (2:20-2:30)
```
┌─────────────────────────────────┐
│     Multi-Cloud Support         │
│                                 │
│  ┌─────┐  ┌─────┐  ┌─────┐    │
│  │ GCP │  │ AWS │  │Azure│    │
│  └──┬──┘  └──┬──┘  └──┬──┘    │
│     └────────┴────────┘        │
│              ↓                  │
│         ┌─────────┐            │
│         │  Paddi  │            │
│         └────┬────┘            │
│              ↓                  │
│     GitHub Actions CI/CD        │
└─────────────────────────────────┘
```
**Animation:** Logo transitions
**Caption:** "マルチクラウド対応"

### Scene 8: Impact (2:30-2:50)
```
┌─────────────────────────────────┐
│         Before vs After         │
│                                 │
│  Before:          After:        │
│  📅 3-5 days     ⚡ 5 minutes  │
│  👥 2-3 people   🤖 Automated  │
│  📝 Manual       📊 AI-Powered │
│  ❌ Error risk   ✅ Consistent │
│                                 │
│      Time Saved: 99.8%         │
└─────────────────────────────────┘
```
**Animation:** Number counter animation
**Effect:** Celebration particles

### Closing (2:50-3:00)
```
┌─────────────────────────────────┐
│                                 │
│         PADDI                   │
│                                 │
│  github.com/susumutomita/Paddi  │
│                                 │
│  Built for AI Agent Hackathon   │
│  Powered by Gemini AI           │
│                                 │
│         [QR Code]               │
└─────────────────────────────────┘
```
**Audio:** Music fade out
**Effect:** QR code animation

---

## 🎨 Visual Style Guide

### Color Palette
- Primary: #4285F4 (Google Blue)
- Secondary: #34A853 (Google Green)
- Warning: #FBBC05 (Google Yellow)
- Danger: #EA4335 (Google Red)
- Background: #1A1A1A (Dark)
- Text: #FFFFFF (White)

### Typography
- Headers: Google Sans or Inter
- Terminal: JetBrains Mono or Fira Code
- Body: Roboto

### Animations
- Transitions: 0.3s ease-in-out
- Terminal typing: 50ms per character
- Progress bars: Smooth linear
- Logo reveals: Scale + fade

### Screen Layout
- 16:9 aspect ratio (1920x1080)
- Safe margins: 10% on all sides
- Terminal font size: 16-18pt
- Consistent padding: 24px

### Visual Effects
- Subtle shadows for depth
- Gradient overlays for sections
- Particle effects for celebrations
- Smooth scrolling for reports
- Highlight important text with glow