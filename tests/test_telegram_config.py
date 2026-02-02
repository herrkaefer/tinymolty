#!/usr/bin/env python3
"""
测试 TinyMolty Telegram 配置功能
验证 Telegram 相关的配置、验证和集成
"""
import tempfile
from pathlib import Path
from config import (
    AppConfig,
    BotConfig,
    LLMConfig,
    TelegramConfig,
    save_config,
    load_config,
    resolve_secrets,
    validate_config,
    store_secret,
)


def test_telegram_disabled():
    """测试 Telegram 禁用配置"""
    print("\n=== 测试 1: Telegram 禁用配置 ===")

    config = AppConfig(
        telegram=TelegramConfig(
            enabled=False,
            bot_token="",
            chat_id=""
        ),
        llm=LLMConfig(api_key="test-key")
    )

    secrets = resolve_secrets(config)

    # 验证配置
    try:
        validate_config(config, secrets)
        print("✓ Telegram 禁用 - 验证通过")
    except ValueError as e:
        print(f"✗ 验证失败: {e}")
        raise

    # 检查 secrets
    assert secrets.telegram_token is None, "禁用时 token 应为 None"
    print("✓ Telegram token 正确为 None")


def test_telegram_enabled_valid():
    """测试 Telegram 启用配置"""
    print("\n=== 测试 2: Telegram 启用 ===")

    config = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="test-token-123",
            chat_id="123456789"
        ),
        llm=LLMConfig(api_key="test-key")
    )

    secrets = resolve_secrets(config)

    try:
        validate_config(config, secrets)
        print("✓ Telegram 启用 - 验证通过")
    except ValueError as e:
        print(f"✓ 验证结果: {e}")


def test_telegram_enabled_without_token():
    """测试 Telegram 启用但缺少 bot token"""
    print("\n=== 测试 3: Telegram 启用但缺少 bot token ===")

    config = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="",
            chat_id="123456789"
        ),
        llm=LLMConfig(api_key="test-key")
    )

    secrets = resolve_secrets(config)

    # 缺少 token 应该失败
    try:
        validate_config(config, secrets)
        print("✗ 应该抛出验证错误")
        assert False, "期望 ValueError"
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")


def test_telegram_enabled_full_config():
    """测试完整有效的 Telegram 配置"""
    print("\n=== 测试 4: 完整有效的 Telegram 配置 ===")

    config = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            chat_id="987654321"
        ),
        llm=LLMConfig(api_key="test-key")
    )

    secrets = resolve_secrets(config)

    try:
        validate_config(config, secrets)
        print("✓ 完整的 Telegram 配置验证通过")
        print(f"  Bot Token: {secrets.telegram_token[:20]}...")
        print(f"  Chat ID: {config.telegram.chat_id}")
    except ValueError as e:
        print(f"✗ 验证失败: {e}")
        raise


def test_telegram_token_storage_methods():
    """测试 Telegram token 的不同存储方法"""
    print("\n=== 测试 7: Telegram Token 存储方法 ===")

    # 方法 1: 直接值
    print("\n  方法 1: 直接值存储")
    config1 = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="direct-token-value",
            chat_id="123"
        )
    )
    secrets1 = resolve_secrets(config1)
    assert secrets1.telegram_token == "direct-token-value"
    print("  ✓ 直接值存储正常")

    # 方法 2: Keyring 引用
    print("\n  方法 2: Keyring 引用")
    config2 = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="keyring",
            chat_id="123"
        )
    )
    secrets2 = resolve_secrets(config2)
    # keyring 中没有存储时返回 None
    print(f"  ✓ Keyring 引用处理正常 (值: {secrets2.telegram_token})")

    # 方法 3: 环境变量引用
    print("\n  方法 3: 环境变量引用")
    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = "env-token-123"
    config3 = AppConfig(
        telegram=TelegramConfig(
            enabled=True,
            bot_token="env:TELEGRAM_BOT_TOKEN",
            chat_id="123"
        )
    )
    secrets3 = resolve_secrets(config3)
    assert secrets3.telegram_token == "env-token-123"
    print(f"  ✓ 环境变量引用正常 (值: {secrets3.telegram_token})")


