#!/usr/bin/env python3
"""
测试 TinyMolty 配置注册流程
模拟用户配置和注册流程，验证功能是否正常
"""
import tempfile
from pathlib import Path
from config import (
    AppConfig,
    BotConfig,
    LLMConfig,
    MoltbookConfig,
    PersonalityConfig,
    TelegramConfig,
    UIConfig,
    BehaviorConfig,
    AdvancedConfig,
    save_config,
    load_config,
    resolve_secrets,
    validate_config,
    store_secret,
)


def test_config_creation():
    """测试创建默认配置"""
    print("\n=== 测试 1: 创建默认配置 ===")
    config = AppConfig()
    print(f"✓ Bot 名称: {config.bot.name}")
    print(f"✓ LLM 提供商: {config.llm.provider}")
    print(f"✓ LLM 模型: {config.llm.model}")
    print(f"✓ UI 模式: {config.ui.mode}")
    print("✓ 默认配置创建成功")


def test_config_save_and_load():
    """测试配置保存和加载"""
    print("\n=== 测试 2: 配置保存和加载 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.toml"

        # 创建自定义配置
        config = AppConfig(
            bot=BotConfig(name="TestBot", description="Test bot for configuration"),
            ui=UIConfig(mode="terminal"),
            personality=PersonalityConfig(
                system_prompt="You are a test bot",
                topics_of_interest=["testing", "automation", "AI"]
            ),
            llm=LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key="test-key-placeholder",
                temperature=0.7
            ),
            moltbook=MoltbookConfig(
                credentials_path="~/.config/moltbook/test_credentials.json"
            ),
            telegram=TelegramConfig(
                enabled=False,
                bot_token="test-token",
                chat_id=""
            ),
            behavior=BehaviorConfig(
                enabled_actions=["browse", "upvote", "comment"],
                post_cooldown_minutes=60,
                comment_cooldown_minutes=5,
                browse_interval_minutes=15,
                max_comments_per_day=30,
                max_posts_per_day=10,
                preferred_submolts=["technology", "AI"]
            ),
            advanced=AdvancedConfig(
                log_level="INFO",
                jitter_range_seconds=(5, 30)
            )
        )

        # 保存配置
        saved_path = save_config(config, config_path)
        print(f"✓ 配置已保存到: {saved_path}")

        # 加载配置
        loaded_config = load_config(config_path)
        print(f"✓ 配置已加载")

        # 验证配置内容
        assert loaded_config.bot.name == "TestBot", "Bot 名称不匹配"
        assert loaded_config.llm.provider == "openai", "LLM 提供商不匹配"
        assert loaded_config.llm.model == "gpt-4o-mini", "LLM 模型不匹配"
        assert loaded_config.personality.topics_of_interest == ["testing", "automation", "AI"], "话题不匹配"
        assert loaded_config.behavior.max_comments_per_day == 30, "评论限制不匹配"
        assert loaded_config.advanced.log_level == "INFO", "日志级别不匹配"

        print("✓ 配置内容验证成功")

        # 显示保存的配置文件内容
        print("\n保存的配置文件内容:")
        print("-" * 60)
        print(config_path.read_text())
        print("-" * 60)


def test_secret_resolution():
    """测试密钥解析"""
    print("\n=== 测试 3: 密钥解析 ===")

    # 测试直接值
    config = AppConfig()
    config.llm.api_key = "direct-api-key-123"
    config.telegram.bot_token = "direct-token-456"

    secrets = resolve_secrets(config)
    assert secrets.llm_api_key == "direct-api-key-123", "LLM API Key 解析失败"
    assert secrets.telegram_token == "direct-token-456", "Telegram Token 解析失败"
    print("✓ 直接值密钥解析成功")

    # 测试空值
    config.llm.api_key = ""
    config.telegram.bot_token = ""
    secrets = resolve_secrets(config)
    assert secrets.llm_api_key is None, "空密钥应返回 None"
    assert secrets.telegram_token is None, "空密钥应返回 None"
    print("✓ 空值处理正确")


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试 4: 配置验证 ===")

    # 测试有效的 terminal 模式配置
    config = AppConfig(
        ui=UIConfig(mode="terminal"),
        llm=LLMConfig(api_key="test-key")
    )
    secrets = resolve_secrets(config)
    try:
        validate_config(config, secrets)
        print("✓ Terminal 模式配置验证通过")
    except ValueError as e:
        print(f"✗ 验证失败: {e}")
        raise

    # 测试无效的 telegram 模式配置 (enabled=False 但 mode=telegram)
    config = AppConfig(
        ui=UIConfig(mode="telegram"),
        telegram=TelegramConfig(enabled=False)
    )
    try:
        validate_config(config)
        print("✗ 应该抛出验证错误")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        print(f"✓ 正确捕获验证错误: {e}")


