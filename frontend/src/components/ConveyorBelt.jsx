import { useState, useEffect, useRef } from 'react'
import { scanApi } from '../services/api'
import HeatmapOverlay from './HeatmapOverlay'
import '../styles/ConveyorBelt.css'

function ConveyorBelt({ onScanComplete }) {
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [packages, setPackages] = useState([])
  const [cameraActive, setCameraActive] = useState(true)
  const canvasRef = useRef(null)
  const videoRef = useRef(null)
  const [useCamera, setUseCamera] = useState(false)
  const [lastScanImage, setLastScanImage] = useState(null)
  const [lastHeatmap, setLastHeatmap] = useState(null)

  useEffect(() => {
    if (useCamera && cameraActive) {
      startCamera()
    }
    return () => {
      stopCamera()
    }
  }, [useCamera, cameraActive])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 }
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (error) {
      console.error('无法访问摄像头:', error)
      alert('无法访问摄像头，将使用模拟模式')
    }
  }

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks()
      tracks.forEach(track => track.stop())
    }
  }

  const simulateScan = async () => {
    if (isScanning) return

    setIsScanning(true)
    setScanProgress(0)

    const newPackage = {
      id: Date.now(),
      position: 10,
      status: 'moving',
      trackingNumber: '',
    }
    setPackages(prev => [...prev, newPackage])

    const interval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          return 100
        }
        return prev + 5
      })

      setPackages(prev => prev.map(pkg =>
        pkg.id === newPackage.id
          ? { ...pkg, position: pkg.position + 3 }
          : pkg
      ))
    }, 100)

    setTimeout(async () => {
      clearInterval(interval)

      try {
        if (useCamera && videoRef.current) {
          const canvas = document.createElement('canvas')
          canvas.width = videoRef.current.videoWidth
          canvas.height = videoRef.current.videoHeight
          canvas.getContext('2d').drawImage(videoRef.current, 0, 0)
          const imageData = canvas.toDataURL('image/jpeg', 0.8)

          const result = await scanApi.scanWaybillBase64(imageData, 'CONV-001')
          setPackages(prev => prev.map(pkg =>
            pkg.id === newPackage.id
              ? {
                  ...pkg,
                  status: result.intercept_result?.intercepted ? 'intercepted' : 'scanned',
                  trackingNumber: result.ocr_result.tracking_number,
                  result: result
                }
              : pkg
          ))

          setLastScanImage(imageData)
          setLastHeatmap(result.ocr_result?.heatmap || null)

          if (onScanComplete) {
            onScanComplete(result, imageData)
          }
        } else {
          const sampleImages = [
            createMockImageData('SF1234567890123'),
            createMockImageData('YT9876543210987'),
            createMockImageData('ZTO5678901234567'),
            createMockImageData('JD1122334455667'),
          ]
          const randomImage = sampleImages[Math.floor(Math.random() * sampleImages.length)]

          const result = await scanApi.scanWaybillBase64(randomImage, 'CONV-001')
          setPackages(prev => prev.map(pkg =>
            pkg.id === newPackage.id
              ? {
                  ...pkg,
                  status: result.intercept_result?.intercepted ? 'intercepted' : 'scanned',
                  trackingNumber: result.ocr_result.tracking_number,
                  result: result
                }
              : pkg
          ))

          setLastScanImage(randomImage)
          setLastHeatmap(result.ocr_result?.heatmap || null)

          if (onScanComplete) {
            onScanComplete(result, randomImage)
          }
        }
      } catch (error) {
        console.error('扫描失败:', error)
        setPackages(prev => prev.map(pkg =>
          pkg.id === newPackage.id
            ? { ...pkg, status: 'error' }
            : pkg
        ))
      } finally {
        setIsScanning(false)
        setScanProgress(0)

        setTimeout(() => {
          setPackages(prev => prev.filter(pkg => pkg.id !== newPackage.id))
        }, 3000)
      }
    }, 2000)
  }

  const createMockImageData = (trackingNumber) => {
    const canvas = document.createElement('canvas')
    canvas.width = 400
    canvas.height = 200
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, 400, 200)
    ctx.fillStyle = '#000000'
    ctx.font = 'bold 20px Arial'
    ctx.fillText(trackingNumber, 50, 100)
    ctx.fillText('目的地: 测试城市', 50, 140)
    return canvas.toDataURL('image/jpeg')
  }

  const toggleCamera = () => {
    setUseCamera(!useCamera)
  }

  return (
    <div className="conveyor-container">
      <div className="camera-section">
        <div className="camera-view">
          {useCamera ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="camera-feed"
            />
          ) : (
            <div className="camera-placeholder">
              <div className="scan-line"></div>
              <div className="placeholder-icon">📷</div>
              <div className="placeholder-text">高空相机预览</div>
              <div className="placeholder-subtext">产线 CAM-001 · 1080P</div>
            </div>
          )}
          <div className="camera-overlay">
            <div className="scan-frame">
              <div className="corner top-left"></div>
              <div className="corner top-right"></div>
              <div className="corner bottom-left"></div>
              <div className="corner bottom-right"></div>
              {isScanning && <div className="scanning-line"></div>}
            </div>
          </div>
        </div>
        <div className="camera-controls">
          <button
            className={`control-btn ${useCamera ? 'active' : ''}`}
            onClick={toggleCamera}
          >
            {useCamera ? '📷 实机模式' : '🎭 模拟模式'}
          </button>
          <button
            className={`control-btn primary ${isScanning ? 'scanning' : ''}`}
            onClick={simulateScan}
            disabled={isScanning}
          >
            {isScanning ? '⏳ 扫描中...' : '🔍 开始扫描'}
          </button>
        </div>
      </div>

      <div className="qc-section">
        <div className="qc-header">
          <h3>🔍 质检热力图</h3>
          {lastHeatmap?.enabled ? (
            <span className="qc-hint">红色阴影区域为条码划痕/污损/看不清处</span>
          ) : (
            <span className="qc-hint muted">扫描后将显示异常区域</span>
          )}
        </div>
        <HeatmapOverlay imageSrc={lastScanImage} heatmap={lastHeatmap} />
      </div>

      <div className="conveyor-section">
        <div className="conveyor-label">
          <span>一号传送带 CONV-001</span>
          <span className="conveyor-status running">运行中</span>
        </div>
        <div className="conveyor-belt">
          <div className="belt-surface"></div>
          <div className="belt-rollers">
            <div className="roller"></div>
            <div className="roller"></div>
          </div>
          {packages.map(pkg => (
            <div
              key={pkg.id}
              className={`package package-${pkg.status}`}
              style={{ left: `${pkg.position}%` }}
            >
              <div className="package-icon">📦</div>
              {pkg.trackingNumber && (
                <div className="package-label">{pkg.trackingNumber.slice(0, 8)}...</div>
              )}
            </div>
          ))}
          <div className="scan-station">
            <div className="station-icon">📷</div>
            <div className="station-label">扫描工位</div>
          </div>
          <div className="intercept-station">
            <div className="station-icon">🚫</div>
            <div className="station-label">拦截工位</div>
          </div>
        </div>
        <div className="conveyor-info">
          <div className="info-item">
            <span className="info-label">速度</span>
            <span className="info-value">60 件/分钟</span>
          </div>
          <div className="info-item">
            <span className="info-label">今日扫描</span>
            <span className="info-value">1,234 件</span>
          </div>
          <div className="info-item">
            <span className="info-label">拦截数量</span>
            <span className="info-value danger">3 件</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConveyorBelt
