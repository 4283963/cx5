import { useState, useEffect } from 'react'
import './styles/App.css'
import ConveyorBelt from './components/ConveyorBelt'
import ScanPanel from './components/ScanPanel'
import InterceptAlert from './components/InterceptAlert'
import PackageInfo from './components/PackageInfo'
import ScanRecords from './components/ScanRecords'
import ValveStatus from './components/ValveStatus'
import { interceptApi } from './services/api'

function App() {
  const [scanResult, setScanResult] = useState(null)
  const [activeIntercepts, setActiveIntercepts] = useState([])
  const [showAlert, setShowAlert] = useState(false)
  const [currentIntercept, setCurrentIntercept] = useState(null)
  const [systemStatus, setSystemStatus] = useState('running')

  useEffect(() => {
    fetchActiveIntercepts()
    const interval = setInterval(fetchActiveIntercepts, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchActiveIntercepts = async () => {
    try {
      const data = await interceptApi.getActiveIntercepts()
      setActiveIntercepts(data)
      if (data.length > 0 && !showAlert) {
        setCurrentIntercept(data[0])
        setShowAlert(true)
        setSystemStatus('danger')
      } else if (data.length === 0) {
        setSystemStatus('running')
      }
    } catch (error) {
      console.error('获取活跃拦截失败:', error)
    }
  }

  const handleScanComplete = (result) => {
    setScanResult(result)
    if (result.intercept_result?.intercepted) {
      setCurrentIntercept({
        tracking_number: result.ocr_result.tracking_number,
        intercept_level: result.intercept_result.intercept_level,
        intercept_reason: result.intercept_result.intercept_reason,
        package_status: result.intercept_result.package_info?.status,
        destination_city: result.ocr_result.destination_city,
      })
      setShowAlert(true)
      setSystemStatus('danger')
    }
  }

  const handleAlertClose = () => {
    setShowAlert(false)
    setCurrentIntercept(null)
    fetchActiveIntercepts()
  }

  const handleHandleIntercept = async (trackingNumber) => {
    try {
      await interceptApi.handleIntercept(trackingNumber, '操作员')
      setShowAlert(false)
      setCurrentIntercept(null)
      fetchActiveIntercepts()
    } catch (error) {
      console.error('处理拦截失败:', error)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>
          <span className="header-icon">📦</span>
          智慧物流分拨中心 - 快递面单无损扫描与拦截系统
        </h1>
        <div className="header-status">
          <div className="status-item">
            <span className={`status-dot ${systemStatus}`}></span>
            <span>系统状态: {systemStatus === 'running' ? '运行正常' : '拦截告警'}</span>
          </div>
          <div className="status-item">
            <span>活跃拦截: </span>
            <span style={{ color: activeIntercepts.length > 0 ? '#f44336' : '#4caf50', fontWeight: 600 }}>
              {activeIntercepts.length} 件
            </span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="main-panel">
          <div className="panel-card">
            <div className="panel-header">
              <h2>🎥 传送带操作台</h2>
              <span style={{ fontSize: 12, color: '#78909c' }}>一号传送带 · CONV-001</span>
            </div>
            <div className="panel-content">
              <ConveyorBelt onScanComplete={handleScanComplete} />
            </div>
          </div>

          <div className="panel-card">
            <div className="panel-header">
              <h2>📋 扫描操作</h2>
            </div>
            <div className="panel-content">
              <ScanPanel onScanComplete={handleScanComplete} />
            </div>
          </div>

          <div className="panel-card">
            <div className="panel-header">
              <h2>📊 最近扫描记录</h2>
            </div>
            <div className="panel-content">
              <ScanRecords />
            </div>
          </div>
        </div>

        <div className="side-panel">
          {scanResult && (
            <div className="panel-card">
              <div className="panel-header">
                <h2>📦 当前包裹信息</h2>
              </div>
              <div className="panel-content">
                <PackageInfo scanResult={scanResult} />
              </div>
            </div>
          )}

          <div className="panel-card">
            <div className="panel-header">
              <h2>⚙️ 气动阀状态</h2>
            </div>
            <div className="panel-content">
              <ValveStatus />
            </div>
          </div>
        </div>
      </main>

      <InterceptAlert
        visible={showAlert}
        interceptInfo={currentIntercept}
        onClose={handleAlertClose}
        onHandle={handleHandleIntercept}
      />
    </div>
  )
}

export default App
