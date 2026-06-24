from datetime import datetime

from .extensions import db
from .models import Event, Setting


def seed_defaults():
    if not Setting.query.first():
        settings = {
            "platform_name": "心语轻疗愈",
            "platform_slogan": "心理陪伴 · 活动体验 · 社群支持",
            "service_cards": '["情绪压力", "关系修复", "自我成长", "活动体验"]',
        }
        db.session.add_all([Setting(key=key, value=value) for key, value in settings.items()])

    if not Event.query.first():
        db.session.add_all(
            [
                Event(
                    title="情绪疗愈体验课",
                    subtitle="识别压力信号，练习日常情绪调适",
                    cover_color="#cfc7ff",
                    event_time=datetime(2026, 7, 1, 19, 30),
                    event_time_text="本周三 19:30",
                    location="线下体验空间",
                    price_text="免费体验",
                    description="通过轻松的团体活动，学习识别压力与情绪信号，找到适合自己的放松方式。",
                    target_audience="适合希望改善压力感、了解情绪调适方法的成年人。",
                    flow="暖场交流 → 情绪觉察练习 → 放松体验 → 分享答疑",
                    notice="本活动提供一般性情绪支持，不替代医疗诊断、治疗或专业心理咨询。",
                    category="本周",
                    capacity=20,
                ),
                Event(
                    title="周末冥想与情绪舒缓沙龙",
                    subtitle="适合压力、内耗、情绪困扰用户",
                    cover_color="#d8d1ff",
                    event_time=datetime(2026, 7, 4, 14, 0),
                    event_time_text="周六 14:00",
                    location="线下体验空间",
                    price_text="免费体验",
                    description="用呼吸、身体扫描和温和交流，为忙碌的一周留出一段安静时间。",
                    target_audience="适合近期压力较大、容易疲惫或希望体验冥想的成年人。",
                    flow="签到 → 呼吸练习 → 引导冥想 → 茶歇交流",
                    notice="请穿着舒适衣物；如有严重身心不适，请优先寻求专业医疗帮助。",
                    category="本周",
                    capacity=16,
                    is_featured=True,
                ),
                Event(
                    title="亲密关系公开课",
                    subtitle="沟通边界与关系中的自我照顾",
                    cover_color="#e2dcff",
                    event_time=datetime(2026, 7, 7, 20, 0),
                    event_time_text="下周二 20:00",
                    location="线上直播",
                    price_text="免费",
                    description="从日常沟通场景出发，理解关系中的需要、边界与表达。",
                    target_audience="适合希望改善沟通体验、建立健康关系边界的成年人。",
                    flow="主题讲解 → 案例讨论 → 练习 → 答疑",
                    notice="课程不提供个案诊断，不构成医疗或心理治疗建议。",
                    category="免费",
                    capacity=None,
                ),
            ]
        )

    db.session.commit()
