from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable

from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.screen import Screen
from textual.widgets import Footer, Header, MarkdownViewer, TextArea
from textual.containers import Horizontal
from textual_fspicker import FileOpen, FileSave, Filters


class MD(App):
    TITLE = "MD"
    SUB_TITLE = "Markdown Viewer"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer(show_command_palette=True)
        with Horizontal(name="horizontal-layout", id="horizontal-layout"):
            yield TextArea.code_editor(
                text="",
                language="markdown",
                max_checkpoints=100,
                name="markdown-editor",
                id="markdown-editor",
            )
            yield MarkdownViewer(
                markdown="",
                id="markdown-viewer",
                name="markdown-viewer",
                show_table_of_contents=False,
            )

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            title="Save-As",
            help="Save document to disk.",
            callback=self.save_file,
        )
        yield SystemCommand(
            title="Open File",
            help="Load document from disk.",
            callback=self.load_file,
        )
        yield SystemCommand(
            title="Toggle-Preview",
            help="Toggle the markdown preview screen.",
            callback=self.toggle_preview,
        )
        if self.markdown_preview.display:
            yield SystemCommand(
                title="Toggle-Table-of-Contents",
                help="Toggle the markdown preview screen.",
                callback=self.toggle_table_of_contents,
            )

    @property
    def markdown_editor(self) -> TextArea:
        return self.query_one("#markdown-editor", TextArea)

    @property
    def markdown_preview(self) -> MarkdownViewer:
        return self.query_one("#markdown-viewer", MarkdownViewer)

    def toggle_preview(self) -> None:
        preview = self.markdown_preview
        preview.display = not preview.display
        if preview.display:
            preview.document.update(self.markdown_editor.text)

    def toggle_table_of_contents(self) -> None:
        preview_toc = self.markdown_preview.table_of_contents
        preview_toc.display = not preview_toc.display

    @work
    async def load_file(self) -> None:
        if path := await self._open_file_dialog():
            try:
                self.markdown_editor.text = path.read_text()
            except OSError as e:
                self.notify(f"Failed to load document: {e}", title="Open-File")
            self.notify(f"Document loaded: '{path}'", title="Open-File")
        else:
            self.notify(
                "Operation cancelled.", title="Open-File", severity="error"
            )

    @work
    async def save_file(self) -> None:
        if path := await self._save_file_dialog():
            try:
                path.write_text(self.markdown_editor.text)
            except OSError as e:
                self.notify(
                    f"Operation failed: {e}", title="Save-As", severity="error"
                )
            self.notify(f"Document saved to: '{path}'", title="Save-As")
        else:
            self.notify(
                "Operation cancelled.", title="Save-As", severity="error"
            )

    @on(TextArea.Changed, "#markdown-editor")
    def update_preview(self, event: TextArea.Changed) -> None:
        preview = self.markdown_preview
        if preview.display:
            preview.document.update(event.text_area.text)
            if self.focused is event.text_area:
                preview.scroll_to(event.text_area.cursor_location[0])

    async def _open_file_dialog(self) -> Path | None:
        return await self.push_screen_wait(
            FileOpen(
                filters=Filters(
                    ("Markdown", lambda p: p.suffix.lower() == ".md"),
                    ("All Files", lambda p: True),
                )
            )
        )

    async def _save_file_dialog(self) -> Path | None:
        return await self.push_screen_wait(
            FileSave(
                save_button="Save",
                cancel_button="Cancel",
                default_file="README.md",
            )
        )
