"use client";

import { useEffect, useMemo, useState } from "react";

const C = {
  bg: "#F5EFE6",
  card: "#FCF8F1",
  cardAlt: "#F2EBDD",
  border: "rgba(84, 63, 35, 0.14)",
  borderStrong: "rgba(84, 63, 35, 0.24)",
  text: "#2B2116",
  textSub: "#5B4C3C",
  textMuted: "#827162",
  accent: "#B85C38",
  accentSoft: "rgba(184, 92, 56, 0.10)",
  green: "#49745A",
  greenSoft: "rgba(73, 116, 90, 0.12)",
  amber: "#A06A1A",
  amberSoft: "rgba(160, 106, 26, 0.12)",
  red: "#A4473D",
  redSoft: "rgba(164, 71, 61, 0.10)"
};

const PLAN_LIMITS = {
  free: 0,
  pro: 1,
  executive: 10
};

function safeText(value, fallback = "-") {
  const text = typeof value === "string" ? value.trim() : value;
  return text ? String(text) : fallback;
}

function normalizePlan(user) {
  const plan = String(user?.subscription_plan || "free").trim().toLowerCase();
  if (plan === "pro" || plan === "executive") {
    return plan;
  }
  return "free";
}

function isAdmin(user) {
  return String(user?.role || "").trim().toLowerCase() === "admin";
}

function canAccessN8n(user) {
  return isAdmin(user) || ["pro", "executive"].includes(normalizePlan(user));
}

function getPlanLabel(user) {
  if (isAdmin(user)) return "Admin";
  const plan = normalizePlan(user);
  return plan === "free" ? "Free" : plan === "pro" ? "Pro" : "Executive";
}

function getPlanLimit(user) {
  if (isAdmin(user)) return "unlimited";
  const plan = normalizePlan(user);
  return PLAN_LIMITS[plan];
}

function parseJsonObject(raw) {
  const value = raw.trim();
  if (!value) {
    return null;
  }

  const parsed = JSON.parse(value);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Metadata must be a JSON object.");
  }

  return parsed;
}

function formatJsonObject(value) {
  if (!value || typeof value !== "object") {
    return "{\n\n}";
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "{\n\n}";
  }
}

function EditorField({ label, children, helper }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</span>
      {children}
      {helper ? <span style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.45 }}>{helper}</span> : null}
    </label>
  );
}

