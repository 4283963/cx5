import { useState, useEffect } from 'react'
import { scanApi } from '../services/api'
import '../styles/ScanRecords.css'

function ScanRecords() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchRecords()
    const interval = setInterval(fetchRecords, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchRecords = async () => {
    try {
      setLoading(true)
      const data = await scanApi.getScanRecords({ limit: 10 })
      setRecords(data.records || [])
    } catch (error) {
      console.error('获取扫描记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timeStr) => {
    if (!timeStr) return '-'
    const date = new Date(timeStr)
    return date.toLocaleTimeString('zh-CN', { hour12: false })
  }

  return (
    <div className="scan-records">
      <div className="records-header">
        <span className="records-title">最近扫描记录</span>
        <span className="records-count">共 {records.length} 条</span>
      </div>

      {loading && records.length === 0 ? (
        <div className="loading-state">加载中...</div>
      ) : records.length === 0 ? (
        <div className="empty-state">暂无扫描记录</div>
      ) : (
        <div className="records-table-container">
          <table className="records-table">
            <thead>
              <tr>
                <th>运单号</th>
                <th>目的地</th>
                <th>置信度</th>
                <th>状态</th>
                <th>扫描时间</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record, index) => (
                <tr
                  key={record.id || index}
                  className={record.is_intercepted ? 'intercepted-row' : ''}
                >
                  <td className="tracking-cell">
                    <span className="tracking-text">{record.tracking_number}</span>
                  </td>
                  <td>{record.destination_city || '-'}</td>
                  <td>
                    <span className={`confidence-badge ${
                      (record.recognition_confidence || 0) >= 90 ? 'high' :
                      (record.recognition_confidence || 0) >= 70 ? 'medium' : 'low'
                    }`}>
                      {record.recognition_confidence || 0}%
                    </span>
                  </td>
                  <td>
                    {record.is_intercepted ? (
                      <span className="status-tag intercepted">
                        {record.intercept_level || '拦截'}
                      </span>
                    ) : (
                      <span className="status-tag normal">正常</span>
                    )}
                  </td>
                  <td className="time-cell">{formatTime(record.scan_time)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default ScanRecords
