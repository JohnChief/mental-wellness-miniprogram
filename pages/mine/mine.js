const api = require('../../utils/api')

const DEFAULT_AVATAR_META = {
  'default:lotus': { text: '莲', className: 'avatar default-avatar lotus' },
  'default:moon': { text: '月', className: 'avatar default-avatar moon' },
  'default:cloud': { text: '云', className: 'avatar default-avatar cloud' },
  'default:leaf': { text: '叶', className: 'avatar default-avatar leaf' },
  'default:star': { text: '星', className: 'avatar default-avatar star' },
  'default:mountain': { text: '山', className: 'avatar default-avatar mountain' }
}

Page({
  data: {
    loadingProfile: true,
    showGuest: false,
    showLoginForm: false,
    showProfile: false,
    showAvatarImage: false,
    showDefaultAvatar: false,
    showFallbackAvatar: false,
    showDeleteAccount: false,
    showRegisterButton: false,
    showSaveButton: false,
    formTitle: '快速登录',
    formTip: '昵称和头像均为选填，未填写时系统会随机分配，登录后可随时修改。',
    user: null,
    avatarUrl: '',
    avatarChanged: false,
    originalNickname: '',
    defaultAvatarText: '心',
    defaultAvatarClass: 'avatar',
    nickname: '',
    agreed: false,
    checkboxClass: 'checkbox',
    checkboxText: '',
    submitting: false
  },

  onShow() {
    this.loadProfile()
  },

  loadProfile() {
    this.setData({
      loadingProfile: true,
      showGuest: false,
      showLoginForm: false,
      showProfile: false
    })
    api.getCurrentUser()
      .then(user => {
        if (user.registered) {
          this.showLoggedInUser(user)
          return
        }
        this.setData({
          user: null,
          loadingProfile: false,
          showGuest: true,
          showDeleteAccount: false
        })
      })
      .catch(() => {
        this.setData({
          user: null,
          loadingProfile: false,
          showGuest: true,
          showDeleteAccount: false
        })
      })
  },

  openLogin() {
    this.setData({
      showGuest: false,
      showLoginForm: true,
      showRegisterButton: true,
      showSaveButton: false,
      formTitle: '快速登录',
      formTip: '昵称和头像均为选填，未填写时系统会随机分配，登录后可随时修改。',
      avatarUrl: '',
      avatarChanged: false,
      originalNickname: '',
      nickname: '',
      showAvatarImage: false
    })
  },

  editProfile() {
    const user = this.data.user
    if (!user) return
    const isDefaultAvatar = user.avatar_url.indexOf('default:') === 0
    this.setData({
      showProfile: false,
      showLoginForm: true,
      showRegisterButton: false,
      showSaveButton: true,
      formTitle: '修改个人资料',
      formTip: '可以只修改昵称或头像，手机号无需再次授权。',
      nickname: user.nickname,
      originalNickname: user.nickname,
      avatarUrl: isDefaultAvatar ? '' : user.avatar_url,
      avatarChanged: false,
      showAvatarImage: !isDefaultAvatar && Boolean(user.avatar_url)
    })
  },

  cancelLogin() {
    if (this.data.user && this.data.user.registered) {
      this.showLoggedInUser(this.data.user)
      return
    }
    this.setData({
      showGuest: true,
      showLoginForm: false,
      showRegisterButton: false,
      showSaveButton: false
    })
  },

  onChooseAvatar(e) {
    const avatarUrl = e.detail.avatarUrl
    this.setData({
      avatarUrl,
      avatarChanged: true,
      showAvatarImage: Boolean(avatarUrl)
    })
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
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

  authorizePhone(e) {
    if (this.data.submitting) return
    if (!this.data.agreed) {
      return wx.showToast({ title: '请先同意隐私政策', icon: 'none' })
    }

    const phoneCode = e.detail.code || ''
    const errMsg = e.detail.errMsg || ''
    if (!phoneCode) {
      const config = require('../../config')
      if (!config.useMock) {
        const message = errMsg.indexOf('deny') !== -1
          ? '你取消了手机号授权'
          : '手机号授权失败，请重试'
        console.error('getPhoneNumber failed:', e.detail)
        return wx.showToast({ title: message, icon: 'none' })
      }
    }

    this.setData({ submitting: true })
    api.uploadAvatar(this.data.avatarUrl)
      .then(avatarFileId => api.registerUser({
        nickname: this.data.nickname.trim(),
        avatar_url: avatarFileId,
        phone_code: phoneCode || 'mock-phone-code',
        privacy_version: '2026-06-24'
      }))
      .then(user => {
        this.showLoggedInUser(user)
        wx.showToast({ title: '登录成功' })
      })
      .catch(error => {
        this.setData({ submitting: false })
        wx.showToast({ title: error.message, icon: 'none' })
      })
  },

  saveProfile() {
    if (this.data.submitting) return
    const nickname = this.data.nickname.trim()
    if (nickname === this.data.originalNickname && !this.data.avatarChanged) {
      return wx.showToast({ title: '请修改昵称或头像', icon: 'none' })
    }

    this.setData({ submitting: true })
    const avatarPromise = this.data.avatarChanged && this.data.avatarUrl
      ? api.uploadAvatar(this.data.avatarUrl)
      : Promise.resolve('')

    avatarPromise
      .then(avatarFileId => api.updateUserProfile({
        nickname,
        avatar_url: avatarFileId
      }))
      .then(user => {
        this.showLoggedInUser(user)
        wx.showToast({ title: '资料已更新' })
      })
      .catch(error => {
        this.setData({ submitting: false })
        wx.showToast({ title: error.message, icon: 'none' })
      })
  },

  showLoggedInUser(user) {
    const defaultMeta = DEFAULT_AVATAR_META[user.avatar_url]
    this.setData({
      user,
      loadingProfile: false,
      showGuest: false,
      showLoginForm: false,
      showProfile: true,
      showAvatarImage: Boolean(user.avatar_url) && !defaultMeta,
      showDefaultAvatar: Boolean(defaultMeta),
      showFallbackAvatar: !user.avatar_url,
      defaultAvatarText: defaultMeta ? defaultMeta.text : '心',
      defaultAvatarClass: defaultMeta ? defaultMeta.className : 'avatar',
      showDeleteAccount: true,
      showRegisterButton: false,
      showSaveButton: false,
      submitting: false
    })
  },

  openRecords() {
    if (!this.data.user || !this.data.user.registered) {
      this.openLogin()
      return wx.showToast({ title: '请先登录', icon: 'none' })
    }
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
          .then(() => {
            wx.showToast({ title: '已完成注销' })
            this.setData({
              user: null,
              showProfile: false,
              showGuest: true,
              showDefaultAvatar: false,
              showFallbackAvatar: true,
              showDeleteAccount: false,
              avatarUrl: '',
              nickname: ''
            })
          })
          .catch(error => wx.showToast({ title: error.message, icon: 'none' }))
      }
    })
  }
})
