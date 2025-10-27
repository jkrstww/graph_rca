from flask import Flask, session, request, jsonify
from flask_cors import CORS
import uuid
from datetime import timedelta
from graph import FaultAnalyseAgent
import os
from werkzeug.utils import secure_filename
from config import PROJECT_ROOT

active_agents = {}

app = Flask(__name__)
CORS(app)  # 这将允许所有域的所有路由跨域请求
app.permanent_session_lifetime = timedelta(hours=1)  # 会话有效期

@app.route('/test', methods=['GET'])
def test():
    print('success')

    return jsonify({
        "status": "success"
    })

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json() or {}

    # 获取或创建用户ID
    user_id = data.get('user_id')
    session['user_id'] = user_id

    agent_id = str(uuid.uuid4())
    session['agent_id'] = agent_id

    # 创建新的实例
    agent = FaultAnalyseAgent(session_id=str(agent_id), user_id=user_id)

    # 存储Agent引用
    active_agents[agent.id] = agent

    return jsonify({
        "success": True,
        "message": "Agent started successfully",
    })


@app.route('/action/<action_name>', methods=['POST'])
def perform_action(action_name):
    # 从会话中获取agent_id
    agent_id = session.get('session_id')
    user_id = session.get('user_id')
    if not agent_id:
        return jsonify({"error": "No active agent. Please visit /start first."}), 400
    
    # 从全局存储中获取Agent实例
    agent = active_agents.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found. It may have expired."}), 404
    # 获取请求参数
    parameters = request.get_json() or {}
    parameters.update(user_id=user_id)
    print("parameters:" + str(parameters))

    # 执行操作
    try:
        if action_name == 'chat':
            from sse_starlette.sse import EventSourceResponse
            return EventSourceResponse(agent.perform_action('chat', parameters))
        else:
            result = agent.perform_action(action_name, parameters)
            response = {}
            response.update(result)

            return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/status')
def get_status():
    agent_id = session.get('session_id')
    if not agent_id:
        return jsonify({"error": "No active agent"}), 400

    agent = active_agents.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify({
        "session_id": agent.id,
        "user_id": agent.user_id,
        "state": agent.state
    })

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(PROJECT_ROOT, '/temp', filename)
        file.save(file_path)
        return jsonify({
            'message': '文件上传成功', 
            'filename': filename
        }), 200
    
    return jsonify({'error': '文件类型不允许'}), 400

@app.route('/end')
def end_session():
    agent_id = session.get('agent_id')
    if agent_id and agent_id in active_agents:
        # 清理Agent实例
        del active_agents[agent_id]

    # 清除会话
    session.clear()
    return jsonify({"message": "Session ended successfully"})


# 定期清理过期Agent的函数（可选）
def cleanup_expired_agents():
    # 这里可以实现清理逻辑，例如基于最后访问时间
    pass


if __name__ == '__main__':
    app.run(debug=True, port=5007)

