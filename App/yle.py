# Kurcxa OS (made by: Giorgi Kurtskhalia)

import sys
import os
import json
import time
import hashlib
import getpass
from functools import partial
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, QSize, QUrl, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPalette, QIcon, QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QTextEdit, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QMessageBox, QFrame, QSizePolicy, QStackedLayout, QProgressBar,
    QSplashScreen, QInputDialog, QMenu, QAction, QDialog, QFormLayout, QComboBox,
    QListView, QToolButton, QGridLayout, QStyle, QSpacerItem
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# ---------------------------
# Utility functions & constants
# ---------------------------

APP_DIR = Path.home() / ".kurcxa_os_v2"
USERS_DIR = APP_DIR / "users"
SETTINGS_FILE = APP_DIR / "settings.json"

for d in (APP_DIR, USERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"theme": "dark", "last_user": None, "pinned_apps": ["Kurcxa Browser", "File Explorer", "Text Editor"]}

def save_settings(s):
    SETTINGS_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")

SETTINGS = load_settings()

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def resource_pixmap(path, fallback_color=None, size=None):
    if path and os.path.exists(path):
        pm = QPixmap(path)
        if size:
            pm = pm.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return pm
    pm = QPixmap(size if size else QSize(800, 600))
    pm.fill(fallback_color if fallback_color else QColor("#0b3d3f"))
    return pm

def ensure_user_dir(username):
    d = USERS_DIR / username
    d.mkdir(parents=True, exist_ok=True)
    return d

# ---------------------------
# Account Manager
# ---------------------------

class AccountManager:
    """
    Lightweight account manager storing users under ~/.kurcxa_os_v2/users/<username>/
    Each user has 'credentials.json' and 'vfs.json' (virtual filesystem).
    Passwords are stored as SHA256(username + salt + password).
    This is a toy approach for the demo only.
    """
    def __init__(self):
        self.users_index = {}  # username -> info
        self.load_index()

    def load_index(self):
        # index by scanning users dir
        self.users_index = {}
        for p in USERS_DIR.iterdir():
            if p.is_dir():
                creds = p / "credentials.json"
                if creds.exists():
                    try:
                        data = json.loads(creds.read_text(encoding="utf-8"))
                        self.users_index[p.name] = data
                    except Exception:
                        pass

    def user_exists(self, username):
        return username in self.users_index

    def create_user(self, username, password, display_name=None):
        if not username or self.user_exists(username):
            raise ValueError("invalid or already exists")
        salt = hashlib.sha256(os.urandom(32)).hexdigest()
        pw_hash = sha256_hex(username + salt + password)
        info = {
            "username": username,
            "display_name": display_name or username,
            "salt": salt,
            "pw_hash": pw_hash,
            "created": time.time(),
            "last_login": None
        }
        d = ensure_user_dir(username)
        creds = d / "credentials.json"
        creds.write_text(json.dumps(info, indent=2), encoding="utf-8")
        # initialize vfs
        vfs = {
            "root": {
                "type": "dir",
                "name": "/",
                "children": {
                    "Documents": {"type": "dir", "name": "Documents", "children": {}},
                    "Notes": {"type": "dir", "name": "Notes", "children": {}},
                    "Desktop": {"type": "dir", "name": "Desktop", "children": {}}
                }
            },
            "meta": {"last_modified": time.time()}
        }
        vfile = d / "vfs.json"
        vfile.write_text(json.dumps(vfs, indent=2), encoding="utf-8")
        self.load_index()
        return True

    def verify_login(self, username, password):
        if not self.user_exists(username):
            return False
        info = self.users_index[username]
        salt = info.get("salt", "")
        return info.get("pw_hash") == sha256_hex(username + salt + password)

    def get_user_info(self, username):
        return self.users_index.get(username)

    def set_last_login(self, username):
        if not self.user_exists(username):
            return
        info = self.users_index[username]
        info["last_login"] = time.time()
        creds = ensure_user_dir(username) / "credentials.json"
        creds.write_text(json.dumps(info, indent=2), encoding="utf-8")
        self.load_index()

# ---------------------------
# Virtual File System (per user)
# ---------------------------

