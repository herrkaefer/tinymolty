#!/usr/bin/env python3
"""
测试 Moltbook 注册流程
"""
import asyncio
import tempfile
from pathlib import Path


async def test_registration():
    """测试注册功能"""
    print("\n=== 测试 1: Moltbook Agent 注册 ===")

    from moltbook.registration import register_agent, save_credentials

    # 使用测试数据
    test_name = f"TestMolty_{asyncio.get_event_loop().time():.0f}"
    test_desc = "A test agent for TinyMolty registration flow"

    print(f"\n注册测试 Agent:")
    print(f"  名称: {test_name}")
    print(f"  描述: {test_desc}")

    try:
        response = await register_agent(test_name, test_desc)

        print(f"\n✅ 注册成功！")
        print(f"  Agent 名称: {response.agent_name}")
        print(f"  API Key: {response.api_key[:20]}...")
        print(f"  Claim URL: {response.claim_url}")
        print(f"  Verification Code: {response.verification_code}")

        # 测试保存凭证
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_path = Path(tmpdir) / "credentials.json"
            saved_path = save_credentials(
                response.api_key,
                response.agent_name,
                cred_path
            )

            print(f"\n✅ 凭证已保存到: {saved_path}")

            # 验证文件内容
            import json
            data = json.loads(saved_path.read_text())
            assert data["api_key"] == response.api_key
            assert data["agent_name"] == response.agent_name
            print(f"✅ 凭证内容验证通过")

            # 检查文件权限
            import stat
            mode = saved_path.stat().st_mode
            assert mode & 0o777 == 0o600
            print(f"✅ 文件权限正确 (600)")

        return response

    except Exception as e:
        print(f"\n✗ 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_api_connection(api_key: str):
    """测试 API 连接"""
    print("\n=== 测试 2: API 连接测试 ===")

    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                "https://www.moltbook.com/api/v1/agents/me",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ API 连接成功！")
                print(f"  Agent ID: {data.get('id', 'N/A')}")
                print(f"  Agent 名称: {data.get('name', 'N/A')}")
                print(f"  状态: {data.get('status', 'N/A')}")
                return True
            else:
                print(f"\n✗ API 返回错误: {response.status_code}")
                print(f"  响应: {response.text}")
                return False

        except Exception as e:
            print(f"\n✗ API 连接失败: {e}")
            return False


async def test_claim_status(api_key: str):
    """测试认领状态检查"""
    print("\n=== 测试 3: 认领状态检查 ===")

    from moltbook.registration import check_claim_status

    try:
        status = await check_claim_status(api_key)
        print(f"\n✅ 状态查询成功")
        print(f"  状态: {status}")
        return status
    except Exception as e:
        print(f"\n✗ 状态查询失败: {e}")
        return None


async def test_complete_flow():
    """测试完整注册流程"""
    print("=" * 60)
    print("Moltbook 注册流程测试")
    print("=" * 60)

    # 测试注册
    response = await test_registration()
    if not response:
        print("\n✗ 注册测试失败，后续测试跳过")
        return

    # 测试 API 连接
    await test_api_connection(response.api_key)

    # 测试认领状态
    await test_claim_status(response.api_key)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print()
    print("⚠️  注意：测试创建的 Agent 账号信息：")
    print(f"   Agent 名称: {response.agent_name}")
    print(f"   API Key: {response.api_key}")
    print(f"   Claim URL: {response.claim_url}")
    print(f"   Verification Code: {response.verification_code}")
    print()
    print("   如需使用此账号，请访问 Claim URL 完成验证。")
    print("=" * 60)


def main():
    """主函数"""
    try:
        asyncio.run(test_complete_flow())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
