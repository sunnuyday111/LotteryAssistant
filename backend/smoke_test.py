"""端到端冒烟测试：验证完整业务流程。

运行方式（在 backend 目录下）：
    .venv\\Scripts\\python.exe smoke_test.py

依赖：httpx（FastAPI TestClient 需要）
    pip install httpx
"""

import io
import sys

from fastapi.testclient import TestClient

from app.main import app

# Windows 控制台默认 cp1252，无法编码中文；强制切换到 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

client = TestClient(app)


def section(title: str) -> None:
    print(f"\n{'=' * 50}\n{title}\n{'=' * 50}")


def main() -> None:
    # 1. 健康检查
    section("1. 健康检查")
    r = client.get("/api/health")
    assert r.status_code == 200, r.text
    print("OK:", r.json())

    # 2. 创建活动
    section("2. 创建活动")
    r = client.post(
        "/api/events",
        json={
            "name": "冒烟测试年会",
            "location": "三楼宴会厅",
            "description": "自动化测试活动",
        },
    )
    assert r.status_code == 201, r.text
    event = r.json()
    event_id = event["id"]
    token = event["checkin_token"]
    print(f"OK: 活动 ID={event_id}, token={token}")

    # 3. 导入名单（CSV）
    section("3. 导入参与者名单")
    csv_content = (
        "姓名,手机号,部门\n"
        "张三,13800000001,技术部\n"
        "李四,13800000002,市场部\n"
        "王五,13800000003,人事部\n"
        "张三重复,13800000001,技术部\n"  # 重复手机号
        ",13800000009,无姓名\n"  # 缺姓名
    )
    r = client.post(
        f"/api/events/{event_id}/participants/import",
        files={"file": ("list.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 200, r.text
    result = r.json()
    print("OK:", result)
    assert result["imported"] == 3, "应导入 3 条"
    assert result["duplicated"] == 1, "应有 1 条重复"
    assert result["invalid"] == 1, "应有 1 条格式错误"

    # 4. 获取参与者列表
    section("4. 获取参与者列表")
    r = client.get(f"/api/events/{event_id}/participants")
    assert r.status_code == 200, r.text
    participants = r.json()
    print(f"OK: 共 {len(participants)} 人")
    assert len(participants) == 3

    # 5. 扫码签到
    section("5. 扫码签到")
    r = client.post(
        f"/api/checkin/{token}",
        json={"phone": "13800000001", "name": "张三"},
    )
    assert r.status_code == 200, r.text
    print("OK:", r.json())
    assert r.json()["success"] is True

    # 6. 重复签到
    section("6. 重复签到（应提示已签到）")
    r = client.post(f"/api/checkin/{token}", json={"phone": "13800000001"})
    assert r.status_code == 200, r.text
    print("OK:", r.json())
    assert r.json()["already_checked_in"] is True

    # 7. 未在名单中签到
    section("7. 未在名单中签到（应失败）")
    r = client.post(f"/api/checkin/{token}", json={"phone": "19999999999"})
    assert r.status_code == 200, r.text
    print("OK:", r.json())
    assert r.json()["success"] is False

    # 8. 再签到两人
    section("8. 再签到两人")
    for phone in ["13800000002", "13800000003"]:
        r = client.post(f"/api/checkin/{token}", json={"phone": phone})
        assert r.json()["success"] is True
    print("OK: 已签到 3 人")

    # 9. 创建奖项
    section("9. 创建奖项")
    r = client.post(
        f"/api/events/{event_id}/prizes",
        json={"name": "一等奖", "quantity": 1, "sort_order": 0},
    )
    assert r.status_code == 201, r.text
    prize1 = r.json()
    r = client.post(
        f"/api/events/{event_id}/prizes",
        json={"name": "二等奖", "quantity": 2, "sort_order": 1},
    )
    prize2 = r.json()
    print(f"OK: 一等奖 ID={prize1['id']}, 二等奖 ID={prize2['id']}")

    # 10. 抽奖
    section("10. 抽奖（一等奖 1 人）")
    r = client.post(
        f"/api/events/{event_id}/draws",
        json={"prize_id": prize1["id"], "count": 1},
    )
    assert r.status_code == 200, r.text
    draw_result = r.json()
    print("OK:", draw_result)
    assert draw_result["success"] is True
    assert len(draw_result["winners"]) == 1
    winner1_id = draw_result["winners"][0]["participant_id"]

    # 11. 抽奖（二等奖 2 人，应排除已中奖者）
    section("11. 抽奖（二等奖 2 人，排除已中奖者）")
    r = client.post(
        f"/api/events/{event_id}/draws",
        json={"prize_id": prize2["id"], "count": 2},
    )
    assert r.status_code == 200, r.text
    draw_result2 = r.json()
    print("OK:", draw_result2)
    assert draw_result2["success"] is True
    assert len(draw_result2["winners"]) == 2
    winner_ids = {w["participant_id"] for w in draw_result2["winners"]}
    assert winner1_id not in winner_ids, "已中奖者不应再次中奖"

    # 12. 名额抽完后再抽
    section("12. 一等奖名额已满，再抽应失败")
    r = client.post(
        f"/api/events/{event_id}/draws",
        json={"prize_id": prize1["id"], "count": 1},
    )
    print("OK:", r.json())
    assert r.json()["success"] is False

    # 13. 统计
    section("13. 数据统计")
    r = client.get(f"/api/events/{event_id}/stats")
    assert r.status_code == 200, r.text
    stats = r.json()
    print("OK:", stats)
    assert stats["total_participants"] == 3
    assert stats["checked_in"] == 3
    assert stats["checkin_rate"] == 1.0

    # 14. 导出签到明细
    section("14. 导出签到明细 Excel")
    r = client.get(f"/api/events/{event_id}/export/checkins")
    assert r.status_code == 200, r.text
    assert len(r.content) > 0
    print(f"OK: 文件大小 {len(r.content)} 字节")

    # 15. 导出中奖名单
    section("15. 导出中奖名单 Excel")
    r = client.get(f"/api/events/{event_id}/export/draws")
    assert r.status_code == 200, r.text
    assert len(r.content) > 0
    print(f"OK: 文件大小 {len(r.content)} 字节")

    # 16. 签到二维码
    section("16. 生成签到二维码")
    r = client.get(f"/api/events/{event_id}/qrcode")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    print(f"OK: PNG 大小 {len(r.content)} 字节")

    # 17. 中奖记录
    section("17. 获取中奖记录")
    r = client.get(f"/api/events/{event_id}/draws")
    assert r.status_code == 200, r.text
    records = r.json()
    print(f"OK: 共 {len(records)} 条中奖记录")
    assert len(records) == 3

    # 18. 清理
    section("18. 删除测试活动")
    r = client.delete(f"/api/events/{event_id}")
    assert r.status_code == 204, r.text
    print("OK: 已删除")

    print("\n" + "=" * 50)
    print("全部测试通过！")
    print("=" * 50)


if __name__ == "__main__":
    main()
