# -*- coding: utf-8 -*-
# Copyright (c) 2026 himbeertoni9817
# Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
# See LICENSE file in the project root for full license terms.

APP_VERSION = "2.3.0"
CHANGELOG = """Version 2.3.0:
Features:
1. The Program now Searches for Cover Images in Subfolders inside /cover/ too.
"""

import sys
import os
import json
import heapq
import math
import uuid
import urllib.request
import urllib.error
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QSignalBlocker, QEvent, QSize, QPoint, QThread, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QPainterPath, QIcon, QFont, QBrush,
    QStandardItemModel, QStandardItem, QFontMetrics, QTransform, QPolygonF, QImage,
    QImageReader
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem,
    QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLineEdit, QLabel, QSplitter,
    QListView, QFrame, QAbstractItemView, QScrollArea, QGridLayout, QDialog,
    QListWidget, QListWidgetItem, QCheckBox, QTextEdit, QTabWidget, QMessageBox
)

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtGui import QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture
    HAS_OPENGL = True
except Exception:
    HAS_OPENGL = False
    QOpenGLWidget = QWidget

DEFAULT_GITHUB_OWNER = "himbeertoni9817"
DEFAULT_GITHUB_REPO = "Himko-WayFinder"
DEFAULT_GITHUB_BRANCH = "main"

IMAGE_CACHE_QIMAGE = {}
MAX_CACHE_ENTRIES = 400

def load_scaled_qimage(fpath, target_width=250):
    if not fpath or not os.path.exists(fpath):
        return QImage()

    cache_key = (fpath, target_width)
    if cache_key in IMAGE_CACHE_QIMAGE:
        return IMAGE_CACHE_QIMAGE[cache_key]

    reader = QImageReader(fpath)
    reader.setAutoTransform(True)
    orig_size = reader.size()

    img = QImage()
    if orig_size.isValid() and orig_size.width() > 0:
        aspect_ratio = orig_size.height() / orig_size.width()
        target_height = max(1, int(target_width * aspect_ratio))
        reader.setScaledSize(QSize(target_width, target_height))
        img = reader.read()

    if img.isNull():
        raw_img = QImage(fpath)
        if not raw_img.isNull():
            img = raw_img.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)

    if not img.isNull():
        if len(IMAGE_CACHE_QIMAGE) >= MAX_CACHE_ENTRIES:
            IMAGE_CACHE_QIMAGE.clear()
        IMAGE_CACHE_QIMAGE[cache_key] = img

    return img


class BackgroundThumbnailLoader(QThread):
    image_loaded = pyqtSignal(str, int, QImage, object)

    def __init__(self, requests):
        super().__init__()
        self.requests = requests  # list of (fpath, target_width, user_data)

    def run(self):
        for fpath, target_width, user_data in self.requests:
            if self.isInterruptionRequested():
                break
            img = load_scaled_qimage(fpath, target_width)
            if not img.isNull():
                self.image_loaded.emit(fpath, target_width, img, user_data)


TRANSLATIONS = {
    'de': {
        'edit_mode': "Bearbeitungsmodus",
        'normal_mode': "Normaler Modus",
        'load_map': "Karte Laden",
        'save_export': "Speichern & Export",
        'online_store': "Maps Installieren",
        'explorer': "Explorer",
        'properties': "Eigenschaften",
        'new_folder': "Neuer Ordner",
        'name': "Name",
        'display_name': "Anzeigename",
        'font_size': "Textgröße",
        'length': "Länge",
        'node_radius': "Endpunkt Radius",
        'modes': "Modi",
        'icon': "Icon",
        'level': "Höhen-Level",
        'start_level': "Startpunkt Level",
        'end_level': "Endpunkt Level",
        'ramp': "Rampe",
        'route_planner': "Routenplaner",
        'start_marker': "Start-Marker",
        'add_stop': "+ Zwischenstopp",
        'calculate_route': "Route berechnen",
        'clear_route': "Route löschen",
        'travel_mode': "Hauptmodus",
        'total_distance': "Gesamtlänge",
        'select_target': "Marker auswählen...",
        'no_route_found': "Keine Route gefunden!",
        'covers': "Bilder (Cover)",
        'select_covers': "Bilder auswählen...",
        'no_covers_found': "Keine Bilder im Ordner /cover/ gefunden.",
        'no_covers_selected': "Keine normalen Bilder für diesen Marker.",
        'no_covers_360_selected': "Keine 360° Bilder für diesen Marker.",
        'covers_selected_count': "{count} Bild(er) gewählt",
        'select_images_title': "Cover-Bilder auswählen",
        'select_marker_title': "Marker auswählen",
        'pick_on_map': "Auf Karte anklicken",
        'no_markers_found': "Keine Marker vorhanden.",
        'search_placeholder': "Suchen...",
        'confirm': "Übernehmen",
        'close': "Schließen",
        'description': "Beschreibung",
        'no_description': "Keine Beschreibung vorhanden.",
        'tab_normal': "Normal",
        'tab_360': "360°",
        'col_image': "Bild / Datei",
        'col_normal': "Normal",
        'col_360': "360°",
        'local_maps_title': "Lokale Karten Verwalten",
        'local_maps_header': "Installierte / Lokale Karten in /maps/:",
        'no_local_maps': "Keine Karten im Ordner /maps/ gefunden.",
        'save_dialog_title': "Karte Speichern & Exportieren",
        'lbl_filename': "Map ID / Dateiname (ohne Endung):",
        'lbl_title': "Titel der Karte:",
        'lbl_version': "Version (z.B. 1.0.0):",
        'lbl_desc': "Beschreibung:",
        'lbl_cover': "Haupt-Cover für die Map:",
        'no_cover': "Kein Cover",
        'save_local_btn': "Nur Lokal Speichern",
        'export_package_btn': "Für GitHub Exportieren",
        'store_dialog_title': "Maps Download & Updates",
        'refresh_btn': "Suchen / Aktualisieren",
        'status_connecting': "Verbinde mit GitHub...",
        'btn_install': "Installieren",
        'btn_update': "Aktualisieren",
        'btn_download_images': "Bilder herunterladen",
        'btn_installed': "Installiert",
        'dl_covers': "Bilder mit herunterladen",
        'mode_auto': "Auto",
        'mode_opnv': "ÖPNV",
        'mode_fuss': "Fuß",
        'mode_fahrrad': "Fahrrad",
        'mode_flugzeug': "Flugzeug",
        'update_title': "Update verfügbar",
        'update_header': "Eine neue Version ist verfügbar",
        'update_installed': "Installierte Version",
        'update_latest': "Neueste Version",
        'update_changelog': "Changelog:",
        'update_later': "Später",
        'update_now': "Installieren",
    },
    'en': {
        'edit_mode': "Edit Mode",
        'normal_mode': "Normal Mode",
        'load_map': "Load Map",
        'save_export': "Save & Export",
        'online_store': "GitHub Maps",
        'explorer': "Explorer",
        'properties': "Properties",
        'new_folder': "New Folder",
        'name': "Name",
        'display_name': "Display Name",
        'font_size': "Text Size",
        'length': "Length",
        'node_radius': "Endpoint Radius",
        'modes': "Modes",
        'icon': "Icon",
        'level': "Elevation Level",
        'start_level': "Start Point Level",
        'end_level': "End Point Level",
        'ramp': "Ramp",
        'route_planner': "Route Planner",
        'start_marker': "Start Marker",
        'add_stop': "+ Waypoint",
        'calculate_route': "Calculate Route",
        'clear_route': "Clear Route",
        'travel_mode': "Primary Mode",
        'total_distance': "Total Distance",
        'select_target': "Select Marker...",
        'no_route_found': "No route found!",
        'covers': "Images (Cover)",
        'select_covers': "Select images...",
        'no_covers_found': "No images found in /cover/ folder.",
        'no_covers_selected': "No normal images for this marker.",
        'no_covers_360_selected': "No 360° images for this marker.",
        'covers_selected_count': "{count} image(s) selected",
        'select_images_title': "Select Cover Images",
        'select_marker_title': "Select Marker",
        'pick_on_map': "Click on map",
        'no_markers_found': "No markers available.",
        'search_placeholder': "Search...",
        'confirm': "Apply",
        'close': "Close",
        'description': "Description",
        'no_description': "No description available.",
        'tab_normal': "Normal",
        'tab_360': "360°",
        'col_image': "Image / File",
        'col_normal': "Normal",
        'col_360': "360°",
        'local_maps_title': "Manage Local Maps",
        'local_maps_header': "Installed / Local Maps in /maps/:",
        'no_local_maps': "No maps found in /maps/ folder.",
        'save_dialog_title': "Save Map & Export",
        'lbl_filename': "Map ID / Filename (without extension):",
        'lbl_title': "Map Title:",
        'lbl_version': "Version (e.g. 1.0.0):",
        'lbl_desc': "Description:",
        'lbl_cover': "Main Cover Image for Map:",
        'no_cover': "No Cover",
        'save_local_btn': "Save Locally Only",
        'export_package_btn': "Export for GitHub",
        'store_dialog_title': "Maps Download & Updates",
        'refresh_btn': "Search / Refresh",
        'status_connecting': "Connecting to GitHub...",
        'btn_install': "Install",
        'btn_update': "Update",
        'btn_download_images': "Download Images",
        'btn_installed': "Installed",
        'dl_covers': "Download with Images",
        'mode_auto': "Car",
        'mode_opnv': "Transit",
        'mode_fuss': "Walk",
        'mode_fahrrad': "Bicycle",
        'mode_flugzeug': "Airplane",
        'update_title': "Update Available!",
        'update_header': "A new Version is available",
        'update_installed': "Installed Version",
        'update_latest': "Latest Version",
        'update_changelog': "Changelog:",
        'update_later': "Later",
        'update_now': "Install Now",
    }
}

UNIT_FACTORS = {
    'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'km': 1000.0,
    'lichtjahre': 9.461e15, 'lightyears': 9.461e15
}

def safe_int(val, default=0):
    if val is None: return default
    try: return int(float(val))
    except (ValueError, TypeError): return default

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def safe_str(val, default=""):
    if val is None: return default
    return str(val)

def safe_bool(val, default=False):
    if val is None: return default
    if isinstance(val, bool): return val
    if isinstance(val, (int, float)): return bool(val)
    if isinstance(val, str): return val.lower() in ("true", "1", "yes")
    return default

def safe_point(raw_pt, default_x=0.0, default_y=0.0):
    if isinstance(raw_pt, (list, tuple)) and len(raw_pt) >= 2:
        return QPointF(safe_float(raw_pt[0], default_x), safe_float(raw_pt[1], default_y))
    return QPointF(default_x, default_y)

def get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_cover_dir():
    d = os.path.join(get_base_dir(), "cover")
    os.makedirs(d, exist_ok=True)
    return d

def get_all_cover_files():
    cover_dir = get_cover_dir()
    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    relative_files = []
    if os.path.exists(cover_dir):
        for root, _, files in os.walk(cover_dir):
            for f in files:
                if f.lower().endswith(valid_exts):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, cover_dir).replace("\\", "/")
                    relative_files.append(rel_path)
    return sorted(relative_files)

def get_maps_dir():
    d = os.path.join(get_base_dir(), "maps")
    os.makedirs(d, exist_ok=True)
    return d

def get_icons_dir():
    d = os.path.join(get_base_dir(), "icons", "marker")
    os.makedirs(d, exist_ok=True)
    return d

def get_ui_icons_dir():
    d = os.path.join(get_base_dir(), "icons", "app")
    os.makedirs(d, exist_ok=True)
    return d

def get_ui_icon(filename):
    path = os.path.join(get_ui_icons_dir(), filename)
    if os.path.exists(path):
        return QIcon(path)
    alt_path = os.path.join(get_base_dir(), "icons", filename)
    if os.path.exists(alt_path):
        return QIcon(alt_path)
    return QIcon()


class AppUpdateWorker(QThread):
    update_available = pyqtSignal(str, str, bytes)

    def __init__(self, current_version, owner=DEFAULT_GITHUB_OWNER, repo=DEFAULT_GITHUB_REPO, branch=DEFAULT_GITHUB_BRANCH):
        super().__init__()
        self.current_version = current_version
        self.owner = owner
        self.repo = repo
        self.branch = branch

    def parse_version(self, v_str):
        try:
            return tuple(map(int, v_str.strip().strip('"\'').split('.')))
        except Exception:
            return (0, 0, 0)

    def run(self):
        url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}/WayFinder.pyw"
        headers = {'User-Agent': 'WayFinder-App/1.0'}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                code_bytes = resp.read()
                code_text = code_bytes.decode('utf-8', errors='ignore')

                remote_version = None
                remote_changelog = "Keine Änderungsprotokoll-Details angegeben."

                for line in code_text.splitlines():
                    if line.startswith("APP_VERSION ="):
                        remote_version = line.split("=", 1)[1].strip().strip('"\'')

                if 'CHANGELOG = """' in code_text:
                    try:
                        remote_changelog = code_text.split('CHANGELOG = """')[1].split('"""')[0].strip()
                    except Exception:
                        pass
                elif "CHANGELOG = '''" in code_text:
                    try:
                        remote_changelog = code_text.split("CHANGELOG = '''")[1].split("'''")[0].strip()
                    except Exception:
                        pass

                if remote_version:
                    if self.parse_version(remote_version) > self.parse_version(self.current_version):
                        self.update_available.emit(remote_version, remote_changelog, code_bytes)
        except Exception:
            pass


