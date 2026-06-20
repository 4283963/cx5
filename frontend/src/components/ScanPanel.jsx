import { useState, useRef } from 'react'
import { scanApi } from '../services/api'
import '../styles/ScanPanel.css'

function ScanPanel({ onScanComplete }) {
  const [isUploading, setIsUploading] = useState(false)
  const [previewImage, setPreviewImage] = useState(null)
  const [scanHistory, setScanHistory] = useState([])
  const fileInputRef = useRef(null)

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      setPreviewImage(e.target.result)
    }
    reader.readAsDataURL(file)

    setIsUploading(true)
    try {
      const result = await scanApi.scanWaybill(file, 'CONV-001')

      setScanHistory(prev => [
        {
          id: Date.now(),
          trackingNumber: result.ocr_result.tracking_number,
          city: result.ocr_result.destination_city,
          confidence: result.ocr_result.confidence,
          intercepted: result.intercept_result?.intercepted,
          time: new Date().toLocaleTimeString()
        },
        ...prev.slice(0, 9)
      ])

      if (onScanComplete) {
        onScanComplete(result)
      }
    } catch (error) {
      console.error('扫描失败:', error)
      alert('扫描识别失败，请重试')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = async (event) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      setPreviewImage(e.target.result)
    }
    reader.readAsDataURL(file)

    setIsUploading(true)
    try {
      const result = await scanApi.scanWaybill(file, 'CONV-001')

      setScanHistory(prev => [
        {
          id: Date.now(),
          trackingNumber: result.ocr_result.tracking_number,
          city: result.ocr_result.destination_city,
          confidence: result.ocr_result.confidence,
          intercepted: result.intercept_result?.intercepted,
          time: new Date().toLocaleTimeString()
        },
        ...prev.slice(0, 9)
      ])

      if (onScanComplete) {
        onScanComplete(result)
      }
    } catch (error) {
      console.error('扫描失败:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="scan-panel">
      <div className="upload-section">
        <div
          className={`upload-area ${isUploading ? 'uploading' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={triggerFileInput}
        >
          {previewImage ? (
            <div className="preview-container">
              <img src={previewImage} alt="预览" className="preview-image" />
              {isUploading && (
                <div className="upload-overlay">
                  <div className="loading-spinner"></div>
                  <span>识别中...</span>
                </div>
              )}
            </div>
          ) : (
            <div className="upload-placeholder">
              <div className="upload-icon">📄</div>
              <div className="upload-text">点击或拖拽面单图片到此处</div>
              <div className="upload-hint">支持 JPG、PNG、BMP 格式</div>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      <div className="history-section">
        <div className="history-header">
          <h3>最近识别记录</h3>
          <span className="history-count">{scanHistory.length} 条</span>
        </div>
        <div className="history-list">
          {scanHistory.length === 0 ? (
            <div className="empty-history">暂无识别记录</div>
          ) : (
            scanHistory.map(item => (
              <div key={item.id} className={`history-item ${item.intercepted ? 'intercepted' : ''}`}>
                <div className="history-main">
                  <span className="tracking-number">{item.trackingNumber}</span>
                  <span className="destination-city">{item.city}</span>
                </div>
                <div className="history-sub">
                  <span className="confidence">置信度: {(item.confidence * 100).toFixed(1)}%</span>
                  <span className="scan-time">{item.time}</span>
                </div>
                {item.intercepted && <span className="intercept-badge">拦截</span>}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default ScanPanel
