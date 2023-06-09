from PIL import Image, ImageDraw, ImageFont
import jieba

def add_text_to_image(text, image_path, text_color, background, padding=10, target_size=(640, 480), font_path="fonts/Hiragino Sans GB.ttc", font_size=16):
    # Open the image
    image = Image.open(image_path)

    # Resize the image to the target size while maintaining the aspect ratio
    image = image.resize(target_size)

    # Convert the image to RGBA mode
    image = image.convert("RGBA")

    # Create a new transparent image with the same size as the original image
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    # Create a draw object for the overlay image
    draw = ImageDraw.Draw(overlay)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Split the text into lines if it exceeds the available width
    lines = []

    # Split the text into individual Chinese characters
    words = [char for char in jieba.cut(text)]
    current_line = words[0]
    for word in words[1:]:
        if draw.textsize(current_line  + word, font=font)[0] <= target_size[0] - 2 * padding:
            current_line +=  word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    # Calculate the height of the background rectangle based on the number of lines
    text_height = draw.textsize(lines[0], font=font)[1]

    if len(lines) == 1:
        box_height = text_height + padding * 2
    else:
        box_height = (text_height + padding) * len(lines) +  padding

    # Calculate the position of the background rectangle
    box_position = ((target_size[0] - draw.textsize(lines[0], font=font)
                    [0]) // 2 - padding, target_size[1] - box_height - padding)

    # Calculate the width of the background rectangle
    box_width = draw.textsize(lines[0], font=font)[0] + 2 * padding

    # Draw a rectangle with the specified background color and alpha
    draw.rectangle(
        (box_position, (box_position[0] + box_width, box_position[1] + box_height)), fill=background)

    # Calculate the starting y-position for drawing the text
    start_y = box_position[1] + padding

    # Draw the text on the overlay image
    for line in lines:
        text_width, text_height = draw.textsize(line, font=font)
        text_position = ((target_size[0] - text_width) // 2, start_y)
        print(line, text_position)
        draw.text(text_position, line, font=font, fill=text_color)
        start_y += text_height + padding

    # Paste the overlay image onto the original image using alpha composite
    image = Image.alpha_composite(image, overlay)

    # Convert the image back to RGB mode
    image = image.convert("RGB")

    # Save the resulting image
    image.save(image_path)


# # 示例用法
# text = "这是一段测试字幕。这段字幕可能会比较长，需要换行显示。如果字幕文本的宽度超过了目标图像的宽度，将会自动换行显示，并确保整体居中。"
# image_path = "images/1686290882-anything-v4.0.png"
# text_color = (255, 255, 255)  # 白色字体
# background = (0, 0, 0, 128)  # 半透明黑色底部浮层
# padding = 10
# target_size = (640, 480)
# font_path = "fonts/Hiragino Sans GB.ttc"
# font_size = 16

# add_text_to_image(text, image_path, text_color, background,
#                   padding, target_size, font_path, font_size)