class AppUpdateDialog(QDialog):
    def __init__(self, current_ver, new_ver, changelog_text, new_code_bytes, lang='de', parent=None):
        super().__init__(parent)
        self.new_code_bytes = new_code_bytes
        t = TRANSLATIONS.get(lang, TRANSLATIONS['de'])
        
        self.setWindowTitle(t['update_title'])
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        lbl_header = QLabel(f"<b>{t['update_header']}</b>")
        lbl_header.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl_header)

        lbl_vers = QLabel(f"{t['update_installed']}: <b>{current_ver}</b>  ➔  {t['update_latest']}: <b style='color: #27ae60;'>{new_ver}</b>")
        layout.addWidget(lbl_vers)

        layout.addWidget(QLabel(f"<b>{t['update_changelog']}</b>"))
        txt_change = QTextEdit()
        txt_change.setReadOnly(True)
        txt_change.setPlainText(changelog_text)
        layout.addWidget(txt_change)

        btn_box = QHBoxLayout()
        btn_later = QPushButton(t['update_later'])
        btn_later.clicked.connect(self.reject)

        btn_update = QPushButton(t['update_now'])
        btn_update.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px;")
        btn_update.clicked.connect(self.install_update)

        btn_box.addWidget(btn_later)
        btn_box.addWidget(btn_update)
        layout.addLayout(btn_box)

    def install_update(self):
        try:
            target_path = os.path.abspath(sys.argv[0])
            with open(target_path, 'wb') as f:
                f.write(self.new_code_bytes)

            QMessageBox.information(
                self, "Success",
                "New Version installed successfully!\n\nRestarting now."
            )
            self.accept()
            QProcess.startDetached(sys.executable, sys.argv)
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update couldn't be saved:\n{e}")


class GitHubMapWorker(QThread):
    manifests_loaded = pyqtSignal(list)
    preview_loaded = pyqtSignal(str, bytes)
    download_finished = pyqtSignal(str, bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, action="fetch_manifests", owner=DEFAULT_GITHUB_OWNER, repo=DEFAULT_GITHUB_REPO, branch=DEFAULT_GITHUB_BRANCH, map_data=None, image_name=None, download_images=True):
        super().__init__()
        self.action = action
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.map_data = map_data
        self.image_name = image_name
        self.download_images = download_images

    def run(self):
        headers = {'User-Agent': 'WayFinder-App/1.0'}
        raw_base = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}"
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/maps"

        if self.action == "fetch_manifests":
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    files_list = json.loads(resp.read().decode('utf-8'))
                
                manifests = []
                if isinstance(files_list, list):
                    for file_obj in files_list:
                        if isinstance(file_obj, dict):
                            name = file_obj.get("name", "")
                            if name.endswith("_install.json"):
                                dl_url = f"{raw_base}/maps/{name}"
                                m_req = urllib.request.Request(dl_url, headers=headers)
                                with urllib.request.urlopen(m_req, timeout=8) as m_resp:
                                    m_data = json.loads(m_resp.read().decode('utf-8'))
                                    m_data["_install_filename"] = name
                                    manifests.append(m_data)
                
                self.manifests_loaded.emit(manifests)
            except Exception as e:
                self.error_occurred.emit(f"⚠️ GitHub Repo Error:\n({str(e)})")

        elif self.action == "fetch_preview" and self.image_name:
            try:
                img_url = f"{raw_base}/cover/{self.image_name}"
                req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    img_bytes = resp.read()
                    self.preview_loaded.emit(self.image_name, img_bytes)
            except Exception:
                pass

        elif self.action == "download_package" and self.map_data:
            try:
                map_id = self.map_data.get('id', 'unknown')
                
                def download_file(rel_path, target_folder):
                    url = f"{raw_base}/{rel_path}"
                    clean_rel = rel_path.split('/', 1)[-1] if '/' in rel_path else rel_path
                    dest = os.path.join(target_folder, clean_rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    req = urllib.request.Request(url, headers=headers)
                    try:
                        with urllib.request.urlopen(req, timeout=10) as r, open(dest, 'wb') as f:
                            f.write(r.read())
                    except urllib.error.HTTPError as err:
                        if err.code == 404:
                            raise Exception(f"Datei nicht auf GitHub gefunden (404):\n'{rel_path}'") from err
                        raise Exception(f"Fehler bei '{rel_path}': {err}") from err
                    except Exception as err:
                        raise Exception(f"Fehler bei '{rel_path}': {err}") from err

                if self.map_data.get('map_file'): download_file(f"maps/{self.map_data['map_file']}", get_maps_dir())
                if self.map_data.get('image_file'): download_file(f"maps/{self.map_data['image_file']}", get_maps_dir())

                if self.download_images:
                    if self.map_data.get('map_cover'): download_file(f"cover/{self.map_data['map_cover']}", get_cover_dir())
                    for c_file in self.map_data.get('covers', []):
                        if c_file: download_file(f"cover/{c_file}", get_cover_dir())

                for i_file in self.map_data.get('icons', []):
                    if i_file: download_file(f"icons/marker/{i_file}", get_icons_dir())

                install_json_name = self.map_data.get('_install_filename', f"{map_id}_install.json")
                install_dest = os.path.join(get_maps_dir(), install_json_name)
                with open(install_dest, 'w', encoding='utf-8') as f:
                    json.dump(self.map_data, f, indent=2, ensure_ascii=False)

                self.download_finished.emit(map_id, True, "OK")
            except Exception as e:
                self.download_finished.emit(self.map_data.get('id', ''), False, str(e))


class ClickableLabel(QLabel):
    def __init__(self, image_path, click_callback, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.click_callback = click_callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.click_callback:
            self.click_callback(self.image_path)
        super().mousePressEvent(event)


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else (1.0 / 1.15)
        self.scale(zoom_factor, zoom_factor)
        event.accept()


class ZoomableImageViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bildvorschau")
        self.resize(1000, 750)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.scene = QGraphicsScene(self)
        self.view = ZoomableGraphicsView(self.scene, self)
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
            
        layout.addWidget(self.view)


class Panorama360Widget(QOpenGLWidget if HAS_OPENGL else QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.pixmap = QPixmap(image_path)
        self.yaw_deg = 0.0
        self.pitch_deg = 0.0
        self.zoom_factor = 1.0
        self.drag_start_mouse_pos = QPoint()
        self.drag_start_yaw = 0.0
        self.drag_start_pitch = 0.0
        self.is_dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self.use_gl = HAS_OPENGL
        self.program = None
        self.texture = None
        self.gl_initialized = False
        
        if not self.pixmap.isNull():
            max_w = 4096
            if self.pixmap.width() > max_w:
                self.pixmap = self.pixmap.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)
            
            pw, ph = self.pixmap.width(), self.pixmap.height()
            self.tiled_pixmap = QPixmap(pw * 3, ph)
            painter = QPainter(self.tiled_pixmap)
            painter.drawPixmap(0, 0, self.pixmap)
            painter.drawPixmap(pw, 0, self.pixmap)
            painter.drawPixmap(pw * 2, 0, self.pixmap)
            painter.end()
            self.tiled_image = self.tiled_pixmap.toImage()

    def initializeGL(self):
        if not HAS_OPENGL:
            self.use_gl = False
            return
        try:
            ctx = self.context()
            if not ctx: self.use_gl = False; return
            gl = ctx.functions()
            if not gl: self.use_gl = False; return
            
            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            shaders = (
                """#version 120
                attribute vec2 position;
                varying vec2 v_uv;
                void main() {
                    v_uv = vec2(position.x * 0.5 + 0.5, 0.5 - position.y * 0.5);
                    gl_Position = vec4(position, 0.0, 1.0);
                }""",
                """#version 120
                uniform sampler2D u_texture;
                uniform vec2 u_resolution;
                uniform float u_yaw;
                uniform float u_pitch;
                uniform float u_fov;
                varying vec2 v_uv;
                const float PI = 3.14159265358979323846;
                void main() {
                    float aspect = u_resolution.x / u_resolution.y;
                    vec2 ndc = vec2(v_uv.x * 2.0 - 1.0, 1.0 - v_uv.y * 2.0);
                    float f = tan(u_fov * 0.5);
                    vec3 ray = normalize(vec3(ndc.x * aspect * f, ndc.y * f, 1.0));
                    float cos_p = cos(u_pitch);
                    float sin_p = sin(u_pitch);
                    vec3 r1 = vec3(ray.x, ray.y * cos_p + ray.z * sin_p, -ray.y * sin_p + ray.z * cos_p);
                    float cos_y = cos(u_yaw);
                    float sin_y = sin(u_yaw);
                    vec3 r2 = vec3(r1.x * cos_y + r1.z * sin_y, r1.y, -r1.x * sin_y + r1.z * cos_y);
                    vec3 dir = normalize(r2);
                    float lon = atan(dir.x, dir.z);
                    float lat = asin(clamp(dir.y, -0.99999, 0.99999));
                    float u = 0.5 + lon / (2.0 * PI);
                    float v = 0.5 - lat / PI;
                    gl_FragColor = texture2D(u_texture, vec2(u, clamp(v, 0.0001, 0.9999)));
                }"""
            )
            
            vshader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Vertex, self)
            fshader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Fragment, self)
            if vshader.compileSourceCode(shaders[0]) and fshader.compileSourceCode(shaders[1]):
                prog = QOpenGLShaderProgram(self)
                prog.addShader(vshader); prog.addShader(fshader)
                if prog.link():
                    self.program = prog
                    if not self.pixmap.isNull():
                        img = self.pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                        self.texture = QOpenGLTexture(img)
                        self.texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionS, QOpenGLTexture.WrapMode.Repeat)
                        self.texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionT, QOpenGLTexture.WrapMode.ClampToEdge)
                        self.texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
                        self.texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
                    self.gl_initialized = True
                    return
            self.use_gl = False
        except Exception:
            self.use_gl = False
            self.gl_initialized = False

    def resizeGL(self, w, h):
        if self.use_gl and self.gl_initialized:
            try:
                gl = self.context().functions()
                if gl: gl.glViewport(0, 0, w, h)
            except Exception: pass

    def paintGL(self):
        if self.use_gl and self.gl_initialized and self.program and self.texture:
            try:
                gl = self.context().functions()
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                self.program.bind()
                self.texture.bind(0)
                self.program.setUniformValue("u_texture", 0)

                w, h = float(max(1, self.width())), float(max(1, self.height()))
                self.program.setUniformValue("u_resolution", QPointF(w, h))
                self.program.setUniformValue("u_yaw", float(math.radians(self.yaw_deg)))
                self.program.setUniformValue("u_pitch", float(math.radians(self.pitch_deg)))
                self.program.setUniformValue("u_fov", float(math.radians(80.0 / self.zoom_factor)))

                pts = [QPointF(-1.0, -1.0), QPointF(1.0, -1.0), QPointF(-1.0, 1.0), QPointF(1.0, 1.0)]
                pos_attr = self.program.attributeLocation("position")
                self.program.enableAttributeArray(pos_attr)
                self.program.setAttributeArray(pos_attr, pts)
                gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
                self.program.disableAttributeArray(pos_attr)
                self.texture.release(); self.program.release()
                return
            except Exception: self.use_gl = False

        self.paint_cpu()

    def paintEvent(self, event):
        if HAS_OPENGL and self.use_gl: super().paintEvent(event)
        else: self.paint_cpu()

    def paint_cpu(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        w, h = float(self.width()), float(self.height())
        if w <= 0 or h <= 0 or self.pixmap.isNull() or self.tiled_image.isNull(): return

        pw, ph = float(self.pixmap.width()), float(self.pixmap.height())
        cols, rows = 24, 18
        aspect = w / h
        f = math.tan(math.radians(80.0 / self.zoom_factor) / 2.0)
        cos_p, sin_p = math.cos(math.radians(self.pitch_deg)), math.sin(math.radians(self.pitch_deg))
        cos_y, sin_y = math.cos(math.radians(self.yaw_deg)), math.sin(math.radians(self.yaw_deg))

        grid_coords = []
        dx, dy = w / cols, h / rows

        for j in range(rows + 1):
            row_coords = []
            ys = j * dy
            y_c = (1.0 - (2.0 * ys / h)) * f
            for i in range(cols + 1):
                xs = i * dx
                x_c = ((2.0 * xs / w) - 1.0) * aspect * f
                y1 = y_c * cos_p + sin_p
                z1 = -y_c * sin_p + cos_p
                x2 = x_c * cos_y + z1 * sin_y
                y2 = y1
                z2 = -x_c * sin_y + z1 * cos_y
                r = max(1e-6, math.sqrt(x2*x2 + y2*y2 + z2*z2))
                lat = math.asin(max(-0.9999, min(0.9999, y2 / r)))
                lon = math.atan2(x2, z2)
                row_coords.append((xs, ys, lon, lat))
            grid_coords.append(row_coords)

        img_rect = self.tiled_image.rect()
        painter.setPen(Qt.PenStyle.NoPen)

        for j in range(rows):
            for i in range(cols):
                xs0, ys0, lon0, lat0 = grid_coords[j][i]
                xs1, ys1, lon1, lat1 = grid_coords[j][i+1]
                xs2, ys2, lon2, lat2 = grid_coords[j+1][i+1]
                xs3, ys3, lon3, lat3 = grid_coords[j+1][i]
                
                lons = [lon0, lon1, lon2, lon3]
                unwrapped = []
                for l in lons:
                    while l - lon0 > math.pi: l -= 2.0 * math.pi
                    while l - lon0 < -math.pi: l += 2.0 * math.pi
                    unwrapped.append(l)
                l0, l1, l2, l3 = unwrapped
                
                src_x0 = (1.5 + l0 / (2.0 * math.pi)) * pw
                src_y0 = max(0.5, min(ph - 0.5, (0.5 - lat0 / math.pi) * ph))
                src_x1 = (1.5 + l1 / (2.0 * math.pi)) * pw
                src_y1 = max(0.5, min(ph - 0.5, (0.5 - lat1 / math.pi) * ph))
                src_x2 = (1.5 + l2 / (2.0 * math.pi)) * pw
                src_y2 = max(0.5, min(ph - 0.5, (0.5 - lat2 / math.pi) * ph))
                src_x3 = (1.5 + l3 / (2.0 * math.pi)) * pw
                src_y3 = max(0.5, min(ph - 0.5, (0.5 - lat3 / math.pi) * ph))
                
                src_poly = QPolygonF([QPointF(src_x0, src_y0), QPointF(src_x1, src_y1), QPointF(src_x2, src_y2), QPointF(src_x3, src_y3)])
                dst_poly = QPolygonF([QPointF(xs0, ys0), QPointF(xs1, ys1), QPointF(xs2, ys2), QPointF(xs3, ys3)])
                
                src_rect = src_poly.boundingRect().toAlignedRect().intersected(img_rect)
                if src_rect.isEmpty() or src_rect.width() < 1 or src_rect.height() < 1: continue

                sub_img = self.tiled_image.copy(src_rect)
                offset = QPointF(src_rect.x(), src_rect.y())
                src_poly_local = QPolygonF([p - offset for p in src_poly])
                
                clip_path = QPainterPath()
                clip_path.addPolygon(dst_poly)
                painter.save()
                painter.setClipPath(clip_path)
                trans = QTransform()
                res = QTransform.quadToQuad(src_poly_local, dst_poly, trans)
                ok = res[0] if isinstance(res, tuple) else res
                if ok:
                    painter.setTransform(trans)
                    painter.drawImage(0, 0, sub_img)
                else:
                    painter.drawImage(dst_poly.boundingRect().toAlignedRect(), sub_img)
                painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_mouse_pos = event.pos()
            self.drag_start_yaw = self.yaw_deg
            self.drag_start_pitch = self.pitch_deg
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.drag_start_mouse_pos
            deg_per_px = (80.0 / self.zoom_factor) / max(1.0, float(self.height()))
            self.yaw_deg = (self.drag_start_yaw - delta.x() * deg_per_px) % 360.0
            self.pitch_deg = max(-88.5, min(88.5, self.drag_start_pitch + delta.y() * deg_per_px))
            self.update()

    def wheelEvent(self, event):
        self.zoom_factor = min(5.0, self.zoom_factor * 1.15) if event.angleDelta().y() > 0 else max(0.5, self.zoom_factor / 1.15)
        self.update()
        event.accept()


class Panorama360ViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("360° Panorama")
        self.resize(1050, 750)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.viewer_widget = Panorama360Widget(image_path, self)
        layout.addWidget(self.viewer_widget)


class OutlinedTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text="", font_size=12, parent=None):
        super().__init__(text, parent)
        self.base_font_size = font_size
        self._cached_path = QPainterPath()
        self.set_font_size(font_size)

    def set_font_size(self, size):
        self.base_font_size = max(1.0, float(size))
        font = QFont("Arial", int(self.base_font_size), QFont.Weight.Bold)
        self.setFont(font)
        pen_w = max(1.0, self.base_font_size / 3.5)
        self.setPen(QPen(QColor(0, 0, 0), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self._rebuild_path()

    def setText(self, text):
        super().setText(text)
        self._rebuild_path()

    def _rebuild_path(self):
        self._cached_path = QPainterPath()
        if self.text():
            fm = QFontMetrics(self.font())
            self._cached_path.addText(0, fm.ascent(), self.font(), self.text())

    def paint(self, painter, option, widget):
        if not self.text() or self._cached_path.isEmpty(): return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.strokePath(self._cached_path, self.pen())
        painter.fillPath(self._cached_path, self.brush())


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setEditable(True)
        if self.lineEdit(): self.lineEdit().setReadOnly(True)
        self.view().viewport().installEventFilter(self)
        self._changed_callback = None

    def eventFilter(self, widget, event):
        if widget == self.view().viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self._model.itemFromIndex(index)
                if item:
                    item.setCheckState(Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked)
                    self.update_display_text()
                    if self._changed_callback: self._changed_callback()
            return True
        return super().eventFilter(widget, event)

    def add_checkable_item(self, text, checked=False):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._model.appendRow(item)
        self.update_display_text()

    def get_checked_items(self):
        return [self._model.item(i).text() for i in range(self._model.rowCount()) if self._model.item(i).checkState() == Qt.CheckState.Checked]

    def update_display_text(self):
        checked = self.get_checked_items()
        self.setEditText(", ".join(checked) if checked else "-")


class IconGridComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._list_view = QListView(self)
        self._list_view.setViewMode(QListView.ViewMode.IconMode)
        self._list_view.setMovement(QListView.Movement.Static)
        self._list_view.setResizeMode(QListView.ResizeMode.Fixed)
        self._list_view.setSpacing(0)
        
        screen = QApplication.primaryScreen()
        dpi_scale = (screen.logicalDotsPerInch() / 96.0) if screen else 1.0
        self._grid_w = int(64 * dpi_scale)
        self._grid_h = int(64 * dpi_scale)
        self._icon_size = int(36 * dpi_scale)
        self._scrollbar_w = int(14 * dpi_scale)
        
        self._list_view.setGridSize(QSize(self._grid_w, self._grid_h))
        self._list_view.setIconSize(QSize(self._icon_size, self._icon_size))
        self._exact_w = (5 * self._grid_w) + self._scrollbar_w + int(6 * dpi_scale)
        self._list_view.setFixedWidth(self._exact_w)
        self.setView(self._list_view)

    def showPopup(self):
        # Aufklapp-Animationen in Qt deaktivieren
        QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)
        QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateMenu, False)
        QApplication.setEffectEnabled(Qt.UIEffect.UI_FadeMenu, False)

        combo_bot_left = self.mapToGlobal(QPoint(0, self.height()))
        win = self.window()
        win_bot_y = win.mapToGlobal(QPoint(0, win.height())).y() - 8 if win else 600
        avail_h = win_bot_y - combo_bot_left.y()
        target_h = max(int(self._grid_h * 1.5), min(int(self._grid_h * 3.5), avail_h))
        self._list_view.setFixedHeight(target_h)
        
        super().showPopup()
        
        popup = self.view().window()
        target_x = combo_bot_left.x()
        
        screen = QApplication.screenAt(combo_bot_left) or QApplication.primaryScreen()
        if screen:
            avail_geo = screen.availableGeometry()
            max_x = avail_geo.right() - self._exact_w
            min_x = avail_geo.left()
            target_x = max(min_x, min(target_x, max_x))
            
        popup.setGeometry(target_x, combo_bot_left.y(), self._exact_w, target_h + 2)


