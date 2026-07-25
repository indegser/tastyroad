# Naver Map UI Notes

- Use Microsoft Edge through CDP on port 9222.
- Use `agent-browser --cdp 9222` on every command to avoid controlling the wrong browser session.
- Scope place actions to the `pcmap.place.naver.com` frame. The place save control is
  `a[href="#bookmark"][role="button"]`.
- The save modal exposes list rows as `button.swt-save-group-info[role="checkbox"]`.
  Their accessible text includes the exact folder name, visible place count, and
  `선택됨`/`선택해제됨` state.
- Confirm writes with the modal's `button.swt-save-btn`, reopen the modal, and require the
  target list row to remain `선택됨` before updating local sync state.
- Use `button.swt-close-btn` to close a verification modal.
- Do not use screenshots or fixed coordinates to control the UI. Capture screenshots only
  after final failure for diagnostics.
- The `Tastyroad` list was created as a private list.
- Always verify by opening the saved panel and reading the visible count beside `Tastyroad`.
