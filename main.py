import time
import requests
import json
import cv2
import os
import textwrap
from dotenv import load_dotenv
import numpy as np
import subprocess
import re

from add_text_to_image import add_text_to_image

models = ["stabilityai/stable-diffusion-2-1", "andite/anything-v4.0"]

# 尝试加载线上环境变量文件
load_dotenv('.env', override=True)

# 尝试加载本地开发环境变量文件
load_dotenv('.local.env', override=True)

# 获取当前脚本所在的目录
current_directory = os.getcwd()

# 读取环境变量
api_token = os.getenv('API_TOKEN')

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
    timeStamp = str(int(time.time()))
    imagePath = "images/" + timeStamp + \
        "-" + model.split("/")[-1] + ".png"
    with open(imagePath, "wb") as f:
        f.write(r.content)
        f.close()
    voicePath = "voices/" + timeStamp + \
        "-" + model.split("/")[-1] + ".mp3"
    convert_text_to_speech(
        text=prompt, output_file=voicePath
    )


def convert_text_to_speech(text, output_file):
        # 指定输出目录
    output_directory = os.path.join(current_directory,"voices")
    # 创建输出目录（如果不存在）
    os.makedirs(output_directory, exist_ok=True)
    # 执行命令，并将工作目录设置为输出目录
    try:
        command = ['edge-tts', '--voice', 'zh-CN-XiaoyiNeural', '--text', text, '--write-media', output_file, '--write-subtitles', f'{output_file}.vtt']
        result = subprocess.run(command, cwd=current_directory, timeout=10)
        print(result)
        duration = get_duration_from_vtt(output_file + ".vtt")
        # 删除 无效音频 or 重新生成？
        if duration == 0.1:
            os.remove(output_file + ".vtt")
            os.remove(output_file)

    except subprocess.CalledProcessError as e:
        print("Command execution failed with return code:", e.returncode)
        print("Command output:", e.output)

def clear_folder(folder_path):
    """清空指定文件夹中的文件"""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)





def split_sentences(text):
    pattern = r'[,.，。]'
    sentences = re.split(pattern, text)
    # 移除空白的句子
    sentences = [sentence.strip()
                 for sentence in sentences if sentence.strip()]
    return sentences
def convertTextToVideo(model, text):

    # 将文本段落进行分句
    sentences = split_sentences(text)

    # 清空 images 文件夹
    clear_folder("images")
    # 清空 voices 文件夹
    clear_folder("voices")

    # 为每个句子生成图片
    for sentence in sentences:
        if sentence.strip() != "":
            generateImage(model, sentence.strip())

    # 合成视频
    frame_width = 640
    frame_height = 480
    timeStamp = str(int(time.time()))
    output_video_path = "videos/" + timeStamp + \
        "-" + model.split("/")[-1] + ".mp4"
    output_video = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(
        *'mp4v'), 30, (frame_width, frame_height))

    image_files = os.listdir('images')
    image_files.sort()

    for image_file in image_files:
        if image_file.endswith(".png"):

            text_color = (255, 255, 255)  # 白色文字
            background = (0, 0, 0,128)  # 黑色背景半透明
            image_path = "images/" + image_file
            draw_text = sentences[image_files.index(image_file)]
            add_text_to_image(draw_text, image_path,
                              text_color, background, padding=10)
            image = cv2.imread(image_path)
            resized_image = cv2.resize(image, (frame_width, frame_height))
            output_video.write(resized_image)
            # 添加停顿帧
            duration = get_duration_from_vtt(
                f"voices/{find_file_name_without_extension(image_file)}.mp3.vtt")
            print(duration)
            for _ in range(int(duration * 30)):
                output_video.write(resized_image)

    output_video.release()
    desc_output_video_path = "videos/" + timeStamp + \
        "-" + model.split("/")[-1] + ".withAudio.mp4"

    merge_audio_to_video("voices", output_video_path,
                         desc_output_video_path)

def find_file_name_without_extension(file_path):
    file_name = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name)[0]
    return file_name_without_extension
def merge_audio_to_video(audio_directory, video_file, output_file):
    # 获取目录中的音频文件
    audio_files = [file for file in os.listdir(
        audio_directory) if file.endswith('.mp3')]

    if not audio_files:
        print("No audio files found in the directory.")
        return
    audio_files.sort()
    # 生成FFmpeg命令
    command = [
        'ffmpeg',
        '-i',
        video_file,
    ]

    # 添加音频文件参数
    for audio_file in audio_files:
        command.extend(['-i', audio_directory+'/'+audio_file])

    # 设置音频合并选项
    command.extend([
        '-filter_complex',
        ''.join([f'[{i+1}:0]' for i in range(len(audio_files))]) +
        f'concat=n={len(audio_files)}:v=0:a=1[outa]',
        '-map',
        '0:v',
        '-map',
        '[outa]',
        '-c:v',
        'copy',
        '-c:a',
        'aac',
        '-shortest',
        output_file
    ])

    # 执行FFmpeg命令
    result = subprocess.run(command,cwd=current_directory, timeout=300)
    print(result)

def get_duration_from_vtt(vtt_file):
    print(vtt_file)
    if not os.path.exists(vtt_file):
        return 0.1
    with open(vtt_file, 'r') as file:
        lines = file.readlines()

    total_duration = 0.1

    for line in lines:
        line = line.strip()
        if '-->' in line:
            start_time, end_time = line.split('-->')
            start_time = start_time.strip()
            end_time = end_time.strip()
            start_seconds = convert_time_to_seconds(start_time)
            end_seconds = convert_time_to_seconds(end_time)
            duration = end_seconds - start_seconds
            total_duration += duration

    return total_duration


def convert_time_to_seconds(time):
    hours, minutes, seconds = time.split(':')
    seconds, milliseconds = seconds.split('.')
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    total_seconds = (hours * 3600) + (minutes * 60) + \
        seconds + (milliseconds / 1000)
    return total_seconds


if __name__ == '__main__':
    # convert_text_to_speech("are you ok","hello1.mp3")
    convertTextToVideo(models[1], "我骑着自行车去上学碰到一条小狗在路边狂叫顿时我就火冒三丈想过去打死他可是她不跑我能怎么办呢很烦啊，我就慌了，我就骑着自行车走了")
