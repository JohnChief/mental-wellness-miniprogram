const api = require('../../utils/api')

Page({
  data: {
    loading: true,
    showEmpty: false,
    records: []
  },

  onShow() {
    this.loadRecords()
  },

  loadRecords() {
    this.setData({ loading: true, showEmpty: false })
    api.getMyRegistrations()
      .then(records => {
        const normalizedRecords = records.map(item => {
          const statusMap = {
            registered: '已报名',
            checked_in: '已签到',
            cancelled: '已取消'
          }
          return {
            ...item,
            statusText: statusMap[item.status] || '未知状态',
            statusClass: `status ${item.status}`,
            canCancel: item.status === 'registered'
          }
        })
        this.setData({
          records: normalizedRecords,
          loading: false,
          showEmpty: normalizedRecords.length === 0
        })
      })
      .catch(error => {
        this.setData({ loading: false, showEmpty: true })
        wx.showToast({ title: error.message, icon: 'none' })
      })
  },

  cancel(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '取消报名',
      content: '确定取消本次活动报名吗？',
      success: result => {
        if (!result.confirm) return
        api.cancelRegistration(id).then(() => this.loadRecords())
      }
    })
  }
})
