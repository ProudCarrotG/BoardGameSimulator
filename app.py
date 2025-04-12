from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")  # 添加CORS支持

# 全局游戏状态
players = {}
roles = ['平民']
cards = ['村民', '狼人', '预言家']
discard_pile = []  # 弃牌堆
custom_roles = ['平民']  # 默认身份
custom_cards = ['村民', '狼人', '预言家']  # 默认手牌

# 弃牌逻辑
@app.route('/discard', methods=['POST'])
def discard_card():
    player_name = request.form.get('player_name')
    card_index = int(request.form.get('card_index'))
    
    if player_name not in players:
        return jsonify({'error': '玩家不存在'}), 400
    
    try:
        # 从玩家手牌移到弃牌堆
        discarded = players[player_name]['hand'].pop(card_index)
        discard_pile.append(discarded)
        
        # 通知所有玩家更新弃牌堆
        socketio.emit('discard_update', {
            'player': player_name,
            'discarded': discarded,
            'pile_size': len(discard_pile)
        })
        
        return jsonify({
            'new_hand': players[player_name]['hand'],
            'discarded': discarded
        })
    
    except IndexError:
        return jsonify({'error': '无效的手牌位置'}), 400

# 获取当前身份卡配置
@app.route('/get_card_config', methods=['GET'])
def get_card_config():
    return jsonify({
        'roles': custom_roles,
        'cards': custom_cards
    })

# 更新身份卡配置
@app.route('/update_card_config', methods=['POST'])
def update_card_config():
    global custom_roles, custom_cards
    
    try:
        data = request.get_json()
        custom_roles = data.get('roles', custom_roles)
        custom_cards = data.get('cards', custom_cards)
        
        # 更新游戏实际使用的牌组
        global roles, cards
        roles = custom_roles.copy()
        cards = custom_cards.copy()
        
        return jsonify({'status': '配置已更新'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# 查询玩家数量的接口
@app.route('/players')
def get_players():
    return jsonify({'players': len(players)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join_game():
    player_name = request.form.get('player_name')
    
    if not player_name:
        return jsonify({'error': '请输入名字'}), 400
    
    # 查询已使用的身份牌
    used_role = [player['role'] for player in players.values()]
    # 计算可用的身份牌
    available_roles = [role for role in roles if role not in used_role]
    # 如果可用身份牌为0
    if not available_roles:
        available_roles.append('观众')

    # 查询已使用的手牌
    used_hand = []
    for player in players.values():
        for hand in player['hand']:
            used_hand.append(hand)
    # 计算可用的手牌
    available_hands = [hand for hand in cards if hand not in used_hand]
    # 如果可用手牌为0
    if not available_hands:
        available_hands.append('空')

    # 随机选择身份牌和手牌
    if player_name not in players:
        players[player_name] = {
            'role': random.choice(available_roles),
            'hand': [random.choice(available_hands) for _ in range(3)],
            'joined_at': datetime.now().strftime('%H:%M:%S')
        }
        # 通知所有客户端更新玩家列表
        socketio.emit('players_updated', {
            'players': [{
                'name': name,
                'joined_at': data['joined_at']
            } for name, data in players.items()]
        })
    
    return jsonify({
        'name': player_name,
        'role': players[player_name]['role'],
        'hand': players[player_name]['hand']
    })

@app.route('/reset', methods=['POST'])
def reset_game():
    players.clear()
    socketio.emit('game_reset', {})
    socketio.emit('players_updated', {'players': []})
    return jsonify({'status': '游戏已重置'})

@socketio.on('connect')
def handle_connect():
    print(f'客户端已连接: {request.sid}')
    emit('players_updated', {
        'players': [{
            'name': name,
            'joined_at': data['joined_at']
        } for name, data in players.items()]
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'客户端已断开: {request.sid}')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')