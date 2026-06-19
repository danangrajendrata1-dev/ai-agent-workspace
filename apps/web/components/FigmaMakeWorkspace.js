"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import ProtectedRoute from "./ProtectedRoute";
import { clearToken } from "../lib/auth";
import { getCurrentUser } from "../lib/apiClient";

const C = {
  bg: "#F6F1EA",
  bgDeep: "#EDE6D8",
  card: "#FDFAF5",
  cardInner: "#F2EBE0",
  border: "rgba(90,65,35,0.13)",
  borderMid: "rgba(90,65,35,0.22)",
  accent: "#B85C38",
  accentLight: "rgba(184,92,56,0.10)",
  text: "#2C2217",
  textSub: "#5C4E3E",
  textMuted: "#8A7A68",
  textDim: "#B8A898",
  green: "#4E7A5E",
  greenLight: "rgba(78,122,94,0.12)",
  amber: "#B07820",
  amberLight: "rgba(176,120,32,0.12)"
};

const FONT = {
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
};
const SERIF = {
  fontFamily: '"Instrument Serif", Georgia, "Times New Roman", serif',
  fontStyle: "italic"
};

const NAV_ITEMS = [
  { id: "create-agent", label: "Create Agent", icon: "plus" },
  { id: "import-skill", label: "Import Skill", icon: "upload" },
  { id: "library-skill", label: "Library Skill", icon: "book" },
  { id: "library-workflow", label: "Library Workflow", icon: "workflow" },
  { id: "workflow-n8n", label: "Workflow n8n", icon: "nodes" },
  { id: "activity-log", label: "Activity Log", icon: "activity" }
];

const WIN_META = {
  "create-agent": { title: "Create Agent", width: 560, ix: 230, iy: 60 },
  "import-skill": { title: "Import Skill", width: 520, ix: 290, iy: 80 },
  "library-skill": { title: "Library Skill", width: 680, ix: 210, iy: 90 },
  "library-workflow": { title: "Library Workflow", width: 680, ix: 250, iy: 110 },
  "workflow-n8n": { title: "Workflow n8n", width: 520, ix: 330, iy: 75 },
  "activity-log": { title: "Activity Log", width: 460, ix: 270, iy: 60 },
  settings: { title: "Settings", width: 420, ix: 310, iy: 70 }
};

const PREVIEW_AGENTS = [
  {
    id: 1,
    name: "Doc Converter",
    icon: "DC",
    skillCount: 3,
    skills: ["convert pdf", "convert document", "convert excel"],
    status: "idle",
    activity: ["idle", "sedang convert", "sedang mengirim"],
    needApproval: false
  },
  {
    id: 2,
    name: "Mail Agent",
    icon: "MA",
    skillCount: 3,
    skills: ["draft email", "send report", "schedule send"],
    status: "sending",
    activity: ["queue", "draft ready", "waiting send"],
    needApproval: true
  },
  {
    id: 3,
    name: "Data Parser",
    icon: "DP",
    skillCount: 3,
    skills: ["parse json", "extract csv", "transform xml"],
    status: "active",
    activity: ["parse json", "extract csv", "transform xml"],
    needApproval: false
  },
  {
    id: 4,
    name: "Summarizer",
    icon: "SU",
    skillCount: 3,
    skills: ["summarize doc", "extract key pts", "generate tldr"],
    status: "idle",
    activity: ["idle", "draft summary", "review tldr"],
    needApproval: false
  },
  {
    id: 5,
    name: "Notifier",
    icon: "NO",
    skillCount: 3,
    skills: ["slack notify", "webhook push", "log event"],
    status: "active",
    activity: ["slack notify", "webhook push", "log event"],
    needApproval: false
  },
  {
    id: 6,
    name: "Translator",
    icon: "TR",
    skillCount: 2,
    skills: ["translate text", "detect language"],
    status: "idle",
    activity: ["idle", "review phrase", "translate id-en"],
    needApproval: false
  },
  {
    id: 7,
    name: "Scheduler",
    icon: "SC",
    skillCount: 2,
    skills: ["schedule task", "set reminder"],
    status: "idle",
    activity: ["idle", "queue task", "set reminder"],
    needApproval: false
  }
];

const CHAT_HISTORY = [
  { role: "You", text: "bantu convert dokumen" },
  { role: "Main AI", text: "saya akan arahkan ke agent PDF" },
  { role: "You", text: "lanjut" },
  { role: "Main AI", text: "menunggu approval sebelum melanjutkan" }
];

const SKILL_ROWS = [
  { name: "PDF Helper", type: "file", status: "active", agent: "Doc Converter" },
  { name: "Excel Parser", type: "file", status: "review", agent: "Data Parser" },
  { name: "Mail Draft", type: "function", status: "active", agent: "Mail Agent" },
  { name: "Webhook Push", type: "function", status: "inactive", agent: "Notifier" }
];

