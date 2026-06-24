const api = require('../../utils/api')

Page({
  data: {
    loading: true,
    error: '',
    showContent: false,
    event: null
  },

  onLoad(options) {
    this.eventId = options.id
    this.loadEvent()
  },

  loadEvent() {
    this.setData({ loading: true, error: '', showContent: false })
    api.getEvent(this.eventId)
      .then(event => this.setData({
        event: {
          ...event,
          showRemaining: event.remaining !== null && event.remaining !== undefined
        },
        loading: false,
        showContent: true
      }))
      .catch(error => this.setData({
        loading: false,
        error: error.message,
        showContent: false
      }))
  },

  register() {
    wx.navigateTo({ url: `/pages/registration/registration?id=${this.data.event.id}` })
  }
})
