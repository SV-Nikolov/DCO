"""
Quick Start Guide: Integrating Modern UI Design into DCO

This guide shows how to integrate the modern UI design into your existing
PySide6-based DCO application.
"""

# ============================================================================
# STEP 1: Update your main application entry point (app.py)
# ============================================================================

"""
FILE: app.py (Updated version)

Replace or update your existing app.py with this:
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from dco.ui.main_window import MainWindow
from dco.ui.modern_stylesheet import load_stylesheet


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Apply modern stylesheet
    app.setStyleSheet(load_stylesheet())
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# ============================================================================
# STEP 2: Update existing components to use CSS classes
# ============================================================================

"""
FILE: dco/ui/screens/home.py (Example updates)

When creating cards, add objectName for CSS styling:
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class StatCard(QFrame):
    """Updated card with modern styling."""
    
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        
        # Set object name for CSS styling
        self.setObjectName("statCard")
        
        # Remove old stylesheet
        # self.setStyleSheet("""...""")  # DELETE THIS
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setObjectName("statLabel")  # For CSS
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")  # For CSS
        layout.addWidget(value_label)


# ============================================================================
# STEP 3: Update main_window.py NavigationButton styling
# ============================================================================

"""
FILE: dco/ui/main_window.py (NavigationButton update)

Replace the old NavigationButton stylesheet with modern version:
"""

from PySide6.QtWidgets import QPushButton

class NavigationButton(QPushButton):
    """Modern navigation button with CSS styling."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(50)
        
        # Let the global stylesheet handle styling
        # Remove the old inline stylesheet


# ============================================================================
# STEP 4: Customize colors programmatically
# ============================================================================

"""
If you need to set colors programmatically, use this palette:
"""

COLOR_PALETTE = {
    # Primary
    'primary': '#2563eb',
    'primary_dark': '#1e40af',
    'primary_light': '#dbeafe',
    
    # Backgrounds
    'bg_dark': '#0f172a',
    'bg_darker': '#020617',
    'bg_card': '#1e293b',
    'bg_secondary': '#1a2332',
    
    # Text
    'text_primary': '#f1f5f9',
    'text_secondary': '#cbd5e1',
    'text_muted': '#94a3b8',
    
    # Status
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    
    # Chess
    'chess_light': '#f0d9b5',
    'chess_dark': '#b58863',
}

# Usage example:
from PySide6.QtGui import QColor

def create_colored_button(color_name: str):
    """Create a button with a specific color."""
    button = QPushButton("Click Me")
    color = COLOR_PALETTE.get(color_name, COLOR_PALETTE['primary'])
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {color}dd;
        }}
    """)
    return button


# ============================================================================
# STEP 5: Update card-based layouts
# ============================================================================

"""
For any card-based layouts (like game cards in library.py):

OLD CODE:
    game_widget = QFrame()
    game_widget.setStyleSheet('''
        QFrame {
            background-color: #1e293b;
            border: 1px solid #333;
        }
    ''')

NEW CODE:
    game_widget = QFrame()
    game_widget.setObjectName("cardFrame")  # Uses CSS #cardFrame
"""


# ============================================================================
# STEP 6: Update progress bars
# ============================================================================

"""
For progress bars in batch analysis:

from PySide6.QtWidgets import QProgressBar

def create_progress_bar():
    progress = QProgressBar()
    # Modern stylesheet automatically styles all QProgressBar widgets
    # No need for inline stylesheet
    return progress
"""


# ============================================================================
# STEP 7: Responsive design consideration
# ============================================================================

"""
For responsive layouts, the modern stylesheet includes media query equivalents
in CSS. For PySide6 dynamic resizing:

class ResponsiveWidget(QWidget):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Adjust layout based on window width
        if self.width() < 768:
            # Mobile layout
            self.layout().setSpacing(8)
        elif self.width() < 1200:
            # Tablet layout
            self.layout().setSpacing(12)
        else:
            # Desktop layout
            self.layout().setSpacing(24)
"""


# ============================================================================
# STEP 8: Testing the design
# ============================================================================