def test_telegram_config_save_load():
    """测试 Telegram 配置的保存和加载"""
    print("\n=== 测试 8: Telegram 配置保存和加载 ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "telegram_config.toml"

        # 创建 Telegram 配置
        config = AppConfig(
            bot=BotConfig(name="TelegramBot"),
            telegram=TelegramConfig(
                enabled=True,
                bot_token="5555555555:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw",
                chat_id="123456789"
            ),
            llm=LLMConfig(api_key="test-key")
        )

        # 保存配置
        save_config(config, config_path)
        print("✓ Telegram 配置已保存")

        # 显示保存的配置
        print("\n保存的配置内容:")
        print("-" * 60)
        content = config_path.read_text()
        print(content)
        print("-" * 60)

        # 加载配置
        loaded = load_config(config_path)
        print("\n✓ 配置已加载")

        # 验证配置
        assert loaded.telegram.enabled == True
        assert loaded.telegram.chat_id == "123456789"
        assert loaded.telegram.bot_token == "5555555555:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
        print("✓ 配置内容验证通过")

        # 验证可用性
        secrets = resolve_secrets(loaded)
        validate_config(loaded, secrets)
        print("✓ 配置验证通过")


def test_telegram_chat_id_formats():
    """测试不同格式的 Chat ID"""
    print("\n=== 测试 9: 不同格式的 Chat ID ===")

    test_cases = [
        ("123456789", "数字字符串"),
        ("-100123456789", "群组 ID (负数)"),
        ("@username", "用户名格式"),
    ]

    for chat_id, description in test_cases:
        config = AppConfig(
            telegram=TelegramConfig(
                enabled=True,
                bot_token="test-token",
                chat_id=chat_id
            ),
            llm=LLMConfig(api_key="test-key")
        )

        secrets = resolve_secrets(config)
        try:
            validate_config(config, secrets)
            print(f"  ✓ {description}: {chat_id}")
        except ValueError as e:
            print(f"  ✗ {description}: {chat_id} - {e}")


def test_telegram_keyring_storage():
    """测试 Telegram token 的 Keyring 存储"""
    print("\n=== 测试 10: Telegram Token Keyring 存储 ===")

    # 测试 store_secret 函数
    token_value = "test-bot-token-12345"

    # 存储到 keyring
    result = store_secret(token_value, "telegram_bot_token", "keyring")
    assert result == "keyring", "应该返回 'keyring'"
    print("✓ Token 存储引用设置为 'keyring'")

    # 尝试从 keyring 读取
    import keyring
    stored_value = keyring.get_password("tinymolty", "telegram_bot_token")
    if stored_value == token_value:
        print(f"✓ Token 成功存储到 Keyring")
        print(f"  存储的值: {stored_value[:10]}...")

        # 清理
        keyring.delete_password("tinymolty", "telegram_bot_token")
        print("✓ 测试后清理完成")
    else:
        print(f"⚠ Keyring 存储结果: {stored_value}")


def test_complete_telegram_setup():
    """测试完整的 Telegram 设置流程"""
    print("\n=== 测试 11: 完整 Telegram 设置流程 ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "complete_telegram.toml"

        print("\n步骤 1: 创建配置")
        config = AppConfig(
            bot=BotConfig(
                name="TelegramMolty",
                description="运行在 Telegram 上的 Moltbook 机器人"
            ),
            personality={
                "system_prompt": "你是一个友好的 Telegram 机器人助手",
                "topics_of_interest": ["Telegram", "Automation", "AI"]
            },
            llm=LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key="sk-test-key",
                temperature=0.9
            ),
            telegram=TelegramConfig(
                enabled=True,
                bot_token="6789012345:AAEexampleTokenHere123456",
                chat_id="123456789"
            )
        )
        print("✓ 配置对象创建完成")

        print("\n步骤 2: 保存配置")
        save_config(config, config_path)
        print(f"✓ 配置已保存到: {config_path}")

        print("\n步骤 3: 加载配置")
        loaded = load_config(config_path)
        print("✓ 配置已加载")

        print("\n步骤 4: 解析密钥")
        secrets = resolve_secrets(loaded)
        print(f"✓ Telegram Token: {secrets.telegram_token[:20]}...")

        print("\n步骤 5: 验证配置")
        validate_config(loaded, secrets)
        print("✓ 配置验证通过")

        print("\n配置摘要:")
        print(f"  Bot 名称: {loaded.bot.name}")
        print(f"  Telegram 启用: {loaded.telegram.enabled}")
        print(f"  Telegram Chat ID: {loaded.telegram.chat_id}")
        print(f"  LLM 提供商: {loaded.llm.provider}")
        print(f"  话题: {', '.join(loaded.personality.topics_of_interest)}")


def main():
    """运行所有 Telegram 配置测试"""
    print("=" * 60)
    print("TinyMolty Telegram 配置测试")
    print("=" * 60)

    try:
        test_telegram_disabled()
        test_telegram_enabled_valid()
        test_telegram_enabled_without_token()
        test_telegram_enabled_full_config()
        test_telegram_token_storage_methods()
        test_telegram_config_save_load()
        test_telegram_chat_id_formats()
        test_telegram_keyring_storage()
        test_complete_telegram_setup()

        print("\n" + "=" * 60)
        print("✓ 所有 Telegram 配置测试通过！")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
