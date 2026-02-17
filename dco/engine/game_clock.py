"""
Game clock for time control in chess games.
Manages countdown timers with increment support.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from datetime import datetime
from typing import Optional


class GameClock(QObject):
    """Chess game clock with increment support."""
    
    # Signals
    time_updated = Signal(float)  # Emits remaining time in seconds
    time_expired = Signal()  # Emits when time runs out
    
    def __init__(
        self,
        initial_time_seconds: float,
        increment_seconds: float = 0,
        parent=None
    ):
        """
        Initialize game clock.
        
        Args:
            initial_time_seconds: Starting time in seconds
            increment_seconds: Increment added after each move
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.initial_time = initial_time_seconds
        self.increment = increment_seconds
        self.time_remaining = initial_time_seconds
        
        self.is_running = False
        self.is_paused = False
        self.last_start_time: Optional[datetime] = None
        
        # Timer for UI updates (update every 100ms for smooth display)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_timer_tick)
        self.update_timer.setInterval(100)  # 100ms
    
    def start(self):
        """Start the clock countdown."""
        if self.is_running and not self.is_paused:
            return
        
        self.is_running = True
        self.is_paused = False
        self.last_start_time = datetime.now()
        self.update_timer.start()
    
    def pause(self):
        """Pause the clock."""
        if not self.is_running or self.is_paused:
            return
        
        # Update time remaining before pausing
        self._update_time_remaining()
        
        self.is_paused = True
        self.update_timer.stop()
    
    def resume(self):
        """Resume the clock after pause."""
        if not self.is_running or not self.is_paused:
            return
        
        self.is_paused = False
        self.last_start_time = datetime.now()
        self.update_timer.start()
    
    def stop(self):
        """Stop the clock completely."""
        self.is_running = False
        self.is_paused = False
        self.update_timer.stop()
        self.last_start_time = None
    
    def reset(self, time_seconds: Optional[float] = None):
        """
        Reset the clock to initial or specified time.
        
        Args:
            time_seconds: New time in seconds (uses initial if None)
        """
        was_running = self.is_running
        self.stop()
        
        if time_seconds is not None:
            self.time_remaining = time_seconds
        else:
            self.time_remaining = self.initial_time
        
        self.time_updated.emit(self.time_remaining)
        
        if was_running:
            self.start()
    
    def add_increment(self):
        """Add increment time (called after a move)."""
        if self.increment > 0:
            self.time_remaining += self.increment
            self.time_updated.emit(self.time_remaining)
    
    def _update_time_remaining(self):
        """Update time remaining based on elapsed time."""
        if not self.is_running or self.is_paused or self.last_start_time is None:
            return
        
        now = datetime.now()
        elapsed = (now - self.last_start_time).total_seconds()
        self.time_remaining -= elapsed
        self.last_start_time = now
        
        # Check for flag (time expired)
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.stop()
            self.time_expired.emit()
    
    def _on_timer_tick(self):
        """Called periodically to update time display."""
        self._update_time_remaining()
        self.time_updated.emit(self.time_remaining)
    
    def get_time_remaining(self) -> float:
        """
        Get current time remaining in seconds.
        
        Returns:
            Time remaining in seconds
        """
        if self.is_running and not self.is_paused:
            # Update time but don't modify state
            if self.last_start_time:
                now = datetime.now()
                elapsed = (now - self.last_start_time).total_seconds()
                return max(0, self.time_remaining - elapsed)
        
        return self.time_remaining
    
    def is_flagged(self) -> bool:
        """
        Check if time has expired.
        
        Returns:
            True if time <= 0
        """
        return self.get_time_remaining() <= 0
    
    def format_time(self, seconds: Optional[float] = None) -> str:
        """
        Format time as MM:SS or HH:MM:SS.
        
        Args:
            seconds: Time to format (uses current if None)
            
        Returns:
            Formatted time string
        """
        if seconds is None:
            seconds = self.get_time_remaining()
        
        seconds = max(0, seconds)
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def get_formatted_time(self) -> str:
        """
        Get current time remaining as formatted string.
        
        Returns:
            Formatted time (MM:SS or HH:MM:SS)
        """
        return self.format_time()


class DualGameClock(QObject):
    """Manages clocks for both players in a chess game."""
    
    # Signals
    white_time_updated = Signal(float)
    black_time_updated = Signal(float)
    white_time_expired = Signal()
    black_time_expired = Signal()
    
    def __init__(
        self,
        initial_time_seconds: float,
        increment_seconds: float = 0,
        parent=None
    ):
        """
        Initialize dual clock for both players.
        
        Args:
            initial_time_seconds: Starting time for both players
            increment_seconds: Increment after each move
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.white_clock = GameClock(initial_time_seconds, increment_seconds, self)
        self.black_clock = GameClock(initial_time_seconds, increment_seconds, self)
        
        # Connect signals
        self.white_clock.time_updated.connect(self.white_time_updated.emit)
        self.black_clock.time_updated.connect(self.black_time_updated.emit)
        self.white_clock.time_expired.connect(self.white_time_expired.emit)
        self.black_clock.time_expired.connect(self.black_time_expired.emit)
        
        self.active_clock: Optional[GameClock] = None
    
    def start_white(self):
        """Start white's clock."""
        if self.active_clock == self.black_clock:
            self.black_clock.pause()
        
        self.active_clock = self.white_clock
        self.white_clock.start()
    
    def start_black(self):
        """Start black's clock."""
        if self.active_clock == self.white_clock:
            self.white_clock.pause()
        
        self.active_clock = self.black_clock
        self.black_clock.start()
    
    def switch_turn(self, is_white_turn: bool):
        """
        Switch active clock and add increment to previous player.
        
        Args:
            is_white_turn: True if white's turn, False for black
        """
        # Add increment to the player who just moved
        if self.active_clock is not None:
            self.active_clock.add_increment()
            self.active_clock.pause()
        
        # Start the other player's clock
        if is_white_turn:
            self.start_white()
        else:
            self.start_black()
    
    def pause_both(self):
        """Pause both clocks."""
        self.white_clock.pause()
        self.black_clock.pause()
    
    def resume_active(self):
        """Resume the active clock."""
        if self.active_clock:
            self.active_clock.resume()
    
    def stop_both(self):
        """Stop both clocks."""
        self.white_clock.stop()
        self.black_clock.stop()
        self.active_clock = None
    
    def reset_both(self):
        """Reset both clocks to initial time."""
        self.white_clock.reset()
        self.black_clock.reset()
        self.active_clock = None
    
    def get_white_time(self) -> float:
        """Get white's remaining time in seconds."""
        return self.white_clock.get_time_remaining()
    
    def get_black_time(self) -> float:
        """Get black's remaining time in seconds."""
        return self.black_clock.get_time_remaining()
    
    def get_white_formatted(self) -> str:
        """Get white's time as formatted string."""
        return self.white_clock.get_formatted_time()
    
    def get_black_formatted(self) -> str:
        """Get black's time as formatted string."""
        return self.black_clock.get_formatted_time()
    
    def is_either_flagged(self) -> bool:
        """Check if either player has run out of time."""
        return self.white_clock.is_flagged() or self.black_clock.is_flagged()
