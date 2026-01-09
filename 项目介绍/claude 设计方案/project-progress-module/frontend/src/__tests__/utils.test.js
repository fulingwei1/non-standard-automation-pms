import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

// 测试工具函数
import dayjs from 'dayjs'

describe('进度计算工具函数', () => {
  it('计算时间进度', () => {
    const calculateTimeProgress = (startDate, endDate) => {
      const start = dayjs(startDate)
      const end = dayjs(endDate)
      const today = dayjs()
      
      if (today.isBefore(start)) return 0
      if (today.isAfter(end)) return 100
      
      const total = end.diff(start, 'day')
      const elapsed = today.diff(start, 'day')
      return Math.round((elapsed / total) * 100)
    }
    
    // 未开始
    const future = calculateTimeProgress('2030-01-01', '2030-12-31')
    expect(future).toBe(0)
    
    // 已结束
    const past = calculateTimeProgress('2020-01-01', '2020-12-31')
    expect(past).toBe(100)
  })
  
  it('计算加权进度', () => {
    const calculateWeightedProgress = (tasks) => {
      if (!tasks.length) return 0
      const totalWeight = tasks.reduce((sum, t) => sum + (t.weight || 1), 0)
      const weightedSum = tasks.reduce((sum, t) => sum + t.progress * (t.weight || 1), 0)
      return Math.round(weightedSum / totalWeight)
    }
    
    const tasks = [
      { progress: 100, weight: 10 },
      { progress: 50, weight: 30 },
      { progress: 0, weight: 60 }
    ]
    
    const progress = calculateWeightedProgress(tasks)
    expect(progress).toBe(25) // (100*10 + 50*30 + 0*60) / 100 = 25
  })
  
  it('计算SPI指数', () => {
    const calculateSPI = (actual, planned) => {
      if (planned === 0) return 1
      return Math.round((actual / planned) * 100) / 100
    }
    
    expect(calculateSPI(50, 60)).toBe(0.83)
    expect(calculateSPI(60, 60)).toBe(1)
    expect(calculateSPI(70, 60)).toBe(1.17)
    expect(calculateSPI(0, 0)).toBe(1)
  })
  
  it('判断健康状态', () => {
    const getHealthStatus = (spi) => {
      if (spi >= 0.95) return '绿'
      if (spi >= 0.85) return '黄'
      return '红'
    }
    
    expect(getHealthStatus(1.0)).toBe('绿')
    expect(getHealthStatus(0.95)).toBe('绿')
    expect(getHealthStatus(0.90)).toBe('黄')
    expect(getHealthStatus(0.80)).toBe('红')
  })
})

describe('日期工具函数', () => {
  it('格式化日期', () => {
    const formatDate = (date) => dayjs(date).format('YYYY-MM-DD')
    expect(formatDate('2025-01-15')).toBe('2025-01-15')
  })
  
  it('计算剩余天数', () => {
    const getDaysLeft = (endDate) => {
      return dayjs(endDate).diff(dayjs(), 'day')
    }
    
    const tomorrow = dayjs().add(1, 'day').format('YYYY-MM-DD')
    expect(getDaysLeft(tomorrow)).toBe(1)
  })
  
  it('判断是否逾期', () => {
    const isOverdue = (endDate, status) => {
      if (status === '已完成') return false
      return dayjs(endDate).isBefore(dayjs(), 'day')
    }
    
    const yesterday = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
    expect(isOverdue(yesterday, '进行中')).toBe(true)
    expect(isOverdue(yesterday, '已完成')).toBe(false)
  })
  
  it('判断是否紧急', () => {
    const isUrgent = (endDate, status) => {
      if (status === '已完成') return false
      const days = dayjs(endDate).diff(dayjs(), 'day')
      return days >= 0 && days <= 3
    }
    
    const in2Days = dayjs().add(2, 'day').format('YYYY-MM-DD')
    expect(isUrgent(in2Days, '进行中')).toBe(true)
    
    const in10Days = dayjs().add(10, 'day').format('YYYY-MM-DD')
    expect(isUrgent(in10Days, '进行中')).toBe(false)
  })
})

