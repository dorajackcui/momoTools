import tkinter as tk


class ToggleSwitch(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        variable,
        on_color="#0078D4",
        off_color="#E5E5E5",
        bg="#f0f0f0",
        font=("Segoe UI", 9),
        command=None,
    ):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0, takefocus=0)
        self.variable = variable
        self.on_color = on_color
        self.off_color = off_color
        self.knob_fill = "#FFFFFF"
        self.track_width = 40
        self.track_height = 20
        self.knob_padding = 2
        self.command = command

        self.canvas = tk.Canvas(
            self,
            width=self.track_width,
            height=self.track_height,
            bg=bg,
            highlightthickness=0,
            bd=0,
            takefocus=0,
        )
        self.canvas.pack(side=tk.LEFT)

        self.label = tk.Label(
            self,
            text=text,
            bg=bg,
            fg="#333333",
            font=font,
            highlightthickness=0,
            bd=0,
            takefocus=0,
        )
        self.label.pack(side=tk.LEFT, padx=(8, 0))

        self.canvas.bind("<Button-1>", self._toggle)
        self.label.bind("<Button-1>", self._toggle)
        self.bind("<Button-1>", self._toggle)

        self._trace_id = self.variable.trace_add("write", self._on_var_changed)
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        w, h = self.track_width, self.track_height
        padding = self.knob_padding
        r = h // 2
        track_color = self.on_color if self.variable.get() else self.off_color

        self.canvas.create_oval(0, 0, h, h, fill=track_color, outline="", width=0)
        self.canvas.create_rectangle(r, 0, w - r, h, fill=track_color, outline="", width=0)
        self.canvas.create_oval(w - h, 0, w, h, fill=track_color, outline="", width=0)

        knob_size = h - padding * 2
        knob_x = (w - padding - knob_size) if self.variable.get() else padding
        self.canvas.create_oval(
            knob_x,
            padding,
            knob_x + knob_size,
            padding + knob_size,
            fill=self.knob_fill,
            outline="",
            width=0,
        )

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command is not None:
            self.command()

    def _on_var_changed(self, *_args):
        self._draw()

    def destroy(self):
        if hasattr(self, "_trace_id"):
            try:
                self.variable.trace_remove("write", self._trace_id)
            except Exception:
                pass
        super().destroy()

