# Naver Map UI Notes

- Use Microsoft Edge through CDP on port 9222.
- Use `agent-browser --cdp 9222` on every command to avoid controlling the wrong browser session.
- Naver Map saved-list UI is only partially exposed in accessibility snapshots; use screenshots for row positions and counts.
- The `Tastyroad` list was created as a private list.
- In the 879x914 viewport used during setup, the place detail star was near `(377, 104)`, the `Tastyroad` row checkbox in the save modal was near `(421, 533)`, and the modal save button was near `(255, 860)`.
- Always verify by opening the saved panel and reading the visible count beside `Tastyroad`.
