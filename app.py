from flask import Flask, request, render_template, jsonify, send_from_directory

from text_to_video import convertTextToVideo

from configs import models

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text_to_video():
    # 获取请求中的文本数据
    text = request.form.get('text')
    model = request.form.get('model')
    # 在此处调用您的文本转视频的代码，并生成视频文件
    # videos/1686290882-anything-v4.0.mp4
    video_path = convertTextToVideo(validate_model(model), text)
    return jsonify({'video_path': video_path})


@app.route('/models', methods=['GET'])
def get_available_models():
    return jsonify(models)

@app.route('/videos/<path:filename>')
def get_video(filename):
    return send_from_directory('videos', filename)

def validate_model(model):
    if model in models:
        return model
    else:
        return models[0]




if __name__ == '__main__':
    app.run()
