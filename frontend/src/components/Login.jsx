import React, { useEffect, useState } from 'react';
import './Login.css';

function Login({ onLogin }) {
  const [botUsername, setBotUsername] = useState('ndstrbot');

  useEffect(() => {
    // Load bot username from config
    const loadConfig = async () => {
      try {
        const response = await fetch('/api/config');
        if (response.ok) {
          const config = await response.json();
          setBotUsername(config.bot_username);
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };
    
    loadConfig();
  }, []);

  useEffect(() => {
    // Add Telegram Login Widget script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', botUsername);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    // Define global callback for Telegram widget
    window.onTelegramAuth = async (user) => {
      try {
        const response = await fetch('/api/auth/telegram', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(user)
        });

        if (!response.ok) {
          const error = await response.json();
          alert(error.detail || 'Ошибка авторизации');
          return;
        }

        const data = await response.json();
        if (data.success) {
          onLogin(data.user);
        }
      } catch (error) {
        console.error('Auth error:', error);
        alert('Ошибка при авторизации');
      }
    };

    const widgetContainer = document.getElementById('telegram-login-widget');
    if (widgetContainer) {
      widgetContainer.appendChild(script);
    }

    return () => {
      // Cleanup
      if (widgetContainer && script.parentNode === widgetContainer) {
        widgetContainer.removeChild(script);
      }
      delete window.onTelegramAuth;
    };
  }, [onLogin, botUsername]);

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Яндекс GO Регистрация Автомобилей</h1>
        <h2>Панель Администратора</h2>
        <p className="login-description">
          Для доступа к панели администратора необходимо авторизоваться через Telegram
        </p>
        <div id="telegram-login-widget"></div>
        <p className="login-note">
          ⚠️ Доступ разрешен только администраторам системы
        </p>
      </div>
    </div>
  );
}

export default Login;
