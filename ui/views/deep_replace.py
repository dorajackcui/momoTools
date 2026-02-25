from ui import strings
from ui.views.base import BaseFrame


class DeepReplaceFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        input_frame = self.create_section_card("输入文件夹")
        self.source_label = self.create_picker_with_status(
            button_text="源文件夹（替换文件）",
            command=self.controller.select_source_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
        )
        self.target_label = self.create_picker_with_status(
            button_text="目标文件夹（被替换文件）",
            command=self.controller.select_target_folder,
            default_text=strings.DEFAULT_FOLDER_TEXT,
            parent=input_frame,
        )

        action_frame = self.create_section_card("操作")
        self.create_primary_button(
            text="开始处理",
            command=self.controller.process_files,
            parent=action_frame,
            pady=0,
        )

    def set_source_folder_label(self, folder_path):
        self.set_selected_path_label(self.source_label, folder_path)

    def set_target_folder_label(self, folder_path):
        self.set_selected_path_label(self.target_label, folder_path)
