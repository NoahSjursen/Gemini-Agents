import google.generativeai as genai
import dotenv
import os
import pyautogui
import re
from time import sleep
from PIL import Image, ImageDraw, ImageFont
pyautogui.FAILSAFE = False
dotenv.load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up the model
generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 32,
  "max_output_tokens": 1024,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Get actual screen resolution
screen_width, screen_height = pyautogui.size() 

# Calculate Pixel Count Directly
width_pixels = screen_width
height_pixels = screen_height
print(f"Total Pixels: ({width_pixels}, {height_pixels})")

# Divide screen resolution by 2 for prompt
half_screen_width = screen_width // 2
half_screen_height = screen_height // 2
task = input("Enter your task (or type 'exit' to quit): ")


def grid_image():
    # Take a screenshot at half resolution
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))

    sleep(3)

    # Draw the grid with coordinates
    grid_size = 40
    draw = ImageDraw.Draw(screenshot)
    font = ImageFont.truetype("arial.ttf", 11)

    # Iterate over each grid cell, ensuring full height coverage
    for x in range(0, screenshot.width - grid_size, grid_size):
        for y in range(0, screenshot.height - grid_size, grid_size):
            # Get the pixel color at the center of the cell
            pixel_color = screenshot.getpixel((x + grid_size // 2, y + grid_size // 2))

            # Calculate contrasting color with 50% opacity (lighter)
            contrast_color = (255 - pixel_color[0], 255 - pixel_color[1], 255 - pixel_color[2], 128)  # Adding alpha for opacity

            # Draw the grid line with lighter opacity
            draw.line([(x, y), (x, y + grid_size)], fill=contrast_color, width=1)
            draw.line([(x, y), (x + grid_size, y)], fill=contrast_color, width=1)

            # Draw the coordinates with lighter opacity
            draw.text((x, y), f"\n {x},{y} ", fill=contrast_color, font=font, anchor="la")

    # Handle the last column separately
    x = screenshot.width - grid_size
    for y in range(0, screenshot.height - grid_size, grid_size):
        # Get the pixel color at the center of the cell
        pixel_color = screenshot.getpixel((x + grid_size // 2, y + grid_size // 2))

        # Calculate contrasting color with 50% opacity (lighter)
        contrast_color = (255 - pixel_color[0], 255 - pixel_color[1], 255 - pixel_color[2], 64)  # Adding alpha for opacity

        # Draw the grid line with lighter opacity
        draw.line([(x, y), (x, y + grid_size)], fill=contrast_color, width=1)
        draw.line([(x, y), (x + grid_size, y)], fill=contrast_color, width=1)

        # Draw the coordinates with lighter opacity
        draw.text((x, y), f"\n {x},{y}", fill=contrast_color, font=font, anchor="la")

    # Handle the last row separately
    y = screenshot.height - grid_size
    for x in range(0, screenshot.width - grid_size, grid_size):
        # Get the pixel color at the center of the cell
        pixel_color = screenshot.getpixel((x + grid_size // 2, y + grid_size // 2))

        # Calculate contrasting color with 50% opacity (lighter)
        contrast_color = (255 - pixel_color[0], 255 - pixel_color[1], 255 - pixel_color[2], 128)  # Adding alpha for opacity

        # Draw the grid line with lighter opacity
        draw.line([(x, y), (x, y + grid_size)], fill=contrast_color, width=1)
        draw.line([(x, y), (x + grid_size, y)], fill=contrast_color, width=1)

        # Draw the coordinates with lighter opacity
        draw.text((x, y), f"\n {x},{y}", fill=contrast_color, font=font, anchor="la")

    # Draw the last grid lines for the full height
    for x in range(0, screenshot.width - grid_size, grid_size):
        draw.line([(x, screenshot.height - grid_size), (x, screenshot.height)], fill=contrast_color, width=1)

    # Draw the last grid lines for the full width
    for y in range(0, screenshot.height - grid_size, grid_size):
        draw.line([(screenshot.width - grid_size, y), (screenshot.width, y)], fill=contrast_color, width=1)

    # Save the image
    image_path = "screenshot_grid.png"
    screenshot.save(image_path)

    # Upload the image (assuming you have a 'genai' object defined)
    uploaded_image = genai.upload_file(image_path)
    return uploaded_image

while True:

    uploaded_image = grid_image()
    # Image reasoning prompt
    image_reasoning_prompt = [
        task,
        "Image: ",
        uploaded_image,
        f"Analyze this image and provide a logical response for the next steps to take in order to complete the task: {task}. If you can not get the answer to the specific task using the image provided then you should use logic and reasoning to figure out what comes next using the present data. If you get multiple answers, decide the one you're most confident in and return only that answer. in the format (find: 'object') the object can be anything that you decide. but descibe it clearly with shape, colours, context of what it might be used for, location relative to other object and placement in the image."
    ]
    print("Image Reasoning")
    image_reasoning = model.generate_content(image_reasoning_prompt)
    image_reasoning = image_reasoning.text
    print(image_reasoning)
    # Object location prompt
    object_location_prompt = [
        task,
        image_reasoning,
        "Image: ",
        uploaded_image,
        "The grid squares in this image have numbered coordinates in the top left corner in each cell, representing the actual screen coordinates.",
        f"Using the user's request, {image_reasoning} the '{task}' in the image. Be precise and take your time to analyze the complete image.  Focus on identifying the center of the '{task}'.",
        f"Based on the center of the '{task}', determine the closest grid cell. If the center is closer to the center of a cell than the corner, prioritize the cell center.", 
        f"If the center of the '{task}' falls exactly between two cells, choose the cell that is closer to the top-left corner of the image.",
        "Provide the coordinates from the grid in the format: '(x,y)'  (For example: '(400,200)')",
        "Also provide a reasoning response explaining how you determined the coordinates and how much of the square overlaps the object scale 0,1"
    ]
    response_location = model.generate_content(object_location_prompt)
    print(response_location.text)

    # Extract coordinates
    coordinates_text = response_location.text
    match = re.search(r"\((?P<x>-?\d+),\s*(?P<y>-?\d+)\)", coordinates_text)

    if match:
        x = int(match.group('x'))
        y = int(match.group('y'))
        y+=10
        x+=10
        print(f"Gemini Coordinates: ({x}, {y})")

        # Move cursor to the adjusted coordinates
        pyautogui.moveTo(x*2, y*2, duration=0.5)
        sleep(0.1)
        pyautogui.click()
        uploaded_image = grid_image()
    else:
        print("Coordinates still not found. Check Gemini's response:")
        print(coordinates_text)