class LocalMapManagerDialog(QDialog):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        t = TRANSLATIONS[self.main_win.current_lang]
        self.setWindowTitle(t['local_maps_title'])
        self.resize(720, 500)
        self.loader_thread = None
        
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel(t['local_maps_header'])
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_title)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
        self.load_local_maps()

    def load_local_maps(self):
        t = TRANSLATIONS[self.main_win.current_lang]
        while self.grid.count() > 0:
            child = self.grid.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()

        maps_dir = get_maps_dir()
        cover_dir = get_cover_dir()
        files = [f for f in os.listdir(maps_dir) if f.lower().endswith('.json') and not f.lower().endswith('_install.json')]
        
        if not files:
            lbl_empty = QLabel(t['no_local_maps'])
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(lbl_empty, 0, 0)
            return

        cols = 3
        bg_requests = []
        for idx, fname in enumerate(sorted(files)):
            fpath = os.path.join(maps_dir, fname)
            map_name = fname
            map_cover = ""

            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    map_name = data.get('title', data.get('name', fname))
                    map_cover = data.get('map_cover', '')
            except Exception:
                pass

            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setStyleSheet("QFrame { background-color: #fdfdfd; border: 1px solid #ccc; border-radius: 6px; padding: 6px; }")
            card_lay = QVBoxLayout(card)

            lbl_pix = QLabel()
            lbl_pix.setFixedHeight(110)
            lbl_pix.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_pix.setText(t['no_cover'])
            lbl_pix.setStyleSheet("color: #888;")

            cover_path = os.path.join(cover_dir, map_cover) if map_cover else ""
            if cover_path and os.path.exists(cover_path):
                bg_requests.append((cover_path, 180, lbl_pix))

            lbl_name = QLabel(map_name)
            lbl_name.setStyleSheet("font-weight: bold; font-size: 13px;")
            lbl_file = QLabel(fname)
            lbl_file.setStyleSheet("color: #666; font-size: 10px;")
            
            btn_load = QPushButton(t['load_map'])
            btn_load.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 4px;")
            btn_load.clicked.connect(lambda _, p=fpath: self.load_map(p))

            card_lay.addWidget(lbl_pix)
            card_lay.addWidget(lbl_name)
            card_lay.addWidget(lbl_file)
            card_lay.addWidget(btn_load)

            row, col = idx // cols, idx % cols
            self.grid.addWidget(card, row, col)

        if bg_requests:
            self.loader_thread = BackgroundThumbnailLoader(bg_requests)
            self.loader_thread.image_loaded.connect(self.on_cover_loaded)
            self.loader_thread.start()

    def on_cover_loaded(self, fpath, width, qimg, target_label):
        if not qimg.isNull() and target_label:
            target_label.setPixmap(QPixmap.fromImage(qimg))
            target_label.setStyleSheet("")

    def closeEvent(self, event):
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.requestInterruption()
            self.loader_thread.wait()
        super().closeEvent(event)

    def load_map(self, fpath):
        self.main_win.load_map_from_filepath(fpath)
        self.accept()


class SaveAndExportDialog(QDialog):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        t = TRANSLATIONS[self.main_win.current_lang]
        self.setWindowTitle(t['save_dialog_title'])
        self.resize(500, 420)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(t['lbl_filename']))
        self.txt_filename = QLineEdit(self.main_win.current_map_id or "meine_karte")
        layout.addWidget(self.txt_filename)

        layout.addWidget(QLabel(t['lbl_title']))
        self.txt_title = QLineEdit(self.main_win.current_map_title or "Neue Karte")
        layout.addWidget(self.txt_title)

        layout.addWidget(QLabel(t['lbl_version']))
        self.txt_version = QLineEdit(self.main_win.current_map_version or "1.0.0")
        layout.addWidget(self.txt_version)

        layout.addWidget(QLabel(t['lbl_desc']))
        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(60)
        self.txt_desc.setPlainText(self.main_win.current_map_desc or "")
        layout.addWidget(self.txt_desc)

        layout.addWidget(QLabel(t['lbl_cover']))
        self.cmb_cover = QComboBox()
        
        cover_files = get_all_cover_files()
        self.cmb_cover.addItem(t['no_cover'], "")
        for cf in sorted(cover_files):
            self.cmb_cover.addItem(cf, cf)
            
        if self.main_win.current_map_cover in cover_files:
            self.cmb_cover.setCurrentText(self.main_win.current_map_cover)
            
        layout.addWidget(self.cmb_cover)

        btn_box = QHBoxLayout()
        btn_save_local = QPushButton(t['save_local_btn'])
        btn_save_local.clicked.connect(self.save_local)
        
        btn_export = QPushButton(t['export_package_btn'])
        btn_export.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_export.clicked.connect(self.export_package)

        btn_box.addWidget(btn_save_local)
        btn_box.addWidget(btn_export)
        layout.addLayout(btn_box)

    def save_local(self):
        self.main_win.execute_save_and_export(
            filename=self.txt_filename.text().strip(),
            title=self.txt_title.text().strip(),
            version=self.txt_version.text().strip(),
            desc=self.txt_desc.toPlainText().strip(),
            cover_img=self.cmb_cover.currentData(),
            export_manifest=False
        )
        self.accept()

    def export_package(self):
        self.main_win.execute_save_and_export(
            filename=self.txt_filename.text().strip(),
            title=self.txt_title.text().strip(),
            version=self.txt_version.text().strip(),
            desc=self.txt_desc.toPlainText().strip(),
            cover_img=self.cmb_cover.currentData(),
            export_manifest=True
        )
        self.accept()


