"""Keyframe Interpolation Implementation Example"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Tuple


def parse_time(time_str: str) -> time:
    """Parse HH:MM format to time object."""
    return datetime.strptime(time_str, "%H:%M").time()


def time_to_seconds(t: time) -> int:
    """Convert time to seconds since midnight."""
    return t.hour * 3600 + t.minute * 60 + t.second


def calculate_time_ratio(start_time: time, end_time: time, current_time: time) -> float:
    """
    Calculate ratio (0.0-1.0) of current position between start and end times.
    
    Handles midnight wraparound correctly.
    
    Args:
        start_time: Beginning time
        end_time: Ending time
        current_time: Current time
    
    Returns:
        float: 0.0 to 1.0 representing position between start and end
    
    Example:
        start=22:00, end=02:00, current=00:00
        Returns: 0.5 (halfway through)
    """
    start_s = time_to_seconds(start_time)
    end_s = time_to_seconds(end_time)
    current_s = time_to_seconds(current_time)
    
    # Handle midnight wraparound
    if end_s < start_s:
        # End time is tomorrow
        if current_s < start_s:
            # Current time is also tomorrow
            current_s += 24 * 3600
        end_s += 24 * 3600
    
    total_duration = end_s - start_s
    if total_duration == 0:
        return 0.0
    
    elapsed = current_s - start_s
    ratio = elapsed / total_duration
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, ratio))


def interpolate_value(v1: float, v2: float, ratio: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        v1: Start value
        v2: End value
        ratio: 0.0 to 1.0 (position between v1 and v2)
    
    Returns:
        Interpolated value
    """
    return v1 + (v2 - v1) * ratio


def find_surrounding_keyframes(
    keyframes: List[Dict], 
    current_time: time
) -> Tuple[Dict, Dict]:
    """
    Find the keyframes surrounding the current time.
    
    Args:
        keyframes: List of keyframe dicts with "time", "brightness", "temp"
        current_time: Current time
    
    Returns:
        (previous_keyframe, next_keyframe)
    
    Example:
        keyframes = [
            {"time": "06:00", "brightness": 0.1, "temp": 2700},
            {"time": "12:00", "brightness": 0.8, "temp": 4000},
            {"time": "18:00", "brightness": 0.5, "temp": 3500},
            {"time": "22:00", "brightness": 0.1, "temp": 2700}
        ]
        current_time = 15:00
        Returns: (keyframe at 12:00, keyframe at 18:00)
    """
    if not keyframes:
        # No keyframes - return safe defaults
        default_kf = {"time": "12:00", "brightness": 0.5, "temp": 3000}
        return default_kf, default_kf
    
    if len(keyframes) == 1:
        # Single keyframe - return it for both
        return keyframes[0], keyframes[0]
    
    # Sort keyframes by time
    sorted_kf = sorted(keyframes, key=lambda k: parse_time(k["time"]))
    
    current_s = time_to_seconds(current_time)
    
    # Find the keyframe just before current time
    prev_kf = sorted_kf[-1]  # Default to last (for wraparound)
    next_kf = sorted_kf[0]   # Default to first (for wraparound)
    
    for i, kf in enumerate(sorted_kf):
        kf_time = parse_time(kf["time"])
        kf_s = time_to_seconds(kf_time)
        
        if kf_s <= current_s:
            prev_kf = kf
            next_kf = sorted_kf[(i + 1) % len(sorted_kf)]
        else:
            # Found the next keyframe
            break
    
    return prev_kf, next_kf


def get_interpolated_values(
    keyframes: List[Dict], 
    current_time: time
) -> Tuple[float, int, float]:
    """
    Get interpolated brightness and temperature for current time.
    
    Args:
        keyframes: List of keyframe dicts
        current_time: Current time
    
    Returns:
        (brightness_01, temperature_k, transition_seconds)
    
    Example:
        keyframes = [
            {"time": "06:00", "brightness": 0.1, "temp": 2700},
            {"time": "18:00", "brightness": 0.8, "temp": 4000}
        ]
        current_time = 12:00 (halfway)
        Returns: (0.45, 3350, 2.5)
    """
    if not keyframes:
        # Safe defaults
        return 0.5, 3000, 2.0
    
    if len(keyframes) == 1:
        kf = keyframes[0]
        return kf["brightness"], kf["temp"], 2.0
    
    # Find surrounding keyframes
    prev_kf, next_kf = find_surrounding_keyframes(keyframes, current_time)
    
    # If prev and next are the same, we're exactly on a keyframe
    if prev_kf["time"] == next_kf["time"]:
        return prev_kf["brightness"], prev_kf["temp"], 2.0
    
    # Calculate ratio
    prev_time = parse_time(prev_kf["time"])
    next_time = parse_time(next_kf["time"])
    ratio = calculate_time_ratio(prev_time, next_time, current_time)
    
    # Interpolate brightness
    brightness = interpolate_value(
        prev_kf["brightness"],
        next_kf["brightness"],
        ratio
    )
    
    # Interpolate temperature
    temp = interpolate_value(
        prev_kf["temp"],
        next_kf["temp"],
        ratio
    )
    
    # Calculate recommended transition time
    # Longer for bigger changes
    brightness_delta = abs(next_kf["brightness"] - prev_kf["brightness"])
    temp_delta = abs(next_kf["temp"] - prev_kf["temp"])
    
    # Base transition + extra for large changes
    transition = 2.0
    if brightness_delta > 0.3 or temp_delta > 1000:
        transition = 3.0
    if brightness_delta > 0.5 or temp_delta > 2000:
        transition = 5.0
    
    return brightness, int(temp), transition


# Example Usage
if __name__ == "__main__":
    # Define keyframes
    keyframes = [
        {"time": "06:00", "brightness": 0.1, "temp": 2700},
        {"time": "09:00", "brightness": 0.8, "temp": 5000},
        {"time": "12:00", "brightness": 0.9, "temp": 6000},
        {"time": "18:00", "brightness": 0.5, "temp": 3500},
        {"time": "22:00", "brightness": 0.1, "temp": 2200}
    ]
    
    # Test at different times
    test_times = [
        time(7, 30),   # Morning
        time(12, 0),   # Noon (exact keyframe)
        time(15, 0),   # Afternoon
        time(23, 0),   # Night
        time(1, 0)     # After midnight (wraparound)
    ]
    
    print("Keyframe Interpolation Test:")
    print("-" * 60)
    
    for test_time in test_times:
        brightness, temp, transition = get_interpolated_values(keyframes, test_time)
        print(f"Time: {test_time.strftime('%H:%M')}")
        print(f"  Brightness: {brightness:.2f} (0.0-1.0)")
        print(f"  Temperature: {temp}K")
        print(f"  Transition: {transition}s")
        
        # Show surrounding keyframes
        prev_kf, next_kf = find_surrounding_keyframes(keyframes, test_time)
        print(f"  Between: {prev_kf['time']} → {next_kf['time']}")
        print()