function WorkflowEditorCard({
  title,
  workflow,
  disabled = false,
  onSave,
  onDelete,
  allowDelete = false,
  saveLabel = "Save metadata",
  deleteLabel = "Delete metadata",
  emptyLabel = "Buat workflow metadata baru."
}) {
  const [name, setName] = useState(workflow?.name || "");
  const [slug, setSlug] = useState(workflow?.slug || "");
  const [description, setDescription] = useState(workflow?.description || "");
  const [workflowExternalId, setWorkflowExternalId] = useState(workflow?.workflow_external_id || "");
  const [triggerType, setTriggerType] = useState(workflow?.trigger_type || "manual");
  const [webhookReference, setWebhookReference] = useState(workflow?.webhook_url_reference || "");
  const [status, setStatus] = useState(workflow?.status || "inactive");
  const [riskLevel, setRiskLevel] = useState(workflow?.risk_level || "low");
  const [approvalRequired, setApprovalRequired] = useState(Boolean(workflow?.approval_required ?? true));
  const [metadataText, setMetadataText] = useState(formatJsonObject(workflow?.metadata));
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setName(workflow?.name || "");
    setSlug(workflow?.slug || "");
    setDescription(workflow?.description || "");
    setWorkflowExternalId(workflow?.workflow_external_id || "");
    setTriggerType(workflow?.trigger_type || "manual");
    setWebhookReference(workflow?.webhook_url_reference || "");
    setStatus(workflow?.status || "inactive");
    setRiskLevel(workflow?.risk_level || "low");
    setApprovalRequired(Boolean(workflow?.approval_required ?? true));
    setMetadataText(formatJsonObject(workflow?.metadata));
    setMessage("");
  }, [workflow]);

  async function handleSave() {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setMessage("Name wajib diisi.");
      return;
    }

    setBusy(true);
    setMessage("");

    try {
      const payload = {
        name: trimmedName,
        slug: slug.trim() || undefined,
        description: description.trim() || null,
        workflow_external_id: workflowExternalId.trim() || null,
        trigger_type: triggerType,
        webhook_url_reference: webhookReference.trim() || null,
        status,
        risk_level: riskLevel,
        approval_required: approvalRequired,
        metadata: parseJsonObject(metadataText)
      };

      await onSave?.(workflow?.id || null, payload);
      setMessage("Saved.");
    } catch (error) {
      setMessage(error?.message || "Save gagal.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!workflow?.id) {
      return;
    }

    setBusy(true);
    setMessage("");

    try {
      await onDelete?.(workflow.id);
      setMessage("Deleted.");
    } catch (error) {
      setMessage(error?.message || "Delete gagal.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      style={{
        border: `1px solid ${C.border}`,
        borderRadius: 16,
        background: C.card,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 14
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{title}</div>
          <div style={{ marginTop: 4, fontSize: 12, color: C.textMuted }}>{workflow ? safeText(workflow.workflow_external_id, "Saved workflow") : emptyLabel}</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
          <span
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              border: `1px solid ${C.border}`,
              background: workflow?.status === "disabled" ? C.redSoft : C.amberSoft,
              color: workflow?.status === "disabled" ? C.red : C.amber,
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.05em"
            }}
          >
            {safeText(workflow?.status, "inactive")}
          </span>
          <span style={{ fontSize: 11, color: C.textMuted }}>Save only. No execute.</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
        <EditorField label="Name">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={disabled || busy}
            placeholder="Workflow name"
            style={inputStyle()}
          />
        </EditorField>
        <EditorField label="Slug">
          <input
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            disabled={disabled || busy}
            placeholder="workflow-slug"
            style={inputStyle()}
          />
        </EditorField>
        <EditorField label="Workflow external ID">
          <input
            value={workflowExternalId}
            onChange={(event) => setWorkflowExternalId(event.target.value)}
            disabled={disabled || busy}
            placeholder="n8n workflow id / reference"
            style={inputStyle()}
          />
        </EditorField>
        <EditorField
          label="Trigger type"
          helper="Only metadata. No direct n8n call."
        >
          <select
            value={triggerType}
            onChange={(event) => setTriggerType(event.target.value)}
            disabled={disabled || busy}
            style={inputStyle()}
          >
            <option value="manual">manual</option>
            <option value="webhook">webhook</option>
            <option value="scheduled">scheduled</option>
          </select>
        </EditorField>
        <EditorField label="Risk level">
          <select
            value={riskLevel}
            onChange={(event) => setRiskLevel(event.target.value)}
            disabled={disabled || busy}
            style={inputStyle()}
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>
        </EditorField>
        <EditorField label="Status">
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            disabled={disabled || busy}
            style={inputStyle()}
          >
            <option value="inactive">inactive</option>
            <option value="disabled">disabled</option>
          </select>
        </EditorField>
        <EditorField label="Webhook reference" helper="Safe label only. No raw URL or secret.">
          <input
            value={webhookReference}
            onChange={(event) => setWebhookReference(event.target.value)}
            disabled={disabled || busy}
            placeholder="workflow-webhook-ref"
            style={inputStyle()}
          />
        </EditorField>
      </div>

      <EditorField label="Description">
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          disabled={disabled || busy}
          placeholder="Short workflow note"
          rows={3}
          style={{ ...inputStyle(), resize: "vertical", minHeight: 88 }}
        />
      </EditorField>

      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 12 }}>
        <EditorField label="Metadata JSON" helper="Object only. Empty means no metadata.">
          <textarea
            value={metadataText}
            onChange={(event) => setMetadataText(event.target.value)}
            disabled={disabled || busy}
            placeholder='{\n  "agent_name": "Mail Agent"\n}'
            rows={8}
            style={{ ...inputStyle(), resize: "vertical", minHeight: 150, fontFamily: "Consolas, monospace" }}
          />
        </EditorField>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={calloutStyle}>
            <div style={calloutLabelStyle}>Activation locked</div>
            <div style={calloutTextStyle}>Backend save saja. Tidak ada endpoint activate dari frontend.</div>
          </div>
          <div style={calloutStyle}>
            <div style={calloutLabelStyle}>Execution locked</div>
            <div style={calloutTextStyle}>Tidak ada execute endpoint. Frontend tidak kirim workflow langsung ke n8n.</div>
          </div>
          <div style={calloutStyle}>
            <div style={calloutLabelStyle}>Credential locked</div>
            <div style={calloutTextStyle}>Tidak ada field credential. Jangan simpan raw secret di UI.</div>
          </div>
        </div>
      </div>

      {message ? (
        <div style={{ fontSize: 12, color: busy ? C.textMuted : message.toLowerCase().includes("fail") ? C.red : C.green }}>{message}</div>
      ) : null}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={handleSave}
          disabled={disabled || busy}
          style={primaryButtonStyle(disabled || busy)}
        >
          {workflow?.id ? saveLabel : "Create workflow"}
        </button>
        <button
          type="button"
          onClick={onRefresh}
          disabled={busy}
          style={secondaryButtonStyle(busy)}
        >
          Refresh
        </button>
        {allowDelete && workflow?.id ? (
          <button
            type="button"
            onClick={handleDelete}
            disabled={disabled || busy}
            style={dangerButtonStyle(disabled || busy)}
          >
            {deleteLabel}
          </button>
        ) : null}
      </div>
    </section>
  );
}

