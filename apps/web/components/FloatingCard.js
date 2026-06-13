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
      className={`absolute ${widthClassName} flex max-h-[82vh] flex-col overflow-hidden rounded-[20px] border border-[rgba(62,54,46,0.16)] bg-[#E5E0D3] p-5 shadow-[0_20px_60px_rgba(62,54,46,0.14)]`}
      style={{
        left: position.x,
        top: position.y,
        zIndex
      }}
      onPointerDown={onFocus}
    >
      <div
        onPointerDown={handleDragStart}
        className="mb-6 flex shrink-0 cursor-grab items-start justify-between gap-4 active:cursor-grabbing"
      >
        <div className="w-full">
          <div className="mb-4 flex justify-center">
            <div className="grid grid-cols-6 gap-1.5">
              {Array.from({ length: 12 }).map((_, index) => (
                <span key={index} className="h-1.5 w-1.5 rounded-full bg-[rgba(62,54,46,0.35)]" />
              ))}
            </div>
          </div>
          <h2 className="text-[22px] font-semibold text-[#3E362E]">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.68)]">{subtitle}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.76)] transition hover:bg-[#D5CFBF]"
        >
          x
        </button>
      </div>

      <div className={`scrollbar-thin min-h-0 flex-1 overflow-y-auto pr-1 ${bodyClassName}`}>
        {children}
      </div>

      {footer ? (
        <div className="mt-5 shrink-0 border-t border-[rgba(62,54,46,0.12)] pt-4">
          {footer}
        </div>
      ) : null}
    </section>
  );
}
