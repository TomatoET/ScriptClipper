from __future__ import annotations

from PySide6.QtCore import QByteArray, QDataStream, QIODevice, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QTabWidget, QVBoxLayout, QWidget

from scriptclipper.core.project_model import ARollAsset, BRollAsset


A_ROLL_MIME_TYPE = "application/x-scriptclipper-aroll-asset"
B_ROLL_MIME_TYPE = "application/x-scriptclipper-broll-asset"


class AssetListWidget(QListWidget):
    def __init__(self, mime_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.mime_type = mime_type

    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        item = self.currentItem()
        if not item:
            return
        asset_id = item.data(Qt.UserRole)
        if not asset_id:
            return

        payload = QByteArray()
        stream = QDataStream(payload, QIODevice.WriteOnly)
        stream.writeQString(str(asset_id))
        mime = self.model().mimeData([self.indexFromItem(item)])
        mime.setData(self.mime_type, payload)

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class AssetPanel(QWidget):
    asset_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tabs = QTabWidget()
        self.a_list = AssetListWidget(A_ROLL_MIME_TYPE)
        self.b_list = AssetListWidget(B_ROLL_MIME_TYPE)
        for list_widget in (self.a_list, self.b_list):
            list_widget.setDragEnabled(True)
            list_widget.setAlternatingRowColors(False)
            list_widget.itemClicked.connect(self._emit_asset_selected)

        self.tabs.addTab(self.a_list, "A-roll 口播")
        self.tabs.addTab(self.b_list, "B-roll 画面")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 8, 8)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

    def set_assets(self, a_roll_assets: list[ARollAsset], b_roll_assets: list[BRollAsset]) -> None:
        self._fill_a_roll(a_roll_assets)
        self._fill_b_roll(b_roll_assets)

    def _fill_a_roll(self, assets: list[ARollAsset]) -> None:
        self.a_list.clear()
        for index, asset in enumerate(assets, start=1):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, asset.id)
            card = self._make_card(f"#{index:02d}  A-roll  {asset.duration:.1f}s", asset.text)
            item.setSizeHint(card.sizeHint())
            self.a_list.addItem(item)
            self.a_list.setItemWidget(item, card)

    def _fill_b_roll(self, assets: list[BRollAsset]) -> None:
        self.b_list.clear()
        for index, asset in enumerate(assets, start=1):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, asset.id)
            card = self._make_card(f"#{index:02d}  B-roll  {asset.duration:.1f}s", asset.title, asset.note)
            item.setSizeHint(card.sizeHint())
            self.b_list.addItem(item)
            self.b_list.setItemWidget(item, card)

    def _make_card(self, meta: str, title: str, detail: str = "") -> QWidget:
        card = QFrame()
        card.setObjectName("AssetCard")
        meta_label = QLabel(meta)
        meta_label.setObjectName("AssetMeta")
        title_label = QLabel(title)
        title_label.setObjectName("AssetText")
        title_label.setWordWrap(True)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        layout.addWidget(meta_label)
        layout.addWidget(title_label)
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("MutedText")
            detail_label.setWordWrap(True)
            layout.addWidget(detail_label)
        return card

    def _emit_asset_selected(self, item: QListWidgetItem) -> None:
        self.asset_selected.emit(str(item.data(Qt.UserRole)))
