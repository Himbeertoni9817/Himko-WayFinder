# -*- coding: utf-8 -*-
# Copyright (c) 2026 himbeertoni9817
# Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
# See LICENSE file in the project root for full license terms.

import sys
import os
import json
import heapq
import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QSignalBlocker, QEvent, QTimer
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QPainterPath, QIcon, QTransform, QFont, QBrush,
    QStandardItemModel, QStandardItem, QFontMetrics
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem,
    QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLineEdit, QLabel, QFileDialog, QSplitter,
    QListWidget, QFrame, QAbstractItemView, QGraphicsSimpleTextItem
)

TRANSLATIONS = {
    'de': {
        'edit_mode': "Bearbeitungsmodus",
        'normal_mode': "Normaler Modus",
        'open_image': "Bild öffnen",
        'save_json': "JSON Speichern",
        'load_json': "JSON Laden",
        'explorer': "Explorer",
        'properties': "Eigenschaften",
        'new_folder': "Neuer Ordner",
        'name': "Name",
        'display_name': "Anzeigename",
        'length': "Länge",
        'node_radius': "Endpunkt Radius",
        'modes': "Modi",
        'icon': "Icon",
        'route_planner': "Routenplaner",
        'start_marker': "Start-Marker",
        'add_stop': "+ Zwischenstopp",
        'calculate_route': "Route berechnen",
        'clear_route': "Route löschen",
        'travel_mode': "Hauptmodus",
        'total_distance': "Gesamtlänge",
        'select_target': "Hier Klicken, dann auf Marker",
        'no_route_found': "Keine Route gefunden!",
    },
    'en': {
        'edit_mode': "Edit Mode",
        'normal_mode': "Normal Mode",
        'open_image': "Open Image",
        'save_json': "Save JSON",
        'load_json': "Load JSON",
        'explorer': "Explorer",
        'properties': "Properties",
        'new_folder': "New Folder",
        'name': "Name",
        'display_name': "Display Name",
        'length': "Length",
        'node_radius': "Endpoint Radius",
        'modes': "Modes",
        'icon': "Icon",
        'route_planner': "Route Planner",
        'start_marker': "Start Marker",
        'add_stop': "+ Waypoint",
        'calculate_route': "Calculate Route",
        'clear_route': "Clear Route",
        'travel_mode': "Primary Mode",
        'total_distance': "Total Distance",
        'select_target': "Click here, then on Marker",
        'no_route_found': "No route found!",
    }
}

UNIT_FACTORS = {
    'mm': 0.001,
    'cm': 0.01,
    'm': 1.0,
    'km': 1000.0,
    'lichtjahre': 9.461e15,
    'lightyears': 9.461e15
}

class OutlinedTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text="", font_size=12, parent=None):
        super().__init__(text, parent)
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        self.setFont(font)
        self.setPen(QPen(QColor(0, 0, 0), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.setBrush(QBrush(QColor(255, 255, 255)))

    def paint(self, painter, option, widget):
        if not self.text():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        fm = QFontMetrics(self.font())
        path = QPainterPath()
        path.addText(0, fm.ascent(), self.font(), self.text())
        
        painter.strokePath(path, self.pen())
        painter.fillPath(path, self.brush())

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setEditable(True)
        if self.lineEdit():
            self.lineEdit().setReadOnly(True)
        self.view().viewport().installEventFilter(self)
        self._changed_callback = None

    def eventFilter(self, widget, event):
        if widget == self.view().viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self._model.itemFromIndex(index)
                if item:
                    new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                    item.setCheckState(new_state)
                    self.update_display_text()
                    if self._changed_callback:
                        self._changed_callback()
            return True
        return super().eventFilter(widget, event)

    def add_checkable_item(self, text, checked=False):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._model.appendRow(item)
        self.update_display_text()

    def get_checked_items(self):
        checked = []
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                checked.append(item.text())
        return checked

    def update_display_text(self):
        checked = self.get_checked_items()
        text = ", ".join(checked) if checked else "Keine"
        self.setEditText(text)

class ControlHandle(QGraphicsEllipseItem):
    def __init__(self, point_type, line_item):
        super().__init__(-6, -6, 12, 12, line_item)
        self.point_type = point_type
        self.line_item = line_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setBrush(QColor(255, 0, 0) if point_type != 'ctrl' else QColor(0, 120, 255))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setZValue(100)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.line_item:
            new_pos = self.pos()
            if self.point_type == 'p1':
                self.line_item.p1 = new_pos
            elif self.point_type == 'p2':
                self.line_item.p2 = new_pos
            elif self.point_type == 'ctrl':
                self.line_item.ctrl = new_pos
            self.line_item.update_path(from_handle=True)
        return super().itemChange(change, value)
    
class CurveLineItem(QGraphicsPathItem):
    def __init__(self, id_str, p1, p2, ctrl=None):
        super().__init__()
        self.id_str = id_str
        self.p1 = p1
        self.p2 = p2
        self.ctrl = ctrl if ctrl else QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        
        self.is_edit = True
        self.is_custom_length = False
        self.name = id_str
        self.display_name = ""
        self.length_val = 100.0
        self.length_unit = "m"
        self.node_radius = 8.0
        self.modes = ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"]
        
        self.circle1 = QGraphicsEllipseItem(self)
        self.circle2 = QGraphicsEllipseItem(self)
        
        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
        self.circle1.setPen(pen)
        self.circle2.setPen(pen)
        self.circle1.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.circle2.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        self.handle_p1 = ControlHandle('p1', self)
        self.handle_p2 = ControlHandle('p2', self)
        self.handle_ctrl = ControlHandle('ctrl', self)
        
        self.text_item = OutlinedTextItem("", font_size=14, parent=self)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QPen(QColor(50, 50, 50), 3))
        self.update_path()

    def update_node_radius(self, r):
        self.node_radius = r
        r_neg = -r
        d = r * 2
        self.circle1.setRect(r_neg, r_neg, d, d)
        self.circle2.setRect(r_neg, r_neg, d, d)

    def update_path(self, from_handle=False):
        path = QPainterPath()
        path.moveTo(self.p1)
        path.quadTo(self.ctrl, self.p2)
        self.setPath(path)
        
        if not self.is_custom_length:
            self.length_val = round(path.length(), 1)

        self.update_node_radius(self.node_radius)
        self.circle1.setPos(self.p1)
        self.circle2.setPos(self.p2)
        
        if not from_handle:
            self.handle_p1.setPos(self.p1)
            self.handle_p2.setPos(self.p2)
            self.handle_ctrl.setPos(self.ctrl)
            
        mid_pt = path.pointAtPercent(0.5)
        angle = path.angleAtPercent(0.5)
        
        if 90 < angle < 270:
            angle -= 180
            
        rect = self.text_item.boundingRect()
        self.text_item.setTransformOriginPoint(rect.center())
        self.text_item.setPos(mid_pt.x() - rect.width() / 2, mid_pt.y() - rect.height() / 2)
        self.text_item.setRotation(-angle)

    def set_edit_mode(self, is_edit):
        self.is_edit = is_edit
        self.circle1.setVisible(is_edit)
        self.circle2.setVisible(is_edit)
        show_handles = is_edit and self.isSelected()
        self.handle_p1.setVisible(show_handles)
        self.handle_p2.setVisible(show_handles)
        self.handle_ctrl.setVisible(show_handles)
        
        if not is_edit:
            self.setSelected(False)
            self.setPen(QPen(Qt.PenStyle.NoPen))
            self.text_item.setVisible(bool(self.display_name))
        else:
            self.text_item.setVisible(False)
            self.update_selection_pen()

    def update_selection_pen(self):
        if not self.is_edit:
            self.setPen(QPen(Qt.PenStyle.NoPen))
            return
        sel = self.isSelected()
        self.handle_p1.setVisible(sel)
        self.handle_p2.setVisible(sel)
        self.handle_ctrl.setVisible(sel)
        if sel:
            self.setPen(QPen(QColor(0, 120, 255), 4))
        else:
            self.setPen(QPen(QColor(50, 50, 50), 3))

    def update_text_display(self, text):
        self.display_name = text
        self.text_item.setText(text)
        self.update_path()

class MapMarkerItem(QGraphicsPixmapItem):
    def __init__(self, id_str, pos, icon_path=""):
        super().__init__()
        self.id_str = id_str
        self.name = id_str
        self.display_name = id_str
        self.icon_rel_path = icon_path
        self.base_pixmap = None
        
        self.text_item = OutlinedTextItem("", font_size=12, parent=self)
        
        self.setPos(pos)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        self.load_icon_image(icon_path)

    def load_icon_image(self, icon_path):
        self.icon_rel_path = icon_path if icon_path else ""
        
        if os.path.isabs(self.icon_rel_path):
            full_p = self.icon_rel_path
        else:
            full_p = os.path.join(os.path.dirname(__file__), self.icon_rel_path)
            
        full_p = os.path.normpath(full_p)

        if os.path.exists(full_p) and self.icon_rel_path:
            pix = QPixmap(full_p)
            if not pix.isNull():
                self.base_pixmap = pix
            else:
                self.base_pixmap = QPixmap(32, 32)
                self.base_pixmap.fill(Qt.GlobalColor.red)
        else:
            self.base_pixmap = QPixmap(32, 32)
            self.base_pixmap.fill(Qt.GlobalColor.red)
        
        self.update_scale_size(1.0)

    def update_scale_size(self, view_scale):
        if not self.base_pixmap or self.base_pixmap.isNull():
            return
        
        max_display_px = 32.0
        target_size = min(max_display_px, max(12.0, max_display_px / max(0.001, view_scale)))
        
        scaled = self.base_pixmap.scaled(
            int(target_size), int(target_size),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.setOffset(-scaled.width() / 2, -scaled.height() / 2)
        self.update_text_position()

    def update_text_position(self):
        self.text_item.setText(self.display_name)
        rect = self.text_item.boundingRect()
        icon_h = self.pixmap().height() if not self.pixmap().isNull() else 32
        self.text_item.setPos(-rect.width() / 2, icon_h / 2 + 2)

    def set_edit_mode(self, is_edit):
        if not is_edit:
            self.setSelected(False)
            self.update_text_position()
            self.text_item.setVisible(True)
        else:
            self.text_item.setVisible(False)

class MapGraphicsView(QGraphicsView):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.bg_pixmap_item = None
        self.is_panning = False
        self.pan_start = QPointF()
        
        self.drawing_line = False
        self.line_start_pt = None
        self.temp_path_item = None
        
        self.route_graphics_items = []

    def set_background_image(self, path):
        if self.bg_pixmap_item and self.bg_pixmap_item.scene() == self.scene:
            self.scene.removeItem(self.bg_pixmap_item)
            self.bg_pixmap_item = None
            
        self.clear_route_display()
        if not os.path.exists(path):
            return
        pix = QPixmap(path)
        if pix.isNull():
            return
        self.bg_pixmap_item = self.scene.addPixmap(pix)
        self.bg_pixmap_item.setZValue(-100)
        self.setSceneRect(QRectF(pix.rect()))

    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1.0 / zoom_in
        sf = zoom_in if event.angleDelta().y() > 0 else zoom_out
        self.scale(sf, sf)
        self.main_win.update_zoom_scales()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        scene_pos = self.mapToScene(event.pos())
        
        if self.main_win.picking_target_marker:
            items = self.scene.items(scene_pos)
            marker = None
            for it in items:
                curr = it
                while curr:
                    if isinstance(curr, MapMarkerItem):
                        marker = curr
                        break
                    curr = curr.parentItem()
                if marker:
                    break
            if marker:
                self.main_win.on_marker_picked(marker)
                event.accept()
                return

        if self.main_win.is_edit_mode:
            tool = self.main_win.current_tool
            if tool == "line":
                if event.button() == Qt.MouseButton.LeftButton:
                    if not self.drawing_line:
                        self.drawing_line = True
                        self.line_start_pt = scene_pos
                        self.temp_path_item = QGraphicsPathItem()
                        self.temp_path_item.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                        self.scene.addItem(self.temp_path_item)
                    else:
                        self.drawing_line = False
                        start_pt = self.line_start_pt
                        if self.temp_path_item:
                            self.scene.removeItem(self.temp_path_item)
                            self.temp_path_item = None
                        
                        self.main_win.create_new_line(start_pt, scene_pos)
                        self.main_win.set_tool("select")
                    event.accept()
                    return
            elif tool == "marker":
                if event.button() == Qt.MouseButton.LeftButton:
                    self.main_win.create_new_marker(scene_pos)
                    self.main_win.set_tool("select")
                    event.accept()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        if self.drawing_line and self.temp_path_item:
            scene_pos = self.mapToScene(event.pos())
            p = QPainterPath()
            p.moveTo(self.line_start_pt)
            p.lineTo(scene_pos)
            self.temp_path_item.setPath(p)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def clear_route_display(self):
        for item in self.route_graphics_items:
            if item.scene() == self.scene:
                self.scene.removeItem(item)
        self.route_graphics_items.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'de'
        self.is_edit_mode = False
        self.current_tool = "select"
        self.picking_target_marker = False
        self.active_waypoint_btn = None
        self.current_image_filename = ""
        
        self.items_dict = {}
        self.line_counter = 1
        self.marker_counter = 1
        self.folder_counter = 1
        
        self.init_ui()

    def get_maps_dir(self):
        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "maps"))
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir, exist_ok=True)
        return maps_dir

    def tr(self, key):
        return TRANSLATIONS[self.current_lang].get(key, key)

    def init_ui(self):
        self.setWindowTitle("Himko WayFinder")
        self.setGeometry(100, 100, 1280, 800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.outer_layout = QVBoxLayout(self.central_widget)
        self.outer_layout.setContentsMargins(4, 4, 4, 4)
        
        self.top_file_bar = QHBoxLayout()
        self.btn_open_img = QPushButton()
        self.btn_save_json = QPushButton()
        self.btn_load_json = QPushButton()
        
        self.btn_open_img.clicked.connect(self.open_image_dialog)
        self.btn_save_json.clicked.connect(self.save_json_dialog)
        self.btn_load_json.clicked.connect(self.load_json_dialog)
        
        self.top_file_bar.addWidget(self.btn_open_img)
        self.top_file_bar.addWidget(self.btn_save_json)
        self.top_file_bar.addWidget(self.btn_load_json)
        self.top_file_bar.addStretch()
        
        self.outer_layout.addLayout(self.top_file_bar)
        
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = MapGraphicsView(self)
        
        self.edit_panel = QWidget()
        self.normal_panel = QWidget()
        
        self.setup_edit_panel()
        self.setup_normal_panel()
        
        self.main_layout.addWidget(self.view, stretch=1)
        self.main_layout.addWidget(self.edit_panel)
        self.main_layout.addWidget(self.normal_panel)
        
        self.outer_layout.addLayout(self.main_layout)
        
        self.edit_panel.setVisible(False)
        self.normal_panel.setVisible(True)
        
        self.view_overlay_btn = QPushButton("✏️ Mode", self.view)
        self.view_overlay_btn.setFixedSize(120, 32)
        self.view_overlay_btn.move(10, 10)
        self.view_overlay_btn.clicked.connect(self.toggle_mode)
        
        self.view.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.apply_translations()

    def setup_edit_panel(self):
        layout = QHBoxLayout(self.edit_panel)
        layout.setContentsMargins(4, 4, 4, 4)
        
        left_toolbar = QVBoxLayout()
        self.btn_select = QPushButton("👆")
        self.btn_line = QPushButton("📈")
        self.btn_marker = QPushButton("📍")
        
        self.btn_select.setCheckable(True)
        self.btn_line.setCheckable(True)
        self.btn_marker.setCheckable(True)
        self.btn_select.setChecked(True)
        
        self.btn_select.clicked.connect(lambda: self.set_tool("select"))
        self.btn_line.clicked.connect(lambda: self.set_tool("line"))
        self.btn_marker.clicked.connect(lambda: self.set_tool("marker"))
        
        left_toolbar.addWidget(self.btn_select)
        left_toolbar.addWidget(self.btn_line)
        left_toolbar.addWidget(self.btn_marker)
        left_toolbar.addStretch()
        
        right_side = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        top_box = QWidget()
        top_lay = QVBoxLayout(top_box)
        top_lay.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        self.lbl_explorer = QLabel()
        self.btn_add_folder = QPushButton("+ 📁")
        self.btn_add_folder.clicked.connect(self.create_new_folder)
        top_bar.addWidget(self.lbl_explorer)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_add_folder)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        self.tree.installEventFilter(self)
        
        top_lay.addLayout(top_bar)
        top_lay.addWidget(self.tree)
        
        bottom_box = QWidget()
        bot_lay = QVBoxLayout(bottom_box)
        bot_lay.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_props = QLabel()
        self.prop_table = QTableWidget()
        self.prop_table.setColumnCount(2)
        self.prop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prop_table.horizontalHeader().setVisible(False)
        
        bot_lay.addWidget(self.lbl_props)
        bot_lay.addWidget(self.prop_table)
        
        splitter.addWidget(top_box)
        splitter.addWidget(bottom_box)
        
        right_side.addWidget(splitter)
        layout.addLayout(left_toolbar)
        layout.addLayout(right_side)

    def setup_normal_panel(self):
        lay = QVBoxLayout(self.normal_panel)
        
        self.lbl_route_title = QLabel()
        self.lbl_route_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItems(["Deutsch", "English"])
        self.cmb_lang.currentIndexChanged.connect(self.change_language)
        
        lay.addWidget(self.lbl_route_title)
        lay.addWidget(self.cmb_lang)
        
        line_frame = QFrame()
        line_frame.setFrameShape(QFrame.Shape.HLine)
        lay.addWidget(line_frame)
        
        self.lbl_mode_sel = QLabel()
        self.cmb_primary_mode = QComboBox()
        self.cmb_primary_mode.addItems(["Auto", "ÖPNV", "Fuß", "Fahrrad", "Flugzeug"])
        
        lay.addWidget(self.lbl_mode_sel)
        lay.addWidget(self.cmb_primary_mode)
        
        self.lbl_start = QLabel()
        self.cmb_start_marker = QComboBox()
        lay.addWidget(self.lbl_start)
        lay.addWidget(self.cmb_start_marker)
        
        self.waypoints_container = QVBoxLayout()
        lay.addLayout(self.waypoints_container)
        
        self.btn_add_waypoint = QPushButton("+")
        self.btn_add_waypoint.clicked.connect(self.add_waypoint_field)
        lay.addWidget(self.btn_add_waypoint)
        
        self.btn_calc_route = QPushButton()
        self.btn_calc_route.clicked.connect(self.run_route_algorithm)
        lay.addWidget(self.btn_calc_route)

        self.btn_clear_route = QPushButton()
        self.btn_clear_route.clicked.connect(self.clear_route_all)
        lay.addWidget(self.btn_clear_route)
        
        self.lbl_dist_res = QLabel()
        self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: green;")
        lay.addWidget(self.lbl_dist_res)
        
        lay.addStretch()

    def apply_translations(self):
        t = TRANSLATIONS[self.current_lang]
        self.view_overlay_btn.setText(t['edit_mode'] if not self.is_edit_mode else t['normal_mode'])
        
        self.lbl_explorer.setText(t['explorer'])
        self.lbl_props.setText(t['properties'])
        self.btn_open_img.setText(t['open_image'])
        self.btn_save_json.setText(t['save_json'])
        self.btn_load_json.setText(t['load_json'])
        
        self.lbl_route_title.setText(t['route_planner'])
        self.lbl_mode_sel.setText(t['travel_mode'])
        self.lbl_start.setText(t['start_marker'])
        self.btn_add_waypoint.setText(t['add_stop'])
        self.btn_calc_route.setText(t['calculate_route'])
        self.btn_clear_route.setText(t['clear_route'])

    def change_language(self, index):
        self.current_lang = 'de' if index == 0 else 'en'
        self.apply_translations()

    def clear_route_all(self):
        self.view.clear_route_display()
        self.lbl_dist_res.setText("")

    def toggle_mode(self):
        self.clear_route_all()
        self.is_edit_mode = not self.is_edit_mode
        self.edit_panel.setVisible(self.is_edit_mode)
        self.normal_panel.setVisible(not self.is_edit_mode)
        
        for item in self.scene_all_items():
            if isinstance(item, (CurveLineItem, MapMarkerItem)):
                item.set_edit_mode(self.is_edit_mode)
        
        if not self.is_edit_mode:
            self.populate_marker_combos()
            
        self.apply_translations()

    def scene_all_items(self):
        return self.view.scene.items()

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        self.btn_select.setChecked(tool_name == "select")
        self.btn_line.setChecked(tool_name == "line")
        self.btn_marker.setChecked(tool_name == "marker")

    def create_new_line(self, p1, p2):
        id_str = f"Line_{self.line_counter}"
        self.line_counter += 1
        
        line_item = CurveLineItem(id_str, p1, p2)
        line_item.set_edit_mode(True)
        self.view.scene.addItem(line_item)
        line_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, id_str)
            tree_item.setIcon(0, self.get_app_icon("line.png"))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, id_str)
            self.tree.addTopLevelItem(tree_item)
            self.tree.setCurrentItem(tree_item)
        
        self.items_dict[id_str] = {'graphics': line_item, 'tree': tree_item, 'type': 'line'}
        self.build_properties_table(id_str)
        self.update_zoom_scales()

    def create_new_marker(self, pos):
        id_str = f"Marker_{self.marker_counter}"
        self.marker_counter += 1
        
        marker_item = MapMarkerItem(id_str, pos, "icons/marker/default.png")
        marker_item.set_edit_mode(True)
        self.view.scene.addItem(marker_item)
        marker_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, id_str)
            tree_item.setIcon(0, self.get_app_icon("marker.png"))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, id_str)
            self.tree.addTopLevelItem(tree_item)
            self.tree.setCurrentItem(tree_item)
            
        self.items_dict[id_str] = {'graphics': marker_item, 'tree': tree_item, 'type': 'marker'}
        self.build_properties_table(id_str)
        self.update_zoom_scales()

    def create_new_folder(self):
        id_str = f"Folder_{self.folder_counter}"
        self.folder_counter += 1
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem()
            tree_item.setText(0, id_str)
            tree_item.setIcon(0, self.get_app_icon("folder.png"))
            tree_item.setFlags(
                tree_item.flags() | 
                Qt.ItemFlag.ItemIsEditable | 
                Qt.ItemFlag.ItemIsDragEnabled | 
                Qt.ItemFlag.ItemIsDropEnabled
            )
            tree_item.setData(0, Qt.ItemDataRole.UserRole, id_str)
            self.tree.addTopLevelItem(tree_item)
            
        self.items_dict[id_str] = {'graphics': None, 'tree': tree_item, 'type': 'folder'}

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        else:
            super().keyPressEvent(event)

    def delete_selected_item(self):
        if not self.is_edit_mode:
            return
        selected_tree_items = self.tree.selectedItems()
        if not selected_tree_items:
            return
        tree_item = selected_tree_items[0]
        id_str = tree_item.data(0, Qt.ItemDataRole.UserRole)
        if id_str in self.items_dict:
            d = self.items_dict[id_str]
            g = d['graphics']
            if g and g.scene() == self.view.scene:
                self.view.scene.removeItem(g)
            
            parent = tree_item.parent()
            if parent:
                parent.removeChild(tree_item)
            else:
                idx = self.tree.indexOfTopLevelItem(tree_item)
                self.tree.takeTopLevelItem(idx)
                
            del self.items_dict[id_str]
            self.prop_table.setRowCount(0)
            self.populate_marker_combos()

    def get_app_icon(self, name):
        p = os.path.join(os.path.dirname(__file__), "icons", "app", name)
        if os.path.exists(p):
            return QIcon(p)
        return QIcon()

    def eventFilter(self, source, event):
        if source == self.tree and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_F2:
                item = self.tree.currentItem()
                if item:
                    self.tree.editItem(item, 0)
                    return True
        return super().eventFilter(source, event)

    def on_tree_item_changed(self, item, column):
        id_str = item.data(0, Qt.ItemDataRole.UserRole)
        if id_str in self.items_dict:
            new_text = item.text(0)
            gitem = self.items_dict[id_str]['graphics']
            if gitem:
                gitem.name = new_text

    def on_tree_selection_changed(self):
        selected_tree_items = self.tree.selectedItems()
        
        with QSignalBlocker(self.view.scene):
            for item in self.scene_all_items():
                if isinstance(item, (CurveLineItem, MapMarkerItem)):
                    item.setSelected(False)
                    if isinstance(item, CurveLineItem):
                        item.update_selection_pen()

        if not selected_tree_items:
            self.prop_table.setRowCount(0)
            return
            
        tree_item = selected_tree_items[0]
        id_str = tree_item.data(0, Qt.ItemDataRole.UserRole)
        
        if id_str in self.items_dict:
            data = self.items_dict[id_str]
            gitem = data['graphics']
            
            if gitem:
                with QSignalBlocker(self.view.scene):
                    gitem.setSelected(True)
                    if isinstance(gitem, CurveLineItem):
                        gitem.update_selection_pen()
                self.build_properties_table(id_str)
            else:
                self.prop_table.setRowCount(0)
        else:
            self.prop_table.setRowCount(0)

    def on_scene_selection_changed(self):
        if not self.is_edit_mode:
            return
        selected_gitems = [i for i in self.view.scene.selectedItems() if isinstance(i, (CurveLineItem, MapMarkerItem))]
        
        for item in self.scene_all_items():
            if isinstance(item, CurveLineItem):
                item.update_selection_pen()
                
        if not selected_gitems:
            with QSignalBlocker(self.tree):
                self.tree.clearSelection()
            self.prop_table.setRowCount(0)
            return
            
        gitem = selected_gitems[0]
        for id_str, d in self.items_dict.items():
            if d['graphics'] == gitem:
                with QSignalBlocker(self.tree):
                    self.tree.setCurrentItem(d['tree'])
                self.build_properties_table(id_str)
                break

    def build_properties_table(self, id_str):
        self.prop_table.clear()
        self.prop_table.setRowCount(0)
        
        data = self.items_dict.get(id_str)
        if not data or not data['graphics']:
            return
            
        gitem = data['graphics']
        t = TRANSLATIONS[self.current_lang]
        
        if data['type'] == 'line':
            self.prop_table.setRowCount(5)
            
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name)
            le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)
            
            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name)
            le_dname.textChanged.connect(lambda txt: gitem.update_text_display(txt))
            self.prop_table.setCellWidget(1, 1, le_dname)
            
            self.prop_table.setItem(2, 0, QTableWidgetItem(t['length']))
            w_len = QWidget()
            l_len = QHBoxLayout(w_len)
            l_len.setContentsMargins(0, 0, 0, 0)
            le_val = QLineEdit(str(gitem.length_val))
            cmb_u = QComboBox()
            cmb_u.addItems(["mm", "cm", "m", "km", "lichtjahre"])
            cmb_u.setCurrentText(gitem.length_unit)
            
            le_val.textChanged.connect(lambda txt: self.set_line_length_val(gitem, txt))
            cmb_u.currentTextChanged.connect(lambda txt: self.set_line_length_unit(gitem, txt))
            
            l_len.addWidget(le_val)
            l_len.addWidget(cmb_u)
            self.prop_table.setCellWidget(2, 1, w_len)
            
            self.prop_table.setItem(3, 0, QTableWidgetItem(t['node_radius']))
            le_radius = QLineEdit(str(gitem.node_radius))
            le_radius.textChanged.connect(lambda txt: self.set_line_node_radius(gitem, txt))
            self.prop_table.setCellWidget(3, 1, le_radius)

            self.prop_table.setItem(4, 0, QTableWidgetItem(t['modes']))
            chk_combo = CheckableComboBox()
            for m in ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"]:
                chk_combo.add_checkable_item(m, m in gitem.modes)
            
            chk_combo._changed_callback = lambda combo=chk_combo, target=gitem: setattr(target, 'modes', combo.get_checked_items())
            self.prop_table.setCellWidget(4, 1, chk_combo)

        elif data['type'] == 'marker':
            self.prop_table.setRowCount(3)
            
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name)
            le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)
            
            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name)
            le_dname.textChanged.connect(lambda txt: (setattr(gitem, 'display_name', txt), gitem.update_text_position()))
            self.prop_table.setCellWidget(1, 1, le_dname)
            
            self.prop_table.setItem(2, 0, QTableWidgetItem(t['icon']))
            cmb_icon = QComboBox()
            
            marker_icons_dir = os.path.join(os.path.dirname(__file__), "icons", "marker")
            icon_files = []
            if os.path.exists(marker_icons_dir):
                icon_files = [os.path.join("icons", "marker", f) for f in os.listdir(marker_icons_dir) if f.endswith(('.png', '.jpg'))]
            
            for path in icon_files:
                cmb_icon.addItem(os.path.basename(path), path)
                
            cmb_icon.currentIndexChanged.connect(lambda idx: gitem.load_icon_image(cmb_icon.itemData(idx)))
            self.prop_table.setCellWidget(2, 1, cmb_icon)

    def set_line_length_val(self, gitem, txt):
        try:
            val = float(txt)
            if val >= 0:
                gitem.length_val = val
                gitem.is_custom_length = True
        except ValueError:
            pass

    def set_line_length_unit(self, gitem, txt):
        gitem.length_unit = txt

    def set_line_node_radius(self, gitem, txt):
        try:
            val = float(txt)
            if val > 0:
                gitem.update_node_radius(val)
        except ValueError:
            pass

    def update_item_name(self, id_str, new_name):
        d = self.items_dict.get(id_str)
        if d:
            with QSignalBlocker(self.tree):
                d['tree'].setText(0, new_name)
            if d['graphics']:
                d['graphics'].name = new_name

    def update_zoom_scales(self):
        scale_factor = self.view.transform().m11()
        if scale_factor <= 0:
            return
        for item in self.scene_all_items():
            if isinstance(item, MapMarkerItem):
                item.update_scale_size(scale_factor)

    def open_image_dialog(self):
        maps_folder = os.path.join(os.path.dirname(__file__), "maps")
        if not os.path.exists(maps_folder):
            os.makedirs(maps_folder, exist_ok=True)
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Use Image", maps_folder, "Bilder (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.current_image_filename = os.path.basename(file_path)
            self.view.set_background_image(file_path)

    def save_json_dialog(self):
        maps_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "maps")).replace("\\", "/")
        os.makedirs(maps_folder, exist_ok=True)

        path, _ = QFileDialog.getSaveFileName(self, "Save", maps_folder, "JSON Files (*.json)")
        if not path:
            return
            
        lines_data = []
        markers_data = []
        folders_data = []

        # Rekursive Funktion zum Speichern von Baumknoten & Eltern-Kind-Beziehungen
        def process_tree_item(tree_item, parent_id=None):
            id_str = tree_item.data(0, Qt.ItemDataRole.UserRole)
            if not id_str or id_str not in self.items_dict:
                return

            d = self.items_dict[id_str]
            item_type = d['type']
            g = d['graphics']

            if item_type == 'folder':
                folders_data.append({
                    'id': id_str,
                    'name': tree_item.text(0),
                    'parent': parent_id
                })
            elif item_type == 'line' and g:
                lines_data.append({
                    'id': id_str,
                    'name': g.name,
                    'display_name': g.display_name,
                    'p1': [g.p1.x(), g.p1.y()],
                    'p2': [g.p2.x(), g.p2.y()],
                    'ctrl': [g.ctrl.x(), g.ctrl.y()],
                    'length_val': g.length_val,
                    'length_unit': g.length_unit,
                    'node_radius': g.node_radius,
                    'modes': g.modes,
                    'parent': parent_id
                })
            elif item_type == 'marker' and g:
                markers_data.append({
                    'id': id_str,
                    'name': g.name,
                    'display_name': g.display_name,
                    'pos': [g.pos().x(), g.pos().y()],
                    'icon': g.icon_rel_path,
                    'parent': parent_id
                })

            for child_idx in range(tree_item.childCount()):
                process_tree_item(tree_item.child(child_idx), parent_id=id_str)

        # Alle Top-Level-Einträge durchgehen
        for top_idx in range(self.tree.topLevelItemCount()):
            process_tree_item(self.tree.topLevelItem(top_idx), parent_id=None)

        out = {
            'image': self.current_image_filename,
            'folders': folders_data,
            'lines': lines_data,
            'markers': markers_data
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=4)

    def load_json_dialog(self):
        maps_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "maps")).replace("\\", "/")
        os.makedirs(maps_folder, exist_ok=True)

        path, _ = QFileDialog.getOpenFileName(self, "Öffnen", maps_folder, "JSON Files (*.json)")
        if not path:
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.view.scene.clear()
        self.view.bg_pixmap_item = None
        self.items_dict.clear()
        self.tree.clear()
        
        img_name = data.get('image', '')
        self.current_image_filename = img_name
        if img_name:
            img_path = os.path.join(maps_folder, img_name)
            if os.path.exists(img_path):
                self.view.set_background_image(img_path)

        created_tree_items = {}

        # 1. Ordner laden und im Baum erstellen
        for f in data.get('folders', []):
            f_id = f['id']
            tree_item = QTreeWidgetItem()
            tree_item.setText(0, f.get('name', f_id))
            tree_item.setIcon(0, self.get_app_icon("folder.png"))
            tree_item.setFlags(
                tree_item.flags() | 
                Qt.ItemFlag.ItemIsEditable | 
                Qt.ItemFlag.ItemIsDragEnabled | 
                Qt.ItemFlag.ItemIsDropEnabled
            )
            tree_item.setData(0, Qt.ItemDataRole.UserRole, f_id)
            created_tree_items[f_id] = tree_item
            self.items_dict[f_id] = {'graphics': None, 'tree': tree_item, 'type': 'folder'}

        # 2. Linien laden
        for l in data.get('lines', []):
            l_id = l['id']
            p1 = QPointF(l['p1'][0], l['p1'][1])
            p2 = QPointF(l['p2'][0], l['p2'][1])
            ctrl = QPointF(l['ctrl'][0], l['ctrl'][1])
            
            line_item = CurveLineItem(l_id, p1, p2, ctrl)
            line_item.name = l.get('name', l_id)
            line_item.update_text_display(l.get('display_name', ''))
            line_item.length_val = l.get('length_val', round(line_item.path().length(), 1))
            line_item.is_custom_length = 'length_val' in l
            line_item.length_unit = l.get('length_unit', 'm')
            line_item.node_radius = l.get('node_radius', 8.0)
            line_item.modes = l.get('modes', ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"])
            
            line_item.set_edit_mode(self.is_edit_mode)
            self.view.scene.addItem(line_item)
            
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, line_item.name)
            tree_item.setIcon(0, self.get_app_icon("line.png"))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, l_id)
            
            created_tree_items[l_id] = tree_item
            self.items_dict[l_id] = {'graphics': line_item, 'tree': tree_item, 'type': 'line'}

        # 3. Marker laden
        for m in data.get('markers', []):
            m_id = m['id']
            pos = QPointF(m['pos'][0], m['pos'][1])
            marker_item = MapMarkerItem(m_id, pos, m.get('icon', ''))
            marker_item.name = m.get('name', m_id)
            marker_item.display_name = m.get('display_name', m_id)
            
            marker_item.set_edit_mode(self.is_edit_mode)
            self.view.scene.addItem(marker_item)
            
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, marker_item.name)
            tree_item.setIcon(0, self.get_app_icon("marker.png"))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, m_id)
            
            created_tree_items[m_id] = tree_item
            self.items_dict[m_id] = {'graphics': marker_item, 'tree': tree_item, 'type': 'marker'}

        # 4. Hierarchie im Baum (Ordner-Verknüpfungen) neu aufbauen
        all_elements = data.get('folders', []) + data.get('lines', []) + data.get('markers', [])
        for elem in all_elements:
            e_id = elem['id']
            parent_id = elem.get('parent')
            t_item = created_tree_items.get(e_id)
            if not t_item:
                continue

            if parent_id and parent_id in created_tree_items:
                parent_tree_item = created_tree_items[parent_id]
                parent_tree_item.addChild(t_item)
            else:
                self.tree.addTopLevelItem(t_item)
            
        self.populate_marker_combos()
        self.update_zoom_scales()

    def populate_marker_combos(self):
        self.cmb_start_marker.clear()
        for id_str, d in self.items_dict.items():
            if d['type'] == 'marker' and d['graphics']:
                self.cmb_start_marker.addItem(d['graphics'].display_name or d['graphics'].name, id_str)

    def add_waypoint_field(self):
        row_w = QWidget()
        lay = QHBoxLayout(row_w)
        lay.setContentsMargins(0, 0, 0, 0)
        
        btn_pick = QPushButton(self.tr('select_target'))
        btn_pick.clicked.connect(lambda checked, b=btn_pick: self.start_picking_marker(b))
        
        btn_rem = QPushButton("❌")
        btn_rem.setFixedWidth(30)
        btn_rem.clicked.connect(lambda checked, r=row_w: self.remove_waypoint_field(r))
        
        lay.addWidget(btn_pick)
        lay.addWidget(btn_rem)
        
        self.waypoints_container.addWidget(row_w)

    def remove_waypoint_field(self, widget):
        if self.active_waypoint_btn and widget.isAncestorOf(self.active_waypoint_btn):
            self.picking_target_marker = False
            self.active_waypoint_btn = None
            
        self.waypoints_container.removeWidget(widget)
        widget.deleteLater()

    def start_picking_marker(self, btn):
        self.picking_target_marker = True
        self.active_waypoint_btn = btn
        btn.setText("...")

    def on_marker_picked(self, marker_item):
        if self.active_waypoint_btn:
            try:
                self.active_waypoint_btn.setText(marker_item.display_name or marker_item.name)
                self.active_waypoint_btn.setProperty("marker_id", marker_item.id_str)
            except RuntimeError:
                pass
        self.picking_target_marker = False
        self.active_waypoint_btn = None

    def run_route_algorithm(self):
        self.clear_route_all()
        start_id = self.cmb_start_marker.currentData()
        if not start_id:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return
            
        target_ids = []
        for i in range(self.waypoints_container.count()):
            w = self.waypoints_container.itemAt(i).widget()
            if w:
                btn = w.findChild(QPushButton)
                if btn:
                    mid = btn.property("marker_id")
                    if mid:
                        target_ids.append(mid)
                    
        if not target_ids:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return

        selected_mode = self.cmb_primary_mode.currentText()
        all_stops = [start_id] + target_ids
        
        total_path_elements = []
        total_len_meters = 0.0
        route_failed = False
        
        for i in range(len(all_stops) - 1):
            s_id = all_stops[i]
            e_id = all_stops[i+1]
            sub_elements, sub_len = self.find_path_between_markers(s_id, e_id, selected_mode)
            if sub_elements:
                total_path_elements.extend(sub_elements)
                total_len_meters += sub_len
            else:
                route_failed = True
                break
                
        if route_failed or not total_path_elements:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return

        self.render_route(total_path_elements, selected_mode)
        
        display_text = f"{self.tr('total_distance')}: {total_len_meters:.2f} m"
        if total_len_meters > 1000:
            display_text = f"{self.tr('total_distance')}: {total_len_meters/1000.0:.2f} km"
        self.lbl_dist_res.setText(display_text)
        self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: green;")

    def find_path_between_markers(self, start_m_id, end_m_id, primary_mode):
        if start_m_id not in self.items_dict or end_m_id not in self.items_dict:
            return [], 0.0
            
        start_m = self.items_dict[start_m_id]['graphics']
        end_m = self.items_dict[end_m_id]['graphics']
        if not start_m or not end_m:
            return [], 0.0
        
        all_lines = [d['graphics'] for d in self.items_dict.values() if d['type'] == 'line' and d['graphics']]
        if not all_lines:
            return [], 0.0

        nodes = []
        def get_node_id(pt):
            for idx, n in enumerate(nodes):
                if QLineF(n, pt).length() <= 30.0:
                    return idx
            nodes.append(pt)
            return len(nodes) - 1

        adj = {}
        for line in all_lines:
            u = get_node_id(line.p1)
            v = get_node_id(line.p2)
            if u == v:
                continue
            
            len_m = line.length_val * UNIT_FACTORS.get(line.length_unit, 1.0)
            
            # --- MODI-PRÜFUNG ---
            line_modes = line.modes if line.modes else []
            
            # Prüfen, ob die Straße AUSSCHLIESSLICH aus ÖPNV, Flugzeug oder beidem besteht
            restricted_modes = {"ÖPNV", "Transit", "Flugzeug", "Airplane"}
            is_exclusively_restricted = len(line_modes) > 0 and all(m in restricted_modes for m in line_modes)

            if primary_mode in ["Fuß", "Walk"]:
                # Fuß-Modus: Darf alle Straßen nutzen, AUSSER sie sind exklusiv ÖPNV/Flugzeug
                if is_exclusively_restricted:
                    continue  # Diese Straße wird für Fußgänger komplett ignoriert
                
                cost_mult = 1.0 if "Fuß" in line_modes or "Walk" in line_modes else 1.5
                used_mode = "Fuß"
            else:
                # Andere Modi (Auto, ÖPNV, etc.)
                is_primary = primary_mode in line_modes
                is_foot = "Fuß" in line_modes or "Walk" in line_modes
                
                if is_primary:
                    cost_mult = 1.0
                    used_mode = primary_mode
                elif is_foot and not is_exclusively_restricted:
                    cost_mult = 2.5
                    used_mode = "Fuß"
                else:
                    continue  # Nicht kompatible Straßen ignorieren
            
            cost = len_m * cost_mult
            
            if u not in adj: adj[u] = []
            if v not in adj: adj[v] = []
            
            adj[u].append((v, cost, len_m, line, used_mode))
            adj[v].append((u, cost, len_m, line, used_mode))

        if not nodes or not adj:
            return [], 0.0

        def find_closest_adj_node(pt):
            best_idx = -1
            best_dist = float('inf')
            for node_idx in adj.keys():
                d = QLineF(nodes[node_idx], pt).length()
                if d < best_dist:
                    best_dist = d
                    best_idx = node_idx
            return best_idx

        start_node_idx = find_closest_adj_node(start_m.pos())
        end_node_idx = find_closest_adj_node(end_m.pos())

        if start_node_idx == -1 or end_node_idx == -1:
            return [], 0.0

        pq = [(0.0, start_node_idx, [], 0.0)]
        visited = set()
        found_path = None
        found_len = 0.0

        while pq:
            cost, curr, path, real_len = heapq.heappop(pq)
            if curr in visited:
                continue
            visited.add(curr)

            if curr == end_node_idx:
                found_path = path
                found_len = real_len
                break

            for nxt, weight, l_m, line_obj, mode in adj.get(curr, []):
                if nxt not in visited:
                    heapq.heappush(pq, (cost + weight, nxt, path + [(line_obj, mode)], real_len + l_m))

        if found_path is None:
            return [], 0.0

        # --- First/Last Mile Anschlussstrecken ---
        total_elements = []
        extra_len = 0.0

        start_node_pt = nodes[start_node_idx]
        dist_start = QLineF(start_m.pos(), start_node_pt).length()
        if dist_start > 2.0:
            p_start = QPainterPath()
            p_start.moveTo(start_m.pos())
            p_start.lineTo(start_node_pt)
            total_elements.append((p_start, "Anschluss_Fuß"))
            extra_len += dist_start

        for line_obj, mode in found_path:
            total_elements.append((line_obj.path(), mode))

        end_node_pt = nodes[end_node_idx]
        dist_end = QLineF(end_node_pt, end_m.pos()).length()
        if dist_end > 2.0:
            p_end = QPainterPath()
            p_end.moveTo(end_node_pt)
            p_end.lineTo(end_m.pos())
            total_elements.append((p_end, "Anschluss_Fuß"))
            extra_len += dist_end

        return total_elements, (found_len + extra_len)

    def render_route(self, path_elements, primary_mode):
        mode_styles = {
            'Auto': (QColor(0, 102, 255), Qt.PenStyle.SolidLine, 6),
            'Car': (QColor(0, 102, 255), Qt.PenStyle.SolidLine, 6),
            'ÖPNV': (QColor(153, 51, 204), Qt.PenStyle.DashDotLine, 6),
            'Transit': (QColor(153, 51, 204), Qt.PenStyle.DashDotLine, 6),
            'Fuß': (QColor(0, 160, 80), Qt.PenStyle.DotLine, 5),
            'Walk': (QColor(0, 160, 80), Qt.PenStyle.DotLine, 5),
            'Fahrrad': (QColor(255, 128, 0), Qt.PenStyle.DashLine, 5),
            'Bicycle': (QColor(255, 128, 0), Qt.PenStyle.DashLine, 5),
            'Flugzeug': (QColor(220, 20, 60), Qt.PenStyle.DashDotDotLine, 4),
            'Airplane': (QColor(220, 20, 60), Qt.PenStyle.DashDotDotLine, 4),
            'Anschluss_Fuß': (QColor(255, 0, 127), Qt.PenStyle.DotLine, 4),
        }
        
        for path_geo, mode in path_elements:
            path_item = QGraphicsPathItem()
            path_item.setPath(path_geo)
            
            color, style, width = mode_styles.get(mode, (QColor(0, 102, 255), Qt.PenStyle.SolidLine, 6))
            pen = QPen(color, width, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            
            path_item.setPen(pen)
            path_item.setZValue(10)
            
            self.view.scene.addItem(path_item)
            self.view.route_graphics_items.append(path_item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())