"""
To verify the modern design is working:

1. Run the application:
   python app.py

2. Check that:
   - Sidebar has dark gradient background
   - Navigation items highlight in blue when active
   - Cards have subtle shadows and borders
   - Buttons have gradient backgrounds
   - Text is clearly readable with good contrast
   - Hover effects work smoothly

3. Test on different screen sizes:
   - Resize the window
   - Verify layout adjusts responsively
   - Check that all text is still readable
"""


# ============================================================================
# STEP 9: Custom widget styling examples
# ============================================================================

"""
If you create custom widgets, use objectName for CSS:
"""

class CustomGameCard(QFrame):
    def __init__(self, game_data, parent=None):
        super().__init__(parent)
        self.setObjectName("gameCard")  # Or create custom CSS
        
        # Custom styling if needed
        self.setStyleSheet("""
            #gameCard {
                /* Inherits from global stylesheet */
                /* Add custom rules only if needed */
            }
        """)


# ============================================================================
# STEP 10: Import and use the modern stylesheet in other modules
# ============================================================================

"""
If you need access to the stylesheet in other modules:
"""

from dco.ui.modern_stylesheet import load_stylesheet

def apply_stylesheet_to_app(app):
    """Apply the modern stylesheet to the application."""
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)


# ============================================================================
# FREQUENTLY ASKED QUESTIONS
# ============================================================================

"""
Q: How do I change the primary color?
A: Edit the STYLESHEET variable in modern_stylesheet.py
   Find: --color-primary: #2563eb;
   Replace with your desired color

Q: The fonts look different on my system. Why?
A: The stylesheet uses system fonts. Different OSes have different font
   rendering. This is by design for native look & feel.

Q: Can I use the HTML mockup directly?
A: The HTML mockup (ui_design.html) is for reference and web-based
   previewing. Use the modern_stylesheet.py for your PySide6 app.

Q: How do I add custom styling to a specific widget?
A: Set objectName on the widget, then add CSS rules:
   widget.setObjectName("myCustomWidget")
   Then in the stylesheet, add:
   #myCustomWidget {
       background-color: #custom-color;
   }

Q: Can I use light mode with this design?
A: Yes, you can create a light variant by inverting the colors.
   The current design is dark-mode optimized.

Q: How do I disable animations?
A: Remove or modify the transition declarations in modern_stylesheet.py
   Change: transition: all 0.3s ease;
   To: transition: none;

Q: The colors don't match the mockup exactly. Why?
A: PySide6 renders colors slightly differently than web browsers.
   This is normal and expected. The functionality is the same.

Q: Can I customize spacing/padding?
A: Yes, modify the spacing values in modern_stylesheet.py
   Look for padding: 20px; entries and adjust as needed.
"""


# ============================================================================
# MIGRATION CHECKLIST
# ============================================================================

"""
□ Back up current app.py
□ Install modern_stylesheet.py in dco/ui/
□ Update app.py to import and apply the stylesheet
□ Remove inline stylesheets from all existing components
□ Add objectName to cards and frames for CSS
□ Test all screens and interactions
□ Verify colors and contrast on different displays
□ Test responsive behavior (resize window)
□ Test keyboard navigation
□ Test on mobile/tablet if applicable
□ Commit changes to git
✓ Complete!
"""


# ============================================================================
# SUPPORT & NEXT STEPS
# ============================================================================

"""
FILES TO REFERENCE:
- ui_design.html: Interactive mockup (open in browser)
- modern_stylesheet.py: Qt stylesheet implementation
- UI_DESIGN_SYSTEM.md: Complete design documentation

TO GET STARTED:
1. Copy modern_stylesheet.py to dco/ui/
2. Update your app.py with the code from Step 1
3. Run: python app.py
4. The modern design should be applied!

FOR FURTHER CUSTOMIZATION:
- See UI_DESIGN_SYSTEM.md for color values
- Edit modern_stylesheet.py for style changes
- Reference ui_design.html for mockup of all screens

QUESTIONS?
- Check the FAQ section above
- Review UI_DESIGN_SYSTEM.md design documentation
- Check the HTML mockup for visual reference
"""