def test_complete_setup_flow():
    """测试完整的设置流程模拟"""
    print("\n=== 测试 5: 完整设置流程模拟 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"

        # 模拟用户输入创建配置
        print("模拟用户配置输入...")
        config = AppConfig(
            bot=BotConfig(
                name="TinyMolty测试",
                description="一个测试用的 Moltbook 机器人"
            ),
            ui=UIConfig(mode="terminal"),
            personality=PersonalityConfig(
                system_prompt="你是一个友好的 AI 助手，热爱技术交流",
                topics_of_interest=["Python", "AI", "开源软件"]
            ),
            llm=LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key="sk-test-key-12345",
                temperature=0.8
            ),
            moltbook=MoltbookConfig(
                credentials_path="~/.config/moltbook/credentials.json"
            ),
            telegram=TelegramConfig(
                enabled=False,
                bot_token="keyring",
                chat_id=""
            ),
            behavior=BehaviorConfig(
                enabled_actions=["browse", "upvote", "comment", "post"],
                post_cooldown_minutes=60,
                comment_cooldown_minutes=5,
                browse_interval_minutes=15,
                heartbeat_interval_hours=4,
                max_comments_per_day=30,
                max_posts_per_day=10,
                preferred_submolts=["technology", "python"]
            )
        )

        print("✓ 配置对象创建完成")

        # 保存配置
        saved_path = save_config(config, config_path)
        print(f"✓ 配置已保存到: {saved_path}")

        # 验证文件权限
        import stat
        file_stat = config_path.stat()
        file_mode = stat.filemode(file_stat.st_mode)
        print(f"✓ 配置文件权限: {file_mode}")

        # 重新加载并验证
        loaded_config = load_config(config_path)
        print("✓ 配置已重新加载")

        # 解析密钥
        secrets = resolve_secrets(loaded_config)
        print(f"✓ LLM API Key 已解析: {secrets.llm_api_key[:10]}..." if secrets.llm_api_key else "✓ LLM API Key: None")

        # 验证配置
        validate_config(loaded_config, secrets)
        print("✓ 配置验证通过")

        # 显示最终配置摘要
        print("\n配置摘要:")
        print(f"  Bot 名称: {loaded_config.bot.name}")
        print(f"  描述: {loaded_config.bot.description}")
        print(f"  UI 模式: {loaded_config.ui.mode}")
        print(f"  LLM 提供商: {loaded_config.llm.provider}")
        print(f"  LLM 模型: {loaded_config.llm.model}")
        print(f"  温度: {loaded_config.llm.temperature}")
        print(f"  话题: {', '.join(loaded_config.personality.topics_of_interest)}")
        print(f"  启用的操作: {', '.join(loaded_config.behavior.enabled_actions)}")
        print(f"  每日最大评论数: {loaded_config.behavior.max_comments_per_day}")
        print(f"  每日最大帖子数: {loaded_config.behavior.max_posts_per_day}")
        print(f"  首选 Submolts: {', '.join(loaded_config.behavior.preferred_submolts)}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("TinyMolty 配置注册流程测试")
    print("=" * 60)

    try:
        test_config_creation()
        test_config_save_and_load()
        test_secret_resolution()
        test_config_validation()
        test_complete_setup_flow()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！配置注册流程功能正常")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
