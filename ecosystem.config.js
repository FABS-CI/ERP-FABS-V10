module.exports = {
  apps: [{
    name: 'erp-backend',
    script: './start_gunicorn.sh',
    exec_mode: 'fork',
    autorestart: true,
    env: {
      PORT: 8000,
      PYTHONUNBUFFERED: 1
    }
  }]
};
