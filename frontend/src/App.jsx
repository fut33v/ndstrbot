import React, { useState, useEffect } from 'react';
import { 
  getUsers, 
  getAdmins, 
  getRequests, 
  getCurrentUser,
  logout,
  addAdmin,
  getTemplates,
  getTemplateById,
  deleteTemplate,
  uploadTemplate
} from './services/api';
import DataTable from './components/DataTable';
import StatsCard from './components/StatsCard';
import RequestDetail from './components/RequestDetail';
import Login from './components/Login';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState(null);
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateFile, setTemplateFile] = useState(null);
  const [uploadingTemplate, setUploadingTemplate] = useState(false);

  const formatShortDate = (value) => {
    if (!value) return '—';
    try {
      return new Date(value).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch (error) {
      return value;
    }
  };

  // Проверка авторизации при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      setAuthLoading(true);
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Auth check error:', error);
        setUser(null);
      } finally {
        setAuthLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleAddAdmin = async () => {
    if (!selectedUserId) return;
    try {
      await addAdmin(selectedUserId);
      await loadData(getAdmins, 'admins');
      // Reset selection
      setSelectedUserId(null);
    } catch (error) {
      console.error('Add admin error:', error);
      alert('Не удалось добавить администратора');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      setUser(null);
      setData({});
      setActiveTab('dashboard');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleTemplateUpload = async () => {
    if (!templateName || !templateFile) return;
    
    setUploadingTemplate(true);
    try {
      await uploadTemplate(templateName, templateDescription, templateFile);
      // Reset form
      setTemplateName('');
      setTemplateDescription('');
      setTemplateFile(null);
      // Reload templates
      await loadData(getTemplates, 'templates');
    } catch (error) {
      console.error('Template upload error:', error);
      alert('Не удалось загрузить шаблон: ' + error.message);
    } finally {
      setUploadingTemplate(false);
    }
  };

  const handleTemplateDelete = async (templateId) => {
    const confirmed = window.confirm('Удалить макет? Это действие нельзя отменить.');
    if (!confirmed) return;
    try {
      await deleteTemplate(templateId);
      await loadData(getTemplates, 'templates');
    } catch (error) {
      console.error('Template delete error:', error);
      alert('Не удалось удалить макет: ' + error.message);
    }
  };

  // Функция для загрузки данных из API
  const loadData = async (loader, key) => {
    try {
      let result = await loader();
      // Сортировка заявок по ID в обратном порядке (сначала новые)
      if (key === 'requests' && Array.isArray(result)) {
        result = result.sort((a, b) => b.id - a.id);
      }
      setData(prev => ({ ...prev, [key]: result }));
    } catch (error) {
      console.error(`Error loading ${key}:`, error);
    }
  };

  // Загрузка данных для дашборда при монтировании
  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          loadData(getUsers, 'users'),
          loadData(getAdmins, 'admins'),
          loadData(getRequests, 'requests'),
          loadData(getTemplates, 'templates')
        ]);
      } finally {
        setLoading(false);
      }
    };

    if (activeTab === 'dashboard') {
      loadDashboardData();
    } else {
      setLoading(true);
      switch (activeTab) {
        case 'users':
          loadData(getUsers, 'users');
          break;
        case 'admins':
          // Load admins and users for selector
          loadData(getAdmins, 'admins');
          loadData(getUsers, 'users');
          break;
        case 'requests':
          loadData(getRequests, 'requests');
          break;
        case 'templates':
          loadData(getTemplates, 'templates');
          break;
        default:
          setLoading(false);
      }
    }
  }, [activeTab]);

  // Определение колонок для разных таблиц
  const userColumns = [
    { header: 'ID', key: 'id' },
    { header: 'Telegram ID', key: 'tg_id' },
    { header: 'Username', key: 'username' },
    { header: 'First Name', key: 'first_name' },
    { header: 'Last Name', key: 'last_name' },
    { header: 'Created At', key: 'created_at' },
    { header: 'Last Seen', key: 'last_seen' }
  ];

  const adminColumns = [
    { header: 'ID', key: 'id' },
    { header: 'Telegram ID', key: 'tg_id' },
    { header: 'Username', key: 'username' },
    { header: 'First Name', key: 'first_name' },
    { header: 'Last Name', key: 'last_name' },
    { header: 'Added At', key: 'added_at' },
    { header: 'Added By', key: 'added_by' }
  ];

  const requestColumns = [
    { header: 'ID', key: 'id' },
    {
      header: 'ID пользователя',
      key: 'user_id',
      render: (value, row) => {
        if (row.username) {
          const username = row.username.startsWith('@') ? row.username : `@${row.username}`;
          return (
            <a href={`https://t.me/${username.replace('@', '')}`} target="_blank" rel="noreferrer">
              {value} ({username})
            </a>
          );
        }
        return value;
      }
    },
    { header: 'Категория', key: 'category' },
    { header: 'Статус', key: 'status', render: (value) => {
      const map = {
        submitted: 'Отправлена',
        approved: 'Одобрена',
        rejected: 'Отклонена',
        pending: 'Ожидает',
        draft: 'Черновик'
      };
      return map[value] || value || '—';
    } },
    { header: 'Бренд', key: 'has_brand', render: (value) => value === null ? '—' : value ? 'Да' : 'Нет' },
    { header: 'Год', key: 'year', render: (value) => value || '—' },
    { header: 'Лицензия', key: 'has_license', render: (value) => value === null ? '—' : value ? 'Да' : 'Нет' },
    {
      header: 'Макет',
      key: 'selected_template_id',
      render: (value) => value ? `#${value}` : '—'
    },
    { header: 'Дата создания', key: 'created_at', render: (value) => formatShortDate(value) }
  ];

  const templateColumns = [
    { header: 'ID', key: 'id' },
    { header: 'Название', key: 'name' },
    { header: 'Описание', key: 'description', render: (value) => value || '—' },
    {
      header: 'Предпросмотр',
      key: 'preview',
      render: (_, item) => (
        <a
          href={`/api/templates/${item.id}/preview`}
          target="_blank"
          rel="noreferrer"
        >
          <img
            src={`/api/templates/${item.id}/preview`}
            alt={item.name}
            style={{ maxWidth: '160px', maxHeight: '100px', objectFit: 'cover', borderRadius: '4px' }}
          />
        </a>
      )
    },
    {
      header: 'Действия',
      key: 'actions',
      render: (_, item) => (
        <button
          style={{ padding: '0.25rem 0.75rem', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          onClick={(e) => {
            e.stopPropagation();
            handleTemplateDelete(item.id);
          }}
        >
          Удалить
        </button>
      )
    }
  ];





  const handleRequestClick = (request) => {
    setSelectedRequestId(request.id);
  };

  const handleBackToRequests = () => {
    setSelectedRequestId(null);
  };

  // Показываем индикатор загрузки при проверке авторизации
  if (authLoading) {
    return <div className="loading">Загрузка...</div>;
  }

  // Показываем страницу логина, если пользователь не авторизован
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>Яндекс GO Регистрация Автомобилей - Панель Администратора</h1>
        <div className="header-user-info">
          <span className="user-name">{user.first_name} {user.last_name}</span>
          {user.username && <span className="user-username">@{user.username}</span>}
          <button onClick={handleLogout} className="logout-button">Выйти</button>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''} 
          onClick={() => setActiveTab('dashboard')}
        >
          Панель управления
        </button>
        <button 
          className={activeTab === 'users' ? 'active' : ''} 
          onClick={() => setActiveTab('users')}
        >
          Пользователи
        </button>
        <button 
          className={activeTab === 'admins' ? 'active' : ''} 
          onClick={() => setActiveTab('admins')}
        >
          Администраторы
        </button>
        <button 
          className={activeTab === 'requests' ? 'active' : ''} 
          onClick={() => setActiveTab('requests')}
        >
          Заявки
        </button>
        <button 
          className={activeTab === 'templates' ? 'active' : ''} 
          onClick={() => setActiveTab('templates')}
        >
          Устаревшие макеты
        </button>

      </nav>

      <main className="app-main">
        {loading && <div className="loading">Загрузка...</div>}
        
        {activeTab === 'dashboard' && (
          <div className="dashboard">
            <h2>Панель управления</h2>
            <div className="stats-grid">
              <StatsCard 
                title="Пользователи" 
                value={data.users ? data.users.length : 0} 
              />
              <StatsCard 
                title="Администраторы" 
                value={data.admins ? data.admins.length : 0} 
              />
              <StatsCard 
                title="Заявки" 
                value={data.requests ? data.requests.length : 0} 
              />
              <StatsCard 
                title="Устаревшие макеты" 
                value={data.templates ? data.templates.length : 0} 
              />

            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <DataTable 
            data={data.users} 
            columns={userColumns} 
            title="Пользователи" 
          />
        )}

        {activeTab === 'admins' && (
          <>
            <div className="admin-actions" style={{marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
              <select 
                value={selectedUserId || ''} 
                onChange={(e) => setSelectedUserId(Number(e.target.value) || null)}
              >
                <option value="">Выберите пользователя</option>
                {Array.isArray(data.users) && data.users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.first_name || ''} {u.last_name || ''} {u.username ? `(@${u.username})` : ''} — TG: {u.tg_id}
                  </option>
                ))}
              </select>
              <button onClick={handleAddAdmin}>Добавить администратора</button>
            </div>
            <DataTable 
              data={data.admins} 
              columns={adminColumns} 
              title="Администраторы" 
            />
          </>
        )}

        {activeTab === 'requests' && (
          selectedRequestId ? (
            <RequestDetail 
              requestId={selectedRequestId} 
              onBack={handleBackToRequests}
            />
          ) : (
            <DataTable 
              data={data.requests} 
              columns={requestColumns} 
              title="Заявки"
              onRowClick={handleRequestClick}
            />
          )
        )}

        {activeTab === 'templates' && (
          <>
            <div className="template-upload" style={{marginBottom: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '4px'}}>
              <h3>Загрузить новый макет</h3>
              <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                <input 
                  type="text" 
                  placeholder="Название макета" 
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  style={{padding: '0.5rem'}}
                />
                <textarea 
                  placeholder="Описание макета (необязательно)" 
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  style={{padding: '0.5rem', minHeight: '60px'}}
                />
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={(e) => setTemplateFile(e.target.files[0])}
                  style={{padding: '0.5rem'}}
                />
                <button 
                  onClick={handleTemplateUpload}
                  disabled={!templateName || !templateFile}
                  style={{padding: '0.5rem', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                >
                  Загрузить макет
                </button>
                {uploadingTemplate && <div>Загрузка...</div>}
              </div>
            </div>
            <DataTable 
              data={data.templates} 
              columns={templateColumns} 
              title="Устаревшие макеты" 
            />
          </>
        )}


      </main>
    </div>
  );
}

export default App;