function inputStyle() {
  return {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 12,
    border: `1px solid ${C.border}`,
    background: C.cardAlt,
    color: C.text,
    fontSize: 13,
    outline: "none"
  };
}

function primaryButtonStyle(disabled) {
  return {
    padding: "10px 14px",
    borderRadius: 12,
    border: "none",
    background: disabled ? "rgba(184,92,56,0.35)" : C.accent,
    color: "#fff",
    fontSize: 13,
    fontWeight: 700,
    cursor: disabled ? "not-allowed" : "pointer"
  };
}

function secondaryButtonStyle(disabled) {
  return {
    padding: "10px 14px",
    borderRadius: 12,
    border: `1px solid ${C.border}`,
    background: C.cardAlt,
    color: C.textSub,
    fontSize: 13,
    fontWeight: 600,
    cursor: disabled ? "not-allowed" : "pointer"
  };
}

function dangerButtonStyle(disabled) {
  return {
    padding: "10px 14px",
    borderRadius: 12,
    border: `1px solid ${C.border}`,
    background: disabled ? "rgba(164,71,61,0.06)" : C.redSoft,
    color: C.red,
    fontSize: 13,
    fontWeight: 700,
    cursor: disabled ? "not-allowed" : "pointer"
  };
}

const calloutStyle = {
  border: `1px solid ${C.border}`,
  borderRadius: 14,
  background: C.cardAlt,
  padding: 12
};

const calloutLabelStyle = {
  fontSize: 11,
  fontWeight: 800,
  color: C.textMuted,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  marginBottom: 4
};

const calloutTextStyle = {
  fontSize: 12,
  color: C.textSub,
  lineHeight: 1.55
};

function StatusStrip({ label, value, tone = "neutral" }) {
  const toneStyle =
    tone === "blocked"
      ? { background: C.redSoft, color: C.red }
      : tone === "allowed"
        ? { background: C.greenSoft, color: C.green }
        : tone === "warning"
          ? { background: C.amberSoft, color: C.amber }
          : { background: C.cardAlt, color: C.textMuted };

  return (
    <div style={{ padding: "10px 12px", borderRadius: 14, border: `1px solid ${C.border}`, background: C.card }}>
      <div style={{ fontSize: 11, fontWeight: 800, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, ...toneStyle }}>{value}</div>
    </div>
  );
}

function WorkflowCard({ workflow, disabled, onSave, onDelete }) {
  return (
    <WorkflowEditorCard
      key={workflow.id}
      title={safeText(workflow.name, "Saved workflow")}
      workflow={workflow}
      disabled={disabled}
      onSave={onSave}
      onDelete={onDelete}
      allowDelete
      saveLabel="Update metadata"
      deleteLabel="Delete metadata"
      emptyLabel="Saved workflow"
    />
  );
}

