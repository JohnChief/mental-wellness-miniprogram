const api = require('../../utils/api')

Page({
  data: {
    event: null,
    name: '',
    phone: '',
    remark: '',
    agreed: false,
    checkboxClass: 'checkbox',
    checkboxText: '',
    submitting: false
  },

  onLoad(options) {
    this.eventId = options.id
    api.getEvent(options.id).then(event => this.setData({ event }))
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  toggleAgreement() {
    const agreed = !this.data.agreed
    this.setData({
      agreed,
      checkboxClass: agreed ? 'checkbox checked' : 'checkbox',
      checkboxText: agreed ? '✓' : ''
    })
  },

  openPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/agreement?type=privacy' })
  },

  submit() {
    const { name, phone, remark, agreed } = this.data
    if (!name.trim()) return wx.showToast({ title: '请填写姓名', icon: 'none' })
    if (!/^1\d{10}$/.test(phone)) return wx.showToast({ title: '请填写正确手机号', icon: 'none' })
    if (!agreed) return wx.showToast({ title: '请先同意隐私政策', icon: 'none' })
    if (this.data.submitting) return

    this.setData({ submitting: true })
    api.createRegistration({
      event_id: Number(this.eventId),
      name: name.trim(),
      phone,
      remark: remark.trim(),
      privacy_version: '2026-06-24'
    }).then(() => {
      wx.showModal({
        title: '报名成功',
        content: '我们已收到你的报名信息，活动前会与你确认。',
        showCancel: false,
        success: () => wx.redirectTo({ url: '/pages/records/records' })
      })
    }).catch(error => {
      wx.showToast({ title: error.message, icon: 'none' })
    }).finally(() => this.setData({ submitting: false }))
  }
})
