from flask import Flask, session, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import uuid
from datetime import timedelta
from graph import FaultAnalyseAgent
import os
from werkzeug.utils import secure_filename
from config import PROJECT_ROOT, REFERENCE_PATH
from datetime import datetime

import json
import time
import random
os.environ["CUDA_VISIBLE_DEVICES"] = "4" 
AGENT_TIMEOUT_HOURS = 2

active_agents = {}

app = Flask(__name__)
CORS(app)  # 这将允许所有域的所有路由跨域请求
app.permanent_session_lifetime = timedelta(hours=1)  # 会话有效期

app.secret_key = os.urandom(24)  # 生成24字节的随机密钥

def lazy_cleanup():
    """
    惰性清理：在访问Agent时顺便检查并清理过期Agent
    这种方法资源消耗小，但不能保证及时清理
    """
    current_time = datetime.now()
    expired_agents = []
    
    for agent_id, agent in list(active_agents.items()):
        time_since_last_activity = current_time - agent.last_activity
        if time_since_last_activity > timedelta(hours=AGENT_TIMEOUT_HOURS):
            expired_agents.append(agent_id)
    
    for agent_id in expired_agents:
        try:
            active_agents[agent_id].cleanup()
        except Exception as e:
            print(f"清理Agent {agent_id} 资源时出错: {e}")
        finally:
            del active_agents[agent_id]
    
    return len(expired_agents)

@app.route('/test', methods=['GET'])
def test():
    print('success')

    return jsonify({
        "status": "success"
    })

@app.route('/start', methods=['POST'])
def start():
    cleaned_count = lazy_cleanup()
    if cleaned_count > 0:
        print(f"惰性清理了 {cleaned_count} 个过期Agent")
        
    data = request.get_json() or {}

    # 创建文件类型标记，主要是为了在智能对话时确认上传的文件
    session['file_type'] = 'none'
    session['file_path'] = ''

    # 获取或创建用户ID
    user_id = data.get('user_id')
    session['user_id'] = user_id

    agent_id = str(uuid.uuid4())
    session['agent_id'] = agent_id
    session['session_id'] = agent_id

    # 创建新的实例
    agent = FaultAnalyseAgent(session_id=str(agent_id), user_id=str(user_id))

    # 存储Agent引用
    active_agents[agent.id] = agent

    return jsonify({
        "success": True,
        "message": "Agent started successfully",
    })

def generator():
    """模拟股票价格生成器"""
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    prices = {symbol: round(random.uniform(100, 500), 2) for symbol in symbols}
    
    while True:
        # 更新价格
        symbol = random.choice(symbols)
        change = random.uniform(-5, 5)
        prices[symbol] = max(0.01, prices[symbol] + change)

        print(symbol)
        
        yield f"data: {json.dumps({
            'symbol': symbol,
            'price': round(prices[symbol], 2),
            'change': round(change, 2),
            'timestamp': time.time()
        })}\n\n"
        
        time.sleep(0.5)  # 每0.5秒更新一次

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

    # 执行操作
    try:
        if action_name == 'chat':
            upload_file_name = parameters['filename'] if 'filename' in parameters else ''
            upload_file_path = os.path.join(PROJECT_ROOT, 'temp', upload_file_name) if upload_file_name else ''

            if upload_file_name != '':
                file_ext = os.path.splitext(upload_file_name)[1].lower()
                if file_ext in ['.txt', '.pdf', '.docx', '.doc']:
                    upload_file_type = 'document'
                elif file_ext in ['.png', '.jpg', '.jpeg']:
                    upload_file_type = 'image'  
            else:
                upload_file_type = 'none'

            return Response(
                agent.chat_agent.chat(query=parameters['query'], user_id=user_id, upload_file_path=upload_file_path, upload_file_type=upload_file_type),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
                }
            )
            from sse_starlette.sse import EventSourceResponse
            return EventSourceResponse(agent.chat_agent.chat(query=parameters['query'], user_id=user_id))
        elif action_name == 'read_files':
            try:
                print('ssss')
                filename = parameters['filename']
                print(filename)
                file_path = os.path.join(REFERENCE_PATH, filename)
                print(file_path)
                
                # 安全检查：防止路径遍历攻击
                if not os.path.abspath(file_path).startswith(os.path.abspath(REFERENCE_PATH)):
                    return jsonify({'error': '非法文件路径'}), 403
                    
                if not os.path.exists(file_path):
                    return jsonify({'error': '文件不存在'}), 404
                    
                return send_from_directory(
                    REFERENCE_PATH, 
                    filename,
                    as_attachment=False  # True 表示下载，False 表示预览
                )
            except Exception as e:
                return jsonify({'error': str(e)}), 500
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
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc'}

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
        # filename = secure_filename(str(file.filename))
        filename = secure_filename(f"{str(uuid.uuid4())}_{file.filename}")

        file_path = os.path.join(PROJECT_ROOT, 'temp', filename)
        file.save(file_path)
        return jsonify({
            'message': '文件上传成功', 
            'filename': filename
        }), 200
    
    return jsonify({'error': '文件类型不允许'}), 400

