from __future__ import annotations

from typing import ClassVar
from pathlib import Path
from collections.abc import Iterable

from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding, BindingType
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Footer, Header, MarkdownViewer, TextArea
from textual.containers import Horizontal
from textual.worker import get_current_worker
from textual_fspicker import FileOpen, FileSave, Filters


class MD(App):
    TITLE = "MD"
    SUB_TITLE = "Markdown Viewer"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(
            key="!",
            action="app.toggle_preview()",
            description="Toggle markdown preview window",
            key_display="!",
        ),
        Binding(
            key="@",
            action="app.toggle_maximize()",
            description="Maximize/restore markdown preview window",
            key_display="@",
        ),
        Binding(
            key="ctrl+o",
            action="app.open_file()",
            description="Open and read text from file",
            key_display="Ctrl+o",
        ),
        Binding(
            key="ctrl+s",
            action="app.save_file()",
            description="Save document to disk as file",
            key_display="Ctrl+s",
        ),
        Binding(
            key="ctrl+t",
            action="app.toggle_table_of_contents()",
            description="Toggle markdown table of contents",
            key_display="Ctrl+t",
        ),
    ]

    @property
    def markdown_editor(self) -> TextArea:
        return self.query_one("#markdown-editor", TextArea)

    @property
    def markdown_preview(self) -> MarkdownViewer:
        return self.query_one("#markdown-preview", MarkdownViewer)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(name="horizontal-layout", id="horizontal-layout"):
            yield TextArea.code_editor(
                id="markdown-editor",
                name="markdown-editor",
                language="markdown",
            )
            yield MarkdownViewer(
                id="markdown-preview",
                name="markdown-preview",
                show_table_of_contents=False,
            )
        yield Footer(show_command_palette=True)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "toggle_table_of_contents":
            return self.markdown_preview.display
        else:
            return True

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            title="Open file",
            help="Load a markdown document from disk.",
            callback=self.action_open_file,
        )
        yield SystemCommand(
            title="Save file",
            help="Save a markdown document to disk.",
            callback=self.action_save_file,
        )
        yield SystemCommand(
            title="Toggle preview",
            help="Toggle the markdown preview screen.",
            callback=self.action_toggle_preview,
        )
        if self.markdown_preview.display:
            yield SystemCommand(
                title="Toggle Table-of-Contents",
                help="Toggle the markdown preview screen.",
                callback=self.action_toggle_table_of_contents,
            )

    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.update_preview(event.text_area.text)

    async def action_save_file(self) -> None:
        self.save_file()

    async def action_open_file(self) -> None:
        self.open_file()

    async def action_toggle_preview(self) -> None:
        focused, preview = self.screen.focused, self.markdown_preview
        self.screen.focused = None
        preview.display = not preview.display
        if preview.display:
            self.update_preview(self.markdown_editor.text)
        self.screen.focused = focused

    async def action_toggle_maximize(self) -> None:
        if self.screen.maximized is None:
            focused = self.screen.focused
            self.screen.focused = None
            self.screen.maximized = self.markdown_preview
            self.screen.focused = focused
        else:
            self.screen.minimize()

    async def action_toggle_table_of_contents(self) -> None:
        toc = self.markdown_preview.table_of_contents
        toc.display = not toc.display

    @work(exclusive=True)
    async def open_file(self) -> None:
        if path := await self._open_file_dialog():
            try:
                self.markdown_editor.text = path.read_text()
            except OSError as e:
                self.notify(f"Failed to load document: {e}", title="Open file")
            else:
                self.notify(f"Document loaded: '{path}'", title="Open file")
        else:
            self.notify(
                "Operation cancelled.", title="Open file", severity="error"
            )

    @work(exclusive=True)
    async def save_file(self) -> None:
        if path := await self._save_file_dialog():
            try:
                path.write_text(self.markdown_editor.text)
            except OSError as e:
                self.notify(
                    f"Operation failed: {e}",
                    title="Save file",
                    severity="error",
                )
            else:
                self.notify(f"Document saved to: '{path}'", title="Save file")
        else:
            self.notify(
                "Operation cancelled.", title="Save file", severity="error"
            )

    @work(exclusive=True)
    async def update_preview(self, text: str) -> None:
        if not (worker := get_current_worker()).is_cancelled:
            await self.markdown_preview.document.update(text)

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