const FLOW_ROWS = [
  { name: "Daily Report", type: "schedule", status: "active", agent: "Doc Converter" },
  { name: "Approval Gate", type: "webhook", status: "review", agent: "Mail Agent" },
  { name: "Data Sync", type: "manual", status: "inactive", agent: "Data Parser" }
];

const N8N_ROWS = [
  { name: "Daily Report", id: "wf_001", agent: "Doc Converter", trigger: "schedule", status: "active" },
  { name: "Approval Gate", id: "wf_002", agent: "Mail Agent", trigger: "webhook", status: "review" },
  { name: "Data Sync", id: "wf_003", agent: "Data Parser", trigger: "manual", status: "inactive" }
];

const ACTIVITY_ROWS = [
  { time: "21:10", title: "Skill imported", desc: "PDF Helper imported from GitHub", status: "Waiting Review", tone: "review" },
  { time: "20:45", title: "Agent updated", desc: "Data Agent attached Knowledge Skill", status: "Done", tone: "active" },
  { time: "20:30", title: "Safety event", desc: "Tool skill blocked from execution", status: "Blocked", tone: "inactive" },
  { time: "19:55", title: "Workflow added", desc: "Daily Report linked to Doc Converter", status: "Preview", tone: "inactive" }
];

const SETTINGS_KEYS = [
  { provider: "OpenAI", masked: "sk-************3f2a", status: "encrypted" },
  { provider: "OpenRouter", masked: "not set", status: "not setup" }
];

function SvgIcon({ children, size = 15 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

function MenuIcon({ name }) {
  switch (name) {
    case "plus":
      return (
        <SvgIcon>
          <path d="M12 5v14" />
          <path d="M5 12h14" />
        </SvgIcon>
      );
    case "upload":
      return (
        <SvgIcon>
          <path d="M12 16V6" />
          <path d="m8 10 4-4 4 4" />
          <path d="M5 18h14" />
        </SvgIcon>
      );
    case "book":
      return (
        <SvgIcon>
          <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H20v15.5a.5.5 0 0 1-.8.4C18 19.2 16.5 18 14 18c-2.7 0-4.1 1.3-5.2 1.9a.5.5 0 0 1-.8-.4V6.5Z" />
          <path d="M8 7h8" />
          <path d="M8 10h8" />
        </SvgIcon>
      );
    case "workflow":
      return (
        <SvgIcon>
          <circle cx="6" cy="6" r="2.5" />
          <circle cx="18" cy="12" r="2.5" />
          <circle cx="6" cy="18" r="2.5" />
          <path d="M8.5 7.5 15.5 10.5" />
          <path d="M8.5 16.5 15.5 13.5" />
        </SvgIcon>
      );
    case "nodes":
      return (
        <SvgIcon>
          <rect x="3.5" y="4.5" width="5" height="5" rx="1.2" />
          <rect x="15.5" y="4.5" width="5" height="5" rx="1.2" />
          <rect x="9.5" y="14.5" width="5" height="5" rx="1.2" />
          <path d="M8.5 7h7" />
          <path d="M12 9.5v5" />
        </SvgIcon>
      );
    case "activity":
      return (
        <SvgIcon>
          <path d="M3 12h4l2.2-5 4.2 10 2.2-5H21" />
        </SvgIcon>
      );
    case "settings":
      return (
        <SvgIcon>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a1.9 1.9 0 1 1-2.7 2.7l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a1.9 1.9 0 1 1-3.8 0v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a1.9 1.9 0 1 1-2.7-2.7l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a1.9 1.9 0 1 1 0-3.8h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a1.9 1.9 0 1 1 2.7-2.7l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a1.9 1.9 0 1 1 3.8 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a1.9 1.9 0 1 1 2.7 2.7l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6h.2a1.9 1.9 0 1 1 0 3.8h-.2a1 1 0 0 0-.9.6Z" />
        </SvgIcon>
      );
    case "logout":
      return (
        <SvgIcon>
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="M16 17l5-5-5-5" />
          <path d="M21 12H9" />
        </SvgIcon>
      );
    default:
      return null;
  }
}

function useWindowDrag(ix, iy) {
  const [pos, setPos] = useState({ x: ix, y: iy });
  const active = useRef(false);
  const offset = useRef({ x: 0, y: 0 });

  useEffect(() => {
    function handleMove(event) {
      if (!active.current) return;
      setPos({
        x: Math.max(16, event.clientX - offset.current.x),
        y: Math.max(16, event.clientY - offset.current.y)
      });
    }

    function handleUp() {
      active.current = false;
    }

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, []);

  function handleDown(event) {
    active.current = true;
    offset.current = {
      x: event.clientX - pos.x,
      y: event.clientY - pos.y
    };
  }

  return { pos, handleDown };
}

function Label({ text }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        color: C.textMuted,
        marginBottom: 5,
        textTransform: "uppercase",
        letterSpacing: "0.05em"
      }}
    >
      {text}
    </div>
  );
}

