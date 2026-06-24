const api = require('../../utils/api')

Page({
  data: {
    loading: true,
    error: '',
    showContent: false,
    settings: {},
    featuredEvent: null,
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
        this.setData({
          settings: data.settings,
          featuredEvent: data.featured_event,
          events: data.events,
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
    wx.switchTab({ url: '/pages/activity/activity' })
  }
})