class OnlineMapStoreDialog(QDialog):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        t = TRANSLATIONS[self.main_win.current_lang]
        self.setWindowTitle(t['store_dialog_title'])
        self.resize(780, 550)
        
        self.workers = []
        self.layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Repo Owner:"))
        self.txt_owner = QLineEdit(DEFAULT_GITHUB_OWNER)
        top_bar.addWidget(self.txt_owner)
        
        top_bar.addWidget(QLabel("Repo:"))
        self.txt_repo = QLineEdit(DEFAULT_GITHUB_REPO)
        top_bar.addWidget(self.txt_repo)

        self.chk_download_images = QCheckBox(t['dl_covers'])
        self.chk_download_images.setChecked(True)
        top_bar.addWidget(self.chk_download_images)

        self.btn_refresh = QPushButton(t['refresh_btn'])
        self.btn_refresh.clicked.connect(self.fetch_manifests)
        top_bar.addWidget(self.btn_refresh)
        self.layout.addLayout(top_bar)

        self.lbl_status = QLabel(t['status_connecting'])
        self.lbl_status.setStyleSheet("color: #555; font-weight: bold; margin: 4px;")
        self.layout.addWidget(self.lbl_status)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        self.preview_cache = {}
        self.fetch_manifests()

    def track_worker(self, worker):
        self.workers.append(worker)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        return worker

    def fetch_manifests(self):
        t = TRANSLATIONS[self.main_win.current_lang]
        self.lbl_status.setText(t['status_connecting'])
        self.btn_refresh.setEnabled(False)
        
        while self.grid.count() > 0:
            child = self.grid.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()

        worker = GitHubMapWorker(
            action="fetch_manifests",
            owner=self.txt_owner.text().strip(),
            repo=self.txt_repo.text().strip()
        )
        worker.manifests_loaded.connect(self.populate_grid)
        worker.error_occurred.connect(self.on_error)
        self.track_worker(worker).start()

    def on_error(self, err_msg):
        self.btn_refresh.setEnabled(True)
        self.lbl_status.setText(err_msg)
        self.lbl_status.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px;")

    def populate_grid(self, manifests):
        t = TRANSLATIONS[self.main_win.current_lang]
        self.btn_refresh.setEnabled(True)
        if not manifests:
            self.lbl_status.setText("Keine *_install.json Manifeste gefunden.")
            return

        self.lbl_status.setText(f"{len(manifests)} Maps:")
        self.lbl_status.setStyleSheet("color: #27ae60; font-weight: bold;")

        maps_dir = get_maps_dir()
        cover_dir = get_cover_dir()
        cols = 3

        def parse_ver(v_str):
            if not v_str:
                return (0, 0, 0)
            try:
                return tuple(map(int, str(v_str).strip().strip('"\'').split('.')))
            except Exception:
                return (0, 0, 0)

        for idx, item in enumerate(manifests):
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 6px; padding: 6px; }")
            c_lay = QVBoxLayout(card)

            lbl_cover = QLabel()
            lbl_cover.setFixedHeight(110)
            lbl_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_cover.setText("...")
            c_lay.addWidget(lbl_cover)

            map_cover_file = item.get("map_cover", "")
            if map_cover_file:
                if map_cover_file in self.preview_cache:
                    pix = QPixmap()
                    pix.loadFromData(self.preview_cache[map_cover_file])
                    lbl_cover.setPixmap(pix.scaled(180, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    w_img = GitHubMapWorker(
                        action="fetch_preview",
                        owner=self.txt_owner.text().strip(),
                        repo=self.txt_repo.text().strip(),
                        image_name=map_cover_file
                    )
                    w_img.preview_loaded.connect(lambda name, data, lbl=lbl_cover: self.on_preview_loaded(name, data, lbl))
                    self.track_worker(w_img).start()
            else:
                lbl_cover.setText(t['no_cover'])

            lbl_title = QLabel(item.get("name", "Unbekannt"))
            lbl_title.setStyleSheet("font-weight: bold; font-size: 13px;")
            c_lay.addWidget(lbl_title)

            github_ver = str(item.get("version", "1.0.0")).strip()
            lbl_ver = QLabel(f"Version: {github_ver}")
            lbl_ver.setStyleSheet("color: #777; font-size: 10px;")
            c_lay.addWidget(lbl_ver)

            lbl_desc = QLabel(item.get("description", ""))
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #444; font-size: 11px;")
            c_lay.addWidget(lbl_desc)

            map_file = item.get("map_file", "")
            map_id = item.get("id", "")
            install_json_filename = item.get("_install_filename", f"{map_id}_install.json") if map_id else ""
            
            local_file_path = os.path.join(maps_dir, map_file) if map_file else ""
            install_file_path = os.path.join(maps_dir, install_json_filename) if install_json_filename else ""

            local_exists = False
            local_version = ""

            if install_file_path and os.path.exists(install_file_path):
                local_exists = True
                try:
                    with open(install_file_path, 'r', encoding='utf-8') as f:
                        l_data = json.load(f)
                        raw_v = l_data.get("version")
                        if raw_v is not None:
                            local_version = str(raw_v).strip()
                except Exception:
                    pass

            if local_file_path and os.path.exists(local_file_path):
                local_exists = True
                if not local_version:
                    try:
                        with open(local_file_path, 'r', encoding='utf-8') as f:
                            l_data = json.load(f)
                            raw_v = l_data.get("version")
                            if raw_v is not None:
                                local_version = str(raw_v).strip()
                    except Exception:
                        pass

            missing_covers = False
            if map_cover_file and not os.path.exists(os.path.join(cover_dir, map_cover_file)):
                missing_covers = True

            if not missing_covers:
                for c_file in item.get("covers", []):
                    if c_file and not os.path.exists(os.path.join(cover_dir, c_file)):
                        missing_covers = True
                        break

            force_images = False
            if not local_exists:
                btn_text = t['btn_install']
                btn_style = "background-color: #2ecc71; color: white; font-weight: bold;"
                btn_enabled = True
            elif parse_ver(local_version) < parse_ver(github_ver):
                btn_text = t['btn_update']
                btn_style = "background-color: #e67e22; color: white; font-weight: bold;"
                btn_enabled = True
            elif missing_covers:
                btn_text = t['btn_download_images']
                btn_style = "background-color: #3498db; color: white; font-weight: bold;"
                btn_enabled = True
                force_images = True
            else:
                btn_text = t['btn_installed']
                btn_style = "background-color: #95a5a6; color: white;"
                btn_enabled = False

            btn_dl = QPushButton(btn_text)
            btn_dl.setStyleSheet(btn_style)
            btn_dl.setEnabled(btn_enabled)
            btn_dl.clicked.connect(lambda _, m=item, b=btn_dl, fi=force_images: self.download_map_package(m, b, force_images=fi))
            c_lay.addWidget(btn_dl)

            row, col = idx // cols, idx % cols
            self.grid.addWidget(card, row, col)

    def on_preview_loaded(self, name, img_bytes, label):
        self.preview_cache[name] = img_bytes
        pix = QPixmap()
        pix.loadFromData(img_bytes)
        label.setPixmap(pix.scaled(180, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def download_map_package(self, map_data, button, force_images=False):
        button.setEnabled(False)
        button.setText("...")
        
        dl_images = force_images or self.chk_download_images.isChecked()

        worker = GitHubMapWorker(
            action="download_package",
            owner=self.txt_owner.text().strip(),
            repo=self.txt_repo.text().strip(),
            map_data=map_data,
            download_images=dl_images
        )
        worker.download_finished.connect(lambda m_id, ok, msg, b=button: self.on_download_complete(ok, msg, b))
        self.track_worker(worker).start()

    def on_download_complete(self, ok, msg, button):
        t = TRANSLATIONS[self.main_win.current_lang]
        if ok:
            button.setEnabled(False)
            button.setText(t['btn_installed'])
            button.setStyleSheet("background-color: #95a5a6; color: white;")
        else:
            button.setEnabled(True)
            button.setText("Error")
            QMessageBox.warning(self, "Error", msg)


class CoverSelectDialog(QDialog):
    def __init__(self, selected_covers, selected_covers_360, lang='de', parent=None):
        super().__init__(parent)
        self.lang = lang
        t = TRANSLATIONS[self.lang]
        self.setWindowTitle(t['select_images_title'])
        self.resize(580, 480)
        self.loader_thread = None
        
        self.selected_covers = list(selected_covers)
        self.selected_covers_360 = list(selected_covers_360)
        
        layout = QVBoxLayout(self)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(t['search_placeholder'])
        self.search_edit.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_edit)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([t['col_image'], t['col_normal'], t['col_360']])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 80)
        
        cover_dir = get_cover_dir()
        files = get_all_cover_files()
        
        self.row_data = []
        if not files:
            lbl_empty = QLabel(t['no_covers_found'])
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_empty)
        else:
            self.table.setRowCount(len(files))
            bg_requests = []
            for row, fname in enumerate(files):
                fpath = os.path.normpath(os.path.join(cover_dir, fname))
                item_fname = QTableWidgetItem(fname)
                bg_requests.append((fpath, 48, item_fname))
                
                chk_normal = QCheckBox()
                chk_360 = QCheckBox()
                chk_normal.setChecked(fname in self.selected_covers)
                chk_360.setChecked(fname in self.selected_covers_360)
                
                chk_normal.stateChanged.connect(lambda state, c=chk_360: c.setChecked(False) if state == Qt.CheckState.Checked.value else None)
                chk_360.stateChanged.connect(lambda state, c=chk_normal: c.setChecked(False) if state == Qt.CheckState.Checked.value else None)
                
                w_norm, w_360 = QWidget(), QWidget()
                l_norm, l_360 = QHBoxLayout(w_norm), QHBoxLayout(w_360)
                l_norm.setAlignment(Qt.AlignmentFlag.AlignCenter); l_norm.setContentsMargins(0,0,0,0); l_norm.addWidget(chk_normal)
                l_360.setAlignment(Qt.AlignmentFlag.AlignCenter); l_360.setContentsMargins(0,0,0,0); l_360.addWidget(chk_360)
                
                self.table.setItem(row, 0, item_fname)
                self.table.setCellWidget(row, 1, w_norm)
                self.table.setCellWidget(row, 2, w_360)
                self.row_data.append((row, fname, fname.lower(), chk_normal, chk_360))
            layout.addWidget(self.table)

            if bg_requests:
                self.loader_thread = BackgroundThumbnailLoader(bg_requests)
                self.loader_thread.image_loaded.connect(self.on_icon_loaded)
                self.loader_thread.start()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton(t['confirm'])
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def on_icon_loaded(self, fpath, width, qimg, item_fname):
        try:
            if not qimg.isNull() and item_fname:
                item_fname.setIcon(QIcon(QPixmap.fromImage(qimg)))
        except Exception:
            pass

    def closeEvent(self, event):
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.requestInterruption()
            self.loader_thread.wait()
        super().closeEvent(event)

    def filter_items(self, text):
        query = text.lower().strip()
        for row, fname, fname_lower, chk_normal, chk_360 in self.row_data:
            self.table.setRowHidden(row, query not in fname_lower)

    def get_selected_covers(self):
        norm_list, c360_list = [], []
        for row, fname, fname_lower, chk_normal, chk_360 in self.row_data:
            if chk_normal.isChecked(): norm_list.append(fname)
            elif chk_360.isChecked(): c360_list.append(fname)
        return norm_list, c360_list


class MarkerSelectDialog(QDialog):
    def __init__(self, items_dict, current_selected_id=None, lang='de', parent=None):
        super().__init__(parent)
        self.lang = lang
        t = TRANSLATIONS[self.lang]
        self.setWindowTitle(t['select_marker_title'])
        self.resize(400, 450)
        self.selected_marker_id = None
        self.pick_on_map_requested = False
        
        layout = QVBoxLayout(self)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(t['search_placeholder'])
        self.search_edit.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_edit)
        
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(24, 24))
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.marker_items_data = []
        
        markers = []
        for m_id, d in items_dict.items():
            if d.get('type') == 'marker' and d.get('graphics'):
                g = d['graphics']
                markers.append((g.display_name or g.name, m_id, g))
        markers.sort(key=lambda x: x[0].lower())
        
        for disp_name, m_id, g in markers:
            lvl_str = f" (Level {g.level})" if getattr(g, 'level', 0) != 0 else ""
            item = QListWidgetItem(f"{disp_name}{lvl_str}")
            item.setData(Qt.ItemDataRole.UserRole, m_id)
            if g.pixmap() and not g.pixmap().isNull(): item.setIcon(QIcon(g.pixmap()))
            if m_id == current_selected_id: item.setSelected(True)
            self.list_widget.addItem(item)
            self.marker_items_data.append((item, m_id, f"{disp_name}{lvl_str}".lower()))
        layout.addWidget(self.list_widget)

        btn_box = QHBoxLayout()
        btn_map = QPushButton(t['pick_on_map']); btn_map.clicked.connect(self.on_pick_on_map); btn_box.addWidget(btn_map)
        btn_box.addStretch()
        btn_ok = QPushButton(t['confirm']); btn_ok.clicked.connect(self.on_confirm); btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def filter_items(self, text):
        query = text.lower().strip()
        for item, m_id, search_str in self.marker_items_data:
            item.setHidden(query not in search_str)

    def on_item_double_clicked(self, item):
        self.selected_marker_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def on_confirm(self):
        sel = self.list_widget.selectedItems()
        if sel:
            self.selected_marker_id = sel[0].data(Qt.ItemDataRole.UserRole)
            self.accept()

    def on_pick_on_map(self):
        self.pick_on_map_requested = True
        self.reject()


class ControlHandle(QGraphicsEllipseItem):
    def __init__(self, point_type, line_item):
        super().__init__(-6, -6, 12, 12, line_item)
        self.point_type = point_type
        self.line_item = line_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.update_handle_color()
        self.setZValue(100)

    def update_handle_color(self):
        if self.line_item and getattr(self.line_item, 'is_ramp', False):
            if self.point_type == 'p1': self.setBrush(QColor(46, 204, 113))
            elif self.point_type == 'p2': self.setBrush(QColor(52, 152, 219))
            else: self.setBrush(QColor(241, 196, 15))
        else:
            self.setBrush(QColor(255, 0, 0) if self.point_type != 'ctrl' else QColor(0, 120, 255))
        self.setPen(QPen(Qt.GlobalColor.black, 1))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.line_item:
            new_pos = self.pos()
            if self.point_type == 'p1': self.line_item.p1 = new_pos
            elif self.point_type == 'p2': self.line_item.p2 = new_pos
            elif self.point_type == 'ctrl': self.line_item.ctrl = new_pos
            self.line_item.update_path(from_handle=True)
        return super().itemChange(change, value)


