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
   - "image_prompt": A stable diffusion style prompt.
   - "camera": Suggested camera angle (e.g., "Wide Shot", "Full Shot", "Medium Shot", "Eye Level", "Overhead"). 

CRITICAL: Ensure variety in camera angles. Avoid using the same shot type (like Medium Shot) for all panels. At least one panel should be a "Wide Shot" or "Full Shot" to show the environment.

Output Format: JSON Array of {num_cuts} objects.
Example:
[
    {{"panel": 1, "description": "...", "text": "...", "image_prompt": "...", "camera": "Wide Shot"}},
    ...
]

RETURN ONLY THE JSON ARRAY. NO MARKDOWN.
"""

# --- Image Generation (Text-to-Image) ---
IMAGE_GEN_STYLE_PREFIX = "Clean cartoon webtoon style. Single panel, single scene. Dynamic composition with depth of field. "
IMAGE_GEN_CLEANUP_INSTRUCTIONS = "No text of any kind. No letters, numbers, logos, watermarks. No speech bubbles. "

IMAGE_GEN_NEGATIVE_PROMPT = (
    "text, letters, words, typography, watermark, logo, signature, "
    "speech bubble, thought bubble, caption, subtitle, "
    "photorealistic, realistic, 3d, photo, render, "
    "blurry, low quality, noise, artifacts, "
    "multiple views, split screen, character sheet, reference sheet, stickers, collection, grid"
)

# --- Image Variation ---
IMAGE_VARIATION_PROMPT_TEMPLATE = (
    "Clean cartoon webtoon style. Single panel, single scene. Gentle lighting. Soft shading. "
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
"character_appearance": "Extremely concise description of the main character (hair, gender, key outfit). (max 10 words)",
"cuts": [
    {{
    "cut_index": 1,
    "summary": "Short summary of the scene",
    "emotion": "Dominant emotion",
    "scene": "Visual scene description including the background and environment",
    "dialogue": "Character dialogue (or null if none)",
    "camera": "Camera angle/shot type (MANDATORY: Wide Shot, Full Shot, Medium Shot, or Close-up. Use variety!)"
    }}
]
}}

Character Profile (STRICTLY FOLLOW THIS):
\"\"\"{profile_prompt}\"\"\"

Diary:
\"\"\"{diary}\"\"\"

CRITICAL: Do not repeat the same camera angle for all cuts. Ensure at least one cut is a 'Wide Shot' or 'Full Shot' to show the character's surroundings clearly.
Ensure all content in the JSON (summary, scene, etc.) is written in English.
"""

# --- Individual Image Prompt Generation (from graph.py) ---
BUILD_IMAGE_PROMPT_TEMPLATE = """
Write an image generation prompt for a webtoon panel.
You must strictly follow the style guide below:
- {style_guide}

Few-Shot Examples (Focus on variety and environment):
Panel (WIDE SHOT, BUS STOP): Panoramic view of a street at sunset. A lonely bus stop with one person waiting. Large bus approaching in the distance.


Cut Information:
- Character: {character_appearance}
- Summary: {summary}
- Emotion: {emotion}
- Scene: {scene}
- Dialogue: {dialogue}
- Camera: {camera}

Output only the single-line prompt text in English.

STRICT RULES:
1. START the prompt with the camera/framing instruction (e.g., "Wide shot of...", "Full body shot of...").
2. Describe the entire composition, emphasizing the ENVIRONMENT and background settings as described in the scene.
3. Place the character within the scene naturally. Do NOT center the character's face/upper body unless a Close-up is explicitly requested.
4. If "Wide Shot" or "Full Shot" is requested, the character should be smaller in the frame, showing the surroundings.
5. Focus on the dynamic visual scene, character action, and movement.
6. Do not include dialogue, speech bubbles, or specific text/captions in the prompt.
7. Just refer to them as "the character".
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
