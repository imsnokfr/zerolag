#!/usr/bin/env python3
"""
ZeroLag Test Script

This script demonstrates the core input handling capabilities of ZeroLag.
It shows mouse movement, clicks, and keyboard input in real-time.
"""

import sys
import time
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from core.input.input_handler import InputHandler
from core.input.mouse_handler import GamingMouseHandler, MouseButton
from core.input.keyboard_handler import GamingKeyboardHandler


def main():
    """Main test function for ZeroLag input handling."""
    print("🎮 ZeroLag Input Handler Test")
    print("=" * 50)
    print("This will test mouse and keyboard input handling.")
    print("Move your mouse, click, and press keys to see the input detection.")
    print("Press Ctrl+C to stop.")
    print()
    
    # Event counters
    mouse_moves = 0
    mouse_clicks = 0
    keyboard_events = 0
    double_clicks = 0
    
    def on_mouse_move(state, event):
        nonlocal mouse_moves
        mouse_moves += 1
        if mouse_moves % 10 == 0:  # Print every 10th movement to avoid spam
            print(f"🖱️  Mouse: ({state.x}, {state.y}) delta: ({state.dx}, {state.dy})")
    
    def on_mouse_click(button, is_press, state, event):
        nonlocal mouse_clicks
        mouse_clicks += 1
        action = "pressed" if is_press else "released"
        print(f"🖱️  Mouse {button.name} {action} at ({state.x}, {state.y})")
    
    def on_double_click(button, state, event):
        nonlocal double_clicks
        double_clicks += 1
        print(f"🖱️  DOUBLE-CLICK: {button.name} at ({state.x}, {state.y})")
    
    def on_keyboard_event(event):
        nonlocal keyboard_events
        keyboard_events += 1
        action = "pressed" if event.event_type.name == "KEY_PRESS" else "released"
        key = event.data.get('key', 'unknown')
        print(f"⌨️  Keyboard: {key} {action}")
    
    # Create input handler
    print("Initializing input handler...")
    input_handler = InputHandler(queue_size=5000, enable_logging=False)
    
    # Create gaming mouse handler
    print("Setting up gaming mouse handler...")
    mouse_handler = GamingMouseHandler(input_handler, enable_logging=False)
    
    # Create gaming keyboard handler
    print("Setting up gaming keyboard handler...")
    keyboard_handler = GamingKeyboardHandler(input_handler, enable_logging=False)
    
    # Set up callbacks
    mouse_handler.set_mouse_move_callback(on_mouse_move)
    mouse_handler.set_mouse_click_callback(on_mouse_click)
    mouse_handler.set_mouse_double_click_callback(on_double_click)
    
    # Add keyboard callback to input handler
    input_handler.add_event_callback("KEY_PRESS", on_keyboard_event)
    input_handler.add_event_callback("KEY_RELEASE", on_keyboard_event)
    
    # Start keyboard tracking
    keyboard_handler.start_tracking()
    
    # Configure mouse settings
    mouse_handler.set_double_click_threshold(0.3)  # 300ms for double-click
    mouse_handler.set_movement_smoothing(True)
    mouse_handler.set_high_frequency_tracking(True)
    
    print("Starting input handlers...")
    if input_handler.start() and mouse_handler.start_tracking():
        print("✅ Input handlers started successfully!")
        print()
        print("🎯 Test Instructions:")
        print("  • Move your mouse around the screen")
        print("  • Click left and right mouse buttons")
        print("  • Try double-clicking for double-click detection")
        print("  • Press and release keyboard keys")
        print("  • Press Ctrl+C to stop")
        print()
        
        try:
            # Run for 30 seconds or until interrupted
            start_time = time.time()
            while time.time() - start_time < 30:
                time.sleep(1)
                
                # Get performance stats
                input_stats = input_handler.get_performance_stats()
                mouse_stats = mouse_handler.get_performance_stats()
                keyboard_stats = keyboard_handler.get_keyboard_stats()
                
                print(f"📊 Stats: {mouse_stats['movement_events']} moves, "
                      f"{mouse_stats['click_events']} clicks, "
                      f"{keyboard_stats['total_presses']} key presses, "
                      f"{keyboard_stats['total_simultaneous']} simultaneous, "
                      f"{double_clicks} double-clicks")
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping handlers...")
        
        finally:
            # Cleanup
            mouse_handler.stop_tracking()
            keyboard_handler.stop_tracking()
            input_handler.stop()
            
            # Final statistics
            final_keyboard_stats = keyboard_handler.get_keyboard_stats()
            print("\n📈 Final Results:")
            print(f"  Mouse movements: {mouse_moves}")
            print(f"  Mouse clicks: {mouse_clicks}")
            print(f"  Keyboard presses: {final_keyboard_stats['total_presses']}")
            print(f"  Keyboard releases: {final_keyboard_stats['total_releases']}")
            print(f"  Simultaneous keys: {final_keyboard_stats['total_simultaneous']}")
            print(f"  Double-clicks: {double_clicks}")
            print("✅ Test completed successfully!")
            
    else:
        print("❌ Failed to start input handlers")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