class CurveLineItem(QGraphicsPathItem):
    def __init__(self, id_str, p1, p2, ctrl=None, is_ramp=False):
        super().__init__()
        self.id_str = id_str
        self.p1, self.p2 = p1, p2
        self.ctrl = ctrl if ctrl else QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        self.is_ramp = is_ramp
        self.is_edit = True
        self.is_custom_length = False
        self.name = ""
        self.display_name = ""
        self.max_font_size = 14.0
        self.length_val = 100.0
        self.length_unit = "m"
        self.node_radius = 8.0
        self.modes = ["Auto", "ÖPNV", "Fuß", "Fahrrad", "Flugzeug"]
        self.level = 0
        self.start_level = 0
        self.end_level = 1 if is_ramp else 0
        
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.circle1 = QGraphicsEllipseItem(self)
        self.circle2 = QGraphicsEllipseItem(self)
        self.handle_p1 = ControlHandle('p1', self)
        self.handle_p2 = ControlHandle('p2', self)
        self.handle_ctrl = ControlHandle('ctrl', self)
        self.text_item = OutlinedTextItem("", font_size=14, parent=self)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.update_appearance()
        self.update_path()

    def update_appearance(self):
        pen1 = QPen(QColor(46, 204, 113), 2) if self.is_ramp else QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
        pen2 = QPen(QColor(52, 152, 219), 2) if self.is_ramp else QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
        self.circle1.setPen(pen1); self.circle2.setPen(pen2)
        self.circle1.setBrush(QBrush(Qt.BrushStyle.NoBrush)); self.circle2.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.handle_p1.update_handle_color(); self.handle_p2.update_handle_color(); self.handle_ctrl.update_handle_color()

    def update_node_radius(self, r):
        self.node_radius = r
        self.circle1.setRect(-r, -r, r*2, r*2)
        self.circle2.setRect(-r, -r, r*2, r*2)

    def update_scale_size(self, view_scale):
        self.text_item.set_font_size(max(3.0, self.max_font_size / max(1.0, view_scale)))
        self.update_path(from_handle=True)

    def update_path(self, from_handle=False):
        path = QPainterPath()
        path.moveTo(self.p1)
        path.quadTo(self.ctrl, self.p2)
        self.setPath(path)
        
        if not self.is_custom_length:
            self.length_val = round(path.length(), 1)

        self.update_node_radius(self.node_radius)
        self.circle1.setPos(self.p1); self.circle2.setPos(self.p2)
        if not from_handle:
            self.handle_p1.setPos(self.p1); self.handle_p2.setPos(self.p2); self.handle_ctrl.setPos(self.ctrl)
            
        mid_pt = path.pointAtPercent(0.5)
        angle = path.angleAtPercent(0.5)
        if 90 < angle < 270: angle -= 180
        rect = self.text_item.boundingRect()
        self.text_item.setTransformOriginPoint(rect.center())
        self.text_item.setPos(mid_pt.x() - rect.width() / 2, mid_pt.y() - rect.height() / 2)
        self.text_item.setRotation(-angle)

    def set_edit_mode(self, is_edit):
        self.is_edit = is_edit
        self.circle1.setVisible(is_edit); self.circle2.setVisible(is_edit)
        show_handles = is_edit and self.isSelected()
        self.handle_p1.setVisible(show_handles); self.handle_p2.setVisible(show_handles); self.handle_ctrl.setVisible(show_handles)
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
        self.handle_p1.setVisible(sel); self.handle_p2.setVisible(sel); self.handle_ctrl.setVisible(sel)
        if sel:
            color = QColor(155, 89, 182) if self.is_ramp else QColor(0, 120, 255)
            self.setPen(QPen(color, 4))
        else:
            color = QColor(100, 50, 150) if self.is_ramp else QColor(50, 50, 50)
            self.setPen(QPen(color, 3, Qt.PenStyle.DashDotLine if self.is_ramp else Qt.PenStyle.SolidLine))

    def update_text_display(self, text):
        self.display_name = text
        self.text_item.setText(text)
        self.update_path()


