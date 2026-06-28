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
    emptyTitle: '',
    emptyText: '',
    emptyAction: '',
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
        const isAllFilter = this.data.activeFilter === '全部'
        this.setData({
          events: normalizedEvents,
          loading: false,
          showEmpty: normalizedEvents.length === 0,
          showList: normalizedEvents.length > 0,
          emptyTitle: isAllFilter ? '活动筹备中' : '这个分类暂时没有活动',
          emptyText: isAllFilter
            ? '运营老师还没有发布活动，稍后刷新就能看到最新安排。'
            : '可以切回全部活动，看看其它正在开放的体验。',
          emptyAction: isAllFilter ? '刷新看看' : '查看全部活动'
        })
      })
      .catch(error => this.setData({
        loading: false,
        error: error.message,
        showEmpty: false,
        showList: false
      }))
  },

  handleEmptyAction() {
    if (this.data.activeFilter === '全部') {
      this.loadEvents()
      return
    }

    const filters = this.data.filters.map(item => ({
      ...item,
      className: item.label === '全部' ? 'filter-chip active' : 'filter-chip'
    }))
    this.setData({ activeFilter: '全部', filters })
    this.loadEvents()
  },

  openEvent(e) {
    wx.navigateTo({ url: `/pages/activityDetail/activityDetail?id=${e.currentTarget.dataset.id}` })
  }
})
