"""
Application settings management.
Handles persistent storage and retrieval of user preferences.
"""

from typing import Optional
from PySide6.QtCore import QSettings


class AppSettings:
    """Manages application settings using QSettings."""
    
    def __init__(self):
        self.settings = QSettings("DCO", "DailyChessOffline")
    
    # ===== Engine Settings =====
    
    def get_engine_path(self) -> Optional[str]:
        """Get custom Stockfish engine path."""
        return self.settings.value("engine/path", None)
    
    def set_engine_path(self, path: Optional[str]):
        """Set custom Stockfish engine path."""
        if path:
            self.settings.setValue("engine/path", path)
        else:
            self.settings.remove("engine/path")
    
    def get_engine_threads(self) -> int:
        """Get number of engine threads."""
        return int(self.settings.value("engine/threads", 1))
    
    def set_engine_threads(self, threads: int):
        """Set number of engine threads."""
        self.settings.setValue("engine/threads", threads)
    
    def get_engine_hash(self) -> int:
        """Get engine hash size in MB."""
        return int(self.settings.value("engine/hash", 128))
    
    def set_engine_hash(self, hash_mb: int):
        """Set engine hash size in MB."""
        self.settings.setValue("engine/hash", hash_mb)
    
    def get_engine_depth(self) -> int:
        """Get default engine search depth."""
        return int(self.settings.value("engine/depth", 20))
    
    def set_engine_depth(self, depth: int):
        """Set default engine search depth."""
        self.settings.setValue("engine/depth", depth)
    
    def get_engine_time(self) -> float:
        """Get default engine time per move in seconds."""
        return float(self.settings.value("engine/time_per_move", 0.5))
    
    def set_engine_time(self, time_sec: float):
        """Set default engine time per move in seconds."""
        self.settings.setValue("engine/time_per_move", time_sec)
    
    # ===== Analysis Settings =====
    
    def get_analysis_auto_analyze(self) -> bool:
        """Get whether to auto-analyze imported games."""
        return self.settings.value("analysis/auto_analyze", True, type=bool)
    
    def set_analysis_auto_analyze(self, enabled: bool):
        """Set whether to auto-analyze imported games."""
        self.settings.setValue("analysis/auto_analyze", enabled)
    
    def get_analysis_best_threshold(self) -> int:
        """Get centipawn threshold for 'Best' moves (0 cp)."""
        return int(self.settings.value("analysis/threshold_best", 0))
    
    def set_analysis_best_threshold(self, cp: int):
        """Set centipawn threshold for 'Best' moves."""
        self.settings.setValue("analysis/threshold_best", cp)
    
    def get_analysis_excellent_threshold(self) -> int:
        """Get centipawn threshold for 'Excellent' moves (default: 15 cp loss)."""
        return int(self.settings.value("analysis/threshold_excellent", 15))
    
    def set_analysis_excellent_threshold(self, cp: int):
        """Set centipawn threshold for 'Excellent' moves."""
        self.settings.setValue("analysis/threshold_excellent", cp)
    
    def get_analysis_good_threshold(self) -> int:
        """Get centipawn threshold for 'Good' moves (default: 50 cp loss)."""
        return int(self.settings.value("analysis/threshold_good", 50))
    
    def set_analysis_good_threshold(self, cp: int):
        """Set centipawn threshold for 'Good' moves."""
        self.settings.setValue("analysis/threshold_good", cp)
    
    def get_analysis_inaccuracy_threshold(self) -> int:
        """Get centipawn threshold for 'Inaccuracy' (default: 100 cp loss)."""
        return int(self.settings.value("analysis/threshold_inaccuracy", 100))
    
    def set_analysis_inaccuracy_threshold(self, cp: int):
        """Set centipawn threshold for 'Inaccuracy'."""
        self.settings.setValue("analysis/threshold_inaccuracy", cp)
    
    def get_analysis_mistake_threshold(self) -> int:
        """Get centipawn threshold for 'Mistake' (default: 200 cp loss)."""
        return int(self.settings.value("analysis/threshold_mistake", 200))
    
    def set_analysis_mistake_threshold(self, cp: int):
        """Set centipawn threshold for 'Mistake'."""
        self.settings.setValue("analysis/threshold_mistake", cp)
    
    def get_analysis_add_to_practice(self) -> bool:
        """Get whether to auto-add mistakes to practice database."""
        return self.settings.value("analysis/add_to_practice", True, type=bool)
    
    def set_analysis_add_to_practice(self, enabled: bool):
        """Set whether to auto-add mistakes to practice database."""
        self.settings.setValue("analysis/add_to_practice", enabled)
    
    # ===== Practice Settings =====
    
    def get_practice_offset_plies(self) -> int:
        """Get number of plies before mistake to start practice position."""
        return int(self.settings.value("practice/offset_plies", 2))
    
    def set_practice_offset_plies(self, plies: int):
        """Set number of plies before mistake to start practice position."""
        self.settings.setValue("practice/offset_plies", plies)
    
    def get_practice_difficulty(self) -> str:
        """Get practice difficulty: 'strict' or 'lenient'."""
        return self.settings.value("practice/difficulty", "lenient")
    
    def set_practice_difficulty(self, difficulty: str):
        """Set practice difficulty: 'strict' or 'lenient'."""
        self.settings.setValue("practice/difficulty", difficulty)
    
    def get_practice_spaced_repetition(self) -> bool:
        """Get whether spaced repetition is enabled."""
        return self.settings.value("practice/spaced_repetition", True, type=bool)
    
    def set_practice_spaced_repetition(self, enabled: bool):
        """Set whether spaced repetition is enabled."""
        self.settings.setValue("practice/spaced_repetition", enabled)
    
    def get_practice_session_length(self) -> int:
        """Get default practice session length in positions."""
        return int(self.settings.value("practice/session_length", 10))
    
    def set_practice_session_length(self, length: int):
        """Set default practice session length in positions."""
        self.settings.setValue("practice/session_length", length)
    
    # ===== Appearance Settings =====
    
    def get_theme(self) -> str:
        """Get UI theme: 'light' or 'dark'."""
        return self.settings.value("appearance/theme", "light")
    
    def set_theme(self, theme: str):
        """Set UI theme: 'light' or 'dark'."""
        self.settings.setValue("appearance/theme", theme)
    
    def get_board_light_color(self) -> str:
        """Get light square color for chess board."""
        return self.settings.value("appearance/board_light", "#f0d9b5")
    
    def set_board_light_color(self, color: str):
        """Set light square color for chess board."""
        self.settings.setValue("appearance/board_light", color)
    
    def get_board_dark_color(self) -> str:
        """Get dark square color for chess board."""
        return self.settings.value("appearance/board_dark", "#b58863")
    
    def set_board_dark_color(self, color: str):
        """Set dark square color for chess board."""
        self.settings.setValue("appearance/board_dark", color)
    
    def get_show_coordinates(self) -> bool:
        """Get whether to show board coordinates."""
        return self.settings.value("appearance/show_coordinates", True, type=bool)
    
    def set_show_coordinates(self, show: bool):
        """Set whether to show board coordinates."""
        self.settings.setValue("appearance/show_coordinates", show)
    
    # ===== General Settings =====
    
    def get_username(self) -> str:
        """Get username for game records."""
        return self.settings.value("general/username", "You")
    
    def set_username(self, username: str):
        """Set username for game records."""
        self.settings.setValue("general/username", username)
    
    def get_import_auto_dedupe(self) -> bool:
        """Get whether to automatically skip duplicate imports."""
        return self.settings.value("general/auto_dedupe", True, type=bool)
    
    def set_import_auto_dedupe(self, enabled: bool):
        """Set whether to automatically skip duplicate imports."""
        self.settings.setValue("general/auto_dedupe", enabled)
    
    def get_default_time_control(self) -> str:
        """Get default time control: 'bullet', 'blitz', or 'rapid'."""
        return self.settings.value("general/default_time_control", "blitz")
    
    def set_default_time_control(self, control: str):
        """Set default time control: 'bullet', 'blitz', or 'rapid'."""
        self.settings.setValue("general/default_time_control", control)
    
    # ===== Utility Methods =====
    
    def reset_all(self):
        """Reset all settings to defaults."""
        self.settings.clear()
    
    def sync(self):
        """Ensure settings are written to persistent storage."""
        self.settings.sync()


# Global settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
