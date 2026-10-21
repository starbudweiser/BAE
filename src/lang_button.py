"""Bouton drapeau de la langue et son menu (Automatique, français, anglais, italien, espagnol).

Même présentation que kEYKODES. Le choix est mémorisé dans les QSettings de l'appli
(clé « language », « auto » = langue du Mac).
"""
from PyQt6.QtCore import QLocale, QSettings, Qt
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import QMenu, QPushButton

import i18n
import socle_qt
from i18n import L

AUTO = "auto"  # langue du système


def detect_system_lang() -> str:
    """Langue de l'interface du Mac (Réglages > Général > Langue et région)."""
    return i18n.system_lang(QLocale.system().uiLanguages())


def init_lang(settings: QSettings) -> None:
    """Active la langue mémorisée (à appeler avant de construire l'interface)."""
    choice = settings.value("language", AUTO)
    i18n.set_lang(detect_system_lang() if choice == AUTO else choice)


class LangButton(QPushButton):
    """Drapeau de la langue active ; un clic ouvre le menu de choix, puis appelle on_change()."""

    def __init__(self, settings: QSettings, on_change, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.on_change = on_change
        self.setObjectName("LangButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        size = round(18 * socle_qt.SCALE)
        self.setStyleSheet(
            f"QPushButton#LangButton {{ background: transparent; border: none; border-radius: {socle_qt.m('radius')}px;"
            f" padding: 0; min-height: 0; font-size: {size}px; }}"
            f"QPushButton#LangButton:hover {{ background: {socle_qt.c('surface-hover')}; }}")
        self.setFixedSize(size + 12, size + 8)
        self.clicked.connect(self._open_menu)
        self.refresh()

    def refresh(self):
        code = i18n.get_lang()
        self.setText(i18n.FLAGS[code])
        self.setToolTip(L("Langue : {name}", name=i18n.LANGS[code]))

    def _open_menu(self):
        menu = QMenu(self)
        group = QActionGroup(menu)
        chosen = self.settings.value("language", AUTO)
        system = detect_system_lang()
        auto = menu.addAction(L("Automatique ({lang})", lang=f"{i18n.FLAGS[system]} {i18n.LANGS[system]}"))
        auto.setData(AUTO)
        menu.addSeparator()
        actions = [auto]
        for code, name in i18n.LANGS.items():
            act = menu.addAction(f"{i18n.FLAGS[code]}  {name}")
            act.setData(code)
            actions.append(act)
        for act in actions:
            act.setCheckable(True)
            act.setChecked(act.data() == chosen)
            group.addAction(act)
        picked = menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
        if picked is not None:
            self.settings.setValue("language", picked.data())
            i18n.set_lang(detect_system_lang() if picked.data() == AUTO else picked.data())
            self.refresh()
            self.on_change()