class VirtualFileSystem:
    """
    Simple JSON-backed VFS. Supports read/write/create/delete in a tree structure.
    Node structure:
        { "type": "dir"|"file", "name": "...", ["content": "..."], ["children": {name: node}] }
    We provide convenient path helpers with slash-separated paths like "/Notes/note1.txt"
    """
    def __init__(self, username):
        self.username = username
        self.dir = ensure_user_dir(username)
        self.vfs_file = self.dir / "vfs.json"
        self.load()

    def load(self):
        if not self.vfs_file.exists():
            # create default
            default = {
                "root": {"type": "dir", "name": "/", "children": {}},
                "meta": {"last_modified": time.time()}
            }
            self.tree = default
            self.save()
        else:
            try:
                self.tree = json.loads(self.vfs_file.read_text(encoding="utf-8"))
            except Exception:
                # fallback
                self.tree = {"root": {"type": "dir", "name": "/", "children": {}}, "meta": {"last_modified": time.time()}}
                self.save()

    def save(self):
        self.tree["meta"]["last_modified"] = time.time()
        self.vfs_file.write_text(json.dumps(self.tree, indent=2), encoding="utf-8")

    def resolve(self, path: str):
        # Returns node and parent and name for given path; path like "/Notes/note1.txt" or "/"
        path = (path or "/").strip()
        if path == "/":
            return self.tree["root"], None, "/"
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.tree["root"]
        parent = None
        for part in parts:
            parent = node
            children = parent.get("children", {})
            if part not in children:
                return None, parent, part
            node = children[part]
        return node, parent, node.get("name")

    def list_dir(self, path="/"):
        node, _, _ = self.resolve(path)
        if not node or node.get("type") != "dir":
            return []
        return sorted(node.get("children", {}).values(), key=lambda n: (0 if n["type"]=="dir" else 1, n["name"].lower()))

    def make_dir(self, path, name):
        node, _, _ = self.resolve(path)
        if not node or node.get("type") != "dir":
            raise FileNotFoundError("parent not found")
        if name in node.get("children", {}):
            raise FileExistsError("already exists")
        node.setdefault("children", {})[name] = {"type": "dir", "name": name, "children": {}}
        self.save()

    def create_file(self, path, name, content=""):
        node, _, _ = self.resolve(path)
        if not node or node.get("type") != "dir":
            raise FileNotFoundError("parent not found")
        if name in node.get("children", {}):
            raise FileExistsError("already exists")
        node.setdefault("children", {})[name] = {"type": "file", "name": name, "content": content}
        self.save()

    def read_file(self, filepath):
        node, _, _ = self.resolve(filepath)
        if not node or node.get("type") != "file":
            raise FileNotFoundError("not a file")
        return node.get("content", "")

    def write_file(self, filepath, content):
        node, parent, name = self.resolve(filepath)
        if not node or node.get("type") != "file":
            raise FileNotFoundError("not a file")
        node["content"] = content
        self.save()

    def delete(self, path):
        node, parent, name = self.resolve(path)
        if not parent:
            raise PermissionError("cannot delete root")
        children = parent.get("children", {})
        if name in children:
            del children[name]
            self.save()
        else:
            raise FileNotFoundError("not found")

    def rename(self, path, new_name):
        node, parent, name = self.resolve(path)
        if not parent:
            raise PermissionError("cannot rename root")
        children = parent.get("children", {})
        if new_name in children:
            raise FileExistsError("name exists")
        children[new_name] = node
        del children[name]
        node["name"] = new_name
        self.save()

    def exists(self, path):
        node, _, _ = self.resolve(path)
        return node is not None

# ---------------------------
# Frameless draggable window (base for apps) — improved
# ---------------------------

