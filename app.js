App({
  onLaunch() {
    wx.cloud.init({
      env: 'prod-d6g7im3ft632062b9',
      traceUser: true
    })
  },
  globalData: {
    envId: 'prod-d6g7im3ft632062b9',
    serviceName: 'flask-ytaf'
  }
})
