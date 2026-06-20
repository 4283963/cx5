import HeatmapOverlay from './HeatmapOverlay'
import '../styles/PackageInfo.css'

function PackageInfo({ scanResult, scanImage }) {
  if (!scanResult) return null

  const { ocr_result, intercept_result } = scanResult
  const heatmap = ocr_result?.heatmap

  const getStatusColor = (status) => {
    switch (status) {
      case '正常':
        return 'success'
      case '客户拦截':
      case '疑似违禁品':
        return 'danger'
      default:
        return 'warning'
    }
  }

  return (
    <div className="package-info">
      <div className="package-header">
        <div className="package-icon">📦</div>
        <div className="package-title">
          <div className="package-id">{ocr_result?.tracking_number || '未知'}</div>
          <div className="package-type">快递包裹</div>
        </div>
        {intercept_result?.intercepted ? (
          <div className="intercept-indicator">
            <span className="indicator-dot"></span>
            <span>已拦截</span>
          </div>
        ) : (
          <div className="normal-indicator">
            <span className="indicator-dot"></span>
            <span>正常</span>
          </div>
        )}
      </div>

      {scanImage && (
        <div className="waybill-heatmap-box">
          <div className="box-title">🔍 面单质检热力图</div>
          <HeatmapOverlay imageSrc={scanImage} heatmap={heatmap} />
        </div>
      )}

      <div className="info-grid">
        <div className="info-field">
          <span className="field-label">运单号</span>
          <span className="field-value tracking">
            {ocr_result?.tracking_number || '-'}
          </span>
        </div>

        <div className="info-field">
          <span className="field-label">目的地</span>
          <span className="field-value">
            {ocr_result?.destination_city || '-'}
          </span>
        </div>

        <div className="info-field">
          <span className="field-label">识别置信度</span>
          <span className="field-value confidence">
            {(ocr_result?.confidence * 100).toFixed(1)}%
          </span>
        </div>

        <div className="info-field">
          <span className="field-label">处理耗时</span>
          <span className="field-value">
            {(ocr_result?.processing_time * 1000).toFixed(0)}ms
          </span>
        </div>
      </div>

      {intercept_result?.package_info && (
        <div className="package-details">
          <div className="details-title">详细信息</div>
          <div className="details-grid">
            <div className="detail-item">
              <span className="detail-label">发件人</span>
              <span className="detail-value">
                {intercept_result.package_info.sender || '-'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">收件人</span>
              <span className="detail-value">
                {intercept_result.package_info.receiver || '-'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">重量</span>
              <span className="detail-value">
                {intercept_result.package_info.weight
                  ? `${(intercept_result.package_info.weight / 1000).toFixed(2)} kg`
                  : '-'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">状态</span>
              <span className={`status-badge ${getStatusColor(intercept_result.package_info.status)}`}>
                {intercept_result.package_info.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {intercept_result?.intercepted && (
        <div className="intercept-info-box">
          <div className="intercept-header">
            <span className="intercept-icon">🚫</span>
            <span className="intercept-title">拦截信息</span>
          </div>
          <div className="intercept-content">
            <div className="intercept-row">
              <span>拦截级别</span>
              <span className="level three">
                {intercept_result.intercept_level}
              </span>
            </div>
            <div className="intercept-row">
              <span>拦截原因</span>
              <span>{intercept_result.intercept_reason}</span>
            </div>
            <div className="intercept-row">
              <span>气动阀</span>
              <span className={intercept_result.valve_triggered ? 'success' : 'warning'}>
                {intercept_result.valve_triggered ? '已触发' : '未触发'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PackageInfo
