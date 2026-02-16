"""
ECO (Encyclopedia of Chess Openings) detection for DCO.
Identifies opening names and codes from move sequences.
"""

import json
import os
from typing import Optional, Dict, Tuple
import chess


class ECODetector:
    """Detects chess openings using ECO classification."""
    
    def __init__(self):
        """Initialize ECO detector with opening database."""
        self.eco_data: Dict[str, Dict] = {}
        self._load_eco_data()
    
    def _load_eco_data(self):
        """Load ECO data from JSON file."""
        data_path = os.path.join(
            os.path.dirname(__file__),
            "..", "data", "eco_data.json"
        )
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                eco_list = json.load(f)
            
            # Build lookup dictionary keyed by move sequence
            for entry in eco_list:
                moves_key = entry.get('moves', '').strip()
                if moves_key:
                    self.eco_data[moves_key] = {
                        'eco': entry.get('eco', ''),
                        'name': entry.get('name', ''),
                        'variation': entry.get('variation', '')
                    }
        except Exception as e:
            print(f"Warning: Could not load ECO data: {e}")
            self.eco_data = {}
    
    def detect_opening(
        self, 
        board: chess.Board,
        max_plies: int = 20
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Detect opening from board position using longest-prefix matching.
        
        Args:
            board: Chess board with move history
            max_plies: Maximum number of plies to consider for opening
            
        Returns:
            Tuple of (eco_code, opening_name, variation) or (None, None, None)
        """
        if not self.eco_data:
            return None, None, None
        
        # Build move sequence from board history
        temp_board = chess.Board()
        moves_san = []
        
        for move in list(board.move_stack)[:max_plies]:
            # Get SAN notation for this move
            san = temp_board.san(move)
            moves_san.append(san)
            temp_board.push(move)
        
        # Try longest-prefix matching
        best_match = None
        best_match_length = 0
        
        # Start with full sequence and work backwards
        for length in range(len(moves_san), 0, -1):
            prefix = ' '.join(moves_san[:length])
            
            if prefix in self.eco_data:
                if length > best_match_length:
                    best_match = self.eco_data[prefix]
                    best_match_length = length
                    break  # Found longest match
        
        if best_match:
            return (
                best_match.get('eco'),
                best_match.get('name'),
                best_match.get('variation')
            )
        
        return None, None, None
    
    def get_opening_display_name(
        self,
        eco: Optional[str],
        name: Optional[str],
        variation: Optional[str]
    ) -> str:
        """
        Format opening information for display.
        
        Args:
            eco: ECO code (e.g., "C50")
            name: Opening name (e.g., "Italian Game")
            variation: Variation name (e.g., "Giuoco Piano")
            
        Returns:
            Formatted string like "C50: Italian Game, Giuoco Piano"
        """
        if not eco and not name:
            return ""
        
        parts = []
        
        if eco:
            parts.append(eco)
        
        if name:
            parts.append(name)
        
        if variation:
            parts.append(variation)
        
        # Format as "ECO: Name, Variation" or "ECO: Name" or just "Name"
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            return parts[0]
        elif eco and name and variation:
            return f"{eco}: {name}, {variation}"
        elif eco and name:
            return f"{eco}: {name}"
        else:
            return ", ".join(parts)


# Global ECO detector instance
_eco_detector = None


def get_eco_detector() -> ECODetector:
    """Get global ECO detector instance (singleton)."""
    global _eco_detector
    if _eco_detector is None:
        _eco_detector = ECODetector()
    return _eco_detector
