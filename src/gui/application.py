"""
Main application class for ZeroLag GUI.

This module provides the main QApplication and handles application-level
initialization, error handling, and cleanup.
"""

import sys
import os
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

from src.gui.main_window import ZeroLagMainWindow


class ZeroLagApplication:
    """Main application class for ZeroLag."""
    
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.main_window: Optional[ZeroLagMainWindow] = None
        self.splash_screen: Optional[QSplashScreen] = None
        
    def initialize(self) -> bool:
        """Initialize the application and all components."""
        try:
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("ZeroLag")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("ZeroLag")
            self.app.setOrganizationDomain("zerolag.app")
            
            # Set application properties
            self.app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
            
            # Show splash screen
            self.show_splash_screen()
            
            # Initialize main window
            self.main_window = ZeroLagMainWindow()
            
            # Hide splash screen after a delay
            QTimer.singleShot(2000, self.hide_splash_screen)
            
            return True
            
        except Exception as e:
            self.show_error("Initialization Error", f"Failed to initialize application: {e}")
            return False
            
    def show_splash_screen(self):
        """Show the application splash screen."""
        try:
            # Create a simple splash screen
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.darkGray)
            
            self.splash_screen = QSplashScreen(splash_pixmap)
            self.splash_screen.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            self.splash_screen.show()
            
            # Add text to splash screen
            self.splash_screen.showMessage(
                "ZeroLag\nGaming Input Optimizer\nLoading...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.white
            )
            
        except Exception as e:
            print(f"Error showing splash screen: {e}")
            
    def hide_splash_screen(self):
        """Hide the splash screen and show main window."""
        try:
            if self.splash_screen:
                self.splash_screen.finish(self.main_window)
                self.splash_screen = None
                
            if self.main_window:
                self.main_window.show()
                
        except Exception as e:
            print(f"Error hiding splash screen: {e}")
            
    def run(self) -> int:
        """Run the application main loop."""
        if not self.app or not self.main_window:
            return 1
            
        try:
            return self.app.exec_()
            
        except Exception as e:
            self.show_error("Runtime Error", f"Application error: {e}")
            return 1
            
    def cleanup(self):
        """Clean up application resources."""
        try:
            if self.main_window:
                self.main_window.stop_optimization()
                
            if self.splash_screen:
                self.splash_screen.close()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
    def show_error(self, title: str, message: str):
        """Show an error message dialog."""
        try:
            if self.app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.exec_()
            else:
                print(f"ERROR: {title} - {message}")
                
        except Exception as e:
            print(f"Error showing error dialog: {e}")
            
    def show_warning(self, title: str, message: str):
        """Show a warning message dialog."""
        try:
            if self.app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.exec_()
            else:
                print(f"WARNING: {title} - {message}")
                
        except Exception as e:
            print(f"Error showing warning dialog: {e}")


def main():
    """Main entry point for the ZeroLag GUI application."""
    app = ZeroLagApplication()
    
    try:
        # Initialize application
        if not app.initialize():
            return 1
            
        # Run application
        exit_code = app.run()
        return exit_code
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
        
    except Exception as e:
        app.show_error("Fatal Error", f"Unexpected error: {e}")
        return 1
        
    finally:
        app.cleanup()


if __name__ == "__main__":
    sys.exit(main())
