module.exports = {
  apps: [{
    name: 'dozero-auto',
    script: '/home/ubuntu/dozero/auto.py',
    interpreter: 'python3',
    cwd: '/home/ubuntu/dozero',
    cron_restart: '*/30 * * * *',
    autorestart: false,
    restart_delay: 0,
    max_restarts: 1,
    min_uptime: '30m',
    exec_mode: 'fork',
    env: {
      DOZERO_ENV: 'testnet',
    },
  }],
};
