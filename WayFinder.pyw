# -*- coding: utf-8 -*-
# Copyright (c) 2026 himbeertoni9817
# Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
# See LICENSE file in the project root for full license terms.

import sys
import os
import json
import heapq
import math
import uuid
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, QSignalBlocker, QEvent, QSize, QPoint
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QPainterPath, QIcon, QFont, QBrush,
    QStandardItemModel, QStandardItem, QFontMetrics, QTransform, QPolygonF, QImage
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem,
    QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLineEdit, QLabel, QFileDialog, QSplitter,
    QListView, QFrame, QAbstractItemView, QScrollArea, QGridLayout, QDialog,
    QListWidget, QListWidgetItem, QCheckBox, QTextEdit, QTabWidget
)

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtGui import QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture
    HAS_OPENGL = True
except Exception:
    HAS_OPENGL = False
    QOpenGLWidget = QWidget

TRANSLATIONS = {
    'de': {
        'edit_mode': "Bearbeitungsmodus",
        'normal_mode': "Normaler Modus",
        'open_image': "Bild öffnen",
        'save_json': "JSON Speichern",
        'load_json': "JSON öffnen",
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
        'level': "Höhenstufe",
        'start_level': "Höhenstufe Startpunkt (Grün):",
        'end_level': "Höhenstufe Endpunkt (Blau):",
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
        'covers': "Bilder",
        'select_covers': "Bilder auswählen...",
        'no_covers_found': "Keine Bilder im Ordner /cover/ gefunden.",
        'no_covers_selected': "Keine normalen Bilder für diesen Marker.",
        'no_covers_360_selected': "Keine 360° Bilder für diesen Marker.",
        'covers_selected_count': "{count} Bild(er) gewählt",
        'select_images_title': "Cover-Bilder auswählen",
        'select_marker_title': "Marker auswählen",
        'pick_on_map': "Auf Karte auswählen",
        'no_markers_found': "Keine Marker vorhanden.",
        'search_placeholder': "Suchen...",
        'confirm': "Fertig",
        'close': "Schließen",
        'description': "Beschreibung",
        'no_description': "Keine Beschreibung vorhanden.",
        'tab_normal': "Fotos",
        'tab_360': "360°",
        'col_image': "Bild / Datei",
        'col_normal': "Normal",
        'col_360': "360°",
    },
    'en': {
        'edit_mode': "Edit Mode",
        'normal_mode': "Normal Mode",
        'open_image': "Open Image",
        'save_json': "Save JSON",
        'load_json': "Open JSON",
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
        'start_level': "Elevation Start Point (Green):",
        'end_level': "Elevation End Point (Blue):",
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
        'pick_on_map': "Select on map",
        'no_markers_found': "No markers available.",
        'search_placeholder': "Search...",
        'confirm': "Apply",
        'close': "Close",
        'description': "Description",
        'no_description': "No description available.",
        'tab_normal': "Photos",
        'tab_360': "360°",
        'col_image': "Image / File",
        'col_normal': "Normal",
        'col_360': "360°",
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

def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_str(val, default=""):
    if val is None:
        return default
    return str(val)

def safe_bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return default

def safe_point(raw_pt, default_x=0.0, default_y=0.0):
    if isinstance(raw_pt, (list, tuple)) and len(raw_pt) >= 2:
        return QPointF(safe_float(raw_pt[0], default_x), safe_float(raw_pt[1], default_y))
    return QPointF(default_x, default_y)

def get_cover_dir():
    cover_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "cover"))
    if not os.path.exists(cover_dir):
        os.makedirs(cover_dir, exist_ok=True)
    return cover_dir


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
        self.setWindowTitle("Photo Viewer")
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
            
            pw = self.pixmap.width()
            ph = self.pixmap.height()
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
            if not ctx:
                self.use_gl = False
                return
            gl = ctx.functions()
            if not gl:
                self.use_gl = False
                return
            
            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            
            shaders_to_try = [
                (
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
                ),
                (
                    """
                    attribute vec2 position;
                    varying vec2 v_uv;
                    void main() {
                        v_uv = vec2(position.x * 0.5 + 0.5, 0.5 - position.y * 0.5);
                        gl_Position = vec4(position, 0.0, 1.0);
                    }""",
                    """
                    #ifdef GL_ES
                    precision mediump float;
                    #endif
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
            ]
            
            prog_ok = False
            for vsrc, fsrc in shaders_to_try:
                vshader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Vertex, self)
                if not vshader.compileSourceCode(vsrc):
                    continue
                fshader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Fragment, self)
                if not fshader.compileSourceCode(fsrc):
                    continue
                prog = QOpenGLShaderProgram(self)
                prog.addShader(vshader)
                prog.addShader(fshader)
                if prog.link():
                    self.program = prog
                    prog_ok = True
                    break
            
            if not prog_ok:
                self.use_gl = False
                return

            if not self.pixmap.isNull():
                img = self.pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                self.texture = QOpenGLTexture(img)
                self.texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionS, QOpenGLTexture.WrapMode.Repeat)
                self.texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionT, QOpenGLTexture.WrapMode.ClampToEdge)
                self.texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
                self.texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
                
            self.gl_initialized = True
        except Exception:
            self.use_gl = False
            self.gl_initialized = False

    def resizeGL(self, w, h):
        if self.use_gl and self.gl_initialized:
            try:
                gl = self.context().functions()
                if gl:
                    gl.glViewport(0, 0, w, h)
            except Exception:
                pass

    def paintGL(self):
        if self.use_gl and self.gl_initialized and self.program and self.texture:
            try:
                gl = self.context().functions()
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                
                self.program.bind()
                self.texture.bind(0)
                self.program.setUniformValue("u_texture", 0)

                w = float(max(1, self.width()))
                h = float(max(1, self.height()))
                self.program.setUniformValue("u_resolution", QPointF(w, h))

                yaw_rad = math.radians(self.yaw_deg)
                pitch_rad = math.radians(self.pitch_deg)
                fov_rad = math.radians(80.0 / self.zoom_factor)

                self.program.setUniformValue("u_yaw", float(yaw_rad))
                self.program.setUniformValue("u_pitch", float(pitch_rad))
                self.program.setUniformValue("u_fov", float(fov_rad))

                pts = [
                    QPointF(-1.0, -1.0),
                    QPointF(1.0, -1.0),
                    QPointF(-1.0, 1.0),
                    QPointF(1.0, 1.0)
                ]

                pos_attr = self.program.attributeLocation("position")
                self.program.enableAttributeArray(pos_attr)
                self.program.setAttributeArray(pos_attr, pts)
                
                gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
                
                self.program.disableAttributeArray(pos_attr)
                self.texture.release()
                self.program.release()
                return
            except Exception:
                self.use_gl = False

        self.paint_cpu()

    def paintEvent(self, event):
        if HAS_OPENGL and self.use_gl:
            super().paintEvent(event)
        else:
            self.paint_cpu()

    def paint_cpu(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        w = float(self.width())
        h = float(self.height())
        if w <= 0 or h <= 0 or self.pixmap.isNull() or self.tiled_image.isNull():
            return

        pw = float(self.pixmap.width())
        ph = float(self.pixmap.height())

        cols = 24
        rows = 18

        aspect = w / h
        fov_rad = math.radians(80.0 / self.zoom_factor)
        f = math.tan(fov_rad / 2.0)

        pitch_rad = math.radians(self.pitch_deg)
        yaw_rad = math.radians(self.yaw_deg)

        cos_p, sin_p = math.cos(pitch_rad), math.sin(pitch_rad)
        cos_y, sin_y = math.cos(yaw_rad), math.sin(yaw_rad)

        grid_coords = []
        dx = w / cols
        dy = h / rows

        for j in range(rows + 1):
            row_coords = []
            ys = j * dy
            ny = 1.0 - (2.0 * ys / h)
            y_c = ny * f
            
            for i in range(cols + 1):
                xs = i * dx
                nx = (2.0 * xs / w) - 1.0
                x_c = nx * aspect * f
                z_c = 1.0
                
                x1 = x_c
                y1 = y_c * cos_p + z_c * sin_p
                z1 = -y_c * sin_p + z_c * cos_p
                
                x2 = x1 * cos_y + z1 * sin_y
                y2 = y1
                z2 = -x1 * sin_y + z1 * cos_y
                
                r = math.sqrt(x2 * x2 + y2 * y2 + z2 * z2)
                if r < 1e-6:
                    r = 1e-6
                lat = math.asin(max(-0.9999, min(0.9999, y2 / r)))
                lon = math.atan2(x2, z2)
                
                row_coords.append((xs, ys, lon, lat))
            grid_coords.append(row_coords)

        img_rect = self.tiled_image.rect()
        painter.setPen(Qt.PenStyle.NoPen)

        for j in range(rows):
            for i in range(cols):
                v0 = grid_coords[j][i]
                v1 = grid_coords[j][i+1]
                v2 = grid_coords[j+1][i+1]
                v3 = grid_coords[j+1][i]
                
                xs0, ys0, lon0, lat0 = v0
                xs1, ys1, lon1, lat1 = v1
                xs2, ys2, lon2, lat2 = v2
                xs3, ys3, lon3, lat3 = v3
                
                lons = [lon0, lon1, lon2, lon3]
                ref_lon = lon0
                unwrapped_lons = []
                for l in lons:
                    while l - ref_lon > math.pi:
                        l -= 2.0 * math.pi
                    while l - ref_lon < -math.pi:
                        l += 2.0 * math.pi
                    unwrapped_lons.append(l)
                    
                l0, l1, l2, l3 = unwrapped_lons
                
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
                if src_rect.isEmpty() or src_rect.width() < 1 or src_rect.height() < 1:
                    continue

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
            
            h = max(1.0, float(self.height()))
            fov_deg = 80.0 / self.zoom_factor
            deg_per_px = fov_deg / h
            
            self.yaw_deg = (self.drag_start_yaw - delta.x() * deg_per_px) % 360.0
            self.pitch_deg = max(-88.5, min(88.5, self.drag_start_pitch + delta.y() * deg_per_px))
            self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_factor = min(5.0, self.zoom_factor * 1.15)
        else:
            self.zoom_factor = max(0.5, self.zoom_factor / 1.15)
        self.update()
        event.accept()


class Panorama360ViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("360° Viewer")
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
        if not self.text() or self._cached_path.isEmpty():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.strokePath(self._cached_path, self.pen())
        painter.fillPath(self._cached_path, self.brush())


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


class IconGridComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            QApplication.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)
        except Exception:
            pass
        
        self._list_view = QListView(self)
        self._list_view.setViewMode(QListView.ViewMode.IconMode)
        self._list_view.setMovement(QListView.Movement.Static)
        self._list_view.setResizeMode(QListView.ResizeMode.Fixed)
        self._list_view.setSpacing(0)
        self._list_view.setContentsMargins(0, 0, 0, 0)
        self._list_view.setViewportMargins(0, 0, 0, 0)
        
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
        self._list_view.setWordWrap(True)
        self._list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setView(self._list_view)
        
        font_px = max(9, int(11 * dpi_scale))
        self.setStyleSheet(f"""
            QComboBox {{ combobox-popup: 0; }}
            QComboBox QAbstractItemView {{
                border: 1px solid #a0a0a0; background-color: #ffffff;
                selection-background-color: #cce8ff; selection-color: #000000;
                padding: 0px; margin: 0px; outline: 0; font-size: {font_px}px;
            }}
            QComboBox QAbstractItemView::item {{ padding: 0px; margin: 0px; }}
            QScrollBar:vertical {{ width: {self._scrollbar_w}px; background: #f0f0f0; }}
            QScrollBar::handle:vertical {{ background: #cdcdcd; min-height: 20px; border-radius: 3px; }}
            QScrollBar::handle:vertical:hover {{ background: #a6a6a6; }}
        """)

    def showPopup(self):
        combo_bot_left = self.mapToGlobal(QPoint(0, self.height()))
        win = self.window()
        if win:
            win_bot_y = win.mapToGlobal(QPoint(0, win.height())).y() - 8
            win_right_x = win.mapToGlobal(QPoint(win.width(), 0)).x() - 8
            win_left_x = win.mapToGlobal(QPoint(0, 0)).x() + 8
        else:
            screen_geo = QApplication.primaryScreen().availableGeometry()
            win_bot_y = screen_geo.bottom() - 8
            win_right_x = screen_geo.right() - 8
            win_left_x = screen_geo.left() + 8

        avail_h = win_bot_y - combo_bot_left.y()
        min_h = int(self._grid_h * 1.5)
        max_h = int(self._grid_h * 3.5)
        target_h = max(min_h, min(max_h, avail_h))
        self._list_view.setFixedHeight(target_h)
        super().showPopup()
        
        popup = self.view().window()
        popup_w = self._exact_w
        x = combo_bot_left.x()
        if x + popup_w > win_right_x:
            x = win_right_x - popup_w
        if x < win_left_x:
            x = win_left_x
        y = combo_bot_left.y()
        popup.setGeometry(x, y, popup_w, target_h + 2)
        popup.raise_()


class CoverSelectDialog(QDialog):
    def __init__(self, selected_covers, selected_covers_360, lang='de', parent=None):
        super().__init__(parent)
        self.lang = lang
        t = TRANSLATIONS[self.lang]
        self.setWindowTitle(t['select_images_title'])
        self.resize(580, 480)
        
        self.selected_covers = list(selected_covers)
        self.selected_covers_360 = list(selected_covers_360)
        
        layout = QVBoxLayout(self)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(t['search_placeholder'])
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_edit)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([t['col_image'], t['col_normal'], t['col_360']])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 80)
        
        cover_dir = get_cover_dir()
        valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        files = [f for f in os.listdir(cover_dir) if f.lower().endswith(valid_exts)]
        files.sort()
        
        self.row_data = []
        
        if not files:
            lbl_empty = QLabel(t['no_covers_found'])
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_empty)
        else:
            self.table.setRowCount(len(files))
            for row, fname in enumerate(files):
                fpath = os.path.join(cover_dir, fname)
                
                item_fname = QTableWidgetItem(fname)
                pix = QPixmap(fpath)
                if not pix.isNull():
                    item_fname.setIcon(QIcon(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
                
                chk_normal = QCheckBox()
                chk_360 = QCheckBox()
                
                chk_normal.setChecked(fname in self.selected_covers)
                chk_360.setChecked(fname in self.selected_covers_360)
                
                def make_exclusive_toggle(c_norm=chk_normal, c_360=chk_360):
                    c_norm.stateChanged.connect(lambda state: c_360.setChecked(False) if state == Qt.CheckState.Checked.value else None)
                    c_360.stateChanged.connect(lambda state: c_norm.setChecked(False) if state == Qt.CheckState.Checked.value else None)
                
                make_exclusive_toggle()
                
                w_norm = QWidget()
                l_norm = QHBoxLayout(w_norm)
                l_norm.setAlignment(Qt.AlignmentFlag.AlignCenter)
                l_norm.setContentsMargins(0, 0, 0, 0)
                l_norm.addWidget(chk_normal)
                
                w_360 = QWidget()
                l_360 = QHBoxLayout(w_360)
                l_360.setAlignment(Qt.AlignmentFlag.AlignCenter)
                l_360.setContentsMargins(0, 0, 0, 0)
                l_360.addWidget(chk_360)
                
                self.table.setItem(row, 0, item_fname)
                self.table.setCellWidget(row, 1, w_norm)
                self.table.setCellWidget(row, 2, w_360)
                
                self.row_data.append((row, fname, fname.lower(), chk_normal, chk_360))
                
            layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton(t['confirm'])
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def filter_items(self, text):
        query = text.lower().strip()
        for row, fname, fname_lower, chk_normal, chk_360 in self.row_data:
            self.table.setRowHidden(row, query not in fname_lower)

    def get_selected_covers(self):
        norm_list = []
        c360_list = []
        for row, fname, fname_lower, chk_normal, chk_360 in self.row_data:
            if chk_normal.isChecked():
                norm_list.append(fname)
            elif chk_360.isChecked():
                c360_list.append(fname)
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
        self.search_edit.setClearButtonEnabled(True)
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
                disp_name = g.display_name or g.name
                markers.append((disp_name, m_id, g))
                
        markers.sort(key=lambda x: x[0].lower())
        
        if not markers:
            lbl_empty = QLabel(t['no_markers_found'])
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_empty)
        else:
            for disp_name, m_id, g in markers:
                lvl_str = f" (Level {g.level})" if getattr(g, 'level', 0) != 0 else ""
                full_label = f"{disp_name}{lvl_str}"
                
                item = QListWidgetItem(full_label)
                item.setData(Qt.ItemDataRole.UserRole, m_id)
                
                pix = g.pixmap()
                if pix and not pix.isNull():
                    item.setIcon(QIcon(pix))
                
                if m_id == current_selected_id:
                    item.setSelected(True)
                    
                self.list_widget.addItem(item)
                self.marker_items_data.append((item, m_id, full_label.lower()))
            layout.addWidget(self.list_widget)

        btn_box = QHBoxLayout()
        btn_map = QPushButton(t['pick_on_map'])
        btn_map.clicked.connect(self.on_pick_on_map)
        btn_box.addWidget(btn_map)
        
        btn_box.addStretch()
        btn_ok = QPushButton(t['confirm'])
        btn_ok.clicked.connect(self.on_confirm)
        btn_box.addWidget(btn_ok)
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
            if self.point_type == 'p1':
                self.setBrush(QColor(46, 204, 113))
            elif self.point_type == 'p2':
                self.setBrush(QColor(52, 152, 219))
            else:
                self.setBrush(QColor(241, 196, 15))
        else:
            self.setBrush(QColor(255, 0, 0) if self.point_type != 'ctrl' else QColor(0, 120, 255))
        self.setPen(QPen(Qt.GlobalColor.black, 1))

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
    def __init__(self, id_str, p1, p2, ctrl=None, is_ramp=False):
        super().__init__()
        self.id_str = id_str
        self.p1 = p1
        self.p2 = p2
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
        self.modes = ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"]
        
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
        if getattr(self, 'is_ramp', False):
            pen1 = QPen(QColor(46, 204, 113), 2, Qt.PenStyle.SolidLine)
            pen2 = QPen(QColor(52, 152, 219), 2, Qt.PenStyle.SolidLine)
        else:
            pen1 = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
            pen2 = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
            
        self.circle1.setPen(pen1)
        self.circle2.setPen(pen2)
        self.circle1.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.circle2.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        self.handle_p1.update_handle_color()
        self.handle_p2.update_handle_color()
        self.handle_ctrl.update_handle_color()

    def update_node_radius(self, r):
        self.node_radius = r
        r_neg = -r
        d = r * 2
        self.circle1.setRect(r_neg, r_neg, d, d)
        self.circle2.setRect(r_neg, r_neg, d, d)

    def update_scale_size(self, view_scale):
        effective_size = max(3.0, self.max_font_size / max(1.0, view_scale))
        self.text_item.set_font_size(effective_size)
        self.update_path(from_handle=True)

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
        
        is_ramp = getattr(self, 'is_ramp', False)
        if sel:
            color = QColor(155, 89, 182) if is_ramp else QColor(0, 120, 255)
            self.setPen(QPen(color, 4))
        else:
            color = QColor(100, 50, 150) if is_ramp else QColor(50, 50, 50)
            self.setPen(QPen(color, 3, Qt.PenStyle.DashDotLine if is_ramp else Qt.PenStyle.SolidLine))

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
        effective_font_size = max(3.0, self.max_font_size / max(1.0, view_scale))
        self.text_item.set_font_size(effective_font_size)

        if self.base_pixmap and not self.base_pixmap.isNull():
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
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        
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
                if isinstance(curr, MapMarkerItem):
                    marker = curr
                    break
                curr = curr.parentItem()
            if marker:
                break

        if self.main_win.picking_target_marker:
            if marker:
                self.main_win.on_marker_picked(marker)
                event.accept()
                return

        if not self.main_win.is_edit_mode and event.button() == Qt.MouseButton.LeftButton:
            if marker:
                self.main_win.open_cover_panel(marker)
                event.accept()
                return
            else:
                self.main_win.close_cover_panel()

        if self.main_win.is_edit_mode:
            tool = self.main_win.current_tool
            if tool in ["line", "ramp"]:
                if event.button() == Qt.MouseButton.LeftButton:
                    if not self.drawing_line:
                        self.drawing_line = True
                        self.line_start_pt = scene_pos
                        self.temp_path_item = QGraphicsPathItem()
                        color = Qt.GlobalColor.magenta if tool == "ramp" else Qt.GlobalColor.red
                        self.temp_path_item.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
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
        self.ramp_counter = 1
        self.marker_counter = 1
        self.folder_counter = 1
        
        self.init_ui()

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
        
        self.view_overlay_btn = QPushButton("✏️ Mode", self.view)
        self.view_overlay_btn.setFixedSize(120, 32)
        self.view_overlay_btn.move(10, 10)
        self.view_overlay_btn.clicked.connect(self.toggle_mode)
        
        self.view.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.apply_translations()

    def setup_cover_panel(self):
        lay = QVBoxLayout(self.cover_panel)
        lay.setContentsMargins(4, 4, 4, 4)
        
        header = QHBoxLayout()
        self.lbl_cover_title = QLabel("Marker Covers")
        self.lbl_cover_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        btn_close = QPushButton("❌")
        btn_close.setFixedWidth(30)
        btn_close.clicked.connect(self.close_cover_panel)
        
        header.addWidget(self.lbl_cover_title)
        header.addStretch()
        header.addWidget(btn_close)
        lay.addLayout(header)

        self.btn_toggle_desc = QPushButton()
        self.btn_toggle_desc.setStyleSheet("""
            QPushButton {
                text-align: left;
                font-weight: bold;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #dee2e6; }
        """)
        
        self.lbl_desc_content = QLabel()
        self.lbl_desc_content.setWordWrap(True)
        self.lbl_desc_content.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
                color: #333333;
                font-size: 11px;
            }
        """)
        
        def toggle_description():
            is_visible = self.lbl_desc_content.isVisible()
            self.lbl_desc_content.setVisible(not is_visible)
            prefix = "▶ " if is_visible else "▼ "
            self.btn_toggle_desc.setText(prefix + self.tr('description'))

        self.btn_toggle_desc.clicked.connect(toggle_description)
        
        lay.addWidget(self.btn_toggle_desc)
        lay.addWidget(self.lbl_desc_content)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        lay.addWidget(sep)
        
        self.cover_tab_widget = QTabWidget()
        
        self.tab_normal_scroll = QScrollArea()
        self.tab_normal_scroll.setWidgetResizable(True)
        self.tab_normal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.container_normal = QWidget()
        self.layout_normal = QVBoxLayout(self.container_normal)
        self.layout_normal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tab_normal_scroll.setWidget(self.container_normal)
        
        self.tab_360_scroll = QScrollArea()
        self.tab_360_scroll.setWidgetResizable(True)
        self.tab_360_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.container_360 = QWidget()
        self.layout_360 = QVBoxLayout(self.container_360)
        self.layout_360.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tab_360_scroll.setWidget(self.container_360)
        
        self.cover_tab_widget.addTab(self.tab_normal_scroll, self.tr('tab_normal'))
        self.cover_tab_widget.addTab(self.tab_360_scroll, self.tr('tab_360'))
        
        lay.addWidget(self.cover_tab_widget)

    def open_cover_panel(self, marker_item):
        t = TRANSLATIONS[self.current_lang]
        self.lbl_cover_title.setText(marker_item.display_name or marker_item.name)
        
        desc_text = getattr(marker_item, 'description', '').strip()
        self.btn_toggle_desc.setText("▼ " + t['description'])
        self.lbl_desc_content.setText(desc_text if desc_text else t['no_description'])
        self.lbl_desc_content.setVisible(True)
        
        for layout in (self.layout_normal, self.layout_360):
            while layout.count() > 0:
                child = layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
                    
        cover_dir = get_cover_dir()
        
        covers = getattr(marker_item, 'covers', [])
        valid_covers = [os.path.join(cover_dir, c) for c in covers if os.path.exists(os.path.join(cover_dir, c))]
        
        if not valid_covers:
            lbl_info = QLabel(t['no_covers_selected'])
            lbl_info.setWordWrap(True)
            lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_normal.addWidget(lbl_info)
        else:
            for fpath in valid_covers:
                pix = QPixmap(fpath)
                if not pix.isNull():
                    lbl_img = ClickableLabel(fpath, self.open_full_image_viewer)
                    lbl_img.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
                    scaled_pix = pix.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
                    lbl_img.setPixmap(scaled_pix)
                    lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.layout_normal.addWidget(lbl_img)
                    
        covers_360 = getattr(marker_item, 'covers_360', [])
        valid_covers_360 = [os.path.join(cover_dir, c) for c in covers_360 if os.path.exists(os.path.join(cover_dir, c))]
        
        if not valid_covers_360:
            lbl_info_360 = QLabel(t['no_covers_360_selected'])
            lbl_info_360.setWordWrap(True)
            lbl_info_360.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_360.addWidget(lbl_info_360)
        else:
            for fpath in valid_covers_360:
                pix = QPixmap(fpath)
                if not pix.isNull():
                    lbl_img = ClickableLabel(fpath, self.open_360_image_viewer)
                    lbl_img.setStyleSheet("border: 2px solid #3498db; border-radius: 4px;")
                    scaled_pix = pix.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
                    lbl_img.setPixmap(scaled_pix)
                    lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.layout_360.addWidget(lbl_img)
                    
        self.cover_panel.setVisible(True)

    def open_full_image_viewer(self, image_path):
        dlg = ZoomableImageViewerDialog(image_path, parent=self)
        dlg.exec()

    def open_360_image_viewer(self, image_path):
        dlg = Panorama360ViewerDialog(image_path, parent=self)
        dlg.exec()

    def close_cover_panel(self):
        self.cover_panel.setVisible(False)

    def setup_edit_panel(self):
        layout = QHBoxLayout(self.edit_panel)
        layout.setContentsMargins(4, 4, 4, 4)
        
        left_toolbar = QVBoxLayout()
        self.btn_select = QPushButton()
        self.btn_line = QPushButton()
        self.btn_ramp = QPushButton()
        self.btn_marker = QPushButton()
        
        self.btn_select.setIcon(self.get_app_icon("select.png"))
        self.btn_select.setIconSize(QSize(24, 24))
        self.btn_line.setIcon(self.get_app_icon("line.png"))
        self.btn_line.setIconSize(QSize(24, 24))
        self.btn_ramp.setIcon(self.get_app_icon("ramp.png"))
        self.btn_ramp.setIconSize(QSize(24, 24))
        self.btn_marker.setIcon(self.get_app_icon("marker.png"))
        self.btn_marker.setIconSize(QSize(24, 24))
        
        self.btn_select.setCheckable(True)
        self.btn_line.setCheckable(True)
        self.btn_ramp.setCheckable(True)
        self.btn_marker.setCheckable(True)
        self.btn_select.setChecked(True)
        
        self.btn_select.clicked.connect(lambda: self.set_tool("select"))
        self.btn_line.clicked.connect(lambda: self.set_tool("line"))
        self.btn_ramp.clicked.connect(lambda: self.set_tool("ramp"))
        self.btn_marker.clicked.connect(lambda: self.set_tool("marker"))
        
        left_toolbar.addWidget(self.btn_select)
        left_toolbar.addWidget(self.btn_line)
        left_toolbar.addWidget(self.btn_ramp)
        left_toolbar.addWidget(self.btn_marker)
        left_toolbar.addStretch()
        
        right_side = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        top_box = QWidget()
        top_lay = QVBoxLayout(top_box)
        top_lay.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        self.lbl_explorer = QLabel()
        self.btn_add_folder = QPushButton()
        self.btn_add_folder.setIcon(self.get_app_icon("folder.png"))
        self.btn_add_folder.setIconSize(QSize(18, 18))
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
        
        if not self.btn_start_marker.property("marker_id"):
            self.btn_start_marker.setText(t['select_target'])
            
        self.btn_add_waypoint.setText(t['add_stop'])
        self.btn_calc_route.setText(t['calculate_route'])
        self.btn_clear_route.setText(t['clear_route'])
        
        self.cover_tab_widget.setTabText(0, t['tab_normal'])
        self.cover_tab_widget.setTabText(1, t['tab_360'])

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
                if child and child.widget():
                    child.widget().deleteLater()

    def toggle_mode(self):
        self.clear_route_all()
        self.close_cover_panel()
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
        self.btn_ramp.setChecked(tool_name == "ramp")
        self.btn_marker.setChecked(tool_name == "marker")

    def create_new_line(self, p1, p2, is_ramp=False):
        prefix = "ramp" if is_ramp else "line"
        item_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        
        if is_ramp:
            disp_name = f"Ramp_{self.ramp_counter}"
            self.ramp_counter += 1
            icon_file = "ramp.png"
        else:
            disp_name = f"Line_{self.line_counter}"
            self.line_counter += 1
            icon_file = "line.png"
        
        line_item = CurveLineItem(item_id, p1, p2, is_ramp=is_ramp)
        line_item.name = disp_name
        line_item.set_edit_mode(True)
        self.view.scene.addItem(line_item)
        line_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, disp_name)
            tree_item.setIcon(0, self.get_app_icon(icon_file))
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
        
        marker_item = MapMarkerItem(item_id, pos, "icons/marker/default.png")
        marker_item.name = disp_name
        marker_item.display_name = disp_name
        marker_item.set_edit_mode(True)
        self.view.scene.addItem(marker_item)
        marker_item.setSelected(True)
        
        with QSignalBlocker(self.tree):
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
            tree_item.setText(0, disp_name)
            tree_item.setIcon(0, self.get_app_icon("marker.png"))
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
            tree_item = QTreeWidgetItem()
            tree_item.setText(0, disp_name)
            tree_item.setIcon(0, self.get_app_icon("folder.png"))
            tree_item.setFlags(
                tree_item.flags() | 
                Qt.ItemFlag.ItemIsEditable | 
                Qt.ItemFlag.ItemIsDragEnabled | 
                Qt.ItemFlag.ItemIsDropEnabled
            )
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self.tree.addTopLevelItem(tree_item)
            
        self.items_dict[item_id] = {'graphics': None, 'tree': tree_item, 'type': 'folder'}

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
            is_ramp = getattr(gitem, 'is_ramp', False)
            row_count = 8 if is_ramp else 7
            self.prop_table.setRowCount(row_count)
            
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name)
            le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)
            
            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name)
            le_dname.textChanged.connect(lambda txt: gitem.update_text_display(txt))
            self.prop_table.setCellWidget(1, 1, le_dname)
            
            self.prop_table.setItem(2, 0, QTableWidgetItem(t['font_size']))
            le_fsize = QLineEdit(str(gitem.max_font_size))
            le_fsize.textChanged.connect(lambda txt: self.set_item_font_size(gitem, txt))
            self.prop_table.setCellWidget(2, 1, le_fsize)

            self.prop_table.setItem(3, 0, QTableWidgetItem(t['length']))
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
            self.prop_table.setCellWidget(3, 1, w_len)
            
            self.prop_table.setItem(4, 0, QTableWidgetItem(t['node_radius']))
            le_radius = QLineEdit(str(gitem.node_radius))
            le_radius.textChanged.connect(lambda txt: self.set_line_node_radius(gitem, txt))
            self.prop_table.setCellWidget(4, 1, le_radius)

            if is_ramp:
                self.prop_table.setItem(5, 0, QTableWidgetItem(t['start_level']))
                le_slevel = QLineEdit(str(getattr(gitem, 'start_level', 0)))
                le_slevel.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, level_attr='start_level'))
                self.prop_table.setCellWidget(5, 1, le_slevel)

                self.prop_table.setItem(6, 0, QTableWidgetItem(t['end_level']))
                le_elevel = QLineEdit(str(getattr(gitem, 'end_level', 0)))
                le_elevel.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, level_attr='end_level'))
                self.prop_table.setCellWidget(6, 1, le_elevel)
                
                modes_row = 7
            else:
                self.prop_table.setItem(5, 0, QTableWidgetItem(t['level']))
                le_level = QLineEdit(str(getattr(gitem, 'level', 0)))
                le_level.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, level_attr='level'))
                self.prop_table.setCellWidget(5, 1, le_level)
                
                modes_row = 6

            self.prop_table.setItem(modes_row, 0, QTableWidgetItem(t['modes']))
            chk_combo = CheckableComboBox()
            available_modes = ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"]
            current_modes = getattr(gitem, 'modes', available_modes)
            for m in available_modes:
                chk_combo.add_checkable_item(m, m in current_modes)
            
            chk_combo._changed_callback = lambda combo=chk_combo, target=gitem: setattr(target, 'modes', combo.get_checked_items())
            self.prop_table.setCellWidget(modes_row, 1, chk_combo)

        elif data['type'] == 'marker':
            self.prop_table.setRowCount(7)
            
            self.prop_table.setItem(0, 0, QTableWidgetItem(t['name']))
            le_name = QLineEdit(gitem.name)
            le_name.textChanged.connect(lambda txt: self.update_item_name(id_str, txt))
            self.prop_table.setCellWidget(0, 1, le_name)
            
            self.prop_table.setItem(1, 0, QTableWidgetItem(t['display_name']))
            le_dname = QLineEdit(gitem.display_name)
            le_dname.textChanged.connect(lambda txt: (setattr(gitem, 'display_name', txt), gitem.update_text_position()))
            self.prop_table.setCellWidget(1, 1, le_dname)
            
            self.prop_table.setItem(2, 0, QTableWidgetItem(t['font_size']))
            le_fsize = QLineEdit(str(gitem.max_font_size))
            le_fsize.textChanged.connect(lambda txt: self.set_item_font_size(gitem, txt))
            self.prop_table.setCellWidget(2, 1, le_fsize)

            self.prop_table.setItem(3, 0, QTableWidgetItem(t['level']))
            le_level = QLineEdit(str(getattr(gitem, 'level', 0)))
            le_level.textChanged.connect(lambda txt: self.set_item_level(gitem, txt, level_attr='level'))
            self.prop_table.setCellWidget(3, 1, le_level)

            self.prop_table.setItem(4, 0, QTableWidgetItem(t['icon']))
            cmb_icon = IconGridComboBox()
            
            marker_icons_dir = os.path.join(os.path.dirname(__file__), "icons", "marker")
            icon_files = []
            if os.path.exists(marker_icons_dir):
                icon_files = [os.path.join("icons", "marker", f) for f in os.listdir(marker_icons_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.svg'))]
            
            icon_files.sort(key=lambda x: os.path.basename(x).lower())
            
            current_idx = 0
            for idx, path in enumerate(icon_files):
                full_p = os.path.normpath(os.path.join(os.path.dirname(__file__), path))
                icon = QIcon(full_p) if os.path.exists(full_p) else QIcon()
                icon_name = os.path.splitext(os.path.basename(path))[0]
                cmb_icon.addItem(icon, icon_name, path)
                
                if os.path.normpath(path) == os.path.normpath(gitem.icon_rel_path):
                    current_idx = idx

            cmb_icon.setCurrentIndex(current_idx)
            cmb_icon.currentIndexChanged.connect(lambda idx: gitem.load_icon_image(cmb_icon.itemData(idx)))
            self.prop_table.setCellWidget(4, 1, cmb_icon)

            self.prop_table.setItem(5, 0, QTableWidgetItem(t['covers']))
            btn_covers = QPushButton()
            
            def update_btn_text():
                total_cnt = len(gitem.covers) + len(gitem.covers_360)
                btn_covers.setText(t['covers_selected_count'].format(count=total_cnt) if total_cnt > 0 else t['select_covers'])
                
            update_btn_text()
            
            def open_cover_dialog():
                dlg = CoverSelectDialog(gitem.covers, gitem.covers_360, lang=self.current_lang, parent=self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    norm_list, c360_list = dlg.get_selected_covers()
                    gitem.covers = norm_list
                    gitem.covers_360 = c360_list
                    update_btn_text()
                    
            btn_covers.clicked.connect(open_cover_dialog)
            self.prop_table.setCellWidget(5, 1, btn_covers)

            self.prop_table.setItem(6, 0, QTableWidgetItem(t['description']))
            te_desc = QTextEdit()
            te_desc.setPlainText(getattr(gitem, 'description', ''))
            te_desc.setFixedHeight(75)
            te_desc.textChanged.connect(lambda: setattr(gitem, 'description', te_desc.toPlainText()))
            self.prop_table.setCellWidget(6, 1, te_desc)

    def set_item_font_size(self, gitem, txt):
        try:
            val = float(txt)
            if val > 0:
                gitem.max_font_size = val
                scale_factor = self.view.transform().m11()
                gitem.update_scale_size(scale_factor)
        except ValueError:
            pass

    def set_item_level(self, gitem, txt, level_attr='level'):
        try:
            val = int(txt)
            setattr(gitem, level_attr, val)
        except ValueError:
            pass

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
            if isinstance(item, (MapMarkerItem, CurveLineItem)):
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
                line_entry = {
                    'id': id_str,
                    'name': g.name,
                    'display_name': g.display_name,
                    'font_size': round(g.max_font_size, 1),
                    'p1': [round(g.p1.x(), 2), round(g.p1.y(), 2)],
                    'p2': [round(g.p2.x(), 2), round(g.p2.y(), 2)],
                    'ctrl': [round(g.ctrl.x(), 2), round(g.ctrl.y(), 2)],
                    'length_val': round(g.length_val, 2),
                    'length_unit': g.length_unit,
                    'node_radius': round(g.node_radius, 1),
                    'modes': g.modes,
                    'parent': parent_id
                }
                if getattr(g, 'is_ramp', False):
                    line_entry['is_ramp'] = True
                    line_entry['start_level'] = getattr(g, 'start_level', 0)
                    line_entry['end_level'] = getattr(g, 'end_level', 0)
                else:
                    if getattr(g, 'level', 0) != 0:
                        line_entry['level'] = getattr(g, 'level', 0)
                lines_data.append(line_entry)

            elif item_type == 'marker' and g:
                marker_entry = {
                    'id': id_str,
                    'name': g.name,
                    'display_name': g.display_name,
                    'font_size': round(g.max_font_size, 1),
                    'level': getattr(g, 'level', 0),
                    'pos': [round(g.pos().x(), 2), round(g.pos().y(), 2)],
                    'icon': g.icon_rel_path,
                    'parent': parent_id
                }
                if getattr(g, 'covers', None):
                    marker_entry['covers'] = g.covers
                if getattr(g, 'covers_360', None):
                    marker_entry['covers_360'] = g.covers_360
                if getattr(g, 'description', ''):
                    marker_entry['description'] = g.description
                markers_data.append(marker_entry)

            for child_idx in range(tree_item.childCount()):
                process_tree_item(tree_item.child(child_idx), parent_id=id_str)

        for top_idx in range(self.tree.topLevelItemCount()):
            process_tree_item(self.tree.topLevelItem(top_idx), parent_id=None)

        out = {
            'image': self.current_image_filename,
            'folders': folders_data,
            'lines': lines_data,
            'markers': markers_data
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

    def load_json_dialog(self):
        maps_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "maps")).replace("\\", "/")
        os.makedirs(maps_folder, exist_ok=True)

        path, _ = QFileDialog.getOpenFileName(self, "Öffnen", maps_folder, "JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return

        if not isinstance(data, dict):
            return
            
        self.clear_all_data()
        
        img_name = safe_str(data.get('image'), '')
        self.current_image_filename = img_name
        if img_name:
            img_path = os.path.join(maps_folder, img_name)
            if os.path.exists(img_path):
                self.view.set_background_image(img_path)

        created_tree_items = {}

        folders_list = data.get('folders', [])
        if isinstance(folders_list, list):
            for f in folders_list:
                if not isinstance(f, dict):
                    continue
                f_id = safe_str(f.get('id')) or f"folder_{uuid.uuid4().hex[:8]}"
                f['id'] = f_id
                
                tree_item = QTreeWidgetItem()
                tree_item.setText(0, safe_str(f.get('name'), 'Ordner'))
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

        lines_list = data.get('lines', [])
        if isinstance(lines_list, list):
            for l in lines_list:
                if not isinstance(l, dict):
                    continue
                l_id = safe_str(l.get('id')) or f"line_{uuid.uuid4().hex[:8]}"
                l['id'] = l_id

                p1 = safe_point(l.get('p1'), 0, 0)
                p2 = safe_point(l.get('p2'), 100, 100)
                ctrl_raw = l.get('ctrl')
                ctrl = safe_point(ctrl_raw, (p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2) if ctrl_raw is not None else QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                
                is_ramp = safe_bool(l.get('is_ramp'), False)
                
                line_item = CurveLineItem(l_id, p1, p2, ctrl, is_ramp=is_ramp)
                line_item.name = safe_str(l.get('name'), 'Ramp' if is_ramp else 'Line')
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
                if isinstance(modes_raw, list):
                    line_item.modes = [safe_str(m) for m in modes_raw]
                else:
                    line_item.modes = ["Auto", "Fuß", "ÖPNV", "Fahrrad", "Flugzeug"]
                
                line_item.set_edit_mode(self.is_edit_mode)
                self.view.scene.addItem(line_item)
                
                icon_file = "ramp.png" if is_ramp else "line.png"
                tree_item = QTreeWidgetItem()
                tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
                tree_item.setText(0, line_item.name)
                tree_item.setIcon(0, self.get_app_icon(icon_file))
                tree_item.setData(0, Qt.ItemDataRole.UserRole, l_id)
                
                created_tree_items[l_id] = tree_item
                self.items_dict[l_id] = {'graphics': line_item, 'tree': tree_item, 'type': 'line'}

        markers_list = data.get('markers', [])
        if isinstance(markers_list, list):
            for m in markers_list:
                if not isinstance(m, dict):
                    continue
                m_id = safe_str(m.get('id')) or f"marker_{uuid.uuid4().hex[:8]}"
                m['id'] = m_id

                pos = safe_point(m.get('pos'), 0, 0)
                icon_path = safe_str(m.get('icon'), '')
                
                marker_item = MapMarkerItem(m_id, pos, icon_path)
                marker_item.name = safe_str(m.get('name'), 'Marker')
                marker_item.max_font_size = safe_float(m.get('font_size'), 12.0)
                marker_item.level = safe_int(m.get('level'), 0)
                marker_item.display_name = safe_str(m.get('display_name'), marker_item.name)
                marker_item.description = safe_str(m.get('description'), '')
                
                covers_raw = m.get('covers', [])
                if isinstance(covers_raw, list):
                    marker_item.covers = [safe_str(c) for c in covers_raw]
                    
                covers_360_raw = m.get('covers_360', [])
                if isinstance(covers_360_raw, list):
                    marker_item.covers_360 = [safe_str(c) for c in covers_360_raw]
                
                marker_item.set_edit_mode(self.is_edit_mode)
                self.view.scene.addItem(marker_item)
                
                tree_item = QTreeWidgetItem()
                tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled)
                tree_item.setText(0, marker_item.name)
                tree_item.setIcon(0, self.get_app_icon("marker.png"))
                tree_item.setData(0, Qt.ItemDataRole.UserRole, m_id)
                
                created_tree_items[m_id] = tree_item
                self.items_dict[m_id] = {'graphics': marker_item, 'tree': tree_item, 'type': 'marker'}

        all_elements = []
        for key in ['folders', 'lines', 'markers']:
            lst = data.get(key, [])
            if isinstance(lst, list):
                all_elements.extend([item for item in lst if isinstance(item, dict)])

        for elem in all_elements:
            e_id = elem.get('id')
            if not e_id or e_id not in created_tree_items:
                continue
            t_item = created_tree_items[e_id]

            if t_item.treeWidget() is None and t_item.parent() is None:
                parent_id = elem.get('parent')
                if parent_id and parent_id in created_tree_items and parent_id != e_id:
                    parent_tree_item = created_tree_items[parent_id]
                    parent_tree_item.addChild(t_item)
                else:
                    self.tree.addTopLevelItem(t_item)

        for item_id, t_item in created_tree_items.items():
            if t_item.treeWidget() is None and t_item.parent() is None:
                self.tree.addTopLevelItem(t_item)
            
        self.populate_marker_combos()
        self.update_zoom_scales()

    def populate_marker_combos(self):
        start_id = self.btn_start_marker.property("marker_id")
        if start_id and start_id in self.items_dict:
            g = self.items_dict[start_id]['graphics']
            if g:
                self.btn_start_marker.setText(g.display_name or g.name)
            else:
                self.reset_start_marker_btn()
        else:
            self.reset_start_marker_btn()

    def reset_start_marker_btn(self):
        self.btn_start_marker.setText(self.tr('select_target'))
        self.btn_start_marker.setProperty("marker_id", None)

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
            except RuntimeError:
                pass
        self.picking_target_marker = False
        self.active_waypoint_btn = None

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
        
        start_level = getattr(start_m, 'level', 0)
        end_level = getattr(end_m, 'level', 0)
        
        all_lines = [d['graphics'] for d in self.items_dict.values() if d['type'] == 'line' and d['graphics']]
        if not all_lines:
            direct_p = QPainterPath()
            direct_p.moveTo(start_m.pos())
            direct_p.lineTo(end_m.pos())
            d_len = QLineF(start_m.pos(), end_m.pos()).length()
            return [(direct_p, "Anschluss_Fuß")], d_len

        endpoints = []
        for line_idx, line in enumerate(all_lines):
            l1 = getattr(line, 'start_level', 0) if getattr(line, 'is_ramp', False) else getattr(line, 'level', 0)
            l2 = getattr(line, 'end_level', 0) if getattr(line, 'is_ramp', False) else getattr(line, 'level', 0)
            endpoints.append((line_idx, 'p1', line.p1, l1, line))
            endpoints.append((line_idx, 'p2', line.p2, l2, line))

        num_endpoints = len(endpoints)
        parent = list(range(num_endpoints))

        def find(i):
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        grid = {}
        cell_size = 20.0
        
        for i in range(num_endpoints):
            line_i_idx, p_type_i, pos_i, lvl_i, line_i = endpoints[i]
            cell_key = (int(pos_i.x() // cell_size), int(pos_i.y() // cell_size), lvl_i)
            
            cx, cy, cl = cell_key
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor_key = (cx + dx, cy + dy, cl)
                    if neighbor_key in grid:
                        for j in grid[neighbor_key]:
                            line_j_idx, p_type_j, pos_j, lvl_j, line_j = endpoints[j]
                            if line_i_idx == line_j_idx:
                                if QLineF(pos_i, pos_j).length() <= 2.0:
                                    union(i, j)
                            else:
                                dist = QLineF(pos_i, pos_j).length()
                                snap_thresh = max(line_i.node_radius, line_j.node_radius, 12.0)
                                if dist <= snap_thresh:
                                    union(i, j)
                                    
            if cell_key not in grid:
                grid[cell_key] = []
            grid[cell_key].append(i)

        groups = {}
        for i in range(num_endpoints):
            r = find(i)
            if r not in groups:
                groups[r] = []
            groups[r].append(i)

        node_map = {}
        nodes = []
        node_levels = []
        for group_idx, (r, ep_indices) in enumerate(groups.items()):
            for ep_idx in ep_indices:
                node_map[ep_idx] = group_idx
            
            avg_x = sum(endpoints[ep_idx][2].x() for ep_idx in ep_indices) / len(ep_indices)
            avg_y = sum(endpoints[ep_idx][2].y() for ep_idx in ep_indices) / len(ep_indices)
            grp_level = endpoints[ep_indices[0]][3]
            nodes.append(QPointF(avg_x, avg_y))
            node_levels.append(grp_level)

        adj = {}
        for line_idx, line in enumerate(all_lines):
            ep1_idx = line_idx * 2
            ep2_idx = line_idx * 2 + 1
            
            u = node_map[ep1_idx]
            v = node_map[ep2_idx]
            if u == v:
                continue
            
            len_m = line.length_val * UNIT_FACTORS.get(line.length_unit, 1.0)
            line_modes = line.modes if getattr(line, 'modes', None) else []
            
            restricted_modes = {"ÖPNV", "Transit", "Flugzeug", "Airplane"}
            is_exclusively_restricted = len(line_modes) > 0 and all(m in restricted_modes for m in line_modes)

            if primary_mode in ["Fuß", "Walk"]:
                if is_exclusively_restricted:
                    continue
                cost_mult = 1.0 if ("Fuß" in line_modes or "Walk" in line_modes) else 1.5
                used_mode = "Fuß"
            else:
                is_primary = primary_mode in line_modes
                is_foot = "Fuß" in line_modes or "Walk" in line_modes
                if is_primary:
                    cost_mult = 1.0
                    used_mode = primary_mode
                elif is_foot and not is_exclusively_restricted:
                    cost_mult = 2.5
                    used_mode = "Fuß"
                else:
                    continue
            
            cost = len_m * cost_mult
            if u not in adj: adj[u] = []
            if v not in adj: adj[v] = []
            
            adj[u].append((v, cost, len_m, line, used_mode, 'fwd'))
            adj[v].append((u, cost, len_m, line, used_mode, 'rev'))

        if not nodes or not adj:
            direct_p = QPainterPath()
            direct_p.moveTo(start_m.pos())
            direct_p.lineTo(end_m.pos())
            d_len = QLineF(start_m.pos(), end_m.pos()).length()
            return [(direct_p, "Anschluss_Fuß")], d_len

        OFF_STREET_WEIGHT = 100.0

        pq = []
        for n_idx in adj.keys():
            if node_levels[n_idx] == start_level:
                d_start = QLineF(start_m.pos(), nodes[n_idx]).length()
                c_start = d_start * OFF_STREET_WEIGHT
                heapq.heappush(pq, (c_start, n_idx, [], d_start))

        best_total_cost = QLineF(start_m.pos(), end_m.pos()).length() * 10000.0
        best_path = None
        best_real_len = 0.0

        visited = set()

        while pq:
            cost, curr, path, real_len = heapq.heappop(pq)

            if cost >= best_total_cost:
                break

            if curr in visited:
                continue
            visited.add(curr)

            if node_levels[curr] == end_level:
                d_to_end = QLineF(nodes[curr], end_m.pos()).length()
                total_cost = cost + d_to_end * OFF_STREET_WEIGHT
                total_real_len = real_len + d_to_end

                if total_cost < best_total_cost:
                    best_total_cost = total_cost
                    best_path = (path, curr, d_to_end)
                    best_real_len = total_real_len

            for nxt, weight, l_m, line_obj, mode, direction in adj.get(curr, []):
                if nxt not in visited:
                    heapq.heappush(pq, (cost + weight, nxt, path + [(line_obj, mode, direction)], real_len + l_m))

        if best_path is None:
            direct_p = QPainterPath()
            direct_p.moveTo(start_m.pos())
            direct_p.lineTo(end_m.pos())
            d_len = QLineF(start_m.pos(), end_m.pos()).length()
            return [(direct_p, "Anschluss_Fuß")], d_len

        path_lines, last_node_idx, end_gap_dist = best_path

        total_elements = []
        extra_len = 0.0

        if path_lines:
            first_line_obj, first_mode, first_dir = path_lines[0]
            start_node_pt = first_line_obj.p1 if first_dir == 'fwd' else first_line_obj.p2

            dist_start = QLineF(start_m.pos(), start_node_pt).length()
            if dist_start > 2.0:
                p_start = QPainterPath()
                p_start.moveTo(start_m.pos())
                p_start.lineTo(start_node_pt)
                total_elements.append((p_start, "Anschluss_Fuß"))
                extra_len += dist_start

            current_pt = start_node_pt
            for line_obj, mode, direction in path_lines:
                p_geo = QPainterPath()
                if direction == 'fwd':
                    p_geo.moveTo(line_obj.p1)
                    p_geo.quadTo(line_obj.ctrl, line_obj.p2)
                    current_pt = line_obj.p2
                else:
                    p_geo.moveTo(line_obj.p2)
                    p_geo.quadTo(line_obj.ctrl, line_obj.p1)
                    current_pt = line_obj.p1
                total_elements.append((p_geo, mode))

            dist_end = QLineF(current_pt, end_m.pos()).length()
            if dist_end > 2.0:
                p_end = QPainterPath()
                p_end.moveTo(current_pt)
                p_end.lineTo(end_m.pos())
                total_elements.append((p_end, "Anschluss_Fuß"))
                extra_len += dist_end
        else:
            same_node_pt = nodes[last_node_idx]
            dist_start = QLineF(start_m.pos(), same_node_pt).length()
            dist_end = QLineF(same_node_pt, end_m.pos()).length()

            if dist_start > 2.0:
                p_start = QPainterPath()
                p_start.moveTo(start_m.pos())
                p_start.lineTo(same_node_pt)
                total_elements.append((p_start, "Anschluss_Fuß"))
                extra_len += dist_start

            if dist_end > 2.0:
                p_end = QPainterPath()
                p_end.moveTo(same_node_pt)
                p_end.lineTo(end_m.pos())
                total_elements.append((p_end, "Anschluss_Fuß"))
                extra_len += dist_end

        return total_elements, (best_real_len - end_gap_dist + extra_len)

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