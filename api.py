from flask import Flask, session, request, jsonify
from flask_cors import CORS
import uuid
from datetime import timedelta
from graph import FaultAnalyseAgent

active_agents = {}

app = Flask(__name__)
CORS(app)  # 这将允许所有域的所有路由跨域请求
app.permanent_session_lifetime = timedelta(hours=1)  # 会话有效期

agent = FaultAnalyseAgent('0001')
user_id = '0001'


@app.route('/start')
def start():
    # 获取或创建用户ID
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id

    # 创建新的实例
    agent = FaultAnalyseAgent(user_id)

    # 存储Agent引用
    active_agents[agent.id] = agent
    session['agent_id'] = agent.id

    return jsonify({
        "message": "Agent started successfully",
        "agent_id": agent.id,
        "user_id": user_id
    })


@app.route('/action/<action_name>', methods=['POST'])
def perform_action(action_name):
    # 从会话中获取agent_id
    # agent_id = session.get('agent_id')
    # user_id = session.get('user_id')
    # if not agent_id:
    #     return jsonify({"error": "No active agent. Please visit /start first."}), 400
    #
    # # 从全局存储中获取Agent实例
    # agent = active_agents.get(agent_id)
    # if not agent:
    #     return jsonify({"error": "Agent not found. It may have expired."}), 404
    # 获取请求参数
    parameters = request.get_json() or {}
    print("parameters:" + str(parameters))

    # 执行操作
    try:
        result = agent.perform_action(action_name, parameters)
        return jsonify({
            # "agent_id": agent.id,
            # "user_id": user_id
        }.update(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/status')
def get_status():
    agent_id = session.get('agent_id')
    if not agent_id:
        return jsonify({"error": "No active agent"}), 400

    agent = active_agents.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    return jsonify({
        "agent_id": agent.id,
        "user_id": agent.user_id,
        "state": agent.state
    })


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
    app.run(debug=True)

