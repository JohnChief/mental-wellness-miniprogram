const config = require('../config')
const mock = require('./mock')

function parseResponse(response, fallbackMessage) {
  const body = response.data || {}
  if (response.statusCode >= 400 || body.code) {
    throw new Error(body.message || fallbackMessage)
  }
  return body.data
}

function callContainer(path, method = 'GET', data = {}) {
  return wx.cloud.callContainer({
    config: {
      env: config.envId
    },
    path,
    method,
    data,
    header: {
      'X-WX-SERVICE': config.serviceName,
      'content-type': 'application/json'
    }
  }).then(response => parseResponse(response, '服务暂时不可用'))
}

function callLocalApi(path, method = 'GET', data = {}) {
  const baseUrl = (config.localBaseUrl || '').replace(/\/$/, '')
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${path}`,
      method,
      data,
      header: {
        'content-type': 'application/json',
        'X-DEV-OPENID': config.devOpenid || 'local-dev-user'
      },
      success(response) {
        try {
          resolve(parseResponse(response, '本地服务暂时不可用'))
        } catch (error) {
          reject(error)
        }
      },
      fail(error) {
        reject(new Error(error.errMsg || '本地服务暂时不可用'))
      }
    })
  })
}

function callApi(path, method = 'GET', data = {}) {
  return config.useLocalApi
    ? callLocalApi(path, method, data)
    : callContainer(path, method, data)
}

function getHome() {
  return config.useMock ? Promise.resolve(mock.getHome()) : callApi('/api/home')
}

function getEvents(filter = '全部') {
  return config.useMock
    ? Promise.resolve(mock.getEvents(filter))
    : callApi(`/api/events?filter=${encodeURIComponent(filter)}`)
}

function getEvent(id) {
  return config.useMock
    ? Promise.resolve(mock.getEvent(id))
    : callApi(`/api/events/${id}`)
}

function getCurrentUser() {
  if (config.useMock) {
    const user = wx.getStorageSync('mockUser')
    return Promise.resolve(user || { registered: false })
  }
  return callApi('/api/auth/me')
}

function uploadAvatar(filePath) {
  if (!filePath) return Promise.resolve('')
  if (config.useMock || config.useLocalApi) return Promise.resolve(filePath)

  const extension = (filePath.split('.').pop() || 'jpg').toLowerCase()
  const cloudPath = `avatars/${Date.now()}-${Math.random().toString(36).slice(2)}.${extension}`
  return wx.cloud.uploadFile({
    cloudPath,
    filePath,
    config: {
      env: config.envId
    }
  }).then(result => result.fileID)
}

function registerUser(payload) {
  if (config.useMock) {
    const defaultNicknames = ['清风来客', '云间小憩', '自在行者', '暖心朋友', '松间听雨', '星河旅人']
    const defaultAvatars = ['default:lotus', 'default:moon', 'default:cloud', 'default:leaf', 'default:star', 'default:mountain']
    const user = {
      id: 1,
      nickname: payload.nickname || defaultNicknames[Math.floor(Math.random() * defaultNicknames.length)],
      avatar_url: payload.avatar_url || defaultAvatars[Math.floor(Math.random() * defaultAvatars.length)],
      phone: '',
      is_vip: false,
      registered: true
    }
    wx.setStorageSync('mockUser', user)
    return Promise.resolve(user)
  }
  return callApi('/api/auth/register', 'POST', payload)
}

function updateUserProfile(payload) {
  if (config.useMock) {
    const user = wx.getStorageSync('mockUser') || {}
    const updated = {
      ...user,
      ...(payload.nickname ? { nickname: payload.nickname } : {}),
      ...(payload.avatar_url ? { avatar_url: payload.avatar_url } : {})
    }
    wx.setStorageSync('mockUser', updated)
    return Promise.resolve(updated)
  }
  return callApi('/api/auth/profile', 'PUT', payload)
}

function createRegistration(payload) {
  if (config.useMock) {
    const records = wx.getStorageSync('mockRegistrations') || []
    records.unshift({
      id: Date.now(),
      status: 'registered',
      created_at_text: '刚刚',
      event: mock.getEvent(payload.event_id),
      ...payload
    })
    wx.setStorageSync('mockRegistrations', records)
    return Promise.resolve(records[0])
  }
  return callApi('/api/registrations', 'POST', payload)
}

function getMyRegistrations() {
  return config.useMock
    ? Promise.resolve(wx.getStorageSync('mockRegistrations') || [])
    : callApi('/api/registrations/mine')
}

function cancelRegistration(id) {
  if (config.useMock) {
    const records = (wx.getStorageSync('mockRegistrations') || []).map(item => {
      if (String(item.id) === String(id)) item.status = 'cancelled'
      return item
    })
    wx.setStorageSync('mockRegistrations', records)
    return Promise.resolve()
  }
  return callApi(`/api/registrations/${id}/cancel`, 'PUT')
}

function deleteAccount() {
  if (config.useMock) {
    wx.removeStorageSync('mockRegistrations')
    wx.removeStorageSync('mockUser')
    return Promise.resolve({ deleted: true })
  }
  return callApi('/api/account', 'DELETE')
}

module.exports = {
  getHome,
  getEvents,
  getEvent,
  getCurrentUser,
  uploadAvatar,
  registerUser,
  updateUserProfile,
  createRegistration,
  getMyRegistrations,
  cancelRegistration,
  deleteAccount
}
