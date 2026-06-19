# Figma Make UI Reference — Personal AI Agent Workspace

## Purpose

This document describes which parts of the Figma Make export should be used as the visual and interaction source of truth for the Personal AI Agent Workspace frontend.

The Figma Make export file is:

```text
docs/design/Create Workspace.make
```

This export contains a React/Vite/TypeScript reference app. It must be used as a UI reference only.

Do not copy it directly into the workspace frontend.

---

## Source of Truth

Use the Figma Make export as the primary UI reference.

Inside the Figma Make export, the most important reference file is:

```text
src/app/App.tsx
```

This file contains the full intended UI structure and interaction model.

Use it as the source of truth for:

* layout
* spacing
* colors
* card proportions
* sidebar structure
* floating window behavior
* horizontal agent lane behavior
* bottom prompt behavior
* collapsed chat history behavior
* Activity Log layout
* Settings layout
* table layout
* visual tone

But do not paste the TSX code directly into the project.

---

## Important Rule

The current workspace frontend stack is:

```text
Next.js App Router
JavaScript
Tailwind
No TypeScript
No tsconfig
Existing API client
Existing auth/protected dashboard
```

The Figma Make export stack is:

```text
React
Vite
TypeScript / TSX
Dummy data
Standalone UI app
```

Therefore:

```text
Use Figma Make as visual reference.
Do not import it as source code.
Do not copy TSX into apps/web.
Do not add TypeScript.
Do not add tsconfig.
Do not copy Vite config.
Do not copy Figma Make package.json.
Do not install dependencies from Figma Make unless explicitly approved.
```

---

## What We Use From Figma Make

Use these parts:

### 1. Color Palette

Use this warm personal workspace palette:

```text
bg:           #F6F1EA
bgDeep:       #EDE6D8
card:         #FDFAF5
cardInner:    #F2EBE0
border:       rgba(90,65,35,0.13)
borderMid:    rgba(90,65,35,0.22)
borderStrong: rgba(90,65,35,0.32)
accent:       #B85C38
accentLight:  rgba(184,92,56,0.10)
text:         #2C2217
textSub:      #5C4E3E
textMuted:    #8A7A68
textDim:      #B8A898
green:        #4E7A5E
greenLight:   rgba(78,122,94,0.12)
amber:        #B07820
amberLight:   rgba(176,120,32,0.12)
```

Visual direction:

```text
warm ivory
soft cream cards
dark brown text
muted terracotta accent
calm personal workspace
not dark dashboard
not AI SaaS template
not cyber/neon
```

---

### 2. Typography Direction

Use the Figma Make typography feel:

```text
Main UI font: Inter-like sans-serif
Workspace logo/title: serif italic style
Small labels: uppercase, letter spaced
Tables/cards: simple readable text
```

The workspace title should feel like:

```text
workspace
```

with a softer italic serif style if available.

Do not spend time adding new font dependencies if not already available. Use existing CSS/font setup where possible.

---

### 3. Main App Layout

The full app layout from Figma Make should be reproduced:

```text
Full viewport app
Header at top
Sidebar on left
Main center area with horizontal agent lane
Bottom main AI prompt bar
Floating draggable windows above workspace
```

Structure:

```text
┌──────────────────────────────────────────────┐
│ Topbar: workspace / user / plan / logout      │
├───────────────┬──────────────────────────────┤
│ Sidebar       │ Agent horizontal lane          │
│               │                                │
│               │                                │
│               │                                │
│               ├──────────────────────────────┤
│               │ Chat drawer collapsed          │
│               │ Bottom main AI prompt bar      │
└───────────────┴──────────────────────────────┘
```

Important:

```text
Agent lane is the main center content.
Main AI Chat History must be collapsed by default.
Bottom prompt stays visible.
Floating windows open above the workspace.
```

---

### 4. Sidebar

Use Figma Make sidebar behavior and style.

Sidebar width reference:

```text
196px
```

Sidebar background:

```text
bgDeep: #EDE6D8
```

Sidebar menu items:

```text
Create Agent
Import Skill
Library Skill
Library Workflow
Workflow n8n
Activity Log
Settings
```

Rules:

```text
Settings stays at the bottom.
Buttons use rounded corners.
Buttons have clear spacing.
Sidebar must not feel like a tiny generic admin panel.
```

The menu should open floating windows, not page sections.

---

### 5. Topbar

Use the Figma Make topbar pattern.

