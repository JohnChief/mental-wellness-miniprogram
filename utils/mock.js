const events = [
  {
    id: 1,
    title: '情绪疗愈体验课',
    subtitle: '识别压力信号，练习日常情绪调适',
    event_time_text: '本周三 19:30',
    location: '线下体验空间',
    price_text: '免费体验',
    remaining: 12,
    category: '本周',
    cover_color: '#cfc7ff',
    description: '通过轻松的团体活动，学习识别压力与情绪信号，找到适合自己的放松方式。',
    target_audience: '适合希望改善压力感、了解情绪调适方法的成年人。',
    flow: '暖场交流 → 情绪觉察练习 → 放松体验 → 分享答疑',
    notice: '本活动提供一般性情绪支持，不替代医疗诊断、治疗或专业心理咨询。'
  },
  {
    id: 2,
    title: '周末冥想与情绪舒缓沙龙',
    subtitle: '适合压力、内耗、情绪困扰用户',
    event_time_text: '周六 14:00',
    location: '线下体验空间',
    price_text: '免费体验',
    remaining: 8,
    category: '本周',
    cover_color: '#d8d1ff',
    description: '用呼吸、身体扫描和温和交流，为忙碌的一周留出一段安静时间。',
    target_audience: '适合近期压力较大、容易疲惫或希望体验冥想的成年人。',
    flow: '签到 → 呼吸练习 → 引导冥想 → 茶歇交流',
    notice: '请穿着舒适衣物；如有严重身心不适，请优先寻求专业医疗帮助。'
  },
  {
    id: 3,
    title: '亲密关系公开课',
    subtitle: '沟通边界与关系中的自我照顾',
    event_time_text: '下周二 20:00',
    location: '线上直播',
    price_text: '免费',
    remaining: null,
    category: '免费',
    cover_color: '#e2dcff',
    description: '从日常沟通场景出发，理解关系中的需要、边界与表达。',
    target_audience: '适合希望改善沟通体验、建立健康关系边界的成年人。',
    flow: '主题讲解 → 案例讨论 → 练习 → 答疑',
    notice: '课程不提供个案诊断，不构成医疗或心理治疗建议。'
  }
]

function getHome() {
  return {
    settings: {
      platform_name: '心语轻疗愈',
      platform_slogan: '心理陪伴 · 活动体验 · 社群支持',
      service_cards: ['情绪压力', '关系修复', '自我成长', '活动体验']
    },
    featured_event: events[1],
    events: events.slice(0, 2)
  }
}

function getEvents(filter) {
  if (!filter || filter === '全部') return events
  if (filter === '线下') return events.filter(item => item.location.indexOf('线下') > -1)
  return events.filter(item => item.category === filter)
}

function getEvent(id) {
  return events.find(item => String(item.id) === String(id)) || events[0]
}

module.exports = {
  getHome,
  getEvents,
  getEvent
}
