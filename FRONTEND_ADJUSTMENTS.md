# Frontend Adjustments (to apply after backend is ready)

This document tracks minimal, non-blocking frontend tweaks identified during planning. We will implement the backend first; these can be applied afterward.

## 1) Robust image rendering for sources (important)

Allow both raw base64 and full data URLs (and future JPEG/PNG flexibility) in `SourceCard`.

Suggested change in `frontend/src/components/SourceCard.tsx`:

```tsx
// Replace current imageUrl composition with helper
const toImageUrl = (data: string) => {
  if (data.startsWith("data:")) return data; // already a data URL
  return `data:image/png;base64,${data}`;     // default to PNG if mime not provided
};

// ... inside renderImageSource()
const imageUrl = toImageUrl(source.image_b64);
```

Rationale: Backend may return PNG/JPEG or a full data URL. This avoids broken images.

## 2) Stream toggle UX (defer)

Until SSE streaming is implemented in the backend, either hide or disable the "Stream responses" toggle to avoid confusion.

Option A (hide): remove the Stream block in `frontend/src/components/Chat.tsx`.

Option B (disable):

```tsx
<div className="flex items-center justify-between opacity-50 cursor-not-allowed" title="Streaming coming soon">
  <Label htmlFor="stream" className="text-sm">Stream responses</Label>
  <Switch id="stream" checked={false} disabled />
  {/* Wire up once /api/chat/stream is available */}
  {/* TODO: Replace with SSE consumer via EventSource when backend is ready */}
  
</div>
```

Rationale: Prevents a setting that currently has no effect.

## 3) Be tolerant while wiring upload response (optional)

During backend bring-up, `pages`/`createdAt` may be temporarily missing. Guard UI rendering to avoid crashes.

Examples:

```tsx
// frontend/src/components/UploadDropzone.tsx
toast({
  title: "Upload successful",
  description: `${document.name}${document.pages ? ` has been uploaded (${document.pages} pages)` : ""}`,
});

// frontend/src/components/SidebarDocuments.tsx
<span>{doc.createdAt ? new Date(doc.createdAt).toLocaleDateString() : "—"}</span>
```

Rationale: Lets backend iterate without blocking the UI.

## Backend contracts these changes assume

- `POST /api/chat` returns `sources` with one of `text`, `table_html`, or `image_b64` per item. `image_b64` may be raw base64 or a full `data:*` URL.
- `GET /api/documents` returns `{ documents: [{ id, name, pages, createdAt }] }` (ISO timestamps).
- `POST /api/upload` returns a `Document` shape: `{ id, name, pages, createdAt }`.

## Streaming (later)

When backend SSE is available (e.g., `GET /api/chat/stream?sessionId=...`), add an `EventSource` client in the chat component to append tokens live, then enable the toggle.


