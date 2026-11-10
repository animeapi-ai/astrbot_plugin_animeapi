KEYS_URL = "https://animeapi.ai/dashboard/api-keys"
BILLING_URL = "https://animeapi.ai/dashboard/billing"

MESSAGES = {
    "en": {
        "no_prompt": "Tell me what to draw, for example: /anime a girl with a red umbrella",
        "too_long": "That prompt is too long. Keep it under 1000 characters.",
        "cooldown": "Please wait {seconds}s before generating another image.",
        "busy_user": "Your previous image is still being drawn.",
        "no_key": f"AnimeAPI is not set up yet. The bot owner needs to add an API key in the plugin settings (get a key at {KEYS_URL}).",
        "invalid_key": f"The bot's AnimeAPI key was not accepted. The bot owner should check it at {KEYS_URL}",
        "no_balance": f"The bot's AnimeAPI balance is empty. The bot owner can add funds at {BILLING_URL}",
        "rejected": "The image was rejected: {reason}",
        "busy": "AnimeAPI is busy right now. Try again in a few seconds.",
        "failed": "Image generation failed: {reason}",
        "network": "Could not reach AnimeAPI. Try again later.",
        "bad_model": "Unknown model. Use anime, ultra or ultra-max.",
        "bad_orientation": "Unknown orientation. Use portrait, square or landscape.",
        "model_locked": "Only the default model is enabled on this bot.",
    },
    "zh": {
        "no_prompt": "请告诉我要画什么，例如：/anime 打着红伞的女孩",
        "too_long": "提示词太长了，请控制在 1000 个字符以内。",
        "cooldown": "请等待 {seconds} 秒后再生成。",
        "busy_user": "你的上一张图还在绘制中。",
        "no_key": f"尚未配置 AnimeAPI。请机器人管理员在插件配置中填写 API 密钥（在 {KEYS_URL} 获取密钥）。",
        "invalid_key": f"机器人的 AnimeAPI 密钥无效，请管理员在 {KEYS_URL} 检查。",
        "no_balance": f"机器人的 AnimeAPI 余额不足，管理员可在 {BILLING_URL} 充值。",
        "rejected": "图片被拒绝：{reason}",
        "busy": "AnimeAPI 当前繁忙，请稍后重试。",
        "failed": "图片生成失败：{reason}",
        "network": "无法连接 AnimeAPI，请稍后重试。",
        "bad_model": "未知模型，可选 anime、ultra、ultra-max。",
        "bad_orientation": "未知画幅，可选 portrait、square、landscape。",
        "model_locked": "此机器人只启用了默认模型。",
    },
    "ja": {
        "no_prompt": "何を描くか教えてください。例：/anime 赤い傘の少女",
        "too_long": "プロンプトが長すぎます。1000 文字以内にしてください。",
        "cooldown": "次の生成まで {seconds} 秒お待ちください。",
        "busy_user": "前の画像をまだ描いています。",
        "no_key": f"AnimeAPI が未設定です。ボットの管理者がプラグイン設定で API キーを入力してください（キーは {KEYS_URL} で取得）。",
        "invalid_key": f"ボットの AnimeAPI キーが無効です。管理者は {KEYS_URL} で確認してください。",
        "no_balance": f"ボットの AnimeAPI 残高がありません。管理者は {BILLING_URL} でチャージできます。",
        "rejected": "画像が拒否されました：{reason}",
        "busy": "AnimeAPI が混雑しています。数秒後にもう一度お試しください。",
        "failed": "画像生成に失敗しました：{reason}",
        "network": "AnimeAPI に接続できません。しばらくしてからお試しください。",
        "bad_model": "不明なモデルです。anime、ultra、ultra-max から選んでください。",
        "bad_orientation": "不明な向きです。portrait、square、landscape から選んでください。",
        "model_locked": "このボットでは既定のモデルのみ利用できます。",
    },
}


def text(language: str, key: str, **kwargs: object) -> str:
    table = MESSAGES.get(language, MESSAGES["en"])
    return table.get(key, MESSAGES["en"][key]).format(**kwargs)