Topbar contains:

```text
workspace
user avatar initial
nama user
FREE badge
Logout button
```

Style:

```text
height: compact
background: bgDeep
border bottom: soft brown border
workspace title: serif italic
user badge: small rounded pill
logout: simple rounded button
```

Avoid duplicate cramped workspace labels.

---

### 6. Floating Window System

Use the Figma Make floating window behavior as the main interaction model.

Every menu panel opens as a draggable floating window.

Floating window requirements:

```text
position: fixed
rounded card
soft shadow
header drag handle
close button
z-index focus when clicked
movable by mouse drag
not fullscreen
not fixed side panel
content scrolls internally
```

Reference floating window style:

```text
border radius: 18px
background: #FDFAF5
header background: #EDE6D8
border: rgba(90,65,35,0.22)
soft shadow
max height: around 82vh
```

Reference window widths:

```text
Create Agent:     560px
Import Skill:     520px
Library Skill:    680px
Library Workflow: 680px
Workflow n8n:     520px
Activity Log:     460px
Settings:         420px
```

Reference initial positions:

```text
Create Agent:     x 230, y 60
Import Skill:     x 290, y 80
Library Skill:    x 210, y 90
Library Workflow: x 250, y 110
Workflow n8n:     x 330, y 75
Activity Log:     x 270, y 60
Settings:         x 310, y 70
```

Behavior:

```text
Click sidebar item:
- if window is not open, open it
- if window already open, bring it to front
- close button removes it
- clicking window brings it to front
```

---

### 7. Horizontal Agent Card Lane

Use the Figma Make agent lane behavior.

Requirements:

```text
Agent cards are arranged horizontally.
The row supports many agents.
The row can be dragged left/right.
The row scrolls horizontally.
Cursor changes to grab/grabbing.
Agent cards are not a static grid.
Agent lane takes the main center workspace.
```

Do not make the agent lane a small top strip.

Agent lane label:

```text
Agents — drag to scroll →
```

Reference lane style:

```text
padding: 18px 20px 0
gap between cards: 14px
overflow-x: auto
scrollbar visually hidden or subtle
```

If there are no real agents from API, show a large friendly empty state inside the agent lane area. Do not let the page become mostly empty.

---

### 8. Agent Card

Use the Figma Make agent card as the visual reference.

Reference card:

```text
width: 196px
border radius: 16px
padding: 14px
background: #FDFAF5
border: rgba(90,65,35,0.13)
vertical layout
```

Agent card contents:

```text
icon / animated icon
status chip
agent name
skill count
skill list
activity list
approval area if needed
small command input at bottom
```

Agent icon:

```text
Use user-uploaded static or animated icon concept.
Allowed formats in UI:
PNG, JPG, WebP, GIF
Do not add SVG/Lottie/HTML support.
```

Skill list example:

```text
convert pdf
convert document
convert excel
```

Activity list example:

```text
idle
sedang convert
sedang mengirim
```

Approval area should appear inside the related agent card, not only in Activity Log.

Approval card content:

```text
Approval Needed
Agent needs permission before continuing.
• use workflow
• attach skill
Approve / Reject
```

Safety note:

```text
Approve / Reject UI can be shown only if existing safe approval logic supports it.
Do not trigger runtime/tool/n8n execution from here.
```

Small command input:

```text
ketik untuk menyuruh agent…
send arrow
```

---

### 9. Main AI Prompt Bar

Use the Figma Make bottom prompt bar.

Behavior:

```text
Always visible at the bottom.
Contains History toggle.
Contains main AI prompt input.
Contains model selector.
Contains send button.
Does not call external model yet.
```

Prompt placeholder:

```text
ini tempat untuk main AI bisa langsung menyuruh lewat prompt…
```

Important:

```text
No external model call.
No runtime execution.
No tool execution.
No n8n execution.
Prompt may remain local/preview-only if runtime is not ready.
```

---

### 10. Main AI Chat History

Use the Figma Make `ChatPanel` behavior.

Important:

```text
Collapsed by default.
chatOpen default must be false.
Only opens when History toggle is clicked.
When open, it appears above the bottom prompt bar.
It must not consume the main center workspace by default.
It must not shrink the agent lane into a small strip.
```

Reference behavior:

```text
max-height: 0 when closed
max-height: around 240px when open
smooth transition around 0.28s
```

Panel title:

```text
Main AI Conversation
```

Example local messages:

