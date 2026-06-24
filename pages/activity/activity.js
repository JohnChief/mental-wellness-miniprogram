const api = require('../../utils/api')

Page({
  data: {
    filters: [
      { label: '全部', className: 'filter-chip active' },
      { label: '本周', className: 'filter-chip' },
      { label: '免费', className: 'filter-chip' },
      { label: '线下', className: 'filter-chip' }
    ],
    activeFilter: '全部',
    loading: true,
    error: '',
    showEmpty: false,
    showList: false,
    events: []
  },

  onShow() {
    this.loadEvents()
  },

  onPullDownRefresh() {
    this.loadEvents().finally(() => wx.stopPullDownRefresh())
  },

  selectFilter(e) {
    const activeFilter = e.currentTarget.dataset.filter
    const filters = this.data.filters.map(item => ({
      ...item,
      className: item.label === activeFilter ? 'filter-chip active' : 'filter-chip'
    }))
    this.setData({ activeFilter, filters })
    this.loadEvents()
  },

  loadEvents() {
    this.setData({
      loading: true,
      error: '',
      showEmpty: false,
      showList: false
    })
    return api.getEvents(this.data.activeFilter)
      .then(events => {
        const normalizedEvents = events.map(item => ({
          ...item,
          showRemaining: item.remaining !== null && item.remaining !== undefined
        }))
        this.setData({
          events: normalizedEvents,
          loading: false,
          showEmpty: normalizedEvents.length === 0,
          showList: normalizedEvents.length > 0
        })
      })
      .catch(error => this.setData({
        loading: false,
        error: error.message,
        showEmpty: false,
        showList: false
      }))
  },

  openEvent(e) {
    wx.navigateTo({ url: `/pages/activityDetail/activityDetail?id=${e.currentTarget.dataset.id}` })
  }
})