function InputField({ label, placeholder }) {
  return (
    <div style={{ marginBottom: 10 }}>
      {label ? <Label text={label} /> : null}
      <input
        placeholder={placeholder}
        style={{
          width: "100%",
          padding: "9px 12px",
          borderRadius: 10,
          border: `1.5px solid ${C.border}`,
          background: C.cardInner,
          color: C.text,
          fontSize: 13,
          outline: "none",
          boxSizing: "border-box",
          ...FONT
        }}
      />
    </div>
  );
}

function DropField({ label, placeholder }) {
  return (
    <div style={{ marginBottom: 10 }}>
      {label ? <Label text={label} /> : null}
      <div
        style={{
          padding: "9px 12px",
          borderRadius: 10,
          border: `1.5px solid ${C.border}`,
          background: C.cardInner,
          color: C.textMuted,
          fontSize: 13,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer"
        }}
      >
        <span>{placeholder}</span>
        <span style={{ color: C.textDim }}>v</span>
      </div>
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 12,
        background: C.bgDeep,
        border: `1px solid ${C.border}`,
        ...style
      }}
    >
      {children}
    </div>
  );
}

function statusStyle(status) {
  const map = {
    active: { color: C.green, background: C.greenLight },
    review: { color: C.amber, background: C.amberLight },
    inactive: { color: C.textDim, background: "rgba(0,0,0,0.05)" },
    idle: { color: C.textDim, background: "rgba(0,0,0,0.05)" },
    sending: { color: C.green, background: C.greenLight },
    encrypted: { color: C.green, background: C.greenLight },
    "not setup": { color: C.textDim, background: "rgba(0,0,0,0.05)" },
    "need setup": { color: C.amber, background: C.amberLight },
    ready: { color: C.green, background: C.greenLight },
    locked: { color: C.textMuted, background: "rgba(0,0,0,0.06)" },
    "preview only": { color: C.textMuted, background: "rgba(0,0,0,0.06)" }
  };

  return {
    fontSize: 11,
    fontWeight: 600,
    padding: "3px 9px",
    borderRadius: 7,
    ...(map[String(status).toLowerCase()] || map.inactive)
  };
}

function FloatingWindow({ id, onClose, onFocus, zIndex, children }) {
  const meta = WIN_META[id];
  const { pos, handleDown } = useWindowDrag(meta.ix, meta.iy);

  return (
    <div
      onMouseDown={onFocus}
      style={{
        position: "fixed",
        left: pos.x,
        top: pos.y,
        width: meta.width,
        zIndex,
        background: C.card,
        border: `1.5px solid ${C.borderMid}`,
        borderRadius: 18,
        boxShadow: "0 8px 40px rgba(90,65,35,0.14), 0 2px 8px rgba(90,65,35,0.06)",
        maxHeight: "82vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        ...FONT
      }}
    >
      <div
        onMouseDown={handleDown}
        style={{
          cursor: "grab",
          padding: "11px 16px",
          borderBottom: `1px solid ${C.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: C.bgDeep,
          borderRadius: "16px 16px 0 0",
          userSelect: "none"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: C.textDim, fontSize: 13 }}>::</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{meta.title}</span>
        </div>
        <button
          type="button"
          onMouseDown={(event) => event.stopPropagation()}
          onClick={onClose}
          style={{
            width: 24,
            height: 24,
            borderRadius: 8,
            border: `1px solid ${C.border}`,
            background: "transparent",
            cursor: "pointer",
            color: C.textMuted,
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          x
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 18, scrollbarWidth: "thin" }}>{children}</div>
    </div>
  );
}

function CreateAgentContent() {
  const [pinned, setPinned] = useState(false);

  return (
    <div style={{ display: "flex", gap: 18 }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <InputField label="Agent Name" placeholder="e.g. Doc Converter" />
        <div style={{ marginBottom: 10 }}>
          <Label text="Icon" />
          <div
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              border: `1.5px dashed ${C.borderMid}`,
              background: C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              gap: 8,
              cursor: "pointer"
            }}
          >
            <span style={{ color: C.textDim }}>^</span>
            import icon - PNG, JPG, WebP, GIF
          </div>
        </div>
        <DropField label="Skills" placeholder="search or type skill name..." />
        <DropField label="Brain / Model" placeholder="select AI model..." />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 14 }}>
          <button
            type="button"
            onClick={() => setPinned((value) => !value)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "none",
              border: "none",
              cursor: "pointer",
              color: C.textMuted,
              fontSize: 13,
              ...FONT
            }}
          >
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: 5,
                border: `1.5px solid ${pinned ? C.accent : C.textDim}`,
                background: pinned ? C.accentLight : "transparent",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: C.accent,
                fontSize: 10
              }}
            >
              {pinned ? "v" : ""}
            </div>
            pin agent
          </button>
          <button
            type="button"
            style={{
              padding: "8px 22px",
              borderRadius: 10,
              border: "none",
              background: C.accent,
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              ...FONT
            }}
          >
            Create
          </button>
        </div>
      </div>

      <div style={{ width: 148, flexShrink: 0 }}>
        <Label text="Preview Agent" />
        <Card style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: C.accentLight,
              border: `1px solid ${C.borderMid}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 700,
              color: C.accent
            }}
          >
            AG
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>nama agent</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>icon</div>
          {["skill 2", "brain / model"].map((text) => (
            <div
              key={text}
              style={{
                padding: "6px 9px",
                borderRadius: 8,
                background: C.card,
                border: `1px solid ${C.border}`,
                fontSize: 11,
                color: C.textMuted
              }}
            >
              {text}
            </div>
          ))}
          <div style={{ display: "flex", gap: 6 }}>
            <span style={statusStyle("need setup")}>need setup</span>
            <span style={statusStyle("ready")}>ready</span>
          </div>
        </Card>
      </div>
    </div>
  );
}