@app.route('/upload_reference', methods=['POST'])
def upload_reference_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        # filename = file.filename

        file_path = os.path.join(PROJECT_ROOT, 'static', 'references', filename)
        file.save(file_path)
        return jsonify({
            'message': '文件上传成功', 
            'filename': filename
        }), 200
    
    return jsonify({'error': '文件类型不允许'}), 400

# --- 1. 删除文件的接口 ---
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    删除指定文件
    URL示例: DELETE /delete/b4d6a5-example.pdf
    """
    # 再次使用 secure_filename 防止路径遍历攻击 (如 ../../etc/passwd)
    safe_filename = filename
    file_path = os.path.join(PROJECT_ROOT, 'static', 'references', safe_filename)

    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    try:
        os.remove(file_path)
        return jsonify({
            'message': '文件删除成功',
            'filename': safe_filename
        }), 200
    except Exception as e:
        # 捕获权限错误或其他IO错误
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


# --- 2. 查找/获取文件列表接口 (支持简单的关键词搜索) ---
@app.route('/files', methods=['GET'])
def list_files():
    """
    列出所有文件，或根据关键词搜索文件
    URL示例: 
    - 获取所有: GET /files
    - 搜索: GET /files?q=machine_learning
    """
    upload_dir = os.path.join(PROJECT_ROOT, 'static', 'references')
    
    # 确保目录存在，否则列表为空
    if not os.path.exists(upload_dir):
        return jsonify({'files': [], 'count': 0}), 200

    try:
        all_files = os.listdir(upload_dir)
        
        # 获取搜索关键词
        query = request.args.get('q', '').lower()
        
        # 如果有搜索词，进行过滤；否则返回全部
        if query:
            filtered_files = [f for f in all_files if query in f.lower()]
        else:
            filtered_files = all_files

        # 简单的排序，例如按修改时间倒序（最新的在前）
        filtered_files.sort(key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), reverse=True)

        return jsonify({
            'files': filtered_files,
            'count': len(filtered_files)
        }), 200
    except Exception as e:
        return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500


# --- 3. (可选) 下载/预览单个文件的接口 ---
@app.route('/files/<filename>', methods=['GET'])
def get_file(filename):
    """
    下载或预览文件内容
    URL示例: GET /files/uuid_example.pdf
    """
    upload_dir = os.path.join(PROJECT_ROOT, 'static', 'references')
    try:
        # as_attachment=True 会触发下载，False 则尝试在浏览器显示(如PDF/图片)
        return send_from_directory(upload_dir, filename, as_attachment=False)
    except FileNotFoundError:
        return jsonify({'error': '文件未找到'}), 404

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