describe('甘特图计算', () => {
  it('计算任务条位置', () => {
    const calculateTaskPosition = (startDate, endDate, viewStart, dayWidth) => {
      const start = dayjs(startDate)
      const end = dayjs(endDate)
      const viewStartDate = dayjs(viewStart)
      
      const left = start.diff(viewStartDate, 'day') * dayWidth
      const width = (end.diff(start, 'day') + 1) * dayWidth
      
      return { left, width }
    }
    
    const pos = calculateTaskPosition('2025-01-10', '2025-01-15', '2025-01-01', 40)
    expect(pos.left).toBe(9 * 40) // 第10天，索引9
    expect(pos.width).toBe(6 * 40) // 6天
  })
  
  it('拖拽更新日期', () => {
    const updateDatesFromDrag = (task, deltaX, dayWidth) => {
      const deltaDays = Math.round(deltaX / dayWidth)
      return {
        newStart: dayjs(task.start).add(deltaDays, 'day').format('YYYY-MM-DD'),
        newEnd: dayjs(task.end).add(deltaDays, 'day').format('YYYY-MM-DD')
      }
    }
    
    const task = { start: '2025-01-10', end: '2025-01-15' }
    const result = updateDatesFromDrag(task, 120, 40) // 拖动3个单位
    
    expect(result.newStart).toBe('2025-01-13')
    expect(result.newEnd).toBe('2025-01-18')
  })
})

describe('负荷计算', () => {
  it('计算负荷率', () => {
    const calculateLoadRate = (assignedHours, standardHours = 176) => {
      return Math.round((assignedHours / standardHours) * 100)
    }
    
    expect(calculateLoadRate(176)).toBe(100)
    expect(calculateLoadRate(220)).toBe(125)
    expect(calculateLoadRate(88)).toBe(50)
  })
  
  it('判断负荷状态', () => {
    const getLoadStatus = (rate) => {
      if (rate > 100) return 'overload'
      if (rate > 80) return 'high'
      if (rate > 50) return 'normal'
      return 'low'
    }
    
    expect(getLoadStatus(120)).toBe('overload')
    expect(getLoadStatus(90)).toBe('high')
    expect(getLoadStatus(70)).toBe('normal')
    expect(getLoadStatus(40)).toBe('low')
  })
  
  it('计算可用工时', () => {
    const calculateAvailableHours = (loadRate, standardHours = 176) => {
      if (loadRate >= 100) return 0
      return Math.round((1 - loadRate / 100) * standardHours)
    }
    
    expect(calculateAvailableHours(50)).toBe(88)
    expect(calculateAvailableHours(100)).toBe(0)
    expect(calculateAvailableHours(120)).toBe(0)
  })
})

describe('工时计算', () => {
  it('计算周工时合计', () => {
    const calculateWeekTotal = (weekData) => {
      return Object.values(weekData).reduce((sum, hours) => sum + (hours || 0), 0)
    }
    
    const weekData = {
      '2025-01-06': 8,
      '2025-01-07': 9,
      '2025-01-08': 8,
      '2025-01-09': 7,
      '2025-01-10': 8,
      '2025-01-11': 0,
      '2025-01-12': 0
    }
    
    expect(calculateWeekTotal(weekData)).toBe(40)
  })
  
  it('计算加班工时', () => {
    const calculateOvertime = (dailyHours, standardDaily = 8) => {
      return dailyHours.reduce((sum, hours) => {
        return sum + Math.max(0, hours - standardDaily)
      }, 0)
    }
    
    const hours = [8, 10, 9, 8, 11, 0, 0]
    expect(calculateOvertime(hours)).toBe(4) // 2+1+0+0+3 = 6 超过8小时的
  })
})