```text
You: bantu convert dokumen
Main AI: saya akan arahkan ke agent PDF
You: lanjut
Main AI: menunggu approval sebelum melanjutkan
```

This can be local preview only unless backend conversation endpoint is ready.

---

### 11. Create Agent Floating Window

Use Figma Make `CreateAgentContent`.

Required fields:

```text
Agent Name
Icon
Skills
Brain / Model
pin agent
Create
Preview Agent
```

Icon upload label:

```text
import icon — PNG, JPG, WebP, GIF
```

Preview Agent contains:

```text
icon preview
nama agent
icon
skill 2
brain / model
need setup
ready
```

Do not add runtime behavior here.

Create button may connect to existing safe create-agent API if already wired.

---

### 12. Import Skill Floating Window

Use Figma Make `ImportSkillContent`.

Required fields:

```text
Repository URL
Branch
File Path
Folder Path
preview file path
preview folder path
```

Result card contains:

```text
Skill Name
status
Add
import type
file path
folder path
Content Review
```

Safety:

```text
No repo clone.
No package install.
No script execution.
No auto-approve.
No auto-attach.
```

Use existing safe skill import/preview API only.

---

### 13. Library Skill Floating Window

Use Figma Make table style, but keep our intended columns if supported.

Reference Figma Make compact columns:

```text
nama skill
type
status
agent
action
```

Workspace intended columns:

```text
Nama Skill
Type
Status
Attach Agent
Source URL
Last Update
Action
```

Priority:

```text
Visual style should follow Figma Make table.
Column content should follow workspace requirements where data exists.
```

Table behavior:

```text
search input
Type filter
Status filter
rounded table
alternating soft rows
small action buttons
```

Safe actions only:

```text
View
Review
Attach
Detach
Disable
Edit if existing safe behavior supports it
```

No execution action.

---

### 14. Library Workflow Floating Window

Use the same Figma Make table style as Library Skill.

Reference Figma Make compact columns:

```text
workflow name
trigger
status
agent
action
```

Workspace intended columns:

```text
Workflow Name
Type / Trigger
Status
Attach Agent
Source URL / Workflow ID
Last Update
Action
```

No buttons for:

```text
Run
Execute
Activate
Trigger Now
```

Safe actions only:

```text
View
Edit
Disable
Duplicate
```

---

### 15. Workflow n8n Floating Window

Use Figma Make `WorkflowN8nContent`.

It should be stacked preview cards, not a heavy dashboard/grid.

Each workflow preview card contains:

```text
workflow name
status chip
ID
Agent
Trigger
preview / details area
```

Safety:

```text
No Run button.
No Execute button.
No Activate button.
No Trigger Now button.
No n8n execution call.
```

---

### 16. Activity Log Floating Window

Use Figma Make `ActivityLogContent`.

Style:

```text
timeline / inbox style
not dashboard
not table-heavy
mostly read-only
```

Required:

```text
search activity…
All filter
Today filter
timeline items
```

Each item contains:

```text
time
title
short description
status chip
View Detail button
```

Example items:

```text
21:10 — Skill imported
PDF Helper imported from GitHub
Waiting Review
View Detail

20:45 — Agent updated
Data Agent attached Knowledge Skill
Done
View Detail

20:30 — Safety event
Tool skill blocked from execution
Blocked
View Detail
```

Important:

```text
Do not put primary approval approve/reject actions here.
Primary approval actions belong inside related agent cards.
```

---

### 17. Settings Floating Window

Use Figma Make `SettingsContent`.

Settings must be grouped cards, not a table.

Required sections:

```text
Account / Profile
Brain / Model
API Key Vault
Safety
```

Account / Profile:

```text
Name
Email
Plan
FREE badge
```

Brain / Model:

```text
Default Provider
Default Model
Status: need setup / ready
```

API Key Vault:

```text
Provider name
masked key only
status: encrypted / not setup
Update button
```

Example masked key:

```text
sk-••••••••••••3f2a
```

Safety section:

```text
tool execution: locked
n8n execution: locked
runtime: preview only
```

Workspace should also include if useful:

```text
workflow execution: locked
provider live test: locked
```

Do not show:

```text
Run Tool
Execute n8n
Activate Runtime
Test real model call
Test Connection live call
```

---

## What We Do Not Use From Figma Make

Do not use these directly:

