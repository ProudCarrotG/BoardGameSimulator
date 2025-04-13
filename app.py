from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")  # 添加CORS支持

# 全局游戏状态
players = {}
roles = ["红1", "红2", "蓝1", "蓝2", "X"]
cards = [
    "上忍1",
    "上忍2",
    "上忍3",
    "上忍4",
    "上忍5",
    "上忍6",
    "密探1",
    "密探2",
    "密探3",
    "密探4",
    "密探5",
    "密探6",
    "隐士1",
    "隐士2",
    "隐士3",
    "隐士4",
    "隐士5",
    "隐士6",
    "盲眼刺客1",
    "盲眼刺客2",
    "盲眼刺客3",
    "盲眼刺客4",
    "盲眼刺客5",
    "盲眼刺客6",
    "百变者(骗徒1)",
    "掘墓人(骗徒2)",
    "捣蛋鬼(骗徒3)",
    "灵魂商贩(骗徒4)",
    "窃贼(骗徒5)",
    "裁判(骗徒6)",
    "还诗僧",
    "殉道者",
    "首脑",
]
discard_pile = []  # 弃牌堆
custom_roles = ["红1", "红2", "蓝1", "蓝2", "X"]  # 默认身份
custom_cards = [
    "上忍1",
    "上忍2",
    "上忍3",
    "上忍4",
    "上忍5",
    "上忍6",
    "密探1",
    "密探2",
    "密探3",
    "密探4",
    "密探5",
    "密探6",
    "隐士1",
    "隐士2",
    "隐士3",
    "隐士4",
    "隐士5",
    "隐士6",
    "盲眼刺客1",
    "盲眼刺客2",
    "盲眼刺客3",
    "盲眼刺客4",
    "盲眼刺客5",
    "盲眼刺客6",
    "百变者(骗徒1)",
    "掘墓人(骗徒2)",
    "捣蛋鬼(骗徒3)",
    "灵魂商贩(骗徒4)",
    "窃贼(骗徒5)",
    "裁判(骗徒6)",
    "还诗僧",
    "殉道者",
    "首脑",
]  # 默认手牌
custom_cardNumber = 3  # 默认手牌数量


# 获取弃牌堆当前状态
@app.route("/get_discard_pile", methods=["GET"])
def get_discard_pile():
    return jsonify({"discard_pile": discard_pile, "size": len(discard_pile)})

# 获取玩家手牌当前状态
@app.route("/get_player_hand", methods=["POST"])
def get_player_hand():
    player_name = request.form.get("player_name")
    if player_name not in players:
        return jsonify({"error": "玩家不存在"}), 400
    return jsonify({"hand": players[player_name]["hand"]})

# 获取玩家身份当前状态
@app.route("/get_player_role", methods=["POST"])
def get_player_role():
    player_name = request.form.get("player_name")
    if player_name not in players:
        return jsonify({"error": "玩家不存在"}), 400
    return jsonify({"role": players[player_name]["role"]})

# 更新信号
def update_emit():
    socketio.emit("game_update", {})


# 从弃牌堆拿牌
@app.route("/draw_from_discard", methods=["POST"])
def draw_from_discard():
    player_name = request.form.get("player_name")
    card_index = request.form.get("card_index")  # 指定位置（可选）

    if not discard_pile:
        return jsonify({"error": "弃牌堆为空"}), 400

    # 随机或指定拿牌
    if card_index is None:
        # 随机拿牌
        card = random.choice(discard_pile)
        discard_pile.remove(card)
    else:
        # 指定位置拿牌
        try:
            card_index = int(card_index)
            card = discard_pile.pop(card_index)
        except (IndexError, ValueError):
            return jsonify({"error": "无效的牌位置"}), 400

    # 将牌加入玩家手牌
    players[player_name]["hand"].append(card)

    # 通知所有玩家更新弃牌堆
    update_emit()

    return jsonify(
        {
            "drawn_card": card,
            "new_hand": players[player_name]["hand"],
            "remaining_discard": len(discard_pile),
        }
    )


# 弃牌逻辑
@app.route("/discard", methods=["POST"])
def discard_card():
    player_name = request.form.get("player_name")
    card_index = int(request.form.get("card_index"))

    if player_name not in players:
        return jsonify({"error": "玩家不存在"}), 400

    try:
        # 从玩家手牌移到弃牌堆
        discarded = players[player_name]["hand"].pop(card_index)
        discard_pile.append(discarded)

        # 通知所有玩家更新弃牌堆
        update_emit()

        return jsonify(
            {"new_hand": players[player_name]["hand"], "discarded": discarded}
        )

    except IndexError:
        return jsonify({"error": "无效的手牌位置"}), 400


# 获取当前身份卡配置
@app.route("/get_card_config", methods=["GET"])
def get_card_config():
    return jsonify({"roles": custom_roles, "cards": custom_cards})


# 更新身份卡配置
@app.route("/update_card_config", methods=["POST"])
def update_card_config():
    global custom_roles, custom_cards

    try:
        data = request.get_json()
        custom_roles = data.get("roles", custom_roles)
        custom_cards = data.get("cards", custom_cards)

        # 更新游戏实际使用的牌组
        global roles, cards
        roles = custom_roles.copy()
        cards = custom_cards.copy()

        return jsonify({"status": "配置已更新"})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 查询玩家数量的接口
@app.route("/players")
def get_players():
    return jsonify({"players": len(players)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/join", methods=["POST"])
def join_game():
    player_name = request.form.get("player_name")

    if not player_name:
        return jsonify({"error": "请输入名字"}), 400

    # 查询已使用的身份牌
    used_role = [player["role"] for player in players.values()]
    # 计算可用的身份牌
    available_roles = [role for role in roles if role not in used_role]
    # 如果可用身份牌为0
    if not available_roles:
        available_roles.append("观众")

    player_hands = []
    for _ in range(custom_cardNumber):
        # 查询已使用的手牌
        used_hand = []
        for player in players.values():
            for hand in player["hand"]:
                used_hand.append(hand)
        for hand in player_hands:
            used_hand.append(hand)
        for card in discard_pile:
            used_hand.append(card)
        # 计算可用的手牌
        available_hands = [hand for hand in cards if hand not in used_hand]
        # 如果可用手牌为0
        if not available_hands:
            available_hands.append("空")
        player_hands.append(random.choice(available_hands))

    # 随机选择身份牌和手牌
    if player_name not in players:
        players[player_name] = {
            "role": random.choice(available_roles),
            "hand": player_hands,
            "joined_at": datetime.now().strftime("%H:%M:%S"),
        }
        # 通知所有客户端更新玩家列表
        socketio.emit(
            "players_updated",
            {
                "players": [
                    {"name": name, "joined_at": data["joined_at"]}
                    for name, data in players.items()
                ]
            },
        )

    return jsonify(
        {
            "name": player_name,
            "role": players[player_name]["role"],
            "hand": players[player_name]["hand"],
        }
    )


@app.route("/reset", methods=["POST"])
def reset_game():
    players.clear()
    discard_pile.clear()
    socketio.emit("game_reset", {})
    socketio.emit("players_updated", {"players": []})
    return jsonify({"status": "游戏已重置"})


@socketio.on("connect")
def handle_connect():
    print(f"客户端已连接: {request.sid}")
    emit(
        "players_updated",
        {
            "players": [
                {"name": name, "joined_at": data["joined_at"]}
                for name, data in players.items()
            ]
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    print(f"客户端已断开: {request.sid}")


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0")
