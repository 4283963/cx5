import { useState, useEffect } from 'react'
import { interceptApi } from '../services/api'
import '../styles/ValveStatus.css'

function ValveStatus() {
  const [valves, setValves] = useState([])
  const [loading, setLoading] = useState(false)
  const [triggering, setTriggering] = useState(false)

  useEffect(() => {
    fetchValves()
    const interval = setInterval(fetchValves, 2000)
    return () => clearInterval(interval)
  }, [])

  const fetchValves = async () => {
    try {
      setLoading(true)
      const data = await interceptApi.getAllValves()
      setValves(data.valves || [])
    } catch (error) {
      console.error('获取气动阀状态失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTrigger = async (valveId) => {
    if (triggering) return
    try {
      setTriggering(true)
      await interceptApi.triggerValve(valveId, 2.0)
      await fetchValves()
    } catch (error) {
      console.error('触发气动阀失败:', error)
    } finally {
      setTriggering(false)
    }
  }

  const handleToggle = async (valveId, currentStatus) => {
    try {
      const action = currentStatus === 'open' ? 'close' : 'open'
      await interceptApi.controlValve(valveId, action)
      await fetchValves()
    } catch (error) {
      console.error('控制气动阀失败:', error)
    }
  }

  const formatLastTrigger = (timeStr) => {
    if (!timeStr) return '从未触发'
    const date = new Date(timeStr)
    return date.toLocaleTimeString('zh-CN', { hour12: false })
  }

  return (
    <div className="valve-status">
      {valves.map((valve) => (
        <div key={valve.id} className={`valve-card ${valve.status}`}>
          <div className="valve-header">
            <div className="valve-icon">
              {valve.status === 'open' ? '🔵' : '⚪'}
            </div>
            <div className="valve-info">
              <div className="valve-name">{valve.name}</div>
              <div className="valve-id">{valve.id}</div>
            </div>
            <div className={`valve-status-badge ${valve.status}`}>
              {valve.status === 'open' ? '开启' : '关闭'}
            </div>
          </div>

          <div className="valve-details">
            <div className="detail-row">
              <span className="detail-label">所属传送带</span>
              <span className="detail-value">{valve.conveyor_id}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">累计触发</span>
              <span className="detail-value">{valve.trigger_count} 次</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">最近触发</span>
              <span className="detail-value">{formatLastTrigger(valve.last_trigger)}</span>
            </div>
          </div>

          <div className="valve-actions">
            <button
              className={`action-btn trigger-btn ${triggering ? 'triggering' : ''}`}
              onClick={() => handleTrigger(valve.id)}
              disabled={triggering || valve.status === 'open'}
            >
              {triggering ? '触发中...' : '脉冲触发'}
            </button>
            <button
              className={`action-btn toggle-btn ${valve.status}`}
              onClick={() => handleToggle(valve.id, valve.status)}
            >
              {valve.status === 'open' ? '关闭阀门' : '开启阀门'}
            </button>
          </div>

          {valve.status === 'open' && (
            <div className="valve-active-indicator">
              <div className="active-pulse"></div>
              <span>阀门工作中</span>
            </div>
          )}
        </div>
      ))}

      {valves.length === 0 && !loading && (
        <div className="no-valves">暂无气动阀数据</div>
      )}
    </div>
  )
}

export default ValveStatus