function ImportSkillContent() {
  return (
    <div>
      <InputField label="Repository URL" placeholder="https://github.com/user/repo" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
        <InputField label="Branch" placeholder="main" />
        <InputField label="File Path" placeholder="src/skill.py" />
        <InputField label="Folder Path" placeholder="src/skills/" />
      </div>
      <div style={{ display: "flex", gap: 10, marginBottom: 18 }}>
        {["preview file path", "preview folder path"].map((text) => (
          <button
            key={text}
            type="button"
            style={{
              flex: 1,
              padding: "8px 12px",
              borderRadius: 10,
              border: `1.5px solid ${C.border}`,
              background: C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              cursor: "pointer",
              ...FONT
            }}
          >
            {text}
          </button>
        ))}
      </div>

      <Card>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 3 }}>Skill Name</div>
            <div style={{ fontSize: 13, color: C.textMuted }}>-</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>status</div>
            <button
              type="button"
              style={{
                padding: "5px 16px",
                borderRadius: 8,
                border: "none",
                background: C.accent,
                color: "#fff",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                ...FONT
              }}
            >
              Add
            </button>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 12 }}>
          {["import type", "file path", "folder path"].map((text) => (
            <div
              key={text}
              style={{
                padding: "7px 10px",
                borderRadius: 8,
                background: C.card,
                border: `1px solid ${C.border}`,
                fontSize: 11,
                color: C.textMuted
              }}
            >
              {text}
            </div>
          ))}
        </div>
        <div
          style={{
            padding: 12,
            borderRadius: 10,
            background: C.card,
            border: `1px solid ${C.border}`,
            minHeight: 90
          }}
        >
          <div style={{ fontSize: 11, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Content Review</div>
          <div style={{ fontSize: 12, color: C.textDim, fontFamily: "Consolas, monospace" }}>
            no clone / no install / no script execution
          </div>
        </div>
      </Card>
    </div>
  );
}