export default function N8nPanel({
  currentUser,
  rows = [],
  error = "",
  isLoading = false,
  onRefresh,
  onSaveWorkflow,
  onDeleteWorkflow
}) {
  const ready = Boolean(currentUser) && !isLoading;
  const planLabel = ready ? getPlanLabel(currentUser) : "Loading";
  const planLimit = ready ? getPlanLimit(currentUser) : 0;
  const allowed = ready ? canAccessN8n(currentUser) : false;
  const isAdminUser = ready ? isAdmin(currentUser) : false;
  const accessTone = isAdminUser ? "allowed" : allowed ? "allowed" : "blocked";
  const blockedMessage = useMemo(() => {
    if (allowed) {
      return "";
    }
    return "Free plan blocked. Upgrade to Pro, Executive, or use admin.";
  }, [allowed]);

  const backendMessage = useMemo(() => {
    if (!error) {
      return "";
    }
    if (String(error).toLowerCase().includes("free plan")) {
      return error;
    }
    if (String(error).toLowerCase().includes("backend required")) {
      return error;
    }
    return error;
  }, [error]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <section style={{ border: `1px solid ${C.border}`, borderRadius: 18, background: C.card, padding: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: C.text }}>n8n Registry</div>
            <div style={{ marginTop: 4, fontSize: 12, color: C.textMuted }}>Backend registry only. No direct n8n call from frontend.</div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <span style={pillStyle("neutral")}>execution locked</span>
            <span style={pillStyle("neutral")}>activation locked</span>
            <span style={pillStyle("neutral")}>credential locked</span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10, marginTop: 14 }}>
          <StatusStrip label="Current plan" value={isAdminUser ? "Admin override" : planLabel} tone={allowed ? "allowed" : "blocked"} />
          <StatusStrip label="n8n access" value={allowed ? "Allowed" : "Blocked"} tone={accessTone} />
          <StatusStrip label="Save quota" value={planLimit === "unlimited" ? "Unlimited" : `${planLimit} saved workflow${planLimit === 1 ? "" : "s"}`} tone={allowed ? "allowed" : "blocked"} />
          <StatusStrip label="Backend mode" value={error ? "Needs attention" : "Ready"} tone={error ? "warning" : "allowed"} />
        </div>

        <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
          <div style={infoBoxStyle}>
            <div style={infoTitleStyle}>Blocked state</div>
            <div style={infoTextStyle}>{allowed ? "Tidak diblok oleh plan." : blockedMessage}</div>
          </div>
          <div style={infoBoxStyle}>
            <div style={infoTitleStyle}>Backend requirement</div>
            <div style={infoTextStyle}>
              {backendMessage || "Endpoint /n8n-workflows aktif. Kalau backend hilang, panel ini harus tetap jatuh ke state jelas."}
            </div>
          </div>
        </div>

        <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
          <StatusStrip label="Execution" value="Disabled" tone="blocked" />
          <StatusStrip label="Activation" value="Disabled" tone="blocked" />
          <StatusStrip label="Direct n8n" value="Disabled" tone="blocked" />
        </div>
      </section>

      {isLoading || !currentUser ? (
        <section style={emptyStateStyle}>Loading n8n workflows...</section>
      ) : null}

      {ready && !allowed ? (
        <section style={blockedStateStyle}>
          <div style={infoTitleStyle}>Free plan blocked</div>
          <div style={infoTextStyle}>Panel ini baca aturan backend. Free plan tidak dapat save workflow metadata.</div>
        </section>
      ) : null}

      {ready && error && !String(error).toLowerCase().includes("free plan") ? (
        <section style={blockedStateStyle}>
          <div style={infoTitleStyle}>Backend required</div>
          <div style={infoTextStyle}>{backendMessage}</div>
        </section>
      ) : null}

      <WorkflowEditorCard
      title="New workflow metadata"
      workflow={null}
      disabled={!allowed || Boolean(error)}
      onSave={onSaveWorkflow}
      saveLabel="Create workflow"
      emptyLabel="Buat workflow metadata baru."
    />

      <section style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: C.text }}>Saved workflows</div>
            <div style={{ marginTop: 4, fontSize: 12, color: C.textMuted }}>
              {allowed ? `${rows.length} workflow tersimpan.` : "List dikunci sampai plan sesuai."}
            </div>
          </div>
          <button type="button" onClick={onRefresh} style={refreshButtonStyle(false)}>
            Refresh list
          </button>
        </div>

        {rows.length ? (
          rows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow.raw || workflow}
              disabled={!allowed || Boolean(error)}
              onSave={onSaveWorkflow}
              onDelete={onDeleteWorkflow}
            />
          ))
        ) : (
          <section style={emptyStateStyle}>
            <div style={infoTitleStyle}>No saved workflow</div>
            <div style={infoTextStyle}>
              {allowed
                ? "Belum ada workflow metadata yang disimpan."
                : "Free plan atau backend error mencegah list tampil."}
            </div>
          </section>
        )}
      </section>
    </div>
  );
}

function pillStyle(tone) {
  const tones = {
    neutral: { background: C.cardAlt, color: C.textMuted }
  };
  return {
    padding: "5px 10px",
    borderRadius: 999,
    border: `1px solid ${C.border}`,
    fontSize: 11,
    fontWeight: 800,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    ...tones[tone]
  };
}

const infoBoxStyle = {
  border: `1px solid ${C.border}`,
  borderRadius: 14,
  background: C.cardAlt,
  padding: 12
};

const infoTitleStyle = {
  fontSize: 11,
  fontWeight: 800,
  color: C.textMuted,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  marginBottom: 5
};

const infoTextStyle = {
  fontSize: 12,
  color: C.textSub,
  lineHeight: 1.55
};

const emptyStateStyle = {
  border: `1px dashed ${C.borderStrong}`,
  borderRadius: 16,
  background: C.card,
  padding: 18,
  color: C.textMuted
};

const blockedStateStyle = {
  border: `1px solid ${C.border}`,
  borderRadius: 16,
  background: C.redSoft,
  padding: 16,
  color: C.red
};

function refreshButtonStyle(disabled) {
  return {
    padding: "9px 13px",
    borderRadius: 12,
    border: `1px solid ${C.border}`,
    background: C.cardAlt,
    color: C.textSub,
    fontSize: 13,
    fontWeight: 700,
    cursor: disabled ? "not-allowed" : "pointer"
  };
}
