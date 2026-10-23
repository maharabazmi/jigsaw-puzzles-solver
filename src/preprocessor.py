import cv2
import numpy as np

def detect_background_color(image: np.ndarray) -> np.ndarray:
    """
    Detects background color by sampling perimeter corners and border strips.
    """
    h, w = image.shape[:2]
    margin = max(5, min(15, h // 20, w // 20))
    samples = np.concatenate([
        image[0:margin, 0:margin].reshape(-1, 3),
        image[0:margin, w-margin:w].reshape(-1, 3),
        image[h-margin:h, 0:margin].reshape(-1, 3),
        image[h-margin:h, w-margin:w].reshape(-1, 3),
        image[0:2, :].reshape(-1, 3),
        image[-2:, :].reshape(-1, 3),
        image[:, 0:2].reshape(-1, 3),
        image[:, -2:].reshape(-1, 3),
    ], axis=0)
    return np.median(samples, axis=0)

def segment_jigsaw_pieces(image: np.ndarray, min_area: float = 3000.0):
    """
    Robust adaptive foreground segmentation for jigsaw puzzle pieces.
    Works seamlessly across dark, light, and textured backgrounds.
    
    Returns:
        mask (np.ndarray): Binary mask where 255 represents foreground pieces.
        contours (list[np.ndarray]): List of individual piece contours sorted by area.
        bg_color (np.ndarray): Detected background RGB color.
    """
    h, w = image.shape[:2]
    bg_color = detect_background_color(image)
    
    # Calculate color deviation from background
    color_diff = np.max(np.abs(image.astype(np.float32) - bg_color.astype(np.float32)), axis=2)
    
    # Solid background difference threshold
    # Jigsaw pieces clearly contrast with tabletop/sheet background
    binary = (color_diff > 12.0).astype(np.uint8) * 255
    
    # Morphological cleaning to close subtle boundary notches
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Fill internal holes (e.g., white or plain graphics inside the puzzle artwork)
    raw_contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled_mask = np.zeros((h, w), dtype=np.uint8)
    for c in raw_contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(filled_mask, [c], -1, 255, thickness=cv2.FILLED)
            
    # Extract final clean, continuous contours
    final_contours, _ = cv2.findContours(filled_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    final_contours = sorted(
        [c for c in final_contours if cv2.contourArea(c) >= min_area],
        key=cv2.contourArea,
        reverse=True
    )
    
    return filled_mask, final_contours, bg_color
