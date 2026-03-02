from typing import Dict, Any, List

# --- Storyboard Generation ---
STORYBOARD_PROMPT_TEMPLATE = """
You are a professional webtoon storyboard artist.
Analyze the following diary entry and create a {num_cuts}-cut comic strip storyboard.

Diary Entry:
"{diary_text}"

Style: {style}

Requirements:
1. Break down the story into exactly {num_cuts} panels.
2. For each panel, provide:
   - "description": Visual description of the scene.
   - "text": Brief narration or dialogue (keep it short).
   - "image_prompt": A stable diffusion style prompt for generating the image.

Output Format: JSON Array of {num_cuts} objects.
Example:
[
    {{"panel": 1, "description": "...", "text": "...", "image_prompt": "..."}},
    ...
]

RETURN ONLY THE JSON ARRAY. NO MARKDOWN.
"""

# --- Image Generation (Text-to-Image) ---
IMAGE_GEN_STYLE_PREFIX = "Clean cartoon webtoon style."
IMAGE_GEN_CLEANUP_INSTRUCTIONS = "No text of any kind. No letters, numbers, logos, watermarks. No speech bubbles. "

IMAGE_GEN_NEGATIVE_PROMPT = (
    "text, letters, words, typography, watermark, logo, signature, "
    "speech bubble, thought bubble, caption, subtitle, "
    "photorealistic, realistic, 3d, photo, render, "
    "blurry, low quality, noise, artifacts, "
    "crowd, multiple views, split screen, character sheet, reference sheet, stickers, collection, grid"
)

# --- Image Variation ---
IMAGE_VARIATION_PROMPT_TEMPLATE = (
    "Clean cartoon webtoon style. Gentle lighting. Soft shading. "
    "The provided reference image is for character identity (facial features, hair, outfit) ONLY. "
    "CRITICAL: Create a dynamic scene with movement and action. The composition, camera angle, and framing MUST strictly follow the text description below, NOT the reference image. "
    "Single character, one person only. Full body or medium shot showing active movement. "
    "No text, no stickers, no collection, no grid. "
    "{cut_prompt}"
)

# --- Storyboard Planning (from graph.py - optional but good for consistency) ---
PLAN_STORYBOARD_PROMPT_TEMPLATE = """
You are a professional 'Diary to Comic Storyboard' editor.
Create a {num_cuts}-cut comic storyboard from the diary below.
Output MUST be in JSON format only.

Required Schema:
{{
"character_appearance": "Concise description of the main character based on the profile provided. (max 15 words)",
"cuts": [
    {{
    "cut_index": 1,
    "summary": "Short summary of the scene",
    "emotion": "Dominant emotion",
    "scene": "Visual scene description",
    "dialogue": "Character dialogue (or null if none)",
    "camera": "Camera angle/shot type (or null if none)"
    }}
]
}}

Character Profile (STRICTLY FOLLOW THIS):
\"\"\"{profile_prompt}\"\"\"

Diary:
\"\"\"{diary}\"\"\"

Ensure all content in the JSON (summary, scene, etc.) is written in English.
"""

# --- Individual Image Prompt Generation (from graph.py) ---
BUILD_IMAGE_PROMPT_TEMPLATE = """
Write an image generation prompt for a webtoon panel.
You must strictly follow the style guide below:
- {style_guide}

Few-Shot Examples (Focus on location and action):
Panel 1 (BUS STOP OUTSIDE): Bus stop sign + bus at the curb. Boy is outside on the sidewalk waving. Driver visible through front window waiting.
Panel 2 (RESTAURANT): Restaurant table with tonkatsu plate clearly visible. Boy seated smiling, holding chopsticks.
Panel 3 (HOME DOORWAY): Boy opens front door. Full dog visible wagging and greeting.
Panel 4 (BEDROOM OVERHEAD): Overhead bedroom view with bed. Boy sits on bed with dog nearby, smiling contentedly.

Cut Information:
- Character: {character_appearance}
- Summary: {summary}
- Emotion: {emotion}
- Scene: {scene}
- Dialogue: {dialogue}
- Camera: {camera}

Output only the single-line prompt text in English.
Focus on the dynamic visual scene, character action, and movement. Do not include dialogue, speech bubbles, or specific text/captions in the prompt.
Ensure the prompt describes a single scene showing the character in an active, situational context. 
Do not include phrases like "multiple views," "different poses," or "collection."

CRITICAL: Explicitly specify the camera shot/framing (e.g., "Full body shot", "Medium shot", "Side view") to ensure a varied and dynamic composition. Avoid repeating the same framing in every panel.

Just refer to them as "the character".
"""

# --- Prompt Revision (from graph.py) ---
REVISE_IMAGE_PROMPT_TEMPLATE = """
You are an Image Prompt Rewriter.
Keep the original prompt's core but improve it to resolve the QA failure reason.
Output only the revised single-line prompt text in English.

Original Prompt:
{old_prompt}

QA Failure Reason:
{reason}

Fix Hint:
{fix_hint}
"""
