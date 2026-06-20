import { useState, useEffect } from 'react'
import '../styles/InterceptAlert.css'

function InterceptAlert({ visible, interceptInfo, onClose, onHandle }) {
  const [isVisible, setIsVisible] = useState(false)
  const [alarmActive, setAlarmActive] = useState(false)

  useEffect(() => {
    if (visible) {
      setIsVisible(true)
      setAlarmActive(true)
      const timer = setTimeout(() => setAlarmActive(false), 3000)
      return () => clearTimeout(timer)
    } else {
      const timer = setTimeout(() => setIsVisible(false), 300)
      return () => clearTimeout(timer)
    }
  }, [visible])

  if (!isVisible && !visible) return null

  const handleClose = () => {
    if (onClose) {
      onClose()
    }
  }

  const handleHandle = () => {
    if (onHandle && interceptInfo) {
      onHandle(interceptInfo.tracking_number)
    }
  }

  return (
    <div className={`intercept-alert-overlay ${visible ? 'show' : 'hide'}`}>
      <div className={`intercept-alert ${alarmActive ? 'alarm-active' : ''} ${visible ? 'animate-slide-in' : ''}`}>
        <div className="alert-header">
          <div className="alert-icon">🚨</div>
          <div className="alert-title">
            <h2>三级拦截</h2>
            <span className="alert-subtitle">THIRD LEVEL INTERCEPT</span>
          </div>
          <button className="close-btn" onClick={handleClose}>✕</button>
        </div>

        <div className="alert-body">
          {interceptInfo && (
            <>
              <div className="alert-section">
                <div className="alert-label">运单号</div>
                <div className="alert-value tracking">
                  {interceptInfo.tracking_number}
                </div>
              </div>

              <div className="alert-section">
                <div className="alert-label">拦截级别</div>
                <div className="alert-level-badge">
                  <span className="level-icon">🔴</span>
                  {interceptInfo.intercept_level || '三级拦截'}
                </div>
              </div>

              <div className="alert-section">
                <div className="alert-label">拦截原因</div>
                <div className="alert-value reason">
                  {interceptInfo.intercept_reason || '未知原因'}
                </div>
              </div>

              {interceptInfo.destination_city && (
                <div className="alert-section">
                  <div className="alert-label">目的地</div>
                  <div className="alert-value">
                    {interceptInfo.destination_city}
                  </div>
                </div>
              )}

              {interceptInfo.package_status && (
                <div className="alert-section">
                  <div className="alert-label">包裹状态</div>
                  <div className="status-badge danger">
                    {interceptInfo.package_status}
                  </div>
                </div>
              )}

              <div className="alert-warning">
                <span className="warning-icon">⚠️</span>
                <span>气动阀已触发，包裹已被物理拦截</span>
              </div>
            </>
          )}
        </div>

        <div className="alert-footer">
          <button className="btn btn-secondary" onClick={handleClose}>
            稍后处理
          </button>
          <button className="btn btn-primary" onClick={handleHandle}>
            确认处理
          </button>
        </div>

        {alarmActive && (
          <div className="alarm-flash"></div>
        )}
      </div>
    </div>
  )
}

export default InterceptAlert
