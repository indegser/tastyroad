# Naver Map UI Notes

- Use the persistent `agent-browser` session named `tastyroad-naver-map-sync` by default.
- Use `agent-browser --session tastyroad-naver-map-sync --session-name tastyroad-naver-map-sync` on every manual command to avoid controlling the wrong browser session.
- Scope place actions to the `pcmap.place.naver.com` frame. The place save control is
  `a[href="#bookmark"][role="button"]`.
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
- Always verify by opening the saved panel and reading the visible count beside `Tastyroad`.
