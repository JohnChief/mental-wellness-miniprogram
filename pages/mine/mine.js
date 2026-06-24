const api = require('../../utils/api')

Page({
  data: {
    nickname: '微信用户'
  },

  openRecords() {
    wx.navigateTo({ url: '/pages/records/records' })
  },

  openAgreement(e) {
    wx.navigateTo({ url: `/pages/agreement/agreement?type=${e.currentTarget.dataset.type}` })
  },

  contact() {
    wx.showModal({
      title: '联系客服',
      content: '客服二维码和联系方式将在运营资料确认后配置。',
      showCancel: false
    })
  },

  about() {
    wx.showModal({
      title: '关于我们',
      content: '我们提供一般性情绪支持、身心调适活动与社群陪伴，不提供医疗诊断或治疗。',
      showCancel: false
    })
  },

  deleteAccount() {
    wx.showModal({
      title: '注销账号',
      content: '注销后个人资料与报名中的个人信息将被删除或匿名化，此操作不可撤销。',
      confirmText: '确认注销',
      confirmColor: '#d94b4b',
      success: result => {
        if (!result.confirm) return
        api.deleteAccount()
          .then(() => wx.showToast({ title: '已完成注销' }))
          .catch(error => wx.showToast({ title: error.message, icon: 'none' }))
      }
    })
  }
})