class MapMarkerItem(QGraphicsPixmapItem):
    def __init__(self, id_str, pos, icon_path=""):
        super().__init__()
        self.id_str = id_str
        self.name = ""
        self.display_name = ""
        self.max_font_size = 12.0
        self.level = 0
        self.icon_rel_path = icon_path
        self.base_pixmap = None
        self.covers = []
        self.covers_360 = []
        self.description = ""
        
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.text_item = OutlinedTextItem("", font_size=12, parent=self)
        self.setPos(pos)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.load_icon_image(icon_path)

    def load_icon_image(self, icon_path):
        self.icon_rel_path = icon_path if icon_path else ""
        full_p = self.icon_rel_path if os.path.isabs(self.icon_rel_path) else os.path.join(get_base_dir(), self.icon_rel_path)
        full_p = os.path.normpath(full_p)

        if os.path.exists(full_p) and self.icon_rel_path:
            pix = QPixmap(full_p)
            self.base_pixmap = pix if not pix.isNull() else QPixmap(32, 32)
        else:
            self.base_pixmap = QPixmap(32, 32)
            self.base_pixmap.fill(Qt.GlobalColor.red)
        self.update_scale_size(1.0)

    def update_scale_size(self, view_scale):
        self.text_item.set_font_size(max(3.0, self.max_font_size / max(1.0, view_scale)))
        if self.base_pixmap and not self.base_pixmap.isNull():
            target_size = min(32.0, max(12.0, 32.0 / max(0.001, view_scale)))
            scaled = self.base_pixmap.scaled(int(target_size), int(target_size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
            self.setOffset(-scaled.width() / 2, -scaled.height() / 2)
        self.update_text_position()

    def update_text_position(self):
        self.text_item.setText(self.display_name or self.name)
        rect = self.text_item.boundingRect()
        icon_h = self.pixmap().height() if not self.pixmap().isNull() else 32
        self.text_item.setPos(-rect.width() / 2, icon_h / 2 + 2)

    def set_edit_mode(self, is_edit):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, is_edit)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, is_edit)
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
        if not os.path.exists(path): return
        pix = QPixmap(path)
        if pix.isNull(): return
        self.bg_pixmap_item = self.scene.addPixmap(pix)
        self.bg_pixmap_item.setZValue(-100)
        self.setSceneRect(QRectF(pix.rect()))

    def wheelEvent(self, event):
        sf = 1.15 if event.angleDelta().y() > 0 else (1.0 / 1.15)
        self.scale(sf, sf)
        self.main_win.update_zoom_scales()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        scene_pos = self.mapToScene(event.pos())
        items = self.scene.items(scene_pos)
        marker = None
        for it in items:
            curr = it
            while curr:
                if isinstance(curr, MapMarkerItem): marker = curr; break
                curr = curr.parentItem()
            if marker: break

        if self.main_win.picking_target_marker:
            if marker: self.main_win.on_marker_picked(marker); event.accept(); return

        if not self.main_win.is_edit_mode and event.button() == Qt.MouseButton.LeftButton:
            if marker: self.main_win.open_cover_panel(marker); event.accept(); return
            else: self.main_win.close_cover_panel()

        if self.main_win.is_edit_mode:
            tool = self.main_win.current_tool
            if tool in ["line", "ramp"] and event.button() == Qt.MouseButton.LeftButton:
                if not self.drawing_line:
                    self.drawing_line = True
                    self.line_start_pt = scene_pos
                    self.temp_path_item = QGraphicsPathItem()
                    self.temp_path_item.setPen(QPen(Qt.GlobalColor.magenta if tool == "ramp" else Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                    self.scene.addItem(self.temp_path_item)
                else:
                    self.drawing_line = False
                    start_pt = self.line_start_pt
                    if self.temp_path_item:
                        self.scene.removeItem(self.temp_path_item)
                        self.temp_path_item = None
                    self.main_win.create_new_line(start_pt, scene_pos, is_ramp=(tool == "ramp"))
                    self.main_win.set_tool("select")
                event.accept()
                return
            elif tool == "marker" and event.button() == Qt.MouseButton.LeftButton:
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
            p = QPainterPath()
            p.moveTo(self.line_start_pt)
            p.lineTo(self.mapToScene(event.pos()))
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
            if item.scene() == self.scene: self.scene.removeItem(item)
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
        self.panel_loader_thread = None
        
        self.current_map_id = "meine_karte"
        self.current_map_title = "Neue Karte"
        self.current_map_version = "1.0.0"
        self.current_map_desc = ""
        self.current_map_cover = ""

        self.items_dict = {}
        self.line_counter = 1
        self.ramp_counter = 1
        self.marker_counter = 1
        self.folder_counter = 1
        
        self.init_ui()
        QTimer.singleShot(1000, self.check_app_updates)

    def tr(self, key): return TRANSLATIONS[self.current_lang].get(key, key)

    def init_ui(self):
        self.setWindowTitle("Himko WayFinder")
        self.setGeometry(100, 100, 1280, 800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.outer_layout = QVBoxLayout(self.central_widget)
        self.outer_layout.setContentsMargins(4, 4, 4, 4)
        
        self.setup_top_bar()
        
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = MapGraphicsView(self)
        self.cover_panel = QWidget()
        self.cover_panel.setFixedWidth(290)
        self.setup_cover_panel()
        self.cover_panel.setVisible(False)
        
        self.edit_panel = QWidget()
        self.normal_panel = QWidget()
        self.setup_edit_panel()
        self.setup_normal_panel()
        
        self.main_layout.addWidget(self.cover_panel)
        self.main_layout.addWidget(self.view, stretch=1)
        self.main_layout.addWidget(self.edit_panel)
        self.main_layout.addWidget(self.normal_panel)
        
        self.outer_layout.addLayout(self.main_layout)
        self.edit_panel.setVisible(False)
        self.normal_panel.setVisible(True)
        
        self.view_overlay_btn = QPushButton("Mode", self.view)
        self.view_overlay_btn.setFixedSize(120, 32)
        self.view_overlay_btn.move(10, 10)
        self.view_overlay_btn.clicked.connect(self.toggle_mode)
        
        self.view.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.apply_translations()

    def check_app_updates(self):
        self.app_update_worker = AppUpdateWorker(
            APP_VERSION, 
            owner=DEFAULT_GITHUB_OWNER, 
            repo=DEFAULT_GITHUB_REPO, 
            branch=DEFAULT_GITHUB_BRANCH
        )
        self.app_update_worker.update_available.connect(self.on_app_update_available)
        self.app_update_worker.start()

    def on_app_update_available(self, new_ver, changelog_text, new_code_bytes):
        dlg = AppUpdateDialog(
            APP_VERSION, new_ver, changelog_text, new_code_bytes, 
            lang=self.current_lang, parent=self
        )
        dlg.exec()

    def setup_top_bar(self):
        self.top_file_bar = QHBoxLayout()
        self.btn_load_map = QPushButton()
        self.btn_save_export = QPushButton()
        self.btn_online_store = QPushButton()
        
        self.btn_load_map.clicked.connect(self.open_local_manager_dialog)
        self.btn_save_export.clicked.connect(self.open_save_export_dialog)
        self.btn_online_store.clicked.connect(self.open_online_store_dialog)
        
        self.top_file_bar.addWidget(self.btn_load_map)
        self.top_file_bar.addWidget(self.btn_save_export)
        self.top_file_bar.addWidget(self.btn_online_store)
        self.top_file_bar.addStretch()
        self.outer_layout.addLayout(self.top_file_bar)

    def setup_cover_panel(self):
        lay = QVBoxLayout(self.cover_panel)
        lay.setContentsMargins(4, 4, 4, 4)
        
        header = QHBoxLayout()
        self.lbl_cover_title = QLabel("Marker Covers")
        self.lbl_cover_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        btn_close = QPushButton("X"); btn_close.setFixedWidth(30); btn_close.clicked.connect(self.close_cover_panel)
        header.addWidget(self.lbl_cover_title); header.addStretch(); header.addWidget(btn_close)
        lay.addLayout(header)

        self.btn_toggle_desc = QPushButton()
        self.lbl_desc_content = QLabel()
        self.lbl_desc_content.setWordWrap(True)
        
        def toggle_description():
            vis = self.lbl_desc_content.isVisible()
            self.lbl_desc_content.setVisible(not vis)
            self.btn_toggle_desc.setText(("▶ " if vis else "▼ ") + self.tr('description'))

        self.btn_toggle_desc.clicked.connect(toggle_description)
        lay.addWidget(self.btn_toggle_desc)
        lay.addWidget(self.lbl_desc_content)
        
        self.cover_tab_widget = QTabWidget()
        self.container_normal = QWidget()
        self.layout_normal = QVBoxLayout(self.container_normal)
        self.container_360 = QWidget()
        self.layout_360 = QVBoxLayout(self.container_360)
        
        scroll_norm = QScrollArea(); scroll_norm.setWidgetResizable(True); scroll_norm.setWidget(self.container_normal)
        scroll_360 = QScrollArea(); scroll_360.setWidgetResizable(True); scroll_360.setWidget(self.container_360)
        
        self.cover_tab_widget.addTab(scroll_norm, self.tr('tab_normal'))
        self.cover_tab_widget.addTab(scroll_360, self.tr('tab_360'))
        lay.addWidget(self.cover_tab_widget)

    def open_cover_panel(self, marker_item):
        t = TRANSLATIONS[self.current_lang]
        self.lbl_cover_title.setText(marker_item.display_name or marker_item.name)
        desc_text = getattr(marker_item, 'description', '').strip()
        self.btn_toggle_desc.setText("▼ " + t['description'])
        self.lbl_desc_content.setText(desc_text if desc_text else t['no_description'])
        self.lbl_desc_content.setVisible(True)
        
        if self.panel_loader_thread and self.panel_loader_thread.isRunning():
            self.panel_loader_thread.requestInterruption()
            self.panel_loader_thread.wait()

        for l in (self.layout_normal, self.layout_360):
            while l.count() > 0:
                w = l.takeAt(0).widget()
                if w: w.deleteLater()

        bg_requests = []
        cover_dir = get_cover_dir()
        
        covers = getattr(marker_item, 'covers', [])
        valid_covers = [os.path.join(cover_dir, c) for c in covers if os.path.exists(os.path.join(cover_dir, c))]
        if not valid_covers:
            self.layout_normal.addWidget(QLabel(t['no_covers_selected']))
        else:
            for fpath in valid_covers:
                lbl_img = ClickableLabel(fpath, self.open_full_image_viewer)
                lbl_img.setFixedHeight(140)
                lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_img.setText("...")
                self.layout_normal.addWidget(lbl_img)
                bg_requests.append((fpath, 250, lbl_img))

        covers_360 = getattr(marker_item, 'covers_360', [])
        valid_covers_360 = [os.path.join(cover_dir, c) for c in covers_360 if os.path.exists(os.path.join(cover_dir, c))]
        if not valid_covers_360:
            self.layout_360.addWidget(QLabel(t['no_covers_360_selected']))
        else:
            for fpath in valid_covers_360:
                lbl_img = ClickableLabel(fpath, self.open_360_image_viewer)
                lbl_img.setFixedHeight(140)
                lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_img.setText("...")
                self.layout_360.addWidget(lbl_img)
                bg_requests.append((fpath, 250, lbl_img))

        self.cover_panel.setVisible(True)

        if bg_requests:
            self.panel_loader_thread = BackgroundThumbnailLoader(bg_requests)
            self.panel_loader_thread.image_loaded.connect(self.on_panel_cover_loaded)
            self.panel_loader_thread.start()

    def on_panel_cover_loaded(self, fpath, width, qimg, target_label):
        if not qimg.isNull() and target_label:
            target_label.setFixedHeight(140)
            target_label.setPixmap(QPixmap.fromImage(qimg))
            target_label.setText("")

    def open_full_image_viewer(self, image_path): ZoomableImageViewerDialog(image_path, self).exec()
    def open_360_image_viewer(self, image_path): Panorama360ViewerDialog(image_path, self).exec()
    
    def close_cover_panel(self):
        if self.panel_loader_thread and self.panel_loader_thread.isRunning():
            self.panel_loader_thread.requestInterruption()
            self.panel_loader_thread.wait()
        self.cover_panel.setVisible(False)

    def setup_edit_panel(self):
        layout = QHBoxLayout(self.edit_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        left_tb = QVBoxLayout()
        left_tb.setContentsMargins(2, 2, 2, 2)
        
        self.btn_select = QPushButton()
        self.btn_line = QPushButton()
        self.btn_ramp = QPushButton()
        self.btn_marker = QPushButton()
        
        for btn in (self.btn_select, self.btn_line, self.btn_ramp, self.btn_marker):
            btn.setFixedSize(36, 36)
            btn.setIconSize(QSize(22, 22))
            btn.setCheckable(True)

        self.btn_select.setIcon(get_ui_icon("select.png"))
        self.btn_line.setIcon(get_ui_icon("line.png"))
        self.btn_ramp.setIcon(get_ui_icon("ramp.png"))
        self.btn_marker.setIcon(get_ui_icon("marker.png"))
        
        self.btn_select.setChecked(True)
        
        self.btn_select.clicked.connect(lambda: self.set_tool("select"))
        self.btn_line.clicked.connect(lambda: self.set_tool("line"))
        self.btn_ramp.clicked.connect(lambda: self.set_tool("ramp"))
        self.btn_marker.clicked.connect(lambda: self.set_tool("marker"))
        
        left_tb.addWidget(self.btn_select)
        left_tb.addWidget(self.btn_line)
        left_tb.addWidget(self.btn_ramp)
        left_tb.addWidget(self.btn_marker)
        left_tb.addStretch()
        
        right_side = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        top_box = QWidget()
        top_lay = QVBoxLayout(top_box)
        top_bar = QHBoxLayout()
        
        self.lbl_explorer = QLabel()
        self.lbl_explorer.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.btn_add_folder = QPushButton()
        self.btn_add_folder.setFixedSize(32, 26)
        self.btn_add_folder.setIcon(get_ui_icon("folder.png"))
        self.btn_add_folder.setIconSize(QSize(18, 18))
        self.btn_add_folder.clicked.connect(self.create_new_folder)
        
        top_bar.addWidget(self.lbl_explorer)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_add_folder)
        
        top_lay.addLayout(top_bar)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        top_lay.addWidget(self.tree)
        
        bottom_box = QWidget()
        bot_lay = QVBoxLayout(bottom_box)
        self.lbl_props = QLabel()
        self.lbl_props.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.prop_table = QTableWidget()
        self.prop_table.setColumnCount(2)
        self.prop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prop_table.horizontalHeader().setVisible(False)
        bot_lay.addWidget(self.lbl_props)
        bot_lay.addWidget(self.prop_table)
        
        splitter.addWidget(top_box)
        splitter.addWidget(bottom_box)
        right_side.addWidget(splitter)
        
        layout.addLayout(left_tb)
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
        
        self.lbl_mode_sel = QLabel()
        self.cmb_primary_mode = QComboBox()
        lay.addWidget(self.lbl_mode_sel)
        lay.addWidget(self.cmb_primary_mode)
        
        self.lbl_start = QLabel()
        self.btn_start_marker = QPushButton()
        self.btn_start_marker.clicked.connect(lambda: self.start_picking_marker(self.btn_start_marker))
        lay.addWidget(self.lbl_start)
        lay.addWidget(self.btn_start_marker)
        
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
        lay.addWidget(self.lbl_dist_res)
        lay.addStretch()

    def apply_translations(self):
        t = TRANSLATIONS[self.current_lang]
        self.view_overlay_btn.setText(t['edit_mode'] if not self.is_edit_mode else t['normal_mode'])
        self.btn_load_map.setText(t['load_map'])
        self.btn_save_export.setText(t['save_export'])
        self.btn_online_store.setText(t['online_store'])
        self.lbl_explorer.setText(t['explorer'])
        self.lbl_props.setText(t['properties'])
        self.lbl_route_title.setText(t['route_planner'])
        self.lbl_mode_sel.setText(t['travel_mode'])
        self.lbl_start.setText(t['start_marker'])
        
        if not self.btn_start_marker.property("marker_id"): 
            self.btn_start_marker.setText(t['select_target'])
            
        self.btn_add_waypoint.setText(t['add_stop'])
        self.btn_calc_route.setText(t['calculate_route'])
        self.btn_clear_route.setText(t['clear_route'])
        self.cover_tab_widget.setTabText(0, t['tab_normal'])
        self.cover_tab_widget.setTabText(1, t['tab_360'])

        curr_mode_idx = max(0, self.cmb_primary_mode.currentIndex())
        self.cmb_primary_mode.blockSignals(True)
        self.cmb_primary_mode.clear()
        self.cmb_primary_mode.addItems([
            t['mode_auto'], t['mode_opnv'], t['mode_fuss'], t['mode_fahrrad'], t['mode_flugzeug']
        ])
        self.cmb_primary_mode.setCurrentIndex(curr_mode_idx)
        self.cmb_primary_mode.blockSignals(False)

    def change_language(self, index):
        self.current_lang = 'de' if index == 0 else 'en'
        self.apply_translations()

    def clear_route_all(self):
        self.view.clear_route_display()
        self.lbl_dist_res.setText("")

    def clear_all_data(self):
        with QSignalBlocker(self.tree), QSignalBlocker(self.view.scene):
            self.view.clear_route_display()
            self.view.scene.clear()
            self.view.bg_pixmap_item = None
            self.items_dict.clear()
            self.tree.clear()
            self.prop_table.setRowCount(0)
            self.reset_start_marker_btn()
            self.close_cover_panel()
            while self.waypoints_container.count() > 0:
                child = self.waypoints_container.takeAt(0)
                if child and child.widget(): child.widget().deleteLater()

    def toggle_mode(self):
        self.clear_route_all()
        self.close_cover_panel()
        self.is_edit_mode = not self.is_edit_mode
        self.edit_panel.setVisible(self.is_edit_mode)
        self.normal_panel.setVisible(not self.is_edit_mode)
        for item in self.view.scene.items():
            if isinstance(item, (CurveLineItem, MapMarkerItem)): item.set_edit_mode(self.is_edit_mode)
        if not self.is_edit_mode: self.populate_marker_combos()
        self.apply_translations()

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        self.btn_select.setChecked(tool_name == "select")
        self.btn_line.setChecked(tool_name == "line")
        self.btn_ramp.setChecked(tool_name == "ramp")
        self.btn_marker.setChecked(tool_name == "marker")

    def create_new_line(self, p1, p2, is_ramp=False):
        prefix = "ramp" if is_ramp else "line"
        item_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        disp_name = f"{'Ramp' if is_ramp else 'Line'}_{self.ramp_counter if is_ramp else self.line_counter}"
        if is_ramp: self.ramp_counter += 1
        else: self.line_counter += 1
        
        line_item = CurveLineItem(item_id, p1, p2, is_ramp=is_ramp)
        line_item.name = disp_name
        line_item.set_edit_mode(True)
        self.view.scene.addItem(line_item)
        line_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem([disp_name])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self.tree.addTopLevelItem(tree_item)
            self.tree.setCurrentItem(tree_item)
        
        self.items_dict[item_id] = {'graphics': line_item, 'tree': tree_item, 'type': 'line'}
        self.build_properties_table(item_id)
        self.update_zoom_scales()

    def create_new_marker(self, pos):
        item_id = f"marker_{uuid.uuid4().hex[:8]}"
        disp_name = f"Marker_{self.marker_counter}"
        self.marker_counter += 1
        
        marker_item = MapMarkerItem(item_id, pos, "")
        marker_item.name = disp_name
        marker_item.display_name = disp_name
        marker_item.set_edit_mode(True)
        self.view.scene.addItem(marker_item)
        marker_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem([disp_name])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self.tree.addTopLevelItem(tree_item)
            self.tree.setCurrentItem(tree_item)
            
        self.items_dict[item_id] = {'graphics': marker_item, 'tree': tree_item, 'type': 'marker'}
        self.build_properties_table(item_id)
        self.update_zoom_scales()

    def create_new_folder(self):
        item_id = f"folder_{uuid.uuid4().hex[:8]}"
        disp_name = f"Folder_{self.folder_counter}"
        self.folder_counter += 1
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem([disp_name])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self.tree.addTopLevelItem(tree_item)
        self.items_dict[item_id] = {'graphics': None, 'tree': tree_item, 'type': 'folder'}

    def open_local_manager_dialog(self): LocalMapManagerDialog(self, self).exec()
    def open_save_export_dialog(self): SaveAndExportDialog(self, self).exec()
    def open_online_store_dialog(self): OnlineMapStoreDialog(self, self).exec()

    def execute_save_and_export(self, filename, title, version, desc, cover_img, export_manifest=False):
        if not filename: filename = "meine_karte"
        self.current_map_id = filename
        self.current_map_title = title or filename
        self.current_map_version = version or "1.0.0"
        self.current_map_desc = desc
        self.current_map_cover = cover_img or ""

        maps_dir = get_maps_dir()
        lines_data, markers_data, folders_data = [], [], []
        referenced_covers, referenced_icons = set(), set()

        if self.current_map_cover: referenced_covers.add(self.current_map_cover)

        def process_tree_item(tree_item, parent_id=None):
            id_str = tree_item.data(0, Qt.ItemDataRole.UserRole)
            if not id_str or id_str not in self.items_dict: return
            d = self.items_dict[id_str]
            g = d['graphics']

            if d['type'] == 'folder':
                folders_data.append({'id': id_str, 'name': tree_item.text(0), 'parent': parent_id})
            elif d['type'] == 'line' and g:
                entry = {
                    'id': id_str, 'name': g.name, 'display_name': g.display_name,
                    'font_size': round(g.max_font_size, 1),
                    'p1': [round(g.p1.x(), 2), round(g.p1.y(), 2)],
                    'p2': [round(g.p2.x(), 2), round(g.p2.y(), 2)],
                    'ctrl': [round(g.ctrl.x(), 2), round(g.ctrl.y(), 2)],
                    'length_val': round(g.length_val, 2), 'length_unit': g.length_unit,
                    'node_radius': round(g.node_radius, 1), 'modes': g.modes, 'parent': parent_id
                }
                if getattr(g, 'is_ramp', False):
                    entry['is_ramp'] = True
                    entry['start_level'] = getattr(g, 'start_level', 0)
                    entry['end_level'] = getattr(g, 'end_level', 0)
                else: entry['level'] = getattr(g, 'level', 0)
                lines_data.append(entry)
            elif d['type'] == 'marker' and g:
                entry = {
                    'id': id_str, 'name': g.name, 'display_name': g.display_name,
                    'font_size': round(g.max_font_size, 1), 'level': getattr(g, 'level', 0),
                    'pos': [round(g.pos().x(), 2), round(g.pos().y(), 2)],
                    'icon': g.icon_rel_path, 'parent': parent_id
                }
                if g.covers:
                    entry['covers'] = g.covers
                    for c in g.covers: referenced_covers.add(c)
                if g.covers_360:
                    entry['covers_360'] = g.covers_360
                    for c in g.covers_360: referenced_covers.add(c)
                if g.description: entry['description'] = g.description
                if g.icon_rel_path: referenced_icons.add(os.path.basename(g.icon_rel_path))
                markers_data.append(entry)

            for c_idx in range(tree_item.childCount()):
                process_tree_item(tree_item.child(c_idx), parent_id=id_str)

        for top_idx in range(self.tree.topLevelItemCount()):
            process_tree_item(self.tree.topLevelItem(top_idx))

        map_json_filename = f"{filename}.json"
        map_json_path = os.path.join(maps_dir, map_json_filename)
        
        map_out = {
            'id': filename,
            'title': self.current_map_title,
            'version': self.current_map_version,
            'description': self.current_map_desc,
            'map_cover': self.current_map_cover,
            'image': self.current_image_filename,
            'folders': folders_data,
            'lines': lines_data,
            'markers': markers_data
        }
        
        with open(map_json_path, 'w', encoding='utf-8') as f:
            json.dump(map_out, f, indent=2, ensure_ascii=False)

        if export_manifest:
            install_manifest_name = f"{filename}_install.json"
            install_manifest_path = os.path.join(maps_dir, install_manifest_name)
            manifest_out = {
                'id': filename,
                'name': self.current_map_title,
                'version': self.current_map_version,
                'description': self.current_map_desc,
                'map_cover': self.current_map_cover,
                'map_file': map_json_filename,
                'image_file': self.current_image_filename,
                'covers': sorted(list(referenced_covers)),
                'icons': sorted(list(referenced_icons))
            }
            with open(install_manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_out, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "OK", f"Map & Manifest exported:\n- {map_json_filename}\n- {install_manifest_name}")
        else:
            QMessageBox.information(self, "OK", f"Saved locally: /maps/{map_json_filename}")

    def load_map_from_filepath(self, fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading map: {e}")
            return

        if not isinstance(data, dict): return
        self.clear_all_data()

        self.current_map_id = safe_str(data.get('id'), os.path.splitext(os.path.basename(fpath))[0])
        self.current_map_title = safe_str(data.get('title'), self.current_map_id)
        self.current_map_version = safe_str(data.get('version'), "1.0.0")
        self.current_map_desc = safe_str(data.get('description'), "")
        self.current_map_cover = safe_str(data.get('map_cover'), "")

        img_name = safe_str(data.get('image'), '')
        self.current_image_filename = img_name
        if img_name:
            img_path = os.path.join(get_maps_dir(), img_name)
            if os.path.exists(img_path): self.view.set_background_image(img_path)

        created_tree_items = {}

        for f in data.get('folders', []):
            if not isinstance(f, dict): continue
            f_id = safe_str(f.get('id')) or f"folder_{uuid.uuid4().hex[:8]}"
            tree_item = QTreeWidgetItem([safe_str(f.get('name'), 'Folder')])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, f_id)
            created_tree_items[f_id] = tree_item
            self.items_dict[f_id] = {'graphics': None, 'tree': tree_item, 'type': 'folder'}

        for l in data.get('lines', []):
            if not isinstance(l, dict): continue
            l_id = safe_str(l.get('id')) or f"line_{uuid.uuid4().hex[:8]}"
            p1 = safe_point(l.get('p1'), 0, 0)
            p2 = safe_point(l.get('p2'), 100, 100)
            ctrl_raw = l.get('ctrl')
            ctrl = safe_point(ctrl_raw, (p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2) if ctrl_raw is not None else QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            is_ramp = safe_bool(l.get('is_ramp'), False)

            line_item = CurveLineItem(l_id, p1, p2, ctrl, is_ramp=is_ramp)
            line_item.name = safe_str(l.get('name'), 'Line')
            line_item.max_font_size = safe_float(l.get('font_size'), 14.0)
            base_level = safe_int(l.get('level'), 0)
            line_item.level = base_level
            line_item.start_level = safe_int(l.get('start_level'), base_level)
            line_item.end_level = safe_int(l.get('end_level'), 1 if is_ramp else base_level)
            line_item.update_text_display(safe_str(l.get('display_name'), ''))
            line_item.length_val = safe_float(l.get('length_val'), round(line_item.path().length(), 1))
            line_item.is_custom_length = l.get('length_val') is not None
            line_item.length_unit = safe_str(l.get('length_unit'), 'm')
            line_item.node_radius = safe_float(l.get('node_radius'), 8.0)
            
            modes_raw = l.get('modes')
            line_item.modes = [safe_str(m) for m in modes_raw] if isinstance(modes_raw, list) else ["Auto", "ÖPNV", "Fuß", "Fahrrad", "Flugzeug"]
            line_item.set_edit_mode(self.is_edit_mode)
            self.view.scene.addItem(line_item)

            tree_item = QTreeWidgetItem([line_item.name])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, l_id)
            created_tree_items[l_id] = tree_item
            self.items_dict[l_id] = {'graphics': line_item, 'tree': tree_item, 'type': 'line'}

        for m in data.get('markers', []):
            if not isinstance(m, dict): continue
            m_id = safe_str(m.get('id')) or f"marker_{uuid.uuid4().hex[:8]}"
            marker_item = MapMarkerItem(m_id, safe_point(m.get('pos'), 0, 0), safe_str(m.get('icon'), ''))
            marker_item.name = safe_str(m.get('name'), 'Marker')
            marker_item.max_font_size = safe_float(m.get('font_size'), 12.0)
            marker_item.level = safe_int(m.get('level'), 0)
            marker_item.display_name = safe_str(m.get('display_name'), marker_item.name)
            marker_item.description = safe_str(m.get('description'), '')
            
            covers_raw = m.get('covers', [])
            if isinstance(covers_raw, list): marker_item.covers = [safe_str(c) for c in covers_raw]
            covers_360_raw = m.get('covers_360', [])
            if isinstance(covers_360_raw, list): marker_item.covers_360 = [safe_str(c) for c in covers_360_raw]

            marker_item.set_edit_mode(self.is_edit_mode)
            self.view.scene.addItem(marker_item)

            tree_item = QTreeWidgetItem([marker_item.name])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, m_id)
            created_tree_items[m_id] = tree_item
            self.items_dict[m_id] = {'graphics': marker_item, 'tree': tree_item, 'type': 'marker'}

        all_elements = []
        for k in ['folders', 'lines', 'markers']:
            lst = data.get(k, [])
            if isinstance(lst, list): all_elements.extend([i for i in lst if isinstance(i, dict)])

        for elem in all_elements:
            e_id = elem.get('id')
            if not e_id or e_id not in created_tree_items: continue
            t_item = created_tree_items[e_id]
            parent_id = elem.get('parent')
            if parent_id and parent_id in created_tree_items and parent_id != e_id:
                created_tree_items[parent_id].addChild(t_item)
            else:
                self.tree.addTopLevelItem(t_item)

        for item_id, t_item in created_tree_items.items():
            if t_item.treeWidget() is None and t_item.parent() is None: self.tree.addTopLevelItem(t_item)

        self.populate_marker_combos()
        self.update_zoom_scales()

    def populate_marker_combos(self):
        start_id = self.btn_start_marker.property("marker_id")
        if start_id and start_id in self.items_dict and self.items_dict[start_id]['graphics']:
            g = self.items_dict[start_id]['graphics']
            self.btn_start_marker.setText(g.display_name or g.name)
        else:
            self.reset_start_marker_btn()

    def reset_start_marker_btn(self):
        self.btn_start_marker.setText(self.tr('select_target'))
        self.btn_start_marker.setProperty("marker_id", None)

    def add_waypoint_field(self):
        row_w = QWidget()
        lay = QHBoxLayout(row_w); lay.setContentsMargins(0, 0, 0, 0)
        btn_pick = QPushButton(self.tr('select_target'))
        btn_pick.clicked.connect(lambda checked, b=btn_pick: self.start_picking_marker(b))
        btn_rem = QPushButton("X"); btn_rem.setFixedWidth(30)
        btn_rem.clicked.connect(lambda checked, r=row_w: self.remove_waypoint_field(r))
        lay.addWidget(btn_pick); lay.addWidget(btn_rem)
        self.waypoints_container.addWidget(row_w)

    def remove_waypoint_field(self, widget):
        if self.active_waypoint_btn and widget.isAncestorOf(self.active_waypoint_btn):
            self.picking_target_marker = False
            self.active_waypoint_btn = None
        self.waypoints_container.removeWidget(widget)
        widget.deleteLater()

    def start_picking_marker(self, btn):
        current_id = btn.property("marker_id")
        dlg = MarkerSelectDialog(self.items_dict, current_selected_id=current_id, lang=self.current_lang, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.selected_marker_id and dlg.selected_marker_id in self.items_dict:
                g = self.items_dict[dlg.selected_marker_id]['graphics']
                if g:
                    btn.setText(g.display_name or g.name)
                    btn.setProperty("marker_id", dlg.selected_marker_id)
        elif dlg.pick_on_map_requested:
            self.picking_target_marker = True
            self.active_waypoint_btn = btn
            btn.setText("...")

    def on_marker_picked(self, marker_item):
        if self.active_waypoint_btn:
            try:
                self.active_waypoint_btn.setText(marker_item.display_name or marker_item.name)
                self.active_waypoint_btn.setProperty("marker_id", marker_item.id_str)
            except RuntimeError: pass
        self.picking_target_marker = False
        self.active_waypoint_btn = None

    def on_tree_item_changed(self, item, column):
        id_str = item.data(0, Qt.ItemDataRole.UserRole)
        if id_str in self.items_dict and self.items_dict[id_str]['graphics']:
            self.items_dict[id_str]['graphics'].name = item.text(0)

    def on_tree_selection_changed(self):
        selected_tree_items = self.tree.selectedItems()
        with QSignalBlocker(self.view.scene):
            for item in self.view.scene.items():
                if isinstance(item, (CurveLineItem, MapMarkerItem)):
                    item.setSelected(False)
                    if isinstance(item, CurveLineItem): item.update_selection_pen()

        if not selected_tree_items: self.prop_table.setRowCount(0); return
        tree_item = selected_tree_items[0]
        id_str = tree_item.data(0, Qt.ItemDataRole.UserRole)
        
        if id_str in self.items_dict and self.items_dict[id_str]['graphics']:
            gitem = self.items_dict[id_str]['graphics']
            with QSignalBlocker(self.view.scene):
                gitem.setSelected(True)
                if isinstance(gitem, CurveLineItem): gitem.update_selection_pen()
            self.build_properties_table(id_str)
        else: self.prop_table.setRowCount(0)

    def on_scene_selection_changed(self):
        if not self.is_edit_mode: return
        selected_gitems = [i for i in self.view.scene.selectedItems() if isinstance(i, (CurveLineItem, MapMarkerItem))]
        for item in self.view.scene.items():
            if isinstance(item, CurveLineItem): item.update_selection_pen()
        if not selected_gitems:
            with QSignalBlocker(self.tree): self.tree.clearSelection()
            self.prop_table.setRowCount(0)
            return
        gitem = selected_gitems[0]
        for id_str, d in self.items_dict.items():
            if d['graphics'] == gitem:
                with QSignalBlocker(self.tree): self.tree.setCurrentItem(d['tree'])
                self.build_properties_table(id_str)
                break

    def build_properties_table(self, id_str):
        self.prop_table.clear(); self.prop_table.setRowCount(0)
        data = self.items_dict.get(id_str)
        if not data or not data['graphics']: return
        gitem = data['graphics']
        t = TRANSLATIONS[self.current_lang]

        if data['type'] == 'line':
            is_ramp = getattr(gitem, 'is_ramp', False)
            self.prop_table.setRowCount(8 if is_ramp else 7)
            
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name); le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)

            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name); le_dname.textChanged.connect(lambda txt: gitem.update_text_display(txt))
            self.prop_table.setCellWidget(1, 1, le_dname)

            self.prop_table.setItem(2, 0, QTableWidgetItem(t['font_size']))
            le_fsize = QLineEdit(str(gitem.max_font_size)); le_fsize.textChanged.connect(lambda txt: self.set_item_font_size(gitem, txt))
            self.prop_table.setCellWidget(2, 1, le_fsize)

            self.prop_table.setItem(3, 0, QTableWidgetItem(t['length']))
            w_len = QWidget(); l_len = QHBoxLayout(w_len); l_len.setContentsMargins(0, 0, 0, 0)
            le_val = QLineEdit(str(gitem.length_val))
            cmb_u = QComboBox(); cmb_u.addItems(["mm", "cm", "m", "km", "lichtjahre"]); cmb_u.setCurrentText(gitem.length_unit)
            le_val.textChanged.connect(lambda txt: self.set_line_length_val(gitem, txt))
            cmb_u.currentTextChanged.connect(lambda txt: setattr(gitem, 'length_unit', txt))
            l_len.addWidget(le_val); l_len.addWidget(cmb_u)
            self.prop_table.setCellWidget(3, 1, w_len)

            self.prop_table.setItem(4, 0, QTableWidgetItem(t['node_radius']))
            le_radius = QLineEdit(str(gitem.node_radius)); le_radius.textChanged.connect(lambda txt: self.set_line_node_radius(gitem, txt))
            self.prop_table.setCellWidget(4, 1, le_radius)

            if is_ramp:
                self.prop_table.setItem(5, 0, QTableWidgetItem(t['start_level']))
                le_slevel = QLineEdit(str(getattr(gitem, 'start_level', 0)))
                le_slevel.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, 'start_level'))
                self.prop_table.setCellWidget(5, 1, le_slevel)

                self.prop_table.setItem(6, 0, QTableWidgetItem(t['end_level']))
                le_elevel = QLineEdit(str(getattr(gitem, 'end_level', 0)))
                le_elevel.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, 'end_level'))
                self.prop_table.setCellWidget(6, 1, le_elevel)
                modes_row = 7
            else:
                self.prop_table.setItem(5, 0, QTableWidgetItem(t['level']))
                le_level = QLineEdit(str(getattr(gitem, 'level', 0)))
                le_level.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, 'level'))
                self.prop_table.setCellWidget(5, 1, le_level)
                modes_row = 6

            self.prop_table.setItem(modes_row, 0, QTableWidgetItem(t['modes']))
            chk_combo = CheckableComboBox()
            avail = ["Auto", "ÖPNV", "Fuß", "Fahrrad", "Flugzeug"]
            curr_m = getattr(gitem, 'modes', avail)
            for m in avail: chk_combo.add_checkable_item(m, m in curr_m)
            chk_combo._changed_callback = lambda combo=chk_combo, target=gitem: setattr(target, 'modes', combo.get_checked_items())
            self.prop_table.setCellWidget(modes_row, 1, chk_combo)

        elif data['type'] == 'marker':
            self.prop_table.setRowCount(7)
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name); le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)

            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name)
            le_dname.textChanged.connect(lambda txt: (setattr(gitem, 'display_name', txt), gitem.update_text_position()))
            self.prop_table.setCellWidget(1, 1, le_dname)

            self.prop_table.setItem(2, 0, QTableWidgetItem(t['font_size']))
            le_fsize = QLineEdit(str(gitem.max_font_size)); le_fsize.textChanged.connect(lambda txt: self.set_item_font_size(gitem, txt))
            self.prop_table.setCellWidget(2, 1, le_fsize)

            self.prop_table.setItem(3, 0, QTableWidgetItem(t['level']))
            le_level = QLineEdit(str(getattr(gitem, 'level', 0))); le_level.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, 'level'))
            self.prop_table.setCellWidget(3, 1, le_level)

            self.prop_table.setItem(4, 0, QTableWidgetItem(t['icon']))
            cmb_icon = IconGridComboBox()
            marker_icons_dir = get_icons_dir()
            icon_files = [os.path.join("icons", "marker", f) for f in os.listdir(marker_icons_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.svg'))] if os.path.exists(marker_icons_dir) else []
            icon_files.sort()
            
            cur_idx = 0
            for idx, path in enumerate(icon_files):
                full_p = os.path.normpath(os.path.join(get_base_dir(), path))
                cmb_icon.addItem(QIcon(full_p) if os.path.exists(full_p) else QIcon(), os.path.splitext(os.path.basename(path))[0], path)
                if os.path.normpath(path) == os.path.normpath(gitem.icon_rel_path): cur_idx = idx

            cmb_icon.setCurrentIndex(cur_idx)
            cmb_icon.currentIndexChanged.connect(lambda idx: gitem.load_icon_image(cmb_icon.itemData(idx)))
            self.prop_table.setCellWidget(4, 1, cmb_icon)

            self.prop_table.setItem(5, 0, QTableWidgetItem(t['covers']))
            btn_covers = QPushButton()
            def update_btn_text():
                cnt = len(gitem.covers) + len(gitem.covers_360)
                btn_covers.setText(t['covers_selected_count'].format(count=cnt) if cnt > 0 else t['select_covers'])
            update_btn_text()

            def open_cover_dlg():
                dlg = CoverSelectDialog(gitem.covers, gitem.covers_360, lang=self.current_lang, parent=self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    gitem.covers, gitem.covers_360 = dlg.get_selected_covers()
                    update_btn_text()

            btn_covers.clicked.connect(open_cover_dlg)
            self.prop_table.setCellWidget(5, 1, btn_covers)

            self.prop_table.setItem(6, 0, QTableWidgetItem(t['description']))
            te_desc = QTextEdit(); te_desc.setPlainText(getattr(gitem, 'description', '')); te_desc.setFixedHeight(75)
            te_desc.textChanged.connect(lambda: setattr(gitem, 'description', te_desc.toPlainText()))
            self.prop_table.setCellWidget(6, 1, te_desc)

    def set_item_font_size(self, gitem, txt):
        try:
            val = float(txt)
            if val > 0: gitem.max_font_size = val; gitem.update_scale_size(self.view.transform().m11())
        except ValueError: pass

    def set_item_level(self, gitem, txt, level_attr='level'):
        try: setattr(gitem, level_attr, int(txt))
        except ValueError: pass

    def set_line_length_val(self, gitem, txt):
        try:
            val = float(txt)
            if val >= 0: gitem.length_val = val; gitem.is_custom_length = True
        except ValueError: pass

    def set_line_node_radius(self, gitem, txt):
        try:
            val = float(txt)
            if val > 0: gitem.update_node_radius(val)
        except ValueError: pass

    def update_item_name(self, id_str, new_name):
        d = self.items_dict.get(id_str)
        if d:
            with QSignalBlocker(self.tree): d['tree'].setText(0, new_name)
            if d['graphics']: d['graphics'].name = new_name

    def update_zoom_scales(self):
        sf = self.view.transform().m11()
        if sf <= 0: return
        for item in self.view.scene.items():
            if isinstance(item, (MapMarkerItem, CurveLineItem)): item.update_scale_size(sf)

    def run_route_algorithm(self):
        self.clear_route_all()
        start_id = self.btn_start_marker.property("marker_id")
        if not start_id:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return
            
        target_ids = []
        for i in range(self.waypoints_container.count()):
            w = self.waypoints_container.itemAt(i).widget()
            if w:
                btn = w.findChild(QPushButton)
                if btn and btn.property("marker_id"): target_ids.append(btn.property("marker_id"))
                    
        if not target_ids:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return

        selected_mode_idx = self.cmb_primary_mode.currentIndex()
        internal_modes = ["Auto", "ÖPNV", "Fuß", "Fahrrad", "Flugzeug"]
        selected_mode = internal_modes[selected_mode_idx] if selected_mode_idx < len(internal_modes) else "Auto"

        all_stops = [start_id] + target_ids
        total_path_elements, total_len_meters = [], 0.0
        route_failed = False
        
        for i in range(len(all_stops) - 1):
            sub_elements, sub_len = self.find_path_between_markers(all_stops[i], all_stops[i+1], selected_mode)
            if sub_elements:
                total_path_elements.extend(sub_elements)
                total_len_meters += sub_len
            else: route_failed = True; break
                
        if route_failed or not total_path_elements:
            self.lbl_dist_res.setText(self.tr('no_route_found'))
            self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: red;")
            return

        self.render_route(total_path_elements, selected_mode)
        disp_txt = f"{self.tr('total_distance')}: {total_len_meters:.2f} m"
        if total_len_meters > 1000: disp_txt = f"{self.tr('total_distance')}: {total_len_meters/1000.0:.2f} km"
        self.lbl_dist_res.setText(disp_txt)
        self.lbl_dist_res.setStyleSheet("font-size: 12px; font-weight: bold; color: green;")

    def find_path_between_markers(self, start_m_id, end_m_id, primary_mode):
        if start_m_id not in self.items_dict or end_m_id not in self.items_dict: return [], 0.0
        start_m = self.items_dict[start_m_id]['graphics']
        end_m = self.items_dict[end_m_id]['graphics']
        if not start_m or not end_m: return [], 0.0
        
        start_level = getattr(start_m, 'level', 0)
        end_level = getattr(end_m, 'level', 0)
        all_lines = [d['graphics'] for d in self.items_dict.values() if d['type'] == 'line' and d['graphics']]
        
        if not all_lines:
            direct_p = QPainterPath(); direct_p.moveTo(start_m.pos()); direct_p.lineTo(end_m.pos())
            return [(direct_p, "Anschluss_Fuß")], QLineF(start_m.pos(), end_m.pos()).length()

        endpoints = []
        for line_idx, line in enumerate(all_lines):
            l1 = getattr(line, 'start_level', 0) if getattr(line, 'is_ramp', False) else getattr(line, 'level', 0)
            l2 = getattr(line, 'end_level', 0) if getattr(line, 'is_ramp', False) else getattr(line, 'level', 0)
            endpoints.append((line_idx, 'p1', line.p1, l1, line))
            endpoints.append((line_idx, 'p2', line.p2, l2, line))

        num_ep = len(endpoints)
        parent = list(range(num_ep))

        def find(i):
            path = []
            while parent[i] != i: path.append(i); i = parent[i]
            for n in path: parent[n] = i
            return i

        def union(i, j):
            ri, rj = find(i), find(j)
            if ri != rj: parent[ri] = rj

        grid, cell_size = {}, 20.0
        for i in range(num_ep):
            line_i_idx, _, pos_i, lvl_i, line_i = endpoints[i]
            cell_key = (int(pos_i.x() // cell_size), int(pos_i.y() // cell_size), lvl_i)
            cx, cy, cl = cell_key
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nk = (cx + dx, cy + dy, cl)
                    if nk in grid:
                        for j in grid[nk]:
                            line_j_idx, _, pos_j, _, line_j = endpoints[j]
                            if line_i_idx == line_j_idx:
                                if QLineF(pos_i, pos_j).length() <= 2.0: union(i, j)
                            else:
                                if QLineF(pos_i, pos_j).length() <= max(line_i.node_radius, line_j.node_radius, 12.0): union(i, j)
            if cell_key not in grid: grid[cell_key] = []
            grid[cell_key].append(i)

        groups = {}
        for i in range(num_ep):
            r = find(i)
            if r not in groups: groups[r] = []
            groups[r].append(i)

        node_map, nodes, node_levels = {}, [], []
        for group_idx, (r, ep_indices) in enumerate(groups.items()):
            for ep_idx in ep_indices: node_map[ep_idx] = group_idx
            avg_x = sum(endpoints[ep_idx][2].x() for ep_idx in ep_indices) / len(ep_indices)
            avg_y = sum(endpoints[ep_idx][2].y() for ep_idx in ep_indices) / len(ep_indices)
            nodes.append(QPointF(avg_x, avg_y))
            node_levels.append(endpoints[ep_indices[0]][3])

        adj = {}
        for line_idx, line in enumerate(all_lines):
            u = node_map[line_idx * 2]
            v = node_map[line_idx * 2 + 1]
            if u == v: continue
            len_m = line.length_val * UNIT_FACTORS.get(line.length_unit, 1.0)
            line_modes = line.modes if getattr(line, 'modes', None) else []
            
            restricted = {"ÖPNV", "Transit", "Flugzeug", "Airplane"}
            is_restr = len(line_modes) > 0 and all(m in restricted for m in line_modes)

            if primary_mode in ["Fuß", "Walk"]:
                if is_restr: continue
                cost_mult = 1.0 if ("Fuß" in line_modes or "Walk" in line_modes) else 1.5
                used_mode = "Fuß"
            else:
                if primary_mode in line_modes: cost_mult = 1.0; used_mode = primary_mode
                elif ("Fuß" in line_modes or "Walk" in line_modes) and not is_restr: cost_mult = 2.5; used_mode = "Fuß"
                else: continue
            
            cost = len_m * cost_mult
            if u not in adj: adj[u] = []
            if v not in adj: adj[v] = []
            adj[u].append((v, cost, len_m, line, used_mode, 'fwd'))
            adj[v].append((u, cost, len_m, line, used_mode, 'rev'))

        if not nodes or not adj:
            direct_p = QPainterPath(); direct_p.moveTo(start_m.pos()); direct_p.lineTo(end_m.pos())
            return [(direct_p, "Anschluss_Fuß")], QLineF(start_m.pos(), end_m.pos()).length()

        OFF_STREET_WEIGHT = 100.0
        pq = []
        for n_idx in adj.keys():
            if node_levels[n_idx] == start_level:
                d_start = QLineF(start_m.pos(), nodes[n_idx]).length()
                heapq.heappush(pq, (d_start * OFF_STREET_WEIGHT, n_idx, [], d_start))

        best_total_cost = QLineF(start_m.pos(), end_m.pos()).length() * 10000.0
        best_path, best_real_len = None, 0.0
        visited = set()

        while pq:
            cost, curr, path, real_len = heapq.heappop(pq)
            if cost >= best_total_cost: break
            if curr in visited: continue
            visited.add(curr)

            if node_levels[curr] == end_level:
                d_to_end = QLineF(nodes[curr], end_m.pos()).length()
                total_cost = cost + d_to_end * OFF_STREET_WEIGHT
                if total_cost < best_total_cost:
                    best_total_cost = total_cost
                    best_path = (path, curr, d_to_end)
                    best_real_len = real_len + d_to_end

            for nxt, weight, l_m, line_obj, mode, direction in adj.get(curr, []):
                if nxt not in visited:
                    heapq.heappush(pq, (cost + weight, nxt, path + [(line_obj, mode, direction)], real_len + l_m))

        if best_path is None:
            direct_p = QPainterPath(); direct_p.moveTo(start_m.pos()); direct_p.lineTo(end_m.pos())
            return [(direct_p, "Anschluss_Fuß")], QLineF(start_m.pos(), end_m.pos()).length()

        path_lines, last_node_idx, end_gap_dist = best_path
        total_elements, extra_len = [], 0.0

        if path_lines:
            first_line_obj, _, first_dir = path_lines[0]
            start_node_pt = first_line_obj.p1 if first_dir == 'fwd' else first_line_obj.p2
            dist_start = QLineF(start_m.pos(), start_node_pt).length()
            if dist_start > 2.0:
                p_start = QPainterPath(); p_start.moveTo(start_m.pos()); p_start.lineTo(start_node_pt)
                total_elements.append((p_start, "Anschluss_Fuß")); extra_len += dist_start

            current_pt = start_node_pt
            for line_obj, mode, direction in path_lines:
                p_geo = QPainterPath()
                if direction == 'fwd':
                    p_geo.moveTo(line_obj.p1); p_geo.quadTo(line_obj.ctrl, line_obj.p2)
                    current_pt = line_obj.p2
                else:
                    p_geo.moveTo(line_obj.p2); p_geo.quadTo(line_obj.ctrl, line_obj.p1)
                    current_pt = line_obj.p1
                total_elements.append((p_geo, mode))

            dist_end = QLineF(current_pt, end_m.pos()).length()
            if dist_end > 2.0:
                p_end = QPainterPath(); p_end.moveTo(current_pt); p_end.lineTo(end_m.pos())
                total_elements.append((p_end, "Anschluss_Fuß")); extra_len += dist_end
        else:
            same_node_pt = nodes[last_node_idx]
            dist_start = QLineF(start_m.pos(), same_node_pt).length()
            dist_end = QLineF(same_node_pt, end_m.pos()).length()
            if dist_start > 2.0:
                p_start = QPainterPath(); p_start.moveTo(start_m.pos()); p_start.lineTo(same_node_pt)
                total_elements.append((p_start, "Anschluss_Fuß")); extra_len += dist_start
            if dist_end > 2.0:
                p_end = QPainterPath(); p_end.moveTo(same_node_pt); p_end.lineTo(end_m.pos())
                total_elements.append((p_end, "Anschluss_Fuß")); extra_len += dist_end

        return total_elements, (best_real_len - end_gap_dist + extra_len)

    def render_route(self, path_elements, primary_mode):
        mode_styles = {
            'Auto': (QColor(0, 102, 255), Qt.PenStyle.SolidLine, 6),
            'ÖPNV': (QColor(153, 51, 204), Qt.PenStyle.DashDotLine, 6),
            'Fuß': (QColor(0, 160, 80), Qt.PenStyle.DotLine, 5),
            'Fahrrad': (QColor(255, 128, 0), Qt.PenStyle.DashLine, 5),
            'Flugzeug': (QColor(220, 20, 60), Qt.PenStyle.DashDotDotLine, 4),
            'Anschluss_Fuß': (QColor(255, 0, 127), Qt.PenStyle.DotLine, 4),
        }
        for path_geo, mode in path_elements:
            path_item = QGraphicsPathItem()
            path_item.setPath(path_geo)
            color, style, width = mode_styles.get(mode, (QColor(0, 102, 255), Qt.PenStyle.SolidLine, 6))
            path_item.setPen(QPen(color, width, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            path_item.setZValue(10)
            self.view.scene.addItem(path_item)
            self.view.route_graphics_items.append(path_item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())