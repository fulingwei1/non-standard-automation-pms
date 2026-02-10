/**
 * 认证相关API
 */
import request from '@/utils/request'

/**
 * 用户登录
 */
export function login(data) {
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    data
  })
}

/**
 * 用户登出
 */
export function logout() {
  return request({
    url: '/api/v1/auth/logout',
    method: 'post'
  })
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request({
    url: '/api/v1/auth/userinfo',
    method: 'get'
  })
}

/**
 * 刷新Token
 */
export function refreshToken(refreshToken) {
  return request({
    url: '/api/v1/auth/refresh',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}

/**
 * 修改密码
 */
export function changePassword(data) {
  return request({
    url: '/api/v1/auth/password',
    method: 'put',
    data
  })
}

/**
 * 获取验证码
 */
export function getCaptcha() {
  return request({
    url: '/api/v1/auth/captcha',
    method: 'get'
  })
}
