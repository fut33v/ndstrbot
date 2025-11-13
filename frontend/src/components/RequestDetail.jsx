import React, { useState, useEffect } from 'react';
import { getRequestById, getFilesByRequestId, getTemplateById } from '../services/api';
import './RequestDetail.css';

function RequestDetail({ requestId, onBack }) {
  const [request, setRequest] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [templateInfo, setTemplateInfo] = useState(null);
  const [templateLoading, setTemplateLoading] = useState(false);

  useEffect(() => {
    const loadRequestDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const requestData = await getRequestById(requestId);
        const filesData = await getFilesByRequestId(requestId);
        setRequest(requestData);
        setFiles(filesData);
        if (requestData.selected_template_id) {
          setTemplateLoading(true);
          try {
            const template = await getTemplateById(requestData.selected_template_id);
            setTemplateInfo(template);
          } catch (templateErr) {
            console.error('Error loading template info:', templateErr);
            setTemplateInfo(null);
          } finally {
            setTemplateLoading(false);
          }
        } else {
          setTemplateInfo(null);
          setTemplateLoading(false);
        }
      } catch (err) {
        console.error('Error loading request details:', err);
        setError('Failed to load request details');
      } finally {
        setLoading(false);
      }
    };

    if (requestId) {
      loadRequestDetails();
    }
  }, [requestId]);

  if (loading) {
    return <div className="loading">Загрузка деталей заявки...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={onBack} className="back-button">← Назад к заявкам</button>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="error-container">
        <p className="error-message">Заявка не найдена</p>
        <button onClick={onBack} className="back-button">← Назад к заявкам</button>
      </div>
    );
  }

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'submitted':
        return 'status-badge status-submitted';
      case 'approved':
        return 'status-badge status-approved';
      case 'rejected':
        return 'status-badge status-rejected';
      case 'pending':
        return 'status-badge status-pending';
      default:
        return 'status-badge';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'submitted':
        return 'Отправлена';
      case 'approved':
        return 'Одобрена';
      case 'rejected':
        return 'Отклонена';
      case 'pending':
        return 'Ожидает';
      default:
        return status;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Н/Д';
    return new Date(dateString).toLocaleString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="request-detail">
      <div className="detail-header">
        <button onClick={onBack} className="back-button">← Назад к заявкам</button>
        <h2>Заявка #{request.id}</h2>
      </div>

      <div className="detail-content">
        <div className="detail-section">
          <h3>Информация о заявке</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <label>ID:</label>
              <span>{request.id}</span>
            </div>
            <div className="detail-item">
              <label>ID пользователя:</label>
              <span>{request.user_id}</span>
            </div>
            <div className="detail-item">
              <label>Telegram:</label>
              {request.username ? (
                <a
                  href={`https://t.me/${request.username.replace('@', '')}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {request.username.startsWith('@') ? request.username : `@${request.username}`}
                </a>
              ) : (
                <span>Не указан</span>
              )}
            </div>
            <div className="detail-item">
              <label>Категория:</label>
              <span className="category-badge">{request.category || 'Н/Д'}</span>
            </div>
            <div className="detail-item">
              <label>Статус:</label>
              <span className={getStatusBadgeClass(request.status)}>
                {getStatusText(request.status || 'pending')}
              </span>
            </div>
          </div>
        </div>

        <div className="detail-section">
          <h3>Информация об автомобиле</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <label>Есть бренд:</label>
              <span>{request.has_brand ? '✅ Да' : '❌ Нет'}</span>
            </div>
            <div className="detail-item">
              <label>Год выпуска:</label>
              <span>{request.year || 'Н/Д'}</span>
            </div>
            <div className="detail-item">
              <label>Есть лицензия:</label>
              <span>{request.has_license ? '✅ Да' : '❌ Нет'}</span>
            </div>
            <div className="detail-item">
              <label>Опция лицензии:</label>
              <span>{request.license_option || 'Н/Д'}</span>
            </div>
            <div className="detail-item" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <label style={{ marginBottom: '0.5rem' }}>Выбранный макет:</label>
              {request.selected_template_id ? (
                templateLoading ? (
                  <span>Загрузка...</span>
                ) : templateInfo ? (
                  <div className="template-preview">
                    <div style={{ marginBottom: '0.25rem' }}>
                      #{templateInfo.id} — {templateInfo.name || 'Без названия'}
                    </div>
                    <a
                      href={`/api/templates/${templateInfo.id}/preview`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <img
                        src={`/api/templates/${templateInfo.id}/preview`}
                        alt={templateInfo.name || 'Макет'}
                        style={{
                          maxWidth: '220px',
                          maxHeight: '140px',
                          borderRadius: '6px',
                          border: '1px solid #ddd',
                          objectFit: 'cover'
                        }}
                      />
                    </a>
                  </div>
                ) : (
                  <span>#{request.selected_template_id}</span>
                )
              ) : (
                <span>Не выбрано</span>
              )}
            </div>
          </div>
        </div>

        <div className="detail-section">
          <h3>Временные метки</h3>
          <div className="detail-grid">
            <div className="detail-item">
              <label>Создана:</label>
              <span>{formatDate(request.created_at)}</span>
            </div>
            <div className="detail-item">
              <label>Отправлена:</label>
              <span>{formatDate(request.submitted_at)}</span>
            </div>
            <div className="detail-item">
              <label>Обработана:</label>
              <span>{formatDate(request.processed_at)}</span>
            </div>
          </div>
        </div>

        {request.notes && (
          <div className="detail-section">
            <h3>Примечания</h3>
            <div className="notes-content">
              <p>{request.notes}</p>
            </div>
          </div>
        )}

        <div className="detail-section">
          <h3>Фотографии ({files.filter(f => f.kind === 'auto_photo' || f.kind === 'sts_photo').length})</h3>
          {files.filter(f => f.kind === 'auto_photo' || f.kind === 'sts_photo').length > 0 ? (
            <div className="photo-grid">
              {files.filter(f => f.kind === 'auto_photo' || f.kind === 'sts_photo').map((file) => (
                <div 
                  key={file.id} 
                  className="photo-thumbnail"
                  onClick={() => setSelectedImage(`/api/uploads/${file.path.split('/').pop()}`)}
                >
                  <img 
                    src={`/api/uploads/${file.path.split('/').pop()}`} 
                    alt="Фото"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.classList.add('error');
                    }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="no-files">К этой заявке нет прикрепленных фотографий</p>
          )}
        </div>
      </div>

      {/* Modal for image preview */}
      {selectedImage && (
        <div className="image-modal" onClick={() => setSelectedImage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-button" onClick={() => setSelectedImage(null)}>×</button>
            <img src={selectedImage} alt="Увеличенное фото" />
          </div>
        </div>
      )}
    </div>
  );
}

export default RequestDetail;