class AppWindow(QWidget):
    def __init__(self, title='Window', parent=None, width=720, height=480, resizable=True):
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        # Title bar
        self.titlebar = QFrame()
        self.titlebar.setObjectName("titlebar")
        tb_layout = QHBoxLayout(self.titlebar)
        tb_layout.setContentsMargins(8, 4, 4, 4)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: white; font-weight: 600;")
        tb_layout.addWidget(self.title_label)
        tb_layout.addStretch()
        # small control buttons
        self.min_btn = QPushButton("")
        self.min_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        self.min_btn.setFixedSize(28, 24)
        self.max_btn = QPushButton("")
        self.max_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.max_btn.setFixedSize(28, 24)
        self.close_btn = QPushButton("")
        self.close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.close_btn.setFixedSize(28, 24)
        tb_layout.addWidget(self.min_btn)
        tb_layout.addWidget(self.max_btn)
        tb_layout.addWidget(self.close_btn)
        self.vbox.addWidget(self.titlebar)
        # Content
        self.content = QFrame()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.vbox.addWidget(self.content)
        # events
        self.startPos = None
        self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn.clicked.connect(self.close)
        self.max_btn.clicked.connect(self.toggle_max_restore)
        self._is_max = False
        self._resizable = resizable
        self.setStyleSheet("""
            QWidget { background: #111214; color: #eee; font-family: Segoe UI, Arial; }
            #titlebar { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #232426, stop:1 #1b1c1e); border-bottom: 1px solid rgba(255,255,255,0.03); }
            QPushButton { background: transparent; border: none; color: #ddd; padding:2px; }
            QPushButton:hover { background: rgba(255,255,255,0.03); }
        """)
        # optional drop shadow could be added if needed

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.pos().y() <= self.titlebar.height():
            self.startPos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self.startPos:
            self.move(e.globalPos() - self.startPos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self.startPos = None

    def toggle_max_restore(self):
        if not self._is_max:
            self._normal_geom = self.geometry()
            parent = self.parent() or self.window()
            if hasattr(parent, "geometry"):
                parent_geom = parent.geometry()
                # leave a small border
                self.setGeometry(parent_geom.adjusted(18, 18, -18, -60))
            else:
                self.showMaximized()
            self._is_max = True
        else:
            if hasattr(self, "_normal_geom"):
                self.setGeometry(self._normal_geom)
            self._is_max = False

# ---------------------------
# Text Editor (works with VFS)
# ---------------------------

class TextEditor(AppWindow):
    def __init__(self, vfs: VirtualFileSystem, path=None, parent=None):
        super().__init__("Text Editor - Kurcxa's OS", parent, 760, 520)
        toolbar = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.save_btn = QPushButton("Save")
        self.saveas_btn = QPushButton("Save As")
        self.path_lbl = QLabel(path or "(untitled)")
        toolbar.addWidget(self.open_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.saveas_btn)
        toolbar.addWidget(self.path_lbl)
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)
        self.editor = QTextEdit()
        self.content_layout.addWidget(self.editor)
        self.vfs = vfs
        self.path = path  # path in VFS, e.g. /Notes/n1.txt
        if path:
            try:
                text = self.vfs.read_file(path)
                self.editor.setPlainText(text)
                self.path_lbl.setText(path)
                self.title_label.setText(f"Text Editor — {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.warning(self, "Open error", str(e))
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.saveas_btn.clicked.connect(self.save_file_as)

    def open_file(self):
        # pick from vfs
        folders = self.vfs.list_dir("/")
        # We'll present a simple dialog with directories and files from root recursively - for simplicity, show Documents and Notes
        items = []
        def gather(path="/"):
            for node in self.vfs.list_dir(path):
                np = (path.rstrip("/") + "/" + node["name"]).replace("//", "/")
                if node["type"] == "file":
                    items.append(np)
                else:
                    gather(np)
        gather("/")
        chosen, ok = QInputDialog.getItem(self, "Open file", "Choose file:", items, 0, False)
        if ok and chosen:
            try:
                content = self.vfs.read_file(chosen)
                self.editor.setPlainText(content)
                self.path = chosen
                self.path_lbl.setText(chosen)
                self.title_label.setText(f"Text Editor — {os.path.basename(chosen)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def save_file(self):
        if not self.path:
            return self.save_file_as()
        try:
            self.vfs.write_file(self.path, self.editor.toPlainText())
            QMessageBox.information(self, "Saved", "Saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Save error", str(e))

    def save_file_as(self):
        # ask for folder and name inside VFS
        # choose parent folder
        dirs = []
        def gather_dirs(path="/"):
            dirs.append(path)
            for node in self.vfs.list_dir(path):
                if node["type"] == "dir":
                    np = (path.rstrip("/") + "/" + node["name"]).replace("//", "/")
                    gather_dirs(np)
        gather_dirs("/")
        parent, ok = QInputDialog.getItem(self, "Save in folder", "Folder:", dirs, 0, False)
        if not ok:
            return
        name, ok2 = QInputDialog.getText(self, "File name", "Enter filename (with extension):")
        if not ok2 or not name.strip():
            return
        try:
            self.vfs.create_file(parent, name.strip(), self.editor.toPlainText())
            self.path = (parent.rstrip("/") + "/" + name.strip()).replace("//", "/")
            self.path_lbl.setText(self.path)
            QMessageBox.information(self, "Saved", f"Saved to {self.path}")
        except Exception as e:
            QMessageBox.warning(self, "Save as error", str(e))

# ---------------------------
# File Explorer (virtual FS aware)
# ---------------------------

class FileExplorer(AppWindow):
    def __init__(self, vfs: VirtualFileSystem, parent=None, open_callback=None):
        super().__init__("File Explorer - Kurcxa's OS", parent, 720, 480)
        self.open_callback = open_callback
        self.vfs = vfs
        # top bar
        top = QHBoxLayout()
        self.path_edit = QLineEdit("/")
        self.go_btn = QPushButton("Go")
        top.addWidget(self.path_edit)
        top.addWidget(self.go_btn)
        self.content_layout.addLayout(top)
        # list area
        self.list = QListWidget()
        self.content_layout.addWidget(self.list)
        self.list.itemDoubleClicked.connect(self.on_double)
        self.go_btn.clicked.connect(self.reload)
        # toolbar for operations
        ops = QHBoxLayout()
        self.new_folder_btn = QPushButton("New Folder")
        self.new_note_btn = QPushButton("New Note")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.refresh_btn = QPushButton("Refresh")
        ops.addWidget(self.new_folder_btn)
        ops.addWidget(self.new_note_btn)
        ops.addWidget(self.rename_btn)
        ops.addWidget(self.delete_btn)
        ops.addWidget(self.refresh_btn)
        ops.addStretch()
        self.content_layout.addLayout(ops)
        # connect
        self.new_folder_btn.clicked.connect(self.new_folder)
        self.new_note_btn.clicked.connect(self.new_note)
        self.rename_btn.clicked.connect(self.rename_item)
        self.delete_btn.clicked.connect(self.delete_item)
        self.refresh_btn.clicked.connect(self.reload)
        # context menu
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.context_menu)
        # load root
        self.reload()

    def reload(self):
        p = self.path_edit.text().strip() or "/"
        if not p.startswith("/"):
            p = "/" + p
        node, parent, name = self.vfs.resolve(p)
        if not node or node.get("type") != "dir":
            QMessageBox.warning(self, "Not a folder", f"{p} is not a directory in virtual FS.")
            return
        self.list.clear()
        # show directories first
        for node in self.vfs.list_dir(p):
            item = QListWidgetItem()
            if node["type"] == "dir":
                item.setText(f"[DIR] {node['name']}")
            else:
                item.setText(node['name'])
            item.setData(Qt.UserRole, (p.rstrip("/") + "/" + node["name"]).replace("//", "/"))
            self.list.addItem(item)
        self.current_dir = p
        self.path_edit.setText(p)

    def on_double(self, item):
        full = item.data(Qt.UserRole)
        node, _, _ = self.vfs.resolve(full)
        if node["type"] == "dir":
            self.path_edit.setText(full)
            self.reload()
        else:
            if self.open_callback:
                self.open_callback(full)
            else:
                # open in internal text viewer
                text = self.vfs.read_file(full)
                dlg = QDialog(self)
                dlg.setWindowTitle(full)
                dlg.resize(640, 480)
                ed = QTextEdit()
                ed.setPlainText(text)
                ed.setReadOnly(True)
                lay = QVBoxLayout(dlg)
                lay.addWidget(ed)
                dlg.exec_()

    def new_folder(self):
        name, ok = QInputDialog.getText(self, "New folder", "Folder name:")
        if not ok or not name.strip():
            return
        try:
            self.vfs.make_dir(self.current_dir, name.strip())
            self.reload()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def new_note(self):
        # create a file in Notes by default
        base = "/Notes"
        if not self.vfs.exists(base):
            base = self.current_dir
        name, ok = QInputDialog.getText(self, "New note", "Note name (e.g. note1.txt):", text=f"note_{int(time.time())}.txt")
        if not ok or not name.strip():
            return
        try:
            self.vfs.create_file(base, name.strip(), "New note...\n")
            self.reload()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def rename_item(self):
        item = self.list.currentItem()
        if not item:
            return
        full = item.data(Qt.UserRole)
        node, parent, name = self.vfs.resolve(full)
        if not node:
            QMessageBox.warning(self, "Error", "Item not found")
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=name)
        if not ok or not new_name.strip():
            return
        try:
            self.vfs.rename(full, new_name.strip())
            self.reload()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_item(self):
        item = self.list.currentItem()
        if not item:
            return
        full = item.data(Qt.UserRole)
        r = QMessageBox.question(self, "Delete", f"Delete {full}?", QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            try:
                self.vfs.delete(full)
                self.reload()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def context_menu(self, pos):
        item = self.list.itemAt(pos)
        menu = QMenu(self)
        if item:
            full = item.data(Qt.UserRole)
            node, _, _ = self.vfs.resolve(full)
            if node:
                if node["type"] == "file":
                    open_action = QAction("Open", self)
                    open_action.triggered.connect(lambda: self.on_double(item))
                    menu.addAction(open_action)
                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(self.rename_item)
                del_action = QAction("Delete", self)
                del_action.triggered.connect(self.delete_item)
                menu.addAction(rename_action)
                menu.addAction(del_action)
        else:
            new_folder = QAction("New Folder", self)
            new_folder.triggered.connect(self.new_folder)
            new_note = QAction("New Note", self)
            new_note.triggered.connect(self.new_note)
            menu.addAction(new_folder)
            menu.addAction(new_note)
        menu.exec_(self.list.mapToGlobal(pos))

# ---------------------------
# Browser App (Chromium)
# ---------------------------

class BrowserApp(AppWindow):
    def __init__(self, start_url="https://duckduckgo.com", parent=None):
        super().__init__("Kurcxa Browser", parent, 1100, 700)
        nav = QHBoxLayout()
        self.url_edit = QLineEdit(start_url)
        self.go_btn = QPushButton("Go")
        nav.addWidget(self.url_edit)
        nav.addWidget(self.go_btn)
        self.content_layout.addLayout(nav)
        self.web = QWebEngineView()
        try:
            self.web.setUrl(QUrl(start_url))
        except Exception:
            pass
        self.content_layout.addWidget(self.web)
        self.go_btn.clicked.connect(self.navigate)
        self.url_edit.returnPressed.connect(self.navigate)

    def navigate(self):
        u = self.url_edit.text().strip()
        if not u:
            return
        if not u.startswith("http"):
            u = "https://" + u
        self.web.setUrl(QUrl(u))
        self.url_edit.setText(u)

# ---------------------------
# Tiny AI (toy)
# ---------------------------

class KurcxaAI(AppWindow):
    def __init__(self, parent=None, open_in_browser_cb=None):
        super().__init__("Kurcxa AI Assistant", parent, 640, 420)
        self.open_browser = open_in_browser_cb
        lbl = QLabel("Ask Kurcxa AI about UI elements, apps, or short tech questions.\nType 'open <site>' to open in browser or 'search: <query>'.")
        lbl.setWordWrap(True)
        self.content_layout.addWidget(lbl)
        self.input = QLineEdit()
        self.input.setPlaceholderText("e.g. What does 'taskbar' do?  Or: open python.org")
        self.ask_btn = QPushButton("Ask")
        row = QHBoxLayout()
        row.addWidget(self.input)
        row.addWidget(self.ask_btn)
        self.content_layout.addLayout(row)
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        self.content_layout.addWidget(self.out)
        self.ask_btn.clicked.connect(self.answer)
        self.input.returnPressed.connect(self.answer)
        self.kb = {
            "taskbar": "The taskbar holds quick-launch icons, the Start menu, and the clock. Click app icons to open or switch windows.",
            "start menu": "Start Menu lets you launch apps and access system options like Shutdown and Settings.",
            "browser": "An app used to view websites. Kurcxa Browser uses the embedded Chromium engine via QtWebEngine.",
            "terminal": "A command-line interface where you can type shell commands to interact with the OS.",
            "file explorer": "Shows files and folders on disk; double-click to open files or navigate folders.",
            "text editor": "A basic app to view and edit plain text files.",
            "shutdown": "Closes Kurcxa's OS program. This is a toy simulation — no actual machine power-off.",
            "ai": "Kurcxa AI is a simple helper that answers common questions. If it can't answer, it can open a web search."
        }

    def answer(self):
        q = self.input.text().strip()
        if not q:
            return
        self.out.append(f"> {q}")
        ql = q.lower().strip()
        if ql.startswith("open "):
            target = q[len("open "):].strip()
            if not target.startswith("http"):
                target = "https://" + target
            self.out.append(f"Opening {target} in Kurcxa Browser...")
            if self.open_browser:
                self.open_browser(target)
            return
        for k, v in self.kb.items():
            if k in ql:
                self.out.append(v + "\n")
                return
        if ql.startswith("search:"):
            query = q[len("search:"):].strip()
            url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            self.out.append(f"Searching for {query}...")
            if self.open_browser:
                self.open_browser(url)
            return
        self.out.append("Kurcxa AI: I'm not sure. Try 'search: <query>' or ask about UI elements.")

# ---------------------------
# Login & Account UI
# ---------------------------

class LoginWindow(QDialog):
    def __init__(self, acct_mgr: AccountManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login — Kurcxa's OS")
        self.acct = acct_mgr
        self.resize(480, 260)
        layout = QVBoxLayout(self)
        title = QLabel("<h2>Welcome to Kurcxa's OS</h2>")
        layout.addWidget(title)
        form = QFormLayout()
        self.user_edit = QLineEdit()
        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Username:", self.user_edit)
        form.addRow("Password:", self.pw_edit)
        layout.addLayout(form)
        row = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.create_btn = QPushButton("Create account")
        self.guest_btn = QPushButton("Guest")
        row.addWidget(self.login_btn)
        row.addWidget(self.create_btn)
        row.addWidget(self.guest_btn)
        layout.addLayout(row)
        self.login_btn.clicked.connect(self.do_login)
        self.create_btn.clicked.connect(self.create_account)
        self.guest_btn.clicked.connect(self.login_guest)
        # recent users
        self.user_list = QListWidget()
        self.user_list.setMaximumHeight(80)
        layout.addWidget(QLabel("Existing users:"))
        layout.addWidget(self.user_list)
        self.user_list.itemClicked.connect(self.fill_user)
        self.refresh_users()

    def refresh_users(self):
        self.acct.load_index()
        self.user_list.clear()
        for u in sorted(self.acct.users_index.keys(), key=lambda x: x.lower()):
            it = QListWidgetItem(u)
            self.user_list.addItem(it)

    def fill_user(self, item):
        self.user_edit.setText(item.text())

    def do_login(self):
        u = self.user_edit.text().strip()
        p = self.pw_edit.text()
        if not u:
            QMessageBox.warning(self, "Missing", "Enter username")
            return
        if self.acct.verify_login(u, p):
            self.acct.set_last_login(u)
            self.accept()
            self.selected_user = u
            return
        QMessageBox.warning(self, "Login failed", "Invalid username or password")

    def create_account(self):
        u = self.user_edit.text().strip()
        if not u:
            QMessageBox.warning(self, "Missing", "Enter username")
            return
        if self.acct.user_exists(u):
            QMessageBox.warning(self, "Exists", "User already exists")
            return
        p, ok = QInputDialog.getText(self, "Password", "Enter a password:", QLineEdit.Password)
        if not ok or not p:
            return
        disp, ok2 = QInputDialog.getText(self, "Display name", "Display name (optional):", text=u)
        if not ok2:
            disp = u
        try:
            self.acct.create_user(u, p, disp)
            QMessageBox.information(self, "Created", f"User '{u}' created. You can now login.")
            self.refresh_users()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def login_guest(self):
        guest = "guest"
        if not self.acct.user_exists(guest):
            self.acct.create_user(guest, "guest", "Guest")
        self.acct.set_last_login(guest)
        self.selected_user = guest
        self.accept()

# ---------------------------
# Desktop (main shell)
# ---------------------------

class Desktop(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"Kurcxa's OS — {username}")
        self.setMinimumSize(1000, 640)
        self.setWindowState(Qt.WindowMaximized)
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # load VFS
        self.vfs = VirtualFileSystem(username)

        # wallpaper
        self.desktop_area = QLabel()
        self.desktop_area.setScaledContents(True)
        wpath = ""  # optional wallpaper path
        pix = resource_pixmap(wpath, fallback_color=QColor("#0d2940"), size=QSize(1600, 1000))
        self.desktop_area.setPixmap(pix)
        self.layout.addWidget(self.desktop_area)

        # taskbar
        self.taskbar = QFrame()
        self.taskbar.setFixedHeight(52)
        self.taskbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #121214, stop:1 #0b0b0c);")
        tb_layout = QHBoxLayout(self.taskbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)

        # start button
        self.start_btn = QPushButton("Kurcxa")
        self.start_btn.setFixedWidth(110)
        tb_layout.addWidget(self.start_btn)

        # pinned apps
        self.pinned = SETTINGS.get("pinned_apps", ["Kurcxa Browser", "File Explorer", "Text Editor"])
        for name in self.pinned:
            b = QToolButton()
            b.setText(name.split()[0])  # small label
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.clicked.connect(partial(self.launch_by_name, name))
            b.setFixedWidth(120)
            tb_layout.addWidget(b)

        tb_layout.addStretch()
        # quick status
        self.user_lbl = QLabel(self.username)
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("color: white;")
        tb_layout.addWidget(self.user_lbl)
        tb_layout.addWidget(self.clock_lbl)
        self.layout.addWidget(self.taskbar)

        # start menu (improved)
        self.start_menu = QFrame(self)
        self.start_menu.setStyleSheet("background: #222; color: white; border: 1px solid #444;")
        self.start_menu.setGeometry(10, self.height()-380, 320, 360)
        sm = QVBoxLayout(self.start_menu)
        sm.setContentsMargins(8, 8, 8, 8)
        # user header in start menu
        header = QHBoxLayout()
        self.header_pic = QLabel()
        pm = QPixmap(48, 48)
        pm.fill(QColor("#3a3f44"))
        self.header_pic.setPixmap(pm)
        header.addWidget(self.header_pic)
        user_box = QVBoxLayout()
        self.start_user_lbl = QLabel(f"<b>{self.username}</b>")
        user_box.addWidget(self.start_user_lbl)
        self.switch_btn = QPushButton("Switch user")
        self.switch_btn.setMaximumWidth(120)
        user_box.addWidget(self.switch_btn)
        header.addLayout(user_box)
        sm.addLayout(header)
        sm.addSpacing(4)
        # apps list
        apps = [
            ("Kurcxa Browser", self.launch_browser),
            ("File Explorer", self.launch_explorer),
            ("Text Editor", self.launch_text_editor),
            ("Terminal", self.launch_terminal),
            ("Kurcxa AI Assistant", self.launch_ai),
            ("Settings", self.launch_settings),
            ("Log out", self.logout)
        ]
        # pinned area
        sm.addWidget(QLabel("Pinned"))
        pin_layout = QHBoxLayout()
        for name in self.pinned:
            b = QPushButton(name)
            b.clicked.connect(partial(self.launch_by_name, name))
            pin_layout.addWidget(b)
        sm.addLayout(pin_layout)
        sm.addWidget(QLabel("All apps"))
        for name, cb in apps:
            b = QPushButton(name)
            b.clicked.connect(cb)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            sm.addWidget(b)
        self.start_menu.hide()

        # app windows list
        self.windows = []
        self.app_area = []  # placeholder for open windows (we just track)

        # signals
        self.start_btn.clicked.connect(self.toggle_start_menu)
        self.switch_btn.clicked.connect(self.switch_user)

        # clock
        self.update_clock()
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)

        # quick-launch handlers
        # attach initial user label
        self.user_lbl.setText(self.username)
        self.start_user_lbl.setText(f"<b>{self.username}</b>")

        # initial welcome
        QTimer.singleShot(500, lambda: self.show_status(f"Welcome, {self.username}!"))

    def toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
        else:
            btn_pos = self.start_btn.mapToGlobal(self.start_btn.rect().bottomLeft())
            local = self.mapFromGlobal(btn_pos)
            x = local.x()
            y = self.height() - self.start_menu.height() - self.taskbar.height()
            self.start_menu.move(x, y)
            self.start_menu.show()

    def update_clock(self):
        self.clock_lbl.setText(time.strftime("%Y-%m-%d %H:%M:%S"))

    def register_window(self, w):
        self.windows.append(w)
        w.setParent(self)
        w.show()

    def launch_text_editor(self, path=None):
        win = TextEditor(self.vfs, path, parent=self)
        win.move(140, 140)
        self.register_window(win)

    def launch_explorer(self):
        win = FileExplorer(self.vfs, parent=self, open_callback=self.launch_text_editor)
        win.move(160, 160)
        self.register_window(win)

    def launch_terminal(self):
        win = TerminalApp(parent=self)
        win.move(200, 200)
        self.register_window(win)

    def launch_browser(self, url=None):
        win = BrowserApp(parent=self)
        if url:
            win.web.setUrl(QUrl(url))
            win.url_edit.setText(url)
        win.move(80, 80)
        self.register_window(win)

    def launch_ai(self):
        win = KurcxaAI(parent=self, open_in_browser_cb=self.launch_browser)
        win.move(220, 200)
        self.register_window(win)

    def launch_settings(self):
        w = AppWindow("Settings - Kurcxa's OS", parent=self, width=460, height=300)
        lbl = QLabel("Settings\n\nTheme:")
        lbl.setWordWrap(True)
        w.content_layout.addWidget(lbl)
        theme_combo = QComboBox()
        theme_combo.addItems(["dark", "light"])
        theme_combo.setCurrentText(SETTINGS.get("theme", "dark"))
        def set_theme(t):
            SETTINGS["theme"] = t
            save_settings(SETTINGS)
            apply_theme(app, t)
            self.show_status(f"Theme set to {t}")
        theme_combo.currentTextChanged.connect(set_theme)
        w.content_layout.addWidget(theme_combo)
        w.move(300, 240)
        self.register_window(w)

    def launch_by_name(self, name):
        if "Browser" in name:
            self.launch_browser()
        elif "Explorer" in name:
            self.launch_explorer()
        elif "Text" in name:
            self.launch_text_editor()
        else:
            # fallback
            w = AppWindow(name, parent=self, width=400, height=300)
            w.content_layout.addWidget(QLabel(f"This is a stub for {name}"))
            self.register_window(w)

    def open_in_browser_tab(self, url):
        self.launch_browser(url)

    def switch_user(self):
        # simple logout and show login dialog
        dlg = LoginWindow(AccountManager(), parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_user = getattr(dlg, "selected_user", None)
            if new_user:
                SETTINGS["last_user"] = new_user
                save_settings(SETTINGS)
                QMessageBox.information(self, "Switch", f"Switching to {new_user} — ok to restart shell.")
                QApplication.instance().quit()

    def logout(self):
        r = QMessageBox.question(self, "Logout", "Log out current user?", QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            SETTINGS["last_user"] = None
            save_settings(SETTINGS)
            QApplication.instance().quit()

    def show_status(self, msg):
        # brief status via small message box bottom-left (could be replaced with proper toast)
        s = QLabel(msg, self)
        s.setStyleSheet("background: rgba(0,0,0,0.6); color: white; padding:6px; border-radius:4px;")
        s.move(12, self.height() - self.taskbar.height() - 60)
        s.show()
        QTimer.singleShot(2500, s.deleteLater)

# ---------------------------
# Terminal (shell) — kept simple
# ---------------------------

class TerminalApp(AppWindow):
    def __init__(self, parent=None):
        super().__init__("Terminal - Kurcxa's OS", parent, 760, 460)
        self.proc = None
        # basic simulated terminal for cross-platform
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.cmdline = QLineEdit()
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        btn_layout.addWidget(self.cmdline)
        btn_layout.addWidget(self.run_btn)
        self.content_layout.addWidget(self.output)
        self.content_layout.addLayout(btn_layout)
        self.run_btn.clicked.connect(self.run_cmd)
        self.cmdline.returnPressed.connect(self.run_cmd)

    def run_cmd(self):
        cmd = self.cmdline.text().strip()
        if not cmd:
            return
        self.output.append(f"> {cmd}")
        # basic builtins for safety — do not run arbitrary OS commands
        if cmd in ("help", "h"):
            self.output.append("Builtin commands: help, ls, pwd, echo <text>, whoami")
            return
        if cmd == "ls":
            self.output.append("This terminal is sandboxed. Use File Explorer to inspect files.")
            return
        if cmd.startswith("echo "):
            self.output.append(cmd[len("echo "):])
            return
        if cmd == "whoami":
            try:
                self.output.append(getpass.getuser())
            except Exception:
                self.output.append("unknown")
            return
        self.output.append(f"Command not recognized in this sandboxed terminal: {cmd}")

# ---------------------------
# Theme application
# ---------------------------

def apply_theme(app: QApplication, theme: str):
    pal = QPalette()
    if theme == "dark":
        pal.setColor(QPalette.Window, QColor("#0f1112"))
        pal.setColor(QPalette.WindowText, QColor("#e9eef2"))
        pal.setColor(QPalette.Base, QColor("#121416"))
        pal.setColor(QPalette.Text, QColor("#e9eef2"))
    else:
        pal.setColor(QPalette.Window, QColor("#f3f3f3"))
        pal.setColor(QPalette.WindowText, QColor("#111111"))
        pal.setColor(QPalette.Base, QColor("#ffffff"))
        pal.setColor(QPalette.Text, QColor("#111111"))
    app.setPalette(pal)

# ---------------------------
# Splash and main
# ---------------------------

class Splash(QSplashScreen):
    def __init__(self):
        pix = QPixmap(640, 360)
        pix.fill(QColor("#0b2f3a"))
        super().__init__(pix)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(80, 260, 480, 18)
        self.progress.setMaximum(100)
        self.text = QLabel(self)
        self.text.setGeometry(0, 200, 640, 30)
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("color: white; font-size: 16px;")
        self.dots = 0

    def set_progress(self, val, status="Loading"):
        self.progress.setValue(val)
        dots = "." * (self.dots % 4)
        self.dots += 1
        self.text.setText(f"{status}{dots}")

def main():
    global app
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app, SETTINGS.get("theme", "dark"))
    splash = Splash()
    splash.show()
    for i, label in enumerate(["Initializing UI", "Loading Accounts", "Restoring Session", "Finalizing"], start=1):
        QTimer.singleShot(300 * i, lambda v=i, l=label: splash.set_progress(int(25*v), l))
    t0 = time.time()
    while time.time() - t0 < 1.2:
        app.processEvents()
    acct = AccountManager()
    last = SETTINGS.get("last_user")
    chosen_user = None
    if last and acct.user_exists(last):
        pass
    dlg = LoginWindow(acct)
    res = dlg.exec_()
    if res != QDialog.Accepted:
        sys.exit(0)
    chosen_user = getattr(dlg, "selected_user", None)
    if not chosen_user:
        sys.exit(0)
    SETTINGS["last_user"] = chosen_user
    save_settings(SETTINGS)
    desktop = Desktop(chosen_user)
    desktop.show()
    splash.finish(desktop)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()