function LibraryTable({ rows, columns }) {
  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 12px",
            borderRadius: 10,
            background: C.cardInner,
            border: `1.5px solid ${C.border}`
          }}
        >
          <span style={{ color: C.textDim }}>o</span>
          <input
            placeholder="search..."
            style={{ background: "none", border: "none", outline: "none", fontSize: 13, color: C.text, width: "100%", ...FONT }}
          />
        </div>
        {["Type", "Status"].map((text) => (
          <button
            key={text}
            type="button"
            style={{
              padding: "7px 14px",
              borderRadius: 10,
              border: `1.5px solid ${C.border}`,
              background: C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 5,
              ...FONT
            }}
          >
            {text} <span>v</span>
          </button>
        ))}
      </div>

      <div style={{ borderRadius: 12, border: `1px solid ${C.border}`, overflow: "hidden" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "2fr 1fr 1fr 1.5fr 1fr",
            padding: "8px 14px",
            background: C.bgDeep,
            borderBottom: `1px solid ${C.border}`
          }}
        >
          {columns.map((column) => (
            <div key={column} style={{ fontSize: 11, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {column}
            </div>
          ))}
        </div>
        {rows.map((row, index) => (
          <div
            key={`${row.name}-${index}`}
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr 1fr 1.5fr 1fr",
              padding: "10px 14px",
              borderBottom: index < rows.length - 1 ? `1px solid ${C.border}` : "none",
              background: index % 2 === 0 ? C.card : C.bgDeep,
              alignItems: "center"
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 500, color: C.text }}>{row.name}</div>
            <div style={{ fontSize: 12, color: C.textMuted }}>{row.type}</div>
            <div><span style={statusStyle(row.status)}>{row.status}</span></div>
            <div style={{ fontSize: 12, color: C.textMuted }}>{row.agent}</div>
            <div style={{ display: "flex", gap: 5 }}>
              {["View", "Edit"].map((action) => (
                <button
                  key={action}
                  type="button"
                  style={{
                    fontSize: 11,
                    padding: "3px 8px",
                    borderRadius: 6,
                    border: `1px solid ${C.border}`,
                    background: "none",
                    color: C.textMuted,
                    cursor: "pointer",
                    ...FONT
                  }}
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LibrarySkillContent() {
  return <LibraryTable rows={SKILL_ROWS} columns={["nama skill", "type", "status", "agent", "action"]} />;
}

function LibraryWorkflowContent() {
  return <LibraryTable rows={FLOW_ROWS} columns={["workflow name", "trigger", "status", "agent", "action"]} />;
}

function WorkflowN8nContent() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {N8N_ROWS.map((row) => (
        <Card key={row.id} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{row.name}</div>
            <span style={statusStyle(row.status)}>{row.status}</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            {[
              ["ID", row.id],
              ["Agent", row.agent],
              ["Trigger", row.trigger]
            ].map(([label, value]) => (
              <div key={label} style={{ padding: "7px 10px", borderRadius: 8, background: C.card, border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 10, color: C.textDim, marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
                <div style={{ fontSize: 12, color: C.textSub }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ padding: 10, borderRadius: 8, background: C.card, border: `1px solid ${C.border}`, minHeight: 40 }}>
            <div style={{ fontSize: 11, color: C.textDim }}>preview / details area</div>
          </div>
        </Card>
      ))}
    </div>
  );
}

function ActivityLogContent() {
  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 12px",
            borderRadius: 10,
            background: C.cardInner,
            border: `1.5px solid ${C.border}`
          }}
        >
          <span style={{ color: C.textDim }}>o</span>
          <input
            placeholder="search activity..."
            style={{ background: "none", border: "none", outline: "none", fontSize: 13, color: C.text, width: "100%", ...FONT }}
          />
        </div>
        <button
          type="button"
          style={{
            padding: "7px 14px",
            borderRadius: 10,
            border: `1.5px solid ${C.border}`,
            background: C.cardInner,
            color: C.textMuted,
            fontSize: 12,
            cursor: "pointer",
            ...FONT
          }}
        >
          All
        </button>
        <button
          type="button"
          style={{
            padding: "7px 14px",
            borderRadius: 10,
            border: `1.5px solid ${C.border}`,
            background: C.cardInner,
            color: C.textMuted,
            fontSize: 12,
            cursor: "pointer",
            ...FONT
          }}
        >
          Today
        </button>
      </div>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Today
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {ACTIVITY_ROWS.map((item) => (
          <Card key={`${item.time}-${item.title}`} style={{ background: C.card, padding: 12 }}>
            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ width: 44, flexShrink: 0, fontSize: 12, color: C.textMuted }}>{item.time}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{item.title}</div>
                    <div style={{ fontSize: 12, color: C.textMuted, marginTop: 3 }}>{item.desc}</div>
                  </div>
                  <span style={statusStyle(item.tone)}>{item.status}</span>
                </div>
                <div style={{ marginTop: 9 }}>
                  <button
                    type="button"
                    style={{
                      fontSize: 11,
                      padding: "4px 9px",
                      borderRadius: 7,
                      border: `1px solid ${C.border}`,
                      background: "none",
                      color: C.textMuted,
                      cursor: "pointer",
                      ...FONT
                    }}
                  >
                    View Detail
                  </button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SettingsContent({ currentUser }) {
  const user = currentUser || {
    display_name: "nama user",
    username: "nama user",
    email: "user@email.com",
    subscription_plan: "free"
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Account / Profile
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Name: {user.display_name || user.username}
          </div>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Email: {user.email || "user@email.com"}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>Plan</div>
            <span style={statusStyle("ready")}>{String(user.subscription_plan || "FREE").toUpperCase()}</span>
          </div>
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Brain / Model
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Default Provider: OpenAI
          </div>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Default Model: gpt-4o
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>Status</div>
            <span style={statusStyle("ready")}>ready</span>
          </div>
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          API Key Vault
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {SETTINGS_KEYS.map((item) => (
            <div key={item.provider} style={{ padding: "9px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.provider}</div>
                  <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{item.masked}</div>
                </div>
                <span style={statusStyle(item.status)}>{item.status}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Safety
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          {[
            ["tool execution", "locked"],
            ["n8n execution", "locked"],
            ["runtime", "preview only"],
            ["workflow execution", "locked"],
            ["provider live test", "locked"]
          ].map(([label, value]) => (
            <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 12, color: C.textMuted }}>{label}</div>
              <span style={statusStyle(value)}>{value}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function NavButton({ label, icon, onClick, active = false }) {
  const [hovered, setHovered] = useState(false);
  const onState = hovered || active;

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 12px",
        borderRadius: 12,
        width: "100%",
        textAlign: "left",
        border: `1px solid ${onState ? C.border : "transparent"}`,
        background: onState ? C.card : "transparent",
        color: onState ? C.text : C.textSub,
        fontSize: 13,
        cursor: "pointer",
        transition: "background 180ms ease, border-color 180ms ease, color 180ms ease, transform 180ms ease",
        transform: onState ? "translateX(1px)" : "translateX(0)",
        ...FONT
      }}
    >
      <span
        style={{
          color: onState ? C.accent : C.textMuted,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 16,
          height: 16,
          transition: "color 180ms ease"
        }}
      >
        <MenuIcon name={icon} />
      </span>
      <span>{label}</span>
    </button>
  );
}

function AgentCard({ agent }) {
  const [cmd, setCmd] = useState("");
  const [decision, setDecision] = useState(null);
  const [notes, setNotes] = useState([]);
  const statusMap = {
    idle: { label: "Idle", color: C.textDim, bg: "rgba(0,0,0,0.05)" },
    active: { label: "Running", color: C.amber, bg: C.amberLight },
    sending: { label: "Sending", color: C.green, bg: C.greenLight }
  };
  const status = statusMap[agent.status] || statusMap.idle;

  function handleSend() {
    const trimmed = cmd.trim();
    if (!trimmed) return;
    setNotes((current) => [{ id: Date.now(), text: trimmed }, ...current].slice(0, 2));
    setCmd("");
  }

  return (
    <div
      style={{
        flexShrink: 0,
        width: 196,
        background: C.card,
        border: `1.5px solid ${C.border}`,
        borderRadius: 16,
        padding: 14,
        display: "flex",
        flexDirection: "column",
        gap: 11,
        transition: "border-color 0.18s, box-shadow 0.18s"
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 12,
            background: C.accentLight,
            border: `1px solid ${C.borderMid}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            fontWeight: 700,
            color: C.accent
          }}
        >
          {agent.icon}
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 7, color: status.color, background: status.bg }}>
          {status.label}
        </span>
      </div>

      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 2 }}>{agent.name}</div>
        <div style={{ fontSize: 12, color: C.textMuted }}>skill {agent.skillCount}</div>
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Skills</div>
        {agent.skills.map((skill) => (
          <div key={skill} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <div style={{ width: 4, height: 4, borderRadius: "50%", background: C.textDim, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: C.textMuted }}>{skill}</span>
          </div>
        ))}
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Activity</div>
        {agent.activity.map((activity, index) => (
          <div key={activity} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: index < agent.activity.length - 1 ? 4 : 0 }}>
            <div
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                flexShrink: 0,
                background: index === 0 ? C.textDim : index === 1 ? C.amber : C.green
              }}
            />
            <span style={{ fontSize: 11, color: C.textMuted }}>{activity}</span>
          </div>
        ))}
      </div>

      {agent.needApproval && decision === null ? (
        <div
          style={{
            background: C.amberLight,
            border: `1.5px solid rgba(176,120,32,0.25)`,
            borderRadius: 12,
            padding: 12
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 700, color: C.amber, marginBottom: 3 }}>Approval Needed</div>
          <div style={{ fontSize: 11, color: C.textSub, marginBottom: 7 }}>Agent needs permission before continuing.</div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 9 }}>• use workflow<br />• attach skill</div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              onClick={() => setDecision("approved")}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: "none", background: C.green, color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer", ...FONT }}
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => setDecision("rejected")}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: `1px solid ${C.borderMid}`, background: "none", color: C.textMuted, fontSize: 11, cursor: "pointer", ...FONT }}
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      {agent.needApproval && decision !== null ? (
        <div style={{ fontSize: 12, color: decision === "approved" ? C.green : C.textDim, textAlign: "center", padding: "4px 0" }}>
          {decision === "approved" ? "Approved" : "Rejected"}
        </div>
      ) : null}

      <div style={{ marginTop: "auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 10px",
            borderRadius: 10,
            border: `1.5px solid ${C.border}`,
            background: C.bgDeep
          }}
        >
          <input
            value={cmd}
            onChange={(event) => setCmd(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSend();
              }
            }}
            placeholder="ketik untuk menyuruh agent..."
            style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 11, color: C.text, minWidth: 0, ...FONT }}
          />
          <button type="button" onClick={handleSend} style={{ background: "none", border: "none", cursor: "pointer", color: cmd ? C.accent : C.textDim, padding: 0 }}>
            &gt;
          </button>
        </div>
        {notes.length ? (
          <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
            {notes.map((note) => (
              <div key={note.id} style={{ padding: "7px 9px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
                {note.text}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Sidebar({ onOpen }) {
  const [activeId, setActiveId] = useState("create-agent");

  function handleOpen(id) {
    setActiveId(id);
    onOpen(id);
  }

  return (
    <div
      style={{
        width: 196,
        flexShrink: 0,
        background: C.bgDeep,
        borderRight: `1px solid ${C.border}`,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        padding: "10px 10px 12px"
      }}
    >
      {NAV_ITEMS.map((item) => (
        <NavButton
          key={item.id}
          label={item.label}
          icon={item.icon}
          active={activeId === item.id}
          onClick={() => handleOpen(item.id)}
        />
      ))}
      <div style={{ flex: 1 }} />
      <NavButton
        label="Settings"
        icon="settings"
        active={activeId === "settings"}
        onClick={() => handleOpen("settings")}
      />
    </div>
  );
}

function ChatPanel({ open }) {
  return (
    <div
      style={{
        maxHeight: open ? 240 : 0,
        overflow: "hidden",
        transition: "max-height 0.28s ease",
        borderTop: open ? `1px solid ${C.border}` : "none"
      }}
    >
      <div
        style={{
          padding: "12px 16px 8px",
          background: C.card,
          display: "flex",
          flexDirection: "column",
          gap: 8,
          maxHeight: 240,
          overflowY: "auto"
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
          Main AI Conversation
        </div>
        {CHAT_HISTORY.map((message, index) => (
          <div key={`${message.role}-${index}`} style={{ display: "flex", justifyContent: message.role === "You" ? "flex-end" : "flex-start" }}>
            <div
              style={{
                maxWidth: "70%",
                padding: "7px 12px",
                borderRadius: 12,
                background: message.role === "You" ? C.accentLight : C.bgDeep,
                border: `1px solid ${C.border}`,
                fontSize: 13,
                color: C.textSub
              }}
            >
              <div style={{ fontSize: 10, color: C.textDim, marginBottom: 2 }}>{message.role}</div>
              {message.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WindowContent({ id, currentUser }) {
  switch (id) {
    case "create-agent":
      return <CreateAgentContent />;
    case "import-skill":
      return <ImportSkillContent />;
    case "library-skill":
      return <LibrarySkillContent />;
    case "library-workflow":
      return <LibraryWorkflowContent />;
    case "workflow-n8n":
      return <WorkflowN8nContent />;
    case "activity-log":
      return <ActivityLogContent />;
    case "settings":
      return <SettingsContent currentUser={currentUser} />;
    default:
      return null;
  }
}

export default function FigmaMakeWorkspace() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState(null);
  const [windows, setWindows] = useState([]);
  const [zTop, setZTop] = useState(100);
  const [chatOpen, setChatOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const laneRef = useRef(null);
  const laneDrag = useRef(false);
  const laneX0 = useRef(0);
  const laneScroll = useRef(0);

  useEffect(() => {
    let active = true;

    async function loadUser() {
      try {
        const user = await getCurrentUser();
        if (!active) return;
        setCurrentUser(user);
      } catch {
        if (!active) return;
        setCurrentUser(null);
      }
    }

    loadUser();

    return () => {
      active = false;
    };
  }, []);

  function openWindow(id) {
    const next = zTop + 1;
    setZTop(next);
    setWindows((current) => {
      const existing = current.find((item) => item.id === id);
      if (existing) {
        return current.map((item) => (item.id === id ? { ...item, zIndex: next } : item));
      }
      return [...current, { id, zIndex: next }];
    });
  }

  function closeWindow(id) {
    setWindows((current) => current.filter((item) => item.id !== id));
  }

  function focusWindow(id) {
    const next = zTop + 1;
    setZTop(next);
    setWindows((current) => current.map((item) => (item.id === id ? { ...item, zIndex: next } : item)));
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  function laneDown(event) {
    if (!laneRef.current) return;
    laneDrag.current = true;
    laneX0.current = event.pageX - laneRef.current.getBoundingClientRect().left;
    laneScroll.current = laneRef.current.scrollLeft;
    laneRef.current.style.cursor = "grabbing";
  }

  function laneMove(event) {
    if (!laneDrag.current || !laneRef.current) return;
    const x = event.pageX - laneRef.current.getBoundingClientRect().left;
    laneRef.current.scrollLeft = laneScroll.current - (x - laneX0.current);
  }

  function laneUp() {
    laneDrag.current = false;
    if (laneRef.current) laneRef.current.style.cursor = "grab";
  }

  const user = currentUser || {
    display_name: "nama user",
    username: "nama user",
    subscription_plan: "free",
    email: "user@email.com"
  };

  return (
    <ProtectedRoute>
      <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "column", background: C.bg, overflow: "hidden", ...FONT }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "11px 20px",
            borderBottom: `1px solid ${C.border}`,
            background: C.bgDeep,
            flexShrink: 0
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span style={{ fontSize: 22, color: C.text, ...SERIF }}>workspace</span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: C.accentLight,
                  border: `1.5px solid ${C.borderMid}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 600,
                  color: C.accent
                }}
              >
                U
              </div>
              <span style={{ fontSize: 13, color: C.textSub }}>{user.display_name || user.username}</span>
              <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: C.accentLight, color: C.accent, letterSpacing: "0.05em" }}>
                {String(user.subscription_plan || "FREE").toUpperCase()}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              padding: "7px 14px",
              borderRadius: 10,
              border: `1.5px solid ${C.border}`,
              background: "none",
              color: C.textMuted,
              fontSize: 13,
              cursor: "pointer",
              ...FONT
            }}
          >
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 15, height: 15 }}>
              <MenuIcon name="logout" />
            </span>
            Logout
          </button>
        </div>

        <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
          <Sidebar onOpen={openWindow} />

          <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ flex: 1, padding: "18px 20px 0", minHeight: 0, display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Agents - drag to scroll -&gt;
              </div>
              <div
                ref={laneRef}
                onMouseDown={laneDown}
                onMouseMove={laneMove}
                onMouseUp={laneUp}
                onMouseLeave={laneUp}
                style={{
                  display: "flex",
                  gap: 14,
                  overflowX: "auto",
                  paddingBottom: 12,
                  cursor: "grab",
                  scrollbarWidth: "none",
                  userSelect: "none",
                  flex: 1,
                  alignItems: "flex-start"
                }}
              >
                {PREVIEW_AGENTS.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            </div>

            <div style={{ flexShrink: 0, borderTop: `1px solid ${C.border}`, background: C.bgDeep }}>
              <ChatPanel open={chatOpen} />
              <div style={{ padding: "10px 16px 12px", display: "flex", alignItems: "center", gap: 10 }}>
                <button
                  type="button"
                  onClick={() => setChatOpen((open) => !open)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    padding: "8px 12px",
                    borderRadius: 10,
                    border: `1.5px solid ${C.border}`,
                    background: C.card,
                    color: C.textMuted,
                    fontSize: 12,
                    cursor: "pointer",
                    flexShrink: 0,
                    ...FONT
                  }}
                >
                  {chatOpen ? "^" : "v"} History
                </button>

                <div
                  style={{
                    flex: 1,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 14px",
                    borderRadius: 14,
                    border: `1.5px solid ${C.borderMid}`,
                    background: C.card
                  }}
                >
                  <input
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    placeholder="ini tempat untuk main AI bisa langsung menyuruh lewat prompt..."
                    style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 13, color: C.text, ...FONT }}
                  />
                  <button
                    type="button"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "5px 14px",
                      borderRadius: 9,
                      border: `1px solid ${C.border}`,
                      background: C.cardInner,
                      color: C.textMuted,
                      fontSize: 12,
                      cursor: "pointer",
                      flexShrink: 0,
                      ...FONT
                    }}
                  >
                    model <span>v</span>
                  </button>
                  <button
                    type="button"
                    style={{
                      width: 34,
                      height: 34,
                      borderRadius: 10,
                      border: "none",
                      cursor: "pointer",
                      background: prompt ? C.accent : "rgba(90,65,35,0.1)",
                      color: prompt ? "#fff" : C.textDim,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0
                    }}
                  >
                    &gt;
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {windows.map((windowItem) => (
          <FloatingWindow
            key={windowItem.id}
            id={windowItem.id}
            onClose={() => closeWindow(windowItem.id)}
            onFocus={() => focusWindow(windowItem.id)}
            zIndex={windowItem.zIndex}
          >
            <WindowContent id={windowItem.id} currentUser={user} />
          </FloatingWindow>
        ))}
      </div>
    </ProtectedRoute>
  );
}
