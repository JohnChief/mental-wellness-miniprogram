const config = require('../config')
const mock = require('./mock')

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
  }).then(response => {
    const body = response.data || {}
    if (response.statusCode >= 400 || body.code) {
      throw new Error(body.message || '服务暂时不可用')
    }
    return body.data
  })
}

function getHome() {
  return config.useMock ? Promise.resolve(mock.getHome()) : callContainer('/api/home')
}

function getEvents(filter = '全部') {
  return config.useMock
    ? Promise.resolve(mock.getEvents(filter))
    : callContainer(`/api/events?filter=${encodeURIComponent(filter)}`)
}

function getEvent(id) {
  return config.useMock
    ? Promise.resolve(mock.getEvent(id))
    : callContainer(`/api/events/${id}`)
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
  return callContainer('/api/registrations', 'POST', payload)
}

function getMyRegistrations() {
  return config.useMock
    ? Promise.resolve(wx.getStorageSync('mockRegistrations') || [])
    : callContainer('/api/registrations/mine')
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
  return callContainer(`/api/registrations/${id}/cancel`, 'PUT')
}

function deleteAccount() {
  if (config.useMock) {
    wx.removeStorageSync('mockRegistrations')
    return Promise.resolve({ deleted: true })
  }
  return callContainer('/api/account', 'DELETE')
}

module.exports = {
  getHome,
  getEvents,
  getEvent,
  createRegistration,
  getMyRegistrations,
  cancelRegistration,
  deleteAccount
}
