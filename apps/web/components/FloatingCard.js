"use client";

import { useEffect, useRef } from "react";

export default function FloatingCard({
  title,
  subtitle,
  open,
  position,
  zIndex,
  children,
  footer = null,
  bodyClassName = "",
  widthClassName = "w-[360px]",
  onClose,
  onMove,
  onFocus
}) {
  const dragStateRef = useRef(null);

  useEffect(() => {
    function handlePointerMove(event) {
      if (!dragStateRef.current) {
        return;
      }

      const nextX = Math.max(
        16,
        dragStateRef.current.originX + (event.clientX - dragStateRef.current.pointerX)
      );
      const nextY = Math.max(
        16,
        dragStateRef.current.originY + (event.clientY - dragStateRef.current.pointerY)
      );

      onMove?.({
        x: nextX,
        y: nextY
      });
    }

    function handlePointerUp() {
      dragStateRef.current = null;
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [onMove]);

  if (!open) {
    return null;
  }

  function handleDragStart(event) {
    event.preventDefault();
    onFocus?.();
    dragStateRef.current = {
      pointerX: event.clientX,
      pointerY: event.clientY,
      originX: position.x,
      originY: position.y
    };
  }

  return (
    <section
      className={`fixed ${widthClassName} flex max-h-[82vh] flex-col overflow-hidden rounded-[22px] border border-[rgba(62,54,46,0.14)] bg-[#f4ecdf] shadow-[0_18px_42px_rgba(62,54,46,0.12)]`}
      style={{
        left: position.x,
        top: position.y,
        zIndex
      }}
      onPointerDown={onFocus}
    >
      <div
        onPointerDown={handleDragStart}
        className="flex shrink-0 cursor-grab items-center justify-between gap-4 border-b border-[rgba(62,54,46,0.12)] px-4 py-3 active:cursor-grabbing"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span aria-hidden className="grid h-4 w-4 grid-cols-3 gap-[2px] opacity-55">
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
              <span className="h-1 w-1 rounded-full bg-[rgba(62,54,46,0.42)]" />
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-[18px] font-semibold text-[#3E362E]">{title}</h2>
              {subtitle ? (
                <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.52)]">
                  {subtitle}
                </p>
              ) : null}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] border border-[rgba(62,54,46,0.14)] bg-[#f7f0e1] text-[16px] leading-none text-[rgba(62,54,46,0.68)] transition hover:bg-[#efe2cf]"
        >
          x
        </button>
      </div>

      <div className={`scrollbar-thin min-h-0 flex-1 overflow-y-auto px-4 py-4 ${bodyClassName}`}>
        {children}
      </div>

      {footer ? (
        <div className="shrink-0 border-t border-[rgba(62,54,46,0.12)] px-4 py-4">{footer}</div>
      ) : null}
    </section>
  );
}
