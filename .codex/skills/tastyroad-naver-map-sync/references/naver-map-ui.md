# Naver Map UI Notes

- Use the Codex Edge browser extension connector by default, controlling the user's real
  logged-in Microsoft Edge profile.
- If the Edge extension is unavailable, use the persistent `agent-browser` session named
  `tastyroad-naver-map-sync` as the first fallback.
- Use `agent-browser --session tastyroad-naver-map-sync --session-name tastyroad-naver-map-sync`
  on every fallback manual command to avoid controlling the wrong browser session.
- Scope place actions to the `pcmap.place.naver.com` frame. The place save control is
  `a[href="#bookmark"][role="button"][aria-pressed]`; the broader
  `a[href="#bookmark"][role="button"]` selector is a fallback for UI inspection.
- The save modal exposes list rows as `button.swt-save-group-info[role="checkbox"]`.
  Their accessible text includes the exact folder name, visible place count, and
  `선택됨`/`선택해제됨` state.
- In accessibility snapshots, the list row may include visibility text such as `비공개`
  before `폴더명`.
- Confirm writes with the modal's `button.swt-save-btn`, reopen the modal, and require the
  target list row to remain `선택됨` before updating local sync state.
- Use `button.swt-close-btn` to close a verification modal.
- Do not use screenshots or fixed coordinates to control the UI. Capture screenshots only
  after final failure for diagnostics.
- The `Tastyroad` list was created as a private list.
- `Tastyroad 2` is the active overflow list after the original `Tastyroad` list reached
  its 1,000-place limit.
- Always verify by opening the saved panel or the save modal and reading the visible count
  beside the target list.
