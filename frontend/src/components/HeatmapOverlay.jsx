import { useEffect, useRef, useState } from 'react'
import '../styles/HeatmapOverlay.css'

function HeatmapOverlay({ imageSrc, heatmap, showRegions = true, showGrid = true }) {
  const canvasRef = useRef(null)
  const [imgLoaded, setImgLoaded] = useState(false)
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 })

  const enabled = heatmap?.enabled === true
  const grid = heatmap?.grid || []
  const rows = heatmap?.grid_rows || 0
  const cols = heatmap?.grid_cols || 0
  const regions = heatmap?.regions || []
  const stats = heatmap?.stats

  useEffect(() => {
    if (!enabled || !showGrid || !imgLoaded || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = Math.max(1, cols)
    canvas.height = Math.max(1, rows)
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const score = grid[r]?.[c] ?? 0
        if (score <= 0.05) continue
        const alpha = Math.min(0.75, 0.15 + score * 0.6)
        ctx.fillStyle = `rgba(244, 67, 54, ${alpha.toFixed(3)})`
        ctx.fillRect(c, r, 1, 1)
      }
    }
  }, [enabled, showGrid, grid, rows, cols, imgLoaded])

  const handleImgLoad = (e) => {
    const img = e.target
    setImgSize({ w: img.naturalWidth, h: img.naturalHeight })
    setImgLoaded(true)
  }

  if (!imageSrc) {
    return (
      <div className="heatmap-overlay empty">
        <div className="empty-icon">📷</div>
        <div className="empty-text">暂无面单图像</div>
      </div>
    )
  }

  return (
    <div className="heatmap-overlay">
      <div className="overlay-stage">
        <img
          src={imageSrc}
          alt="面单原图"
          className="overlay-image"
          onLoad={handleImgLoad}
        />
        {enabled && showGrid && imgLoaded && (
          <canvas
            ref={canvasRef}
            className="overlay-canvas"
            style={{ imageRendering: 'pixelated' }}
          />
        )}
        {enabled && showRegions && regions.map((reg, idx) => (
          <div
            key={idx}
            className={`overlay-region ${reg.issue_type || 'damaged'}`}
            style={{
              left: `${(reg.x * 100).toFixed(2)}%`,
              top: `${(reg.y * 100).toFixed(2)}%`,
              width: `${(reg.w * 100).toFixed(2)}%`,
              height: `${(reg.h * 100).toFixed(2)}%`,
            }}
            title={`${reg.issue_label} · 置信度 ${(reg.confidence * 100).toFixed(0)}%`}
          >
            <span className="region-label">
              {reg.issue_label} {(reg.confidence * 100).toFixed(0)}%
            </span>
          </div>
        ))}
        {!enabled && imgLoaded && (
          <div className="overlay-no-data">无质检热力数据</div>
        )}
      </div>

      {enabled && stats && (
        <div className="overlay-legend">
          <div className="legend-bar">
            <span className="legend-label">低问题</span>
            <div className="legend-gradient"></div>
            <span className="legend-label">高问题</span>
          </div>
          <div className="legend-stats">
            <span>平均置信度: <b>{(stats.avg_confidence * 100).toFixed(1)}%</b></span>
            <span>异常区域: <b className={stats.problem_region_count > 0 ? 'danger' : ''}>{stats.problem_region_count}</b> 处</span>
            <span>异常占比: <b>{(stats.problem_ratio * 100).toFixed(1)}%</b></span>
          </div>
        </div>
      )}
    </div>
  )
}

export default HeatmapOverlay
