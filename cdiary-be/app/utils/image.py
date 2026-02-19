import io
from PIL import Image
from typing import List

def combine_images_vertically(image_bytes_list: List[bytes]) -> bytes:
    images = [Image.open(io.BytesIO(b)) for b in image_bytes_list]
    if not images:
        return b""
    
    # Assume all images have same width (they should from Bedrock)
    width = images[0].width
    total_height = sum(img.height for img in images)
    
    combined = Image.new('RGB', (width, total_height))
    
    y_offset = 0
    for img in images:
        combined.paste(img, (0, y_offset))
        y_offset += img.height
        
    output = io.BytesIO()
    combined.save(output, format='PNG')
    return output.getvalue()
