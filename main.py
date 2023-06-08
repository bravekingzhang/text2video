import time
import requests
import json
import cv2
import os
import textwrap
from dotenv import load_dotenv
import numpy as np

models = ["stabilityai/stable-diffusion-2-1", "andite/anything-v4.0"]

# 尝试加载线上环境变量文件
load_dotenv('.env', override=True)

# 尝试加载本地开发环境变量文件
load_dotenv('.local.env', override=True)

# 读取环境变量
api_token = os.getenv('API_TOKEN')
pause_duration = 1

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
def generateImage(model, prompt):
    body = {
        "inputs": prompt
    }
    r = requests.post("https://api-inference.huggingface.co/models/" + model,
                      data=json.dumps(body), headers=headers)
    # 将图片写入到 images 目录下，每个图片使用(时间戳+model).png 来命名
    imagePath = "images/" + str(int(time.time())) + \
        "-" + model.split("/")[-1] + ".png"
    with open(imagePath, "wb") as f:
        f.write(r.content)
        f.close()


def clear_folder(folder_path):
    """清空指定文件夹中的文件"""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def add_text_to_image(image, text, position, font, font_scale, color, thickness, background_color=None, background_alpha=0):
    image_height, image_width, _ = image.shape

    # 获取文本的宽度和高度
    (text_width, text_height), _ = cv2.getTextSize(
        text, font, font_scale, thickness)

    # 计算文本绘制的位置
    x, y = position
    x = max(0, min(x, image_width - text_width))
    y = max(0, min(y, image_height - text_height))

    # 绘制带有背景色的矩形
    if background_color is not None and background_alpha > 0:
        rectangle_position = (x, y)
        rectangle_size = (text_width, text_height)
        background_color = tuple(background_color)  # 将颜色值转换为元组形式
        alpha = int(background_alpha * 255)  # 将透明度转换为合适的范围
        overlay = np.ones((text_height, text_width, 3),
                          dtype=np.uint8) * background_color
        overlay = cv2.addWeighted(overlay, alpha, np.zeros_like(
            overlay), 1 - alpha, 0)
        image_roi = image[y:y+text_height, x:x+text_width]
        image_roi = image_roi.astype(float)
        overlay = overlay.astype(float)
        image_roi = cv2.addWeighted(image_roi, 1.0, overlay, 1.0, 0.0)
        image[y:y+text_height, x:x+text_width] = image_roi.astype(image.dtype)

    # 绘制文本
    cv2.putText(image, text, (x, y + text_height - thickness),
                font, font_scale, color, thickness, cv2.LINE_AA)

    return image


def convertTextToVideo(model, text):

    # 将文本段落进行分句
    sentences = text.split('.')

    # 清空 images 文件夹
    clear_folder("images")

    # 为每个句子生成图片
    for sentence in sentences:
        if sentence.strip() != "":
            generateImage(model, sentence.strip())

    # 合成视频
    frame_width = 640
    frame_height = 480
    output_video = "videos/" + str(int(time.time())) + \
        "-" + model.split("/")[-1] + ".mp4"
    output_video = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(
        *'mp4v'), 30, (frame_width, frame_height))

    image_files = os.listdir('images')
    image_files.sort()

    for image_file in image_files:
        if image_file.endswith(".png"):
            image = cv2.imread(f"images/{image_file}")
            resized_image = cv2.resize(image, (frame_width, frame_height))

            # 添加透明度背景和文字
            y_offset = frame_height - 60  # 文字起始纵坐标
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            text_color = (255, 255, 255)  # 白色文字
            background_color = (0, 0, 0)  # 黑色背景
            background_alpha = 0.5  # 背景透明度

            for line in textwrap.wrap(sentences[image_files.index(image_file)], width=80):
                text_position = (10, y_offset)
                resized_image = add_text_to_image(resized_image, line, text_position, font,
                                                  font_scale, text_color, font_thickness, background_color, background_alpha)
                y_offset += 30  # 调整下一行文字的偏移量

            output_video.write(resized_image)
            # 添加停顿帧
            for _ in range(int(pause_duration * 30)):
                output_video.write(resized_image)

    output_video.release()



if __name__ == '__main__':
    convertTextToVideo(models[0], "One morning,while I was brushing my teeth. suddenly, my puppy ran over and yelled at me. At this time, I heard the sound of a fire truck outside and thought. I thought to myself, it can’t be such a coincidence")