```text
Vite setup
TypeScript / TSX source files
tsconfig
Figma Make package.json
Figma Make pnpm-lock.yaml
Figma Make dependency list
Dummy data as permanent production data
lucide-react dependency if not already installed
raw exported CSS if it conflicts with project Tailwind
```

The dummy arrays in Figma Make are examples only:

```text
AGENTS
SKILL_ROWS
FLOW_ROWS
CHAT_HISTORY
Activity items
API key examples
```

They may be used as visual reference or safe empty-state examples, but should not permanently replace real API data.

---

## Mapping to Workspace Components

Use this mapping when porting manually:

```text
Figma Make App layout
→ apps/web/components/WorkspaceDashboard.js

Figma Make Sidebar / NAV_ITEMS / NavBtn
→ apps/web/components/Sidebar.js

Figma Make top Header
→ apps/web/components/Topbar.js

Figma Make FloatingWindow + useWindowDrag
→ apps/web/components/FloatingCard.js

Figma Make AgentCard + horizontal lane logic
→ WorkspaceDashboard.js or a JavaScript AgentCard component

Figma Make ChatPanel
→ Main AI chat drawer inside WorkspaceDashboard.js or a JS component

Figma Make CreateAgentContent
→ existing Create Agent floating panel content

Figma Make ImportSkillContent
→ existing Import Skill floating panel content

Figma Make LibTable
→ apps/web/components/SimpleTable.js

Figma Make LibrarySkillContent
→ Library Skill floating window content

Figma Make LibraryWorkflowContent
→ Library Workflow floating window content

Figma Make WorkflowN8nContent
→ Workflow n8n floating window content

Figma Make ActivityLogContent
→ apps/web/components/ActivityLogPanelCompact.js

Figma Make SettingsContent
→ apps/web/components/WorkspaceSettingsCompact.js

Figma Make statusChip
→ apps/web/components/StatusBadge.js or local utility
```

---

## Data and API Rules

Keep the real workspace API logic.

Do not replace existing working integrations with dummy data.

Use existing API where available:

```text
agents
skills
skill library
agent skill attach/detach
workflow records
activity logs
model provider settings
model provider API key vault
auth/logout
```

If a UI section has no backend endpoint yet:

```text
show safe placeholder
show preview-only state
report the missing endpoint honestly
do not invent execution behavior
```

---

## Safety Rules

The UI must never expose or call:

```text
runtime execution
tool execution
n8n execution
workflow execute call
provider live test connection
external model call
repo clone
package install
script execution from imported skill
raw API key display
raw secret display
```

No UI buttons for:

```text
Run
Execute
Activate
Trigger Now
Test Connection
Test real model call
```

Allowed safe labels:

```text
Preview
View
Review
Attach
Detach
Disable
Update
Save
Close
History
```

---

## Exact Reproduction Priority

When there is conflict, follow this priority:

```text
1. Figma Make visual and interaction structure
2. docs/design screenshots
3. existing workspace API and safety rules
4. small responsive adjustments
```

Do not invent a new layout.

Do not redesign.

Do not “improve” the UI beyond the Figma Make reference.

The goal is:

```text
same visual structure
same warm style
same floating window behavior
same horizontal agent lane
same collapsed chat behavior
same panel structure
```

---

## Manual Verification Checklist

After implementation, verify in browser:

```text
Sidebar menu order is correct.
Sidebar visually matches Figma Make.
Topbar is simple and not duplicated.
Agent lane is large and central.
Agent cards are horizontal and draggable.
Chat history is collapsed by default.
Bottom prompt bar stays visible.
Clicking History opens chat drawer.
Clicking sidebar opens floating draggable windows.
Floating windows can be moved.
Floating windows can be closed.
Window z-index focus works.
Create Agent window matches reference.
Import Skill window matches reference.
Library Skill table matches reference style.
Library Workflow table matches reference style.
Workflow n8n uses stacked preview cards.
Activity Log uses timeline/inbox style.
Settings uses grouped sections.
No Run/Execute/Activate/Test Connection buttons.
API key is masked only.
No TypeScript files were added.
Frontend lint passes.
Frontend build passes.
```

---

## Notes for Codex

If inspecting `Create Workspace.make`, extract only to a temporary location outside the repo or inspect the zip contents without writing TSX files into the tracked project.

Do not extract `src/app/App.tsx` into `apps/web`.

Do not add any `.ts`, `.tsx`, `.mts`, `.cts`, or `tsconfig.json` file anywhere in the repo.

If a temporary extraction is needed, clean it before final report.
