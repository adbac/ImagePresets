KEY = "com.adbac.ImagePresets.presets"

BASE_PRESETS = {
    "Black & White": dict(
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        enableColor=True,
        red=0,
        green=0,
        blue=0,
        alpha=100,
    ),
    "Black & White - 40%": dict(
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        enableColor=True,
        red=0,
        green=0,
        blue=0,
        alpha=40,
    ),
    "Red": dict(
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        enableColor=True,
        red=255,
        green=0,
        blue=0,
        alpha=100,
    ),
    "Green": dict(
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        enableColor=True,
        red=0,
        green=255,
        blue=0,
        alpha=100,
    ),
    "Blue": dict(
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        enableColor=True,
        red=0,
        green=0,
        blue=255,
        alpha=100,
    ),
}

def normalizeValue(value, current_range, target_range):
    """
    Normalize a value from the current range to the target range.

    :param value: The value to normalize.
    :param current_range: A tuple (min, max) representing the current range of the value.
    :param target_range: A tuple (min, max) representing the target range for the value.
    :return: The normalized value.
    """
    current_min, current_max = current_range
    target_min, target_max = target_range

    # Normalize the value to a 0-1 range
    normalized_value = (value - current_min) / (current_max - current_min)

    # Scale the normalized value to the target range
    scaled_value = normalized_value * (target_max - target_min) + target_min

    return scaled_value

def normalizeColor(color):
    return [normalizeValue(c, (0, 255), (0, 1)) for c in color[:-1]] + [normalizeValue(color[-1], (0, 100), (0, 1))]