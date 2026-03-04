module.exports = {
  apps: [{
    name: 'video-bot',
    script: './app/main.py',
    cwd: '/home/srzwyuu/video-bot',
    interpreter: '/usr/bin/python3',
    env: {
      PATH: '/usr/local/bin:/usr/bin:/bin'
    },
    log_file: '/tmp/flask.log',
    out_file: '/tmp/flask-out.log',
    error_file: '/tmp/flask-error.log',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    restart_delay: 3000
  }]
};
