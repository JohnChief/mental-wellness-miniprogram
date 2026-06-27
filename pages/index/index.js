const api = require('../../utils/api')

Page({
  data: {
    loading: true,
    error: '',
    showContent: false,
    settings: {},
    featuredEvent: null,
    hasFeaturedEvent: false,
    hasEvents: false,
    events: []
  },

  onLoad() {
    this.loadHome()
  },

  onPullDownRefresh() {
    this.loadHome().finally(() => wx.stopPullDownRefresh())
  },

  loadHome() {
    this.setData({ loading: true, error: '', showContent: false })
    return api.getHome()
      .then(data => {
        const events = data.events || []
        const featuredEvent = data.featured_event || null
        this.setData({
          settings: data.settings,
          featuredEvent,
          hasFeaturedEvent: !!featuredEvent,
          hasEvents: events.length > 0,
          events,
          loading: false,
          showContent: true
        })
      })
      .catch(error => {
        this.setData({ loading: false, error: error.message, showContent: false })
      })
  },

  openFeatured() {
    const event = this.data.featuredEvent
    if (event) wx.navigateTo({ url: `/pages/activityDetail/activityDetail?id=${event.id}` })
  },

  openEvent(e) {
    wx.navigateTo({ url: `/pages/activityDetail/activityDetail?id=${e.currentTarget.dataset.id}` })
  },

  openActivities() {
    wx.switchTab({ url: '/pages/activity/activity' })
  },

  openRegistration() {
    wx.showToast({
      title: '咨询入口即将开放',
      icon: 'none'
    })
  }
})
