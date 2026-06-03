THEMES = {
    "Dark": """
QMainWindow, QWidget { background: #111318; color: #e5e8ef; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 13px; }
QMenuBar, QStatusBar { background: #191c23; color: #edf0f7; }
QMenu { background: #1d2028; color: #edf0f7; border: 1px solid #343a47; }
QMenuBar::item:selected, QMenu::item:selected { background: #2c3442; }
QSplitter::handle { background: #252a34; }
#PanelTitle { font-size: 16px; font-weight: 600; color: #f4f6fb; }
#MutedText { color: #8e96a8; }
QListWidget, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QTabWidget::pane {
  background: #191c23; color: #edf0f7; border: 1px solid #303642; border-radius: 6px; selection-background-color: #3a72e8; padding: 6px;
}
QTabBar::tab { background: #20242d; color: #aeb6c7; padding: 8px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #2d6cdf; color: white; }
#AssetCard { background: #20242d; border: 1px solid #343b49; border-radius: 8px; }
#AssetCard:hover { border: 1px solid #4c8dff; }
#AssetMeta { color: #78a7ff; font-weight: 600; }
#AssetText { color: #eff2f8; }
QPushButton { background: #2d6cdf; border: 1px solid #3978ed; border-radius: 6px; color: white; padding: 7px 12px; }
QPushButton:hover { background: #3978ed; }
QSlider::groove:horizontal { height: 5px; background: #303642; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; background: #78a7ff; margin: -5px 0; border-radius: 7px; }
""",
    "Light": """
QMainWindow, QWidget { background: #f4f6fa; color: #1f2430; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 13px; }
QMenuBar, QStatusBar { background: #ffffff; color: #1f2430; border-bottom: 1px solid #d8dee9; }
QMenu { background: #ffffff; color: #1f2430; border: 1px solid #ccd3df; }
QMenuBar::item:selected, QMenu::item:selected { background: #e7edf7; }
QSplitter::handle { background: #d7dde8; }
#PanelTitle { font-size: 16px; font-weight: 600; color: #111827; }
#MutedText { color: #667085; }
QListWidget, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QTabWidget::pane {
  background: #ffffff; color: #1f2430; border: 1px solid #ccd3df; border-radius: 6px; selection-background-color: #2d6cdf; padding: 6px;
}
QTabBar::tab { background: #e9eef6; color: #475467; padding: 8px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #2d6cdf; color: white; }
#AssetCard { background: #ffffff; border: 1px solid #d5dce8; border-radius: 8px; }
#AssetCard:hover { border: 1px solid #2d6cdf; }
#AssetMeta { color: #2563eb; font-weight: 600; }
#AssetText { color: #111827; }
QPushButton { background: #2d6cdf; border: 1px solid #2563eb; border-radius: 6px; color: white; padding: 7px 12px; }
QPushButton:hover { background: #2563eb; }
QSlider::groove:horizontal { height: 5px; background: #cbd5e1; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; background: #2d6cdf; margin: -5px 0; border-radius: 7px; }
""",
    "Blue": """
QMainWindow, QWidget { background: #0c1524; color: #e8f3ff; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 13px; }
QMenuBar, QStatusBar { background: #101d30; color: #e8f3ff; }
QMenu { background: #132238; color: #e8f3ff; border: 1px solid #254466; }
QMenuBar::item:selected, QMenu::item:selected { background: #1d3b5d; }
QSplitter::handle { background: #203654; }
#PanelTitle { font-size: 16px; font-weight: 600; color: #ffffff; }
#MutedText { color: #8fb3d9; }
QListWidget, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QTabWidget::pane {
  background: #111e31; color: #e8f3ff; border: 1px solid #254466; border-radius: 6px; selection-background-color: #00a6ff; padding: 6px;
}
QTabBar::tab { background: #172a43; color: #a6c8eb; padding: 8px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #00a6ff; color: #06121f; }
#AssetCard { background: #14243a; border: 1px solid #285070; border-radius: 8px; }
#AssetCard:hover { border: 1px solid #00c2ff; }
#AssetMeta { color: #69d2ff; font-weight: 600; }
#AssetText { color: #f3f9ff; }
QPushButton { background: #008bd2; border: 1px solid #00a6ff; border-radius: 6px; color: white; padding: 7px 12px; }
QPushButton:hover { background: #00a6ff; }
QSlider::groove:horizontal { height: 5px; background: #254466; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; background: #69d2ff; margin: -5px 0; border-radius: 7px; }
""",
